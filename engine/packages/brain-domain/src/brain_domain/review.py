from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

# ADR-0058's anchoring/selector precision vocabulary is a deliberate, related-but-distinct
# extension of section 108.2's interpretation-time precision (brain_interpretation.result
# .Precision: span/table_cell/block/page/document/unresolved). Do not unify the two — see
# `brain_review.decisions.to_evidence_locator_precision` for the mapping between them.
EvidenceLocatorPrecision = Literal[
    "exact-span", "table-cell", "block", "page", "document", "unresolved"
]


class ReviewItemType(StrEnum):
    LOW_CONFIDENCE_ASSERTION = "LOW_CONFIDENCE_ASSERTION"
    EXTRACTION_CORRECTION = "EXTRACTION_CORRECTION"
    PROVENANCE_CORRECTION = "PROVENANCE_CORRECTION"
    ENTITY_CORRECTION = "ENTITY_CORRECTION"
    RELATIONSHIP_CORRECTION = "RELATIONSHIP_CORRECTION"


class ReviewItemStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    DECIDED = "decided"
    STALE = "stale"
    BLOCKED = "blocked"


class ReviewDecisionAction(StrEnum):
    ACCEPT = "ACCEPT"
    CORRECT = "CORRECT"
    REJECT = "REJECT"
    BLOCKED = "BLOCKED"


class ReviewDecisionReasonCode(StrEnum):
    MISREAD_VALUE = "MISREAD_VALUE"
    WRONG_REGION = "WRONG_REGION"
    NOT_IN_SOURCE = "NOT_IN_SOURCE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    EVIDENCE_UNRESOLVED = "EVIDENCE_UNRESOLVED"


@dataclass(frozen=True, slots=True)
class EvidenceLocator:
    """Where an assertion is grounded in the immutable artifact (ADR-0058)."""

    source: str  # immutable Nebula artifact identity (artifact_id, as a string)
    precision: EvidenceLocatorPrecision
    part: str | None = None
    unresolved_reason: str | None = None
    selector: tuple[dict, ...] = ()


@dataclass(frozen=True, slots=True)
class ReviewItem:
    id: UUID
    type: ReviewItemType
    status: ReviewItemStatus
    assertion_id: UUID
    assertion_version: int
    tenant_id: UUID
    knowledge_base_id: UUID
    created_at: datetime
    review_batch_id: UUID | None = None
    evidence: EvidenceLocator | None = None


@dataclass(frozen=True, slots=True)
class ReviewBatch:
    id: UUID
    review_item_ids: tuple[UUID, ...]
    assembled_at: datetime
    assembling_principal_id: UUID


@dataclass(frozen=True, slots=True)
class ReviewDecision:
    id: UUID
    review_item_id: UUID
    review_batch_id: UUID
    action: ReviewDecisionAction
    reviewer_principal_id: UUID
    decided_at: datetime
    assertion_version: int
    stale: bool
    event_sha256: str
    reason_code: ReviewDecisionReasonCode | None = None
    corrected_value: dict | None = None
    corrected_assertion_id: UUID | None = None
    evidence: EvidenceLocator | None = None
    reviewer_comment: str | None = None
