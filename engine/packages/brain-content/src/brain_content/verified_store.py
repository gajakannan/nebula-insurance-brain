"""Immutable manifest-last byte publication behind both content adapters."""

from __future__ import annotations

from collections.abc import Mapping

from brain_content.manifest import ArtifactVersionUnsupported, parse_manifest
from brain_content.object_store import ObjectAlreadyExistsError, ObjectNotFoundError, ObjectStore
from brain_content.validation import (
    ArtifactConflict,
    ArtifactIntegrityError,
    ArtifactKey,
    VerifiedBundle,
    valid_path,
    verify_bundle,
)


class VerifiedBundleStore:
    def __init__(self, objects: ObjectStore):
        self.objects = objects

    def load_verified(self, key: ArtifactKey) -> VerifiedBundle:
        try:
            return self._load_verified(key)
        except ArtifactVersionUnsupported:
            raise
        except ValueError:
            raise ArtifactIntegrityError("unsafe or malformed retained content") from None

    def _load_verified(self, key: ArtifactKey) -> VerifiedBundle:
        marker = f"{key.prefix}/manifest.json"
        raw = self.objects.read(marker)
        try:
            manifest = parse_manifest(raw)
        except ArtifactVersionUnsupported:
            raise
        except ValueError:
            raise ArtifactIntegrityError("invalid manifest") from None
        if (manifest.tenant_id, manifest.knowledge_base_id) != (
            key.tenant_id,
            key.knowledge_base_id,
        ):
            raise PermissionError("artifact scope mismatch")
        if (
            manifest.artifact_id != key.artifact_id
            or manifest.artifact_contract_version != key.contract_version
        ):
            raise ArtifactIntegrityError("artifact identity mismatch")
        if any(not valid_path(entry.path, key.contract_version) for entry in manifest.files):
            raise ArtifactIntegrityError("invalid bundle filename")
        try:
            files = {
                entry.path: self.objects.read(f"{key.prefix}/{entry.path}")
                for entry in manifest.files
            }
        except ObjectNotFoundError:
            raise ArtifactIntegrityError("accepted bundle is missing a file") from None
        declared = {f"{key.prefix}/{path}" for path in files} | {marker}
        if set(self.objects.list_keys(key.prefix)) != declared:
            raise ArtifactIntegrityError("bundle file inventory mismatch")
        return verify_bundle(key, raw, files)

    def publish(
        self, key: ArtifactKey, manifest_bytes: bytes, files: Mapping[str, bytes]
    ) -> VerifiedBundle:
        incoming = verify_bundle(key, manifest_bytes, files)
        marker = f"{key.prefix}/manifest.json"
        if self.objects.exists(marker):
            prior = self.load_verified(key)
            comparable = incoming.manifest.model_copy(
                update={"created_at": prior.manifest.created_at}
            )
            if comparable != prior.manifest or dict(files) != dict(prior.files):
                raise ArtifactConflict("artifact identity conflict")
            return prior
        for path, data in files.items():
            try:
                self.objects.create_exclusive(f"{key.prefix}/{path}", data)
            except ObjectAlreadyExistsError:
                if self.objects.read(f"{key.prefix}/{path}") != data:
                    raise ArtifactConflict("immutable publication conflict") from None
        try:
            self.objects.create_exclusive(marker, manifest_bytes)
        except ObjectAlreadyExistsError:
            # The winning publisher's exact marker bytes and timestamp survive.
            return self.publish(key, manifest_bytes, files)
        return self.load_verified(key)
