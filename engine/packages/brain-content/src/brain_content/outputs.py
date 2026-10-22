"""Versioned run markers; independent of the immutable parse inventory."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from brain_content.contracts import decode_json, validate_contract
from brain_content.manifest import ArtifactVersionUnsupported
from brain_content.validation import ArtifactIntegrityError

RUN_FILES = frozenset({"result.json", "provenance.json", "graph.json", "metadata.json"})


class PipelineIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    name: str = Field(min_length=1)
    package_version: str = Field(min_length=1)
    configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class RunManifestBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    tenant_id: UUID
    knowledge_base_id: UUID
    artifact_id: UUID
    run_id: UUID
    files: dict[str, str]

    @model_validator(mode="after")
    def contract(self) -> Self:
        validate_contract(
            "interpretation-output-manifest.schema.json", self.model_dump(mode="json")
        )
        return self


class RunManifestV1(RunManifestBase):
    contract_version: Literal[1]


class RunManifestV2(RunManifestBase):
    contract_version: Literal[2]
    pipeline: PipelineIdentity
    document_date_selection_id: UUID | None


RunManifest = RunManifestV1 | RunManifestV2


@dataclass(frozen=True)
class VerifiedRun:
    manifest: RunManifest
    manifest_bytes: bytes
    files: Mapping[str, bytes]


def parse_run_manifest(raw: bytes) -> RunManifest:
    try:
        value = decode_json(raw)
        if not isinstance(value, dict):
            raise ValueError("invalid run marker")
        version = value.get("contract_version")
        if type(version) is not int or version not in (1, 2):
            raise ArtifactVersionUnsupported("ARTIFACT_VERSION_UNSUPPORTED")
        validate_contract("interpretation-output-manifest.schema.json", value)
        return (
            RunManifestV1.model_validate(value)
            if version == 1
            else RunManifestV2.model_validate(value)
        )
    except ArtifactVersionUnsupported:
        raise
    except ValueError:
        raise ArtifactIntegrityError("invalid run marker") from None
