"""F0009 review-boundary unit proofs (S0002 AC5/AC6/AC7, S0005 AC1-AC4)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from brain_domain.review import (
    EvidenceLocator,
    ReviewDecisionAction,
    ReviewDecisionReasonCode,
)
from brain_review.decisions import (
    DecisionRequest,
    ReviewDecisionService,
    compute_event_sha256,
    preflight_batch,
)

from .conftest import make_review_item

VALUE = {"amount": "2000000.00", "currency": "USD"}


def _correct(item, reviewer, *, version=1, value=VALUE, comment=None):
    return DecisionRequest(
        review_item_id=item.id,
        action=ReviewDecisionAction.CORRECT,
        reviewer_principal_id=reviewer,
        assertion_version=version,
        reason_code=ReviewDecisionReasonCode.MISREAD_VALUE,
        corrected_value=value,
        evidence_seen=EvidenceLocator(source="artifact", precision="page"),
        reviewer_comment=comment,
    )


async def test_effective_correction_reserves_exactly_one_reference(repository, audit) -> None:
    item = make_review_item()
    repository.seed_item(item)
    outcome = await ReviewDecisionService(repository, audit).submit(_correct(item, uuid4()))
    assert outcome.applied and outcome.decision.corrected_assertion_id is not None
    assert list(repository.reservations) == [outcome.decision.id]


async def test_reservation_failure_propagates_before_audit(repository, audit) -> None:
    """S0005 AC2: the failure escapes the service before the audit write, so the
    facade rolls back the decision and child in the same unit of work."""
    item = make_review_item()
    repository.seed_item(item)
    repository.fail_reservation = True
    with pytest.raises(RuntimeError, match="injected reservation failure"):
        await ReviewDecisionService(repository, audit).submit(_correct(item, uuid4()))
    assert audit.recorded == []


async def test_replay_creates_no_second_reservation(repository, audit) -> None:
    item = make_review_item()
    repository.seed_item(item)
    service = ReviewDecisionService(repository, audit)
    request = _correct(item, uuid4())
    first = await service.submit(request)
    replay = await service.submit(request)
    assert replay.duplicate and replay.decision.id == first.decision.id
    assert len(repository.reservations) == 1
    assert len(audit.recorded) == 1


@pytest.mark.parametrize(
    "action,reason",
    [
        (ReviewDecisionAction.ACCEPT, None),
        (ReviewDecisionAction.REJECT, ReviewDecisionReasonCode.NOT_IN_SOURCE),
    ],
)
async def test_non_correcting_actions_reserve_nothing(repository, audit, action, reason) -> None:
    item = make_review_item()
    repository.seed_item(item)
    request = DecisionRequest(
        review_item_id=item.id,
        action=action,
        reviewer_principal_id=uuid4(),
        assertion_version=1,
        reason_code=reason,
    )
    outcome = await ReviewDecisionService(repository, audit).submit(request)
    assert outcome.applied and outcome.decision.corrected_assertion_id is None
    assert repository.reservations == {}


async def test_blocked_reserves_nothing(repository, audit) -> None:
    item = make_review_item()
    repository.seed_item(item)
    request = DecisionRequest(
        review_item_id=item.id,
        action=ReviewDecisionAction.BLOCKED,
        reviewer_principal_id=uuid4(),
        assertion_version=1,
        reason_code=ReviewDecisionReasonCode.EVIDENCE_UNRESOLVED,
        evidence_seen=EvidenceLocator(
            source="artifact", precision="unresolved", unresolved_reason="no anchor"
        ),
    )
    await ReviewDecisionService(repository, audit).submit(request)
    assert repository.reservations == {}
    assert repository.corrected_assertions == {}


async def test_stale_correction_retains_the_submission_without_effect(repository, audit) -> None:
    """S0002 AC5: attributed, non-applied, with the submitted value/evidence/comment,
    no child and no reservation; stale routing is unchanged."""
    item = make_review_item(assertion_version=1)
    repository.seed_item(item, assertion_version=2)
    request = _correct(item, uuid4(), comment="saw 2M on page 3")
    outcome = await ReviewDecisionService(repository, audit).submit(request)
    decision = outcome.decision
    assert outcome.applied is False and decision.stale is True
    assert decision.corrected_value == VALUE
    assert decision.evidence == request.evidence_seen
    assert decision.reviewer_comment == "saw 2M on page 3"
    assert decision.corrected_assertion_id is None
    assert repository.reservations == {} and repository.corrected_assertions == {}
    assert len(repository.new_items_opened) == 1


async def test_preflight_clean_batch_refuses_nothing(repository) -> None:
    a, b = make_review_item(), make_review_item()
    repository.seed_item(a)
    repository.seed_item(b)
    refused = await preflight_batch(
        repository, [(a, _correct(a, uuid4())), (b, _correct(b, uuid4()))]
    )
    assert refused == []


async def test_preflight_refuses_every_nonduplicate_submission(repository, audit) -> None:
    """S0002 AC6 (assembly plan Step 3.4): the decided item is ALREADY_DECIDED, its
    sibling BATCH_REFUSED, and an exact replay creates no attempt."""
    reviewer = uuid4()
    decided, sibling, replayed = make_review_item(), make_review_item(), make_review_item()
    for item in (decided, sibling, replayed):
        repository.seed_item(item)
    service = ReviewDecisionService(repository, audit)
    await service.submit(_correct(decided, reviewer, value={"amount": "1"}))
    replay_request = _correct(replayed, reviewer)
    await service.submit(replay_request)

    refused = await preflight_batch(
        repository,
        [
            (decided, _correct(decided, reviewer, value={"amount": "2"})),
            (sibling, _correct(sibling, reviewer)),
            (replayed, replay_request),
        ],
    )
    outcomes = {r.item.id: r.outcome for r in refused}
    assert outcomes == {decided.id: "ALREADY_DECIDED", sibling.id: "BATCH_REFUSED"}
    sibling_refusal = next(r for r in refused if r.item.id == sibling.id)
    assert sibling_refusal.event_sha256 == compute_event_sha256(sibling_refusal.request)


async def test_refused_sibling_resubmitted_alone_applies(repository, audit) -> None:
    """PR-H1 (operator decision 2026-11-24): a stored refusal is never a replay key;
    resubmitting the refused sibling in a clean batch is evaluated and applies."""
    reviewer = uuid4()
    decided, sibling = make_review_item(), make_review_item()
    repository.seed_item(decided)
    repository.seed_item(sibling)
    service = ReviewDecisionService(repository, audit)
    await service.submit(_correct(decided, reviewer, value={"amount": "1"}))
    sibling_request = _correct(sibling, reviewer)
    refused = await preflight_batch(
        repository,
        [(decided, _correct(decided, reviewer, value={"amount": "2"})), (sibling, sibling_request)],
    )
    assert {r.outcome for r in refused} == {"ALREADY_DECIDED", "BATCH_REFUSED"}

    assert await preflight_batch(repository, [(sibling, sibling_request)]) == []
    outcome = await service.submit(sibling_request)
    assert outcome.applied and not outcome.duplicate
    assert outcome.decision.id in repository.reservations
