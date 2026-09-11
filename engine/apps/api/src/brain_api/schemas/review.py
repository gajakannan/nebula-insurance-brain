from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from brain_domain.review import EvidenceLocator, ReviewDecision, ReviewItem
from pydantic import BaseModel, ConfigDict

Precision = Literal["exact-span", "table-cell", "block", "page", "document", "unresolved"]
Action = Literal["ACCEPT", "CORRECT", "REJECT", "BLOCKED"]
ReasonCode = Literal[
    "MISREAD_VALUE", "WRONG_REGION", "NOT_IN_SOURCE", "OUT_OF_SCOPE", "EVIDENCE_UNRESOLVED"
]


class EvidenceLocatorOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    precision: Precision
    part: str | None = None
    unresolved_reason: str | None = None
    selector: list[dict] = []

    @classmethod
    def from_domain(cls, locator: EvidenceLocator | None) -> EvidenceLocatorOut | None:
        if locator is None:
            return None
        return cls(
            source=locator.source,
            precision=locator.precision,
            part=locator.part,
            unresolved_reason=locator.unresolved_reason,
            selector=list(locator.selector),
        )


class ReviewDecisionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    review_item_id: UUID
    review_batch_id: UUID
    action: Action
    reason_code: ReasonCode | None
    corrected_value: dict | None
    corrected_assertion_id: UUID | None
    evidence: EvidenceLocatorOut | None
    reviewer_principal_id: UUID
    reviewer_comment: str | None
    decided_at: datetime
    assertion_version: int
    stale: bool
    event_sha256: str

    @classmethod
    def from_domain(cls, decision: ReviewDecision) -> ReviewDecisionOut:
        return cls(
            id=decision.id,
            review_item_id=decision.review_item_id,
            review_batch_id=decision.review_batch_id,
            action=decision.action.value,
            reason_code=decision.reason_code.value if decision.reason_code else None,
            corrected_value=decision.corrected_value,
            corrected_assertion_id=decision.corrected_assertion_id,
            evidence=EvidenceLocatorOut.from_domain(decision.evidence),
            reviewer_principal_id=decision.reviewer_principal_id,
            reviewer_comment=decision.reviewer_comment,
            decided_at=decision.decided_at,
            assertion_version=decision.assertion_version,
            stale=decision.stale,
            event_sha256=decision.event_sha256,
        )


class ReviewItemOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    type: str
    status: str
    assertion_id: UUID
    assertion_version: int
    tenant_id: UUID
    knowledge_base_id: UUID
    review_batch_id: UUID | None = None
    evidence: EvidenceLocatorOut | None = None
    decision: ReviewDecisionOut | None = None
    created_at: datetime

    @classmethod
    def from_domain(cls, item: ReviewItem, decision: ReviewDecision | None) -> ReviewItemOut:
        return cls(
            id=item.id,
            type=item.type.value,
            status=item.status.value,
            assertion_id=item.assertion_id,
            assertion_version=item.assertion_version,
            tenant_id=item.tenant_id,
            knowledge_base_id=item.knowledge_base_id,
            review_batch_id=item.review_batch_id,
            evidence=EvidenceLocatorOut.from_domain(item.evidence),
            decision=ReviewDecisionOut.from_domain(decision) if decision else None,
            created_at=item.created_at,
        )


class ReviewDecisionIn(BaseModel):
    """Request body shape for one decision in a `ReviewDecisionBatch`.
    `reviewer_principal_id` is never accepted from the client — it always comes
    from the authenticated session (ADR-0049, ADR-0057)."""

    model_config = ConfigDict(extra="forbid")

    review_item_id: UUID
    action: Action
    assertion_version: int
    reason_code: ReasonCode | None = None
    corrected_value: dict | None = None
    evidence: EvidenceLocatorOut | None = None
    reviewer_comment: str | None = None


class ReviewDecisionBatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decisions: list[ReviewDecisionIn]


class ReviewDecisionReceiptOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_ids: list[UUID] = []
    applied: int = 0
    duplicate: bool = False
    stale: int = 0
    blocked: int = 0
