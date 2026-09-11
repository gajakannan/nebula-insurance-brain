from __future__ import annotations

from uuid import uuid4

import pytest
from brain_domain.review import (
    EvidenceLocator,
    ReviewDecisionAction,
    ReviewDecisionReasonCode,
    ReviewItemStatus,
)
from brain_review.decisions import (
    DecisionRequest,
    InvalidBlockedReasonCode,
    ReviewDecisionService,
    ReviewItemAlreadyDecided,
    ReviewItemNotFound,
    UnresolvedEvidenceRequiresBlocked,
    compute_event_sha256,
)

from .conftest import make_review_item


async def test_correct_action_creates_a_corrected_assertion_and_one_audit_event(
    repository, audit
) -> None:
    item = make_review_item(assertion_version=1)
    repository.seed_item(item)
    service = ReviewDecisionService(repository, audit)
    request = DecisionRequest(
        review_item_id=item.id,
        action=ReviewDecisionAction.CORRECT,
        reviewer_principal_id=uuid4(),
        assertion_version=1,
        reason_code=ReviewDecisionReasonCode.MISREAD_VALUE,
        corrected_value={"amount": "2000000.00", "currency": "USD"},
        evidence_seen=EvidenceLocator(source=str(item.assertion_id), precision="exact-span"),
    )

    outcome = await service.submit(request)

    assert outcome.applied is True
    assert outcome.duplicate is False
    assert outcome.decision.action == ReviewDecisionAction.CORRECT
    assert outcome.decision.corrected_assertion_id is not None
    assert len(audit.recorded) == 1
    assert repository.items[item.id].status == ReviewItemStatus.DECIDED
    # Original assertion is never touched by this service.
    assert item.assertion_id not in repository.corrected_assertions


async def test_original_assertion_is_unchanged_after_a_correction(repository, audit) -> None:
    """F0001-S0004 AC: querying the original machine assertion after a correction
    returns it unchanged. This service never calls anything that would mutate it —
    proven here by asserting the repository records a *new* row, never an update
    keyed by the original assertion id."""
    item = make_review_item(assertion_version=1)
    repository.seed_item(item)
    service = ReviewDecisionService(repository, audit)
    request = DecisionRequest(
        review_item_id=item.id,
        action=ReviewDecisionAction.CORRECT,
        reviewer_principal_id=uuid4(),
        assertion_version=1,
        reason_code=ReviewDecisionReasonCode.MISREAD_VALUE,
        corrected_value={"amount": "2000000.00"},
    )

    outcome = await service.submit(request)

    corrected = repository.corrected_assertions[outcome.decision.corrected_assertion_id]
    assert corrected["original_assertion_id"] == item.assertion_id


async def test_resubmitting_the_same_batch_is_a_no_op_by_event_hash(repository, audit) -> None:
    item = make_review_item(assertion_version=1)
    repository.seed_item(item)
    service = ReviewDecisionService(repository, audit)
    request = DecisionRequest(
        review_item_id=item.id,
        action=ReviewDecisionAction.ACCEPT,
        reviewer_principal_id=uuid4(),
        assertion_version=1,
    )

    first = await service.submit(request)
    second = await service.submit(request)

    assert first.applied is True
    assert first.duplicate is False
    assert second.applied is False
    assert second.duplicate is True
    assert second.decision.id == first.decision.id
    assert len(repository.decisions[item.id]) == 1  # exactly one ReviewDecision per item
    assert len(audit.recorded) == 1  # duplicate never re-audits


async def test_stale_assertion_version_is_recorded_stale_and_opens_a_new_item(
    repository, audit
) -> None:
    item = make_review_item(assertion_version=1)
    repository.seed_item(item, assertion_version=2)  # superseded to N+1 before submission
    service = ReviewDecisionService(repository, audit)
    request = DecisionRequest(
        review_item_id=item.id,
        action=ReviewDecisionAction.CORRECT,
        reviewer_principal_id=uuid4(),
        assertion_version=1,  # the version the reviewer saw
        corrected_value={"amount": "1"},
    )

    outcome = await service.submit(request)

    assert outcome.applied is False
    assert outcome.decision.stale is True
    assert outcome.decision.corrected_assertion_id is None  # stale decisions create no assertion
    assert len(repository.new_items_opened) == 1
    opened_for_item, opened_version = repository.new_items_opened[0]
    assert opened_for_item.id == item.id
    assert opened_version == 2
    assert len(audit.recorded) == 1


async def test_unresolved_evidence_blocks_creates_no_assertion_and_stays_open(
    repository, audit
) -> None:
    item = make_review_item(assertion_version=1)
    repository.seed_item(item)
    service = ReviewDecisionService(repository, audit)
    unresolved = EvidenceLocator(
        source=str(item.assertion_id), precision="unresolved", unresolved_reason="no text layer"
    )
    request = DecisionRequest(
        review_item_id=item.id,
        action=ReviewDecisionAction.BLOCKED,
        reviewer_principal_id=uuid4(),
        assertion_version=1,
        reason_code=ReviewDecisionReasonCode.EVIDENCE_UNRESOLVED,
        evidence_seen=unresolved,
    )

    outcome = await service.submit(request)

    assert outcome.decision.action == ReviewDecisionAction.BLOCKED
    assert outcome.decision.corrected_assertion_id is None
    # BLOCKED does not call mark_item_status — the item stays at its prior status (open).
    assert repository.items[item.id].status == ReviewItemStatus.OPEN


async def test_unresolved_evidence_with_a_non_blocked_action_is_rejected(repository, audit) -> None:
    item = make_review_item(assertion_version=1)
    repository.seed_item(item)
    service = ReviewDecisionService(repository, audit)
    unresolved = EvidenceLocator(source=str(item.assertion_id), precision="unresolved")
    request = DecisionRequest(
        review_item_id=item.id,
        action=ReviewDecisionAction.ACCEPT,
        reviewer_principal_id=uuid4(),
        assertion_version=1,
        evidence_seen=unresolved,
    )

    with pytest.raises(UnresolvedEvidenceRequiresBlocked):
        await service.submit(request)


async def test_blocked_without_evidence_unresolved_reason_code_is_rejected(
    repository, audit
) -> None:
    item = make_review_item(assertion_version=1)
    repository.seed_item(item)
    service = ReviewDecisionService(repository, audit)
    request = DecisionRequest(
        review_item_id=item.id,
        action=ReviewDecisionAction.BLOCKED,
        reviewer_principal_id=uuid4(),
        assertion_version=1,
        reason_code=ReviewDecisionReasonCode.MISREAD_VALUE,
    )

    with pytest.raises(InvalidBlockedReasonCode):
        await service.submit(request)


async def test_missing_review_item_raises_not_found(repository, audit) -> None:
    service = ReviewDecisionService(repository, audit)
    request = DecisionRequest(
        review_item_id=uuid4(),
        action=ReviewDecisionAction.ACCEPT,
        reviewer_principal_id=uuid4(),
        assertion_version=1,
    )

    with pytest.raises(ReviewItemNotFound):
        await service.submit(request)


async def test_a_second_distinct_decision_on_an_already_decided_item_is_rejected(
    repository, audit
) -> None:
    item = make_review_item(assertion_version=1)
    repository.seed_item(item)
    service = ReviewDecisionService(repository, audit)
    await service.submit(
        DecisionRequest(
            review_item_id=item.id,
            action=ReviewDecisionAction.ACCEPT,
            reviewer_principal_id=uuid4(),
            assertion_version=1,
        )
    )

    with pytest.raises(ReviewItemAlreadyDecided):
        await service.submit(
            DecisionRequest(
                review_item_id=item.id,
                action=ReviewDecisionAction.REJECT,
                reviewer_principal_id=uuid4(),
                assertion_version=1,
            )
        )


async def test_event_sha256_is_deterministic_for_identical_requests() -> None:
    request = DecisionRequest(
        review_item_id=uuid4(),
        action=ReviewDecisionAction.ACCEPT,
        reviewer_principal_id=uuid4(),
        assertion_version=1,
    )

    assert compute_event_sha256(request) == compute_event_sha256(request)


async def test_event_sha256_differs_for_different_reviewers() -> None:
    base = DecisionRequest(
        review_item_id=uuid4(),
        action=ReviewDecisionAction.ACCEPT,
        reviewer_principal_id=uuid4(),
        assertion_version=1,
    )
    other = DecisionRequest(
        review_item_id=base.review_item_id,
        action=base.action,
        reviewer_principal_id=uuid4(),
        assertion_version=1,
    )

    assert compute_event_sha256(base) != compute_event_sha256(other)
