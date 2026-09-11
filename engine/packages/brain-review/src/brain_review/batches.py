from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from brain_domain.review import ReviewBatch, ReviewItem


def assemble_batch(items: list[ReviewItem], *, assembling_principal_id: UUID) -> ReviewBatch:
    """Groups open review items into one batch the panel can open (F0001-S0004
    Interaction Contract). Entitlement to each item is resolved and rechecked at
    submission, not here — assembly only groups; it does not authorize."""
    if not items:
        raise ValueError("cannot assemble a batch from zero review items")
    return ReviewBatch(
        id=uuid4(),
        review_item_ids=tuple(item.id for item in items),
        assembled_at=datetime.now(UTC),
        assembling_principal_id=assembling_principal_id,
    )
