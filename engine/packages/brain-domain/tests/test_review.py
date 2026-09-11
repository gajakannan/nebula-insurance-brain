from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from brain_domain.review import (
    EvidenceLocator,
    ReviewBatch,
    ReviewDecision,
    ReviewDecisionAction,
    ReviewDecisionReasonCode,
    ReviewItem,
    ReviewItemStatus,
    ReviewItemType,
)


def test_review_item_construction() -> None:
    item = ReviewItem(
        id=uuid4(),
        type=ReviewItemType.LOW_CONFIDENCE_ASSERTION,
        status=ReviewItemStatus.OPEN,
        assertion_id=uuid4(),
        assertion_version=1,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        created_at=datetime.now(UTC),
    )

    assert item.review_batch_id is None
    assert item.evidence is None


def test_evidence_locator_defaults() -> None:
    locator = EvidenceLocator(source="artifact-1", precision="page")

    assert locator.part is None
    assert locator.selector == ()


def test_review_batch_groups_item_ids() -> None:
    batch = ReviewBatch(
        id=uuid4(),
        review_item_ids=(uuid4(), uuid4()),
        assembled_at=datetime.now(UTC),
        assembling_principal_id=uuid4(),
    )

    assert len(batch.review_item_ids) == 2


def test_review_decision_construction() -> None:
    decision = ReviewDecision(
        id=uuid4(),
        review_item_id=uuid4(),
        review_batch_id=uuid4(),
        action=ReviewDecisionAction.CORRECT,
        reviewer_principal_id=uuid4(),
        decided_at=datetime.now(UTC),
        assertion_version=1,
        stale=False,
        event_sha256="a" * 64,
        reason_code=ReviewDecisionReasonCode.MISREAD_VALUE,
    )

    assert decision.stale is False
    assert decision.corrected_assertion_id is None
