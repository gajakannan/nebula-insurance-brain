from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Protocol
from uuid import UUID

from brain_content.manifest import ArtifactManifest, Manifest, parse_manifest
from brain_content.object_store import LocalFilesystemObjectStore, ObjectNotFoundError
from brain_content.validation import ArtifactConflict, ArtifactKey, VerifiedBundle
from brain_content.verified_store import VerifiedBundleStore

ArtifactExists = ArtifactConflict


class ArtifactNotFound(Exception):
    pass


class ContentArtifactStore(Protocol):
    async def load_verified(self, key: ArtifactKey) -> VerifiedBundle: ...

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
        self._verified = VerifiedBundleStore(object_store)

    def _bundle_prefix(self, artifact_id: UUID) -> str:
        return f"bundles/{artifact_id}"

    async def put_bundle[M: Manifest](self, manifest: M, files: Mapping[str, bytes]) -> M:
        key = ArtifactKey(
            manifest.artifact_id,
            manifest.tenant_id,
            manifest.knowledge_base_id,
            manifest.artifact_contract_version,
        )
        bundle = await self.publish_verified(key, manifest.model_dump_json().encode(), files)
        # The verified version discriminator guarantees the concrete model type.
        assert isinstance(bundle.manifest, type(manifest))
        return bundle.manifest

    async def publish_verified(
        self, key: ArtifactKey, manifest_bytes: bytes, files: Mapping[str, bytes]
    ) -> VerifiedBundle:
        return await asyncio.to_thread(self._verified.publish, key, manifest_bytes, files)

    async def load_verified(self, key: ArtifactKey) -> VerifiedBundle:
        return await asyncio.to_thread(self._verified.load_verified, key)

    async def get_manifest(self, artifact_id: UUID) -> ArtifactManifest:
        def _read() -> ArtifactManifest:
            try:
                raw = self._object_store.read(f"{self._bundle_prefix(artifact_id)}/manifest.json")
            except ObjectNotFoundError as exc:
                raise ArtifactNotFound(str(artifact_id)) from exc
            manifest = parse_manifest(raw)
            key = ArtifactKey(artifact_id, manifest.tenant_id, manifest.knowledge_base_id, 1)
            bundle = self._verified.load_verified(key)
            assert isinstance(bundle.manifest, ArtifactManifest)
            return bundle.manifest

        return await asyncio.to_thread(_read)

    async def open_file(self, artifact_id: UUID, path: str) -> bytes:
        manifest = await self.get_manifest(artifact_id)
        key = ArtifactKey(artifact_id, manifest.tenant_id, manifest.knowledge_base_id, 1)
        bundle = await self.load_verified(key)
        try:
            return bundle.files[path]
        except KeyError:
            raise ArtifactNotFound(str(artifact_id)) from None
