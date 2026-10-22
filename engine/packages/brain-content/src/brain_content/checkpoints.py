"""Verified synchronous publication boundary for blocking document workers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal
from uuid import UUID

from brain_content.manifest import ArtifactManifest, Manifest
from brain_content.object_store import ObjectAlreadyExistsError, ObjectNotFoundError, ObjectStore
from brain_content.outputs import (
    RUN_FILES,
    PipelineIdentity,
    RunManifest,
    RunManifestV1,
    RunManifestV2,
    VerifiedRun,
    parse_run_manifest,
)
from brain_content.validation import (
    ArtifactIntegrityError,
    ArtifactKey,
    VerifiedBundle,
    verify_bundle,
)
from brain_content.verified_store import VerifiedBundleStore


class CheckpointStore:
    """ContentArtifactStore namespace with retry-safe, manifest-last publication.

    Authorization belongs to the application service. Scope checks and hashes
    remain mandatory here even when the caller has already authorized the read.
    """

    def __init__(self, objects: ObjectStore) -> None:
        self.objects = objects
        self.verified = VerifiedBundleStore(objects)

    @staticmethod
    def _scope(manifest: Manifest, tenant_id: UUID, knowledge_base_id: UUID) -> None:
        if (manifest.tenant_id, manifest.knowledge_base_id) != (tenant_id, knowledge_base_id):
            raise PermissionError("artifact scope mismatch")

    @staticmethod
    def _verify(manifest: Manifest, files: Mapping[str, bytes]) -> None:
        key = ArtifactKey(
            manifest.artifact_id,
            manifest.tenant_id,
            manifest.knowledge_base_id,
            manifest.artifact_contract_version,
        )
        verify_bundle(key, manifest.model_dump_json().encode(), files)

    def _put_identical(self, key: str, data: bytes) -> None:
        try:
            self.objects.create_exclusive(key, data)
        except ObjectAlreadyExistsError:
            if self.objects.read(key) != data:
                raise ArtifactIntegrityError("immutable publication conflict") from None

    def publish[M: Manifest](self, manifest: M, files: Mapping[str, bytes]) -> M:
        key = ArtifactKey(
            manifest.artifact_id,
            manifest.tenant_id,
            manifest.knowledge_base_id,
            manifest.artifact_contract_version,
        )
        bundle = self.verified.publish(key, manifest.model_dump_json().encode(), files)
        assert isinstance(bundle.manifest, type(manifest))
        return bundle.manifest

    def load_verified(self, key: ArtifactKey) -> VerifiedBundle:
        return self.verified.load_verified(key)

    def load(
        self, artifact_id: UUID, tenant_id: UUID, knowledge_base_id: UUID
    ) -> tuple[ArtifactManifest, dict[str, bytes]]:
        bundle = self.load_verified(ArtifactKey(artifact_id, tenant_id, knowledge_base_id, 1))
        assert isinstance(bundle.manifest, ArtifactManifest)
        return bundle.manifest, dict(bundle.files)

    def publish_run(
        self,
        *,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        artifact_id: UUID,
        run_id: UUID,
        files: Mapping[str, bytes],
        artifact_key: ArtifactKey | None = None,
        output_contract_version: Literal[1, 2] = 1,
        pipeline: PipelineIdentity | None = None,
        document_date_selection_id: UUID | None = None,
    ) -> str:
        self._run_artifact(artifact_id, tenant_id, knowledge_base_id, artifact_key)
        if set(files) != RUN_FILES:
            raise ArtifactIntegrityError("run output inventory mismatch")
        prefix = f"runs/{tenant_id}/{knowledge_base_id}/{run_id}"
        inventory = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
        identity = dict(
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
            artifact_id=artifact_id,
            run_id=run_id,
            files=inventory,
        )
        if output_contract_version == 1:
            if pipeline is not None or document_date_selection_id is not None:
                raise ValueError("v1 run output has no pipeline/date selection fields")
            marker: RunManifest = RunManifestV1(contract_version=1, **identity)
        elif output_contract_version == 2 and pipeline is not None:
            marker = RunManifestV2(
                contract_version=2,
                pipeline=pipeline,
                document_date_selection_id=document_date_selection_id,
                **identity,
            )
        else:
            raise ValueError("v2 run output requires a pipeline identity")
        for name, data in files.items():
            self._put_identical(f"{prefix}/{name}", data)
        # Preserve the established v1 wire serialization and all prior markers.
        self._put_identical(
            f"{prefix}/manifest.json",
            json.dumps(marker.model_dump(mode="json"), sort_keys=True).encode(),
        )
        return f"{prefix}/manifest.json"

    def _run_artifact(
        self,
        artifact_id: UUID,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        key: ArtifactKey | None,
    ) -> VerifiedBundle:
        key = key or ArtifactKey(artifact_id, tenant_id, knowledge_base_id, 1)
        if (key.artifact_id, key.tenant_id, key.knowledge_base_id) != (
            artifact_id,
            tenant_id,
            knowledge_base_id,
        ):
            raise PermissionError("run artifact key has another owner")
        return self.load_verified(key)

    def load_run(
        self,
        *,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        artifact_id: UUID,
        run_id: UUID,
        artifact_key: ArtifactKey | None = None,
    ) -> dict[str, bytes]:
        return dict(
            self.load_run_bundle(
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                artifact_id=artifact_id,
                run_id=run_id,
                artifact_key=artifact_key,
            ).files
        )

    def load_run_bundle(
        self,
        *,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        artifact_id: UUID,
        run_id: UUID,
        artifact_key: ArtifactKey | None = None,
    ) -> VerifiedRun:
        self._run_artifact(artifact_id, tenant_id, knowledge_base_id, artifact_key)
        prefix = f"runs/{tenant_id}/{knowledge_base_id}/{run_id}"
        raw = self.objects.read(f"{prefix}/manifest.json")
        marker = parse_run_manifest(raw)
        if (marker.tenant_id, marker.knowledge_base_id, marker.artifact_id, marker.run_id) != (
            tenant_id,
            knowledge_base_id,
            artifact_id,
            run_id,
        ):
            raise ArtifactIntegrityError("run identity mismatch")
        try:
            files = {name: self.objects.read(f"{prefix}/{name}") for name in marker.files}
        except ObjectNotFoundError:
            raise ArtifactIntegrityError("accepted run is missing a file") from None
        if set(self.objects.list_keys(prefix)) != {
            f"{prefix}/{name}" for name in RUN_FILES | {"manifest.json"}
        }:
            raise ArtifactIntegrityError("run output inventory mismatch")
        if any(
            hashlib.sha256(data).hexdigest() != marker.files[name] for name, data in files.items()
        ):
            raise ArtifactIntegrityError("run output hash mismatch")
        return VerifiedRun(marker, raw, MappingProxyType(files))
