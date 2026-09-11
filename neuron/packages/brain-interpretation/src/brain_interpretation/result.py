from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

Precision = Literal["span", "table_cell", "block", "page", "document", "unresolved"]
InterpretationBasis = Literal["EXPLICIT", "INFERRED", "AMBIGUOUS"]


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int
    x0: float
    y0: float
    x1: float
    y1: float


class EvidenceBinding(BaseModel):
    """Matches `planning-mds/schemas/interpretation-result.schema.json`."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: UUID
    block_id: str | None = None
    page: int | None = None
    bbox: BoundingBox | None = None
    char_start: int | None = None
    char_end: int | None = None
    precision: Precision


class CandidateEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    entity_type: str
    label: str
    evidence: list[EvidenceBinding]


class CandidateRelationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    relationship_type: str
    subject_id: UUID
    object_id: UUID
    evidence: list[EvidenceBinding]


class CandidateAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    subject_type: str
    slot_type: str
    value: dict
    evidence: list[EvidenceBinding]
    model_confidence: float | None
    interpretation_basis: InterpretationBasis


class RunConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend: Literal["openai_compatible"]
    model_id: str
    model_revision: str | None
    endpoint_hash: str
    prompt_hash: str
    schema_hash: str
    context_limit: int
    profile_id: str
    profile_version: str


class Counters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversion_calls: int = 0
    ocr_calls: int = 0
    model_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0


class InterpretationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: UUID
    artifact_id: UUID
    status: Literal["complete", "partial", "failed"]
    entities: list[CandidateEntity]
    assertions: list[CandidateAssertion]
    relationships: list[CandidateRelationship]
    quality_signals: dict[str, float]
    warnings: list[str]
    failed_chunks: list[str]
    run_configuration: RunConfiguration
    counters: Counters
    provenance_ledger_ref: str | None
    created_at: datetime
