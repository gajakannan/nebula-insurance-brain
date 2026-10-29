from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StrictInt, model_validator

from brain_content.contracts import decode_json, validate_contract, wire_value


class ArtifactFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str
    size_bytes: int


class DoclingDocumentRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    schema_version: str
    sha256: str


class ExecutionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parser_package_version: str
    model_artifact_digests: list[str]
    configuration_hash: str
    environment_digest: str


class OcrEngine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    model: str | None
    model_version: str | None


class OcrQuality(BaseModel):
    """OCR observed during one conversion (F0005-S0001-AC2, ADR-0073 amendment).

    `engine` is None when OCR is configured but its engine or assets cannot be
    identified; it is never guessed.
    """

    model_config = ConfigDict(extra="forbid")

    page_count: StrictInt
    pages: list[StrictInt]
    engine: OcrEngine | None

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if self.pages != sorted(set(self.pages)) or any(page < 1 for page in self.pages):
            raise ValueError("OCR pages must be sorted, unique and 1-based")
        if self.page_count != len(self.pages):
            raise ValueError("OCR page count must equal the observed pages")
        return self


class ExtractionQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["complete", "partial", "failed"]
    failed_pages: list[int]
    warnings: list[str]
    # Optional and add-only: historical bundles omit it, meaning "not observed".
    ocr: OcrQuality | None = None


class ArtifactManifest(BaseModel):
    """Matches `planning-mds/schemas/content-artifact-manifest.schema.json`."""

    model_config = ConfigDict(extra="forbid")

    artifact_contract_version: Literal[1]
    tenant_id: UUID
    knowledge_base_id: UUID
    document_id: UUID
    version_id: UUID
    artifact_id: UUID
    source_sha256: str
    artifact_sha256: str
    docling_document: DoclingDocumentRef
    files: list[ArtifactFile]
    execution: ExecutionRecord
    extraction_quality: ExtractionQuality
    page_count: int
    coordinate_origin: Literal["top_left"] = "top_left"
    offset_encoding: Literal["unicode_code_points"] = "unicode_code_points"
    created_at: datetime


# Keep the original import and model intact for legacy producers/consumers.
ArtifactManifestV1 = ArtifactManifest


class ParserExecutionV2(ExecutionRecord):
    parser_name: Literal["docling"]
    projection_version: str


class ArtifactManifestV2(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    artifact_contract_version: Literal[2]
    tenant_id: UUID
    knowledge_base_id: UUID
    document_id: UUID
    version_id: UUID
    artifact_id: UUID
    source_sha256: str
    artifact_sha256: str
    docling_document: DoclingDocumentRef
    files: list[ArtifactFile]
    execution: ParserExecutionV2
    extraction_quality: ExtractionQuality
    page_count: StrictInt
    coordinate_origin: Literal["top_left"]
    offset_encoding: Literal["unicode_code_points"]
    created_at: datetime
    source_file: Literal["source.pdf"]
    recipe_sha256: str
    bundle_hash_algorithm: Literal["sha256-file-inventory-v2"]
    record_contract_version: Literal[2]
    page_number_base: Literal[1]
    coordinate_units: Literal["pdf_points"]
    text_normalization_version: Literal["identity-unicode-v1"]

    @model_validator(mode="before")
    @classmethod
    def input_contract(cls, value: Any) -> Any:
        validate_contract("content-artifact-manifest-v2.schema.json", wire_value(value))
        return value

    @model_validator(mode="after")
    def contract(self) -> Self:
        validate_contract("content-artifact-manifest-v2.schema.json", self.model_dump(mode="json"))
        return self


Manifest = ArtifactManifestV1 | ArtifactManifestV2


class ArtifactVersionUnsupported(ValueError):
    pass


def parse_manifest(raw: bytes) -> Manifest:
    value = decode_json(raw)
    if not isinstance(value, dict):
        raise ValueError("CONTENT_CONTRACT_INVALID")
    version = value.get("artifact_contract_version")
    if type(version) is not int or version not in (1, 2):
        raise ArtifactVersionUnsupported("ARTIFACT_VERSION_UNSUPPORTED")
    name = (
        "content-artifact-manifest.schema.json"
        if version == 1
        else "content-artifact-manifest-v2.schema.json"
    )
    validate_contract(name, value)
    return (
        ArtifactManifestV1.model_validate(value)
        if version == 1
        else ArtifactManifestV2.model_validate(value)
    )
