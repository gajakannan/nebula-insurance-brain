from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from brain_domain.review import EvidenceLocator, ReviewItem, ReviewItemStatus, ReviewItemType

#: Below this model-reported confidence, an assertion is routed to review
#: (F0001-S0004 acceptance criterion: confidence 0.41 against a review policy).
#: Not a calibrated probability threshold (business rule 3) — a proof-scope cutoff;
#: F0026 owns the real extraction-quality thresholds.
LOW_CONFIDENCE_THRESHOLD = 0.5


class ReviewItemSink(Protocol):
    async def create(self, item: ReviewItem) -> None: ...


def route_low_confidence_assertion(
    *,
    assertion_id: UUID,
    assertion_version: int,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    model_confidence: float,
    evidence: EvidenceLocator,
) -> ReviewItem | None:
    """Returns a `ReviewItem` when the review policy routes this assertion, else
    `None`. The only policy modeled at proof scope is the confidence threshold."""
    if model_confidence >= LOW_CONFIDENCE_THRESHOLD:
        return None
    return ReviewItem(
        id=uuid4(),
        type=ReviewItemType.LOW_CONFIDENCE_ASSERTION,
        status=ReviewItemStatus.OPEN,
        assertion_id=assertion_id,
        assertion_version=assertion_version,
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
        created_at=datetime.now(UTC),
        evidence=evidence,
    )
