"""Source-claim carriers. None of these values establishes canonical truth."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

type Kind = Literal["OPEN_STATEMENT", "TYPED_ASSERTION"]
type Mode = Literal["ASSERTED", "OBSERVED", "DERIVED"]
type Origin = Literal[
    "DOCUMENT_INTERPRETATION",
    "SYSTEM_OBSERVATION",
    "HUMAN_REVIEW",
    "CONVERSATION_DISCOVERY",
    "RULE_DERIVATION",
    "AGENT_ANALYSIS",
]
type Basis = Literal["EXPLICIT", "INFERRED", "AMBIGUOUS"]
type Json = None | bool | int | float | str | list[Json] | dict[str, Json]


@dataclass(frozen=True)
class EvidenceClaim:
    artifact_id: UUID
    block_id: str
    quote: str
    model_selector: Mapping[str, Json] | None = None


@dataclass(frozen=True)
class EntityReference:
    id: UUID
    entity_type: str
    label: str
    introducing_evidence: tuple[EvidenceClaim, ...]


@dataclass(frozen=True)
class EntityObject:
    kind: Literal["ENTITY"]
    ref: UUID
    name: str


@dataclass(frozen=True)
class LiteralObject:
    kind: Literal["LITERAL"]
    value: Json


@dataclass(frozen=True)
class AssertionCandidate:
    id: UUID
    assertion_kind: Kind
    subject_ref: UUID
    object: EntityObject | LiteralObject
    predicate_id: str | None
    ontology_release: str | None
    source_relation: str | None
    qualifiers: Mapping[str, Json]
    time_mention_refs: tuple[UUID, ...]
    valid_time_claim: Mapping[str, Json] | None
    mode: Mode
    origin: Origin
    interpretation_basis: Basis
    model_confidence: float | None
    evidence: tuple[EvidenceClaim, ...]


@dataclass(frozen=True)
class ProducerContext:
    tenant_id: UUID
    knowledge_base_id: UUID
    actor_id: UUID
    artifact_id: UUID
    document_version_id: UUID
    run_id: UUID
    origin: Origin
    model_id: str
    prompt_hash: str
    trace_id: str


@dataclass(frozen=True)
class VerifiedBlock:
    artifact_id: UUID
    block_id: str
    text: str
    native_selector: Mapping[str, Json]
    text_origin: Literal["STATED", "OCR", "TRANSCRIBED", "DESCRIBED"] | None
    origin_qualification: Literal["qualified", "legacy_unqualified"]
    producer: Mapping[str, Json] | None
    producer_confidence: float | None


@dataclass(frozen=True)
class TimeReference:
    id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID
    artifact_id: UUID
    block_id: str
    words: str


@dataclass(frozen=True)
class SourceAccessProof:
    tenant_id: UUID
    knowledge_base_id: UUID
    unit_of_work_id: UUID
    source_artifact_ids: tuple[UUID, ...]
    authorization_decision_ids: tuple[UUID, ...]
