"""Content metadata ports. Authority and the transaction belong to the caller."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

from brain_content.validation import ArtifactIntegrityError, ArtifactKey, VerifiedBundle


@dataclass(frozen=True)
class ArtifactMetadata:
    key: ArtifactKey
    document_id: UUID
    version_id: UUID
    source_sha256: str
    artifact_sha256: str
    manifest_sha256: str | None
    recipe_sha256: str | None
    publication_state: Literal["legacy_unverified", "ready", "quarantined"]

    def verify_identity(self, bundle: VerifiedBundle) -> None:
        manifest = bundle.manifest
        if self.publication_state == "quarantined":
            raise ArtifactIntegrityError("artifact is quarantined")
        if (
            bundle.key != self.key
            or manifest.document_id != self.document_id
            or manifest.version_id != self.version_id
            or manifest.source_sha256 != self.source_sha256
            or manifest.artifact_sha256 != self.artifact_sha256
            or (self.manifest_sha256 is not None and self.manifest_sha256 != bundle.manifest_sha256)
            or (
                self.key.contract_version == 2
                and (
                    self.manifest_sha256 is None
                    or self.recipe_sha256 != getattr(manifest, "recipe_sha256", None)
                )
            )
        ):
            raise ArtifactIntegrityError("artifact metadata disagrees with retained bytes")


class ArtifactRepository(Protocol):
    def find_source(
        self, tenant_id: UUID, knowledge_base_id: UUID, source_sha256: str
    ) -> tuple[UUID, tuple[ArtifactKey, ...]] | None: ...

    def get_key(self, artifact_id: UUID) -> ArtifactKey: ...

    def get_metadata(self, artifact_id: UUID) -> ArtifactMetadata: ...

    def register_ready(
        self,
        bundle: VerifiedBundle,
        *,
        actor_id: UUID,
        authorization_decision_id: UUID,
        supersedes_artifact_id: UUID | None,
    ) -> None: ...


class VerifiedContentStore(Protocol):
    def publish(
        self, key: ArtifactKey, manifest_bytes: bytes, files: Mapping[str, bytes]
    ) -> VerifiedBundle: ...

    def load_verified(self, key: ArtifactKey) -> VerifiedBundle: ...
