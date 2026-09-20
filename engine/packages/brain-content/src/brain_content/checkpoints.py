"""Verified synchronous publication boundary for blocking document workers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from uuid import UUID

from brain_content.manifest import ArtifactManifest
from brain_content.object_store import ObjectAlreadyExistsError, ObjectNotFoundError, ObjectStore


class ArtifactIntegrityError(RuntimeError):
    pass


class CheckpointStore:
    """ContentArtifactStore namespace with retry-safe, manifest-last publication.

    Authorization belongs to the application service. Scope checks and hashes
    remain mandatory here even when the caller has already authorized the read.
    """

    def __init__(self, objects: ObjectStore) -> None:
        self.objects = objects

    @staticmethod
    def _scope(manifest: ArtifactManifest, tenant_id: UUID, knowledge_base_id: UUID) -> None:
        if (manifest.tenant_id, manifest.knowledge_base_id) != (tenant_id, knowledge_base_id):
            raise PermissionError("artifact scope mismatch")

    @staticmethod
    def _verify(manifest: ArtifactManifest, files: Mapping[str, bytes]) -> None:
        expected = {entry.path: entry for entry in manifest.files}
        if len(expected) != len(manifest.files) or set(expected) != set(files):
            raise ArtifactIntegrityError("bundle file inventory mismatch")
        for name, entry in expected.items():
            if not name or "/" in name or "\\" in name or name in (".", "..", "manifest.json"):
                raise ArtifactIntegrityError("invalid bundle filename")
            if (
                len(files[name]) != entry.size_bytes
                or hashlib.sha256(files[name]).hexdigest() != entry.sha256
            ):
                raise ArtifactIntegrityError("bundle file hash mismatch")
        digest = hashlib.sha256(
            "".join(expected[p].sha256 for p in sorted(expected)).encode()
        ).hexdigest()
        if digest != manifest.artifact_sha256:
            raise ArtifactIntegrityError("bundle hash mismatch")
        native = expected.get(manifest.docling_document.path)
        if native is None or native.sha256 != manifest.docling_document.sha256:
            raise ArtifactIntegrityError("native document reference mismatch")
        required = {
            "docling-document.json",
            "normalized.md",
            "blocks.jsonl",
            "tables.jsonl",
            "layout.jsonl",
        }
        if not required <= set(expected):
            raise ArtifactIntegrityError("native bundle is incomplete")
        sources = [name for name in files if name.startswith("source.") or name == "source"]
        if sources and (
            len(sources) != 1
            or hashlib.sha256(files[sources[0]]).hexdigest() != manifest.source_sha256
        ):
            raise ArtifactIntegrityError("retained source hash mismatch")

    def _put_identical(self, key: str, data: bytes) -> None:
        try:
            self.objects.create_exclusive(key, data)
        except ObjectAlreadyExistsError:
            if self.objects.read(key) != data:
                raise ArtifactIntegrityError("immutable publication conflict") from None

    def publish(self, manifest: ArtifactManifest, files: Mapping[str, bytes]) -> ArtifactManifest:
        self._verify(manifest, files)
        prefix = f"bundles/{manifest.artifact_id}"
        marker = f"{prefix}/manifest.json"
        if self.objects.exists(marker):
            prior, _ = self.load(
                manifest.artifact_id, manifest.tenant_id, manifest.knowledge_base_id
            )
            comparable = manifest.model_copy(update={"created_at": prior.created_at})
            if comparable != prior:
                raise ArtifactIntegrityError("artifact identity conflict")
            return prior
        for name, data in files.items():
            self._put_identical(f"{prefix}/{name}", data)
        try:
            self.objects.create_exclusive(marker, manifest.model_dump_json().encode())
        except ObjectAlreadyExistsError:
            # A racing publisher may have a different created_at, never different content.
            return self.publish(manifest, files)
        return manifest

    def load(
        self, artifact_id: UUID, tenant_id: UUID, knowledge_base_id: UUID
    ) -> tuple[ArtifactManifest, dict[str, bytes]]:
        prefix = f"bundles/{artifact_id}"
        manifest = ArtifactManifest.model_validate_json(
            self.objects.read(f"{prefix}/manifest.json")
        )
        self._scope(manifest, tenant_id, knowledge_base_id)
        if manifest.artifact_id != artifact_id:
            raise ArtifactIntegrityError("artifact identity mismatch")
        # Validate names before using them as object keys.
        for entry in manifest.files:
            if (
                "/" in entry.path
                or "\\" in entry.path
                or entry.path in ("", ".", "..", "manifest.json")
            ):
                raise ArtifactIntegrityError("invalid bundle filename")
        try:
            files = {
                entry.path: self.objects.read(f"{prefix}/{entry.path}") for entry in manifest.files
            }
        except ObjectNotFoundError:
            raise ArtifactIntegrityError("accepted bundle is missing a file") from None
        self._verify(manifest, files)
        return manifest, files

    def publish_run(
        self,
        *,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        artifact_id: UUID,
        run_id: UUID,
        files: Mapping[str, bytes],
    ) -> str:
        self.load(artifact_id, tenant_id, knowledge_base_id)
        if set(files) != {"result.json", "provenance.json", "graph.json", "metadata.json"}:
            raise ArtifactIntegrityError("run output inventory mismatch")
        prefix = f"runs/{tenant_id}/{knowledge_base_id}/{run_id}"
        inventory = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
        marker = {
            "contract_version": 1,
            "tenant_id": str(tenant_id),
            "knowledge_base_id": str(knowledge_base_id),
            "artifact_id": str(artifact_id),
            "run_id": str(run_id),
            "files": inventory,
        }
        for name, data in files.items():
            self._put_identical(f"{prefix}/{name}", data)
        self._put_identical(f"{prefix}/manifest.json", json.dumps(marker, sort_keys=True).encode())
        return f"{prefix}/manifest.json"

    def load_run(
        self, *, tenant_id: UUID, knowledge_base_id: UUID, artifact_id: UUID, run_id: UUID
    ) -> dict[str, bytes]:
        self.load(artifact_id, tenant_id, knowledge_base_id)
        prefix = f"runs/{tenant_id}/{knowledge_base_id}/{run_id}"
        marker = json.loads(self.objects.read(f"{prefix}/manifest.json"))
        if (
            any(
                marker.get(key) != str(value)
                for key, value in {
                    "tenant_id": tenant_id,
                    "knowledge_base_id": knowledge_base_id,
                    "artifact_id": artifact_id,
                    "run_id": run_id,
                }.items()
            )
            or marker.get("contract_version") != 1
        ):
            raise ArtifactIntegrityError("run identity mismatch")
        if set(marker["files"]) != {
            "result.json",
            "provenance.json",
            "graph.json",
            "metadata.json",
        }:
            raise ArtifactIntegrityError("run output inventory mismatch")
        try:
            files = {name: self.objects.read(f"{prefix}/{name}") for name in marker["files"]}
        except ObjectNotFoundError:
            raise ArtifactIntegrityError("accepted run is missing a file") from None
        if any(
            hashlib.sha256(data).hexdigest() != marker["files"][name]
            for name, data in files.items()
        ):
            raise ArtifactIntegrityError("run output hash mismatch")
        return files
