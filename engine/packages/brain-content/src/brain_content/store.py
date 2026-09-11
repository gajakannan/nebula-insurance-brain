from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Protocol
from uuid import UUID

from brain_content.manifest import ArtifactManifest
from brain_content.object_store import LocalFilesystemObjectStore, ObjectAlreadyExistsError


class ArtifactExists(Exception):
    """Raised by `put_bundle` when the artifact was already accepted (immutability, ADR-0059)."""


class ArtifactNotFound(Exception):
    pass


class ContentArtifactStore(Protocol):
    async def put_bundle(
        self, manifest: ArtifactManifest, files: Mapping[str, bytes]
    ) -> ArtifactManifest: ...

    async def get_manifest(self, artifact_id: UUID) -> ArtifactManifest: ...

    async def open_file(self, artifact_id: UUID, path: str) -> bytes: ...


class LocalContentArtifactStore:
    """`ContentArtifactStore` over `LocalFilesystemObjectStore` (F0001-S0003).

    Bundle layout: `bundles/{artifact_id}/{path}`, with `manifest.json` written last
    as the completion marker — a bundle with files but no manifest is never readable
    as an accepted artifact (ADR-0059's manifest-last protocol).
    """

    def __init__(self, object_store: LocalFilesystemObjectStore) -> None:
        self._object_store = object_store

    def _bundle_prefix(self, artifact_id: UUID) -> str:
        return f"bundles/{artifact_id}"

    async def put_bundle(
        self, manifest: ArtifactManifest, files: Mapping[str, bytes]
    ) -> ArtifactManifest:
        prefix = self._bundle_prefix(manifest.artifact_id)
        manifest_key = f"{prefix}/manifest.json"

        def _write() -> None:
            if self._object_store.exists(manifest_key):
                raise ArtifactExists(str(manifest.artifact_id))
            for relative_path, data in files.items():
                self._object_store.create_exclusive(f"{prefix}/{relative_path}", data)
            try:
                self._object_store.create_exclusive(
                    manifest_key, manifest.model_dump_json(indent=2).encode("utf-8")
                )
            except ObjectAlreadyExistsError as exc:
                raise ArtifactExists(str(manifest.artifact_id)) from exc

        await asyncio.to_thread(_write)
        return manifest

    async def get_manifest(self, artifact_id: UUID) -> ArtifactManifest:
        manifest_key = f"{self._bundle_prefix(artifact_id)}/manifest.json"

        def _read() -> ArtifactManifest:
            try:
                raw = self._object_store.read(manifest_key)
            except Exception as exc:  # noqa: BLE001 — translated to the store's own error type
                raise ArtifactNotFound(str(artifact_id)) from exc
            return ArtifactManifest.model_validate_json(raw)

        return await asyncio.to_thread(_read)

    async def open_file(self, artifact_id: UUID, path: str) -> bytes:
        key = f"{self._bundle_prefix(artifact_id)}/{path}"

        def _read() -> bytes:
            try:
                return self._object_store.read(key)
            except Exception as exc:  # noqa: BLE001
                raise ArtifactNotFound(f"{artifact_id}/{path}") from exc

        return await asyncio.to_thread(_read)
