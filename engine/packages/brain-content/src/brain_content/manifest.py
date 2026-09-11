from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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


class ExtractionQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["complete", "partial", "failed"]
    failed_pages: list[int]
    warnings: list[str]


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
