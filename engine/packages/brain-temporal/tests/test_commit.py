from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from brain_domain.facts import ChangeReason, CommitProposal
from brain_security.audit import InMemoryAuditEventRepository, RepositoryAuditSink
from brain_security.authorization import AuthorizationService
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_temporal.commit import CanonicalCommitService, FactSlotNotFound, StaleVersionError
from brain_temporal.ranges import InvalidRangeError

REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_PATH = REPO_ROOT / "planning-mds" / "security" / "policies" / "model.conf"
POLICY_PATH = REPO_ROOT / "planning-mds" / "security" / "policies" / "policy.csv"


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def _authz() -> AuthorizationService:
    return AuthorizationService(
        CasbinAuthorizationAdapter(MODEL_PATH, POLICY_PATH),
        RepositoryAuditSink(InMemoryAuditEventRepository()),
    )


def _proposal(
    slot_id: UUID,
    *,
    value: dict,
    valid_from: datetime,
    valid_to: datetime | None = None,
    change_reason: ChangeReason | None = None,
    expected_current_version_id: UUID | None = None,
    idempotency_key: str = "commit-key-0001",
) -> CommitProposal:
    return CommitProposal(
        slot_id=slot_id,
        value=value,
        valid_from=valid_from,
        valid_to=valid_to,
        change_reason=change_reason,
        evidence_refs=(uuid4(),),
        review_decision_id=None,
        source_received_at=dt("2026-01-10"),
        artifact_created_at=dt("2026-01-10"),
        assertion_created_at=dt("2026-01-10"),
        expected_current_version_id=expected_current_version_id,
        idempotency_key=idempotency_key,
    )


async def test_first_commit_on_an_empty_slot_creates_one_open_version(
    repository, actor, membership
) -> None:
    slot_id = uuid4()
    repository.seed_slot(slot_id)
    service = CanonicalCommitService(repository, _authz())
    proposal = _proposal(slot_id, value={"amount": "2000000.00"}, valid_from=dt("2026-01-01"))

    result = await service.commit(actor, [membership], proposal, trace_id="t1")

    assert len(result.fact_version_ids) == 1
    version = repository.versions[result.fact_version_ids[0]]
    assert version.valid_start == dt("2026-01-01")
    assert version.valid_end is None
    assert version.recorded_end is None
    assert repository.outbox[0][0] == result.commit_id


async def test_endorsement_answers_the_section_87_matrix(repository, actor, membership) -> None:
    """F0001-S0005 happy path: $2,000,000 valid from 2026-01-01, recorded 2026-01-10;
    an endorsement effective 2026-06-01 sets $5,000,000, accepted 2026-06-14."""
    slot_id = uuid4()
    repository.seed_slot(slot_id)
    service = CanonicalCommitService(repository, _authz())

    first = await service.commit(
        actor,
        [membership],
        _proposal(slot_id, value={"amount": "2000000.00"}, valid_from=dt("2026-01-01")),
        trace_id="t1",
    )
    original_version_id = first.fact_version_ids[0]

    second = await service.commit(
        actor,
        [membership],
        _proposal(
            slot_id,
            value={"amount": "5000000.00"},
            valid_from=dt("2026-06-01"),
            change_reason=ChangeReason.SUPERSEDED,
            expected_current_version_id=original_version_id,
        ),
        trace_id="t2",
    )

    # Bitemporal semantics: the ORIGINAL row's own `valid` range is never rewritten —
    # it keeps recording "we believed this was true from 2026-01-01 onward, no end"
    # exactly as it was accepted. Only its `recorded` range closes: it stops being
    # the *current* answer, but stays readable at its own past recorded coordinates
    # (F0001-S0005 AC: "every prior version remains readable at its original
    # recorded coordinates"). A SPLIT remainder, not a mutation of the original row,
    # is what narrows the valid-time answer for 2026-01-01..2026-06-01 going forward.
    original_after = repository.versions[original_version_id]
    assert original_after.valid_start == dt("2026-01-01")
    assert original_after.valid_end is None  # unchanged — historical belief preserved
    assert original_after.recorded_end is not None  # no longer current

    # Exactly one SPLIT remainder: [2026-01-01, 2026-06-01) still worth $2,000,000,
    # now itself the current answer for that valid window.
    remainder_ids = [v for v in second.fact_version_ids if v != second.fact_version_ids[-1]]
    assert len(remainder_ids) == 1
    remainder = repository.versions[remainder_ids[0]]
    assert remainder.value == {"amount": "2000000.00"}
    assert remainder.valid_start == dt("2026-01-01")
    assert remainder.valid_end == dt("2026-06-01")
    assert remainder.change_reason == ChangeReason.SPLIT
    assert remainder.recorded_end is None  # current

    new_version_id = second.fact_version_ids[-1]
    new_version = repository.versions[new_version_id]
    assert new_version.value == {"amount": "5000000.00"}
    assert new_version.valid_start == dt("2026-06-01")
    assert new_version.valid_end is None
    assert new_version.recorded_end is None  # current

    # "known on 2026-06-05" (before this endorsement's acceptance) resolves to the
    # ORIGINAL row: its recorded range alone still covers that past recorded
    # coordinate, since the split remainder and the new value only become visible
    # at this commit's `canonical_accepted_at`. Exact calendar-date resolution
    # against real recorded ranges is exercised in the Postgres integration proof;
    # here the row ordering itself is what's asserted.
    assert original_after.recorded_start < new_version.recorded_start


async def test_retroactive_correction_splits_the_endorsement_into_two_pieces(
    repository, actor, membership
) -> None:
    slot_id = uuid4()
    repository.seed_slot(slot_id)
    service = CanonicalCommitService(repository, _authz())

    first = await service.commit(
        actor,
        [membership],
        _proposal(slot_id, value={"amount": "2000000.00"}, valid_from=dt("2026-01-01")),
        trace_id="t1",
    )
    endorsement = await service.commit(
        actor,
        [membership],
        _proposal(
            slot_id,
            value={"amount": "5000000.00"},
            valid_from=dt("2026-06-01"),
            expected_current_version_id=first.fact_version_ids[0],
        ),
        trace_id="t2",
    )
    endorsement_version_id = endorsement.fact_version_ids[-1]

    # Correction: move the effective date from 2026-06-01 to 2026-06-03. The new
    # commit's valid range starts later, so the endorsement's own valid range is
    # split: [2026-01-01, 2026-06-01) stays with the original value (untouched, not
    # part of this commit), and [2026-06-01, 2026-06-03) becomes a SPLIT remainder
    # still carrying the endorsement's $5,000,000 value while [2026-06-03, None)
    # carries the corrected value.
    correction = await service.commit(
        actor,
        [membership],
        _proposal(
            slot_id,
            value={"amount": "5000000.00"},
            valid_from=dt("2026-06-03"),
            change_reason=ChangeReason.CORRECTED,
            expected_current_version_id=endorsement_version_id,
        ),
        trace_id="t3",
    )

    endorsement_after = repository.versions[endorsement_version_id]
    assert endorsement_after.recorded_end is not None  # superseded by the correction

    remainder_ids = [v for v in correction.fact_version_ids if v != correction.fact_version_ids[-1]]
    assert len(remainder_ids) == 1
    remainder = repository.versions[remainder_ids[0]]
    assert remainder.valid_start == dt("2026-06-01")
    assert remainder.valid_end == dt("2026-06-03")
    assert remainder.change_reason == ChangeReason.SPLIT
    assert remainder.value == {"amount": "5000000.00"}
    assert remainder.recorded_end is None  # the split piece is itself current

    corrected = repository.versions[correction.fact_version_ids[-1]]
    assert corrected.valid_start == dt("2026-06-03")
    assert corrected.change_reason == ChangeReason.CORRECTED

    change_reasons = [
        c["reason"] for c in repository.changes if c["from_version_id"] == endorsement_version_id
    ]
    assert ChangeReason.CORRECTED in change_reasons


async def test_stale_expected_version_is_rejected(repository, actor, membership) -> None:
    slot_id = uuid4()
    repository.seed_slot(slot_id)
    service = CanonicalCommitService(repository, _authz())
    await service.commit(
        actor,
        [membership],
        _proposal(slot_id, value={"amount": "1"}, valid_from=dt("2026-01-01")),
        trace_id="t1",
    )

    with pytest.raises(StaleVersionError):
        await service.commit(
            actor,
            [membership],
            _proposal(
                slot_id,
                value={"amount": "2"},
                valid_from=dt("2026-06-01"),
                expected_current_version_id=uuid4(),
            ),
            trace_id="t2",
        )


async def test_empty_range_is_rejected_before_any_write(repository, actor, membership) -> None:
    slot_id = uuid4()
    repository.seed_slot(slot_id)
    service = CanonicalCommitService(repository, _authz())

    with pytest.raises(InvalidRangeError):
        await service.commit(
            actor,
            [membership],
            _proposal(
                slot_id,
                value={"amount": "1"},
                valid_from=dt("2026-06-01"),
                valid_to=dt("2026-06-01"),
            ),
            trace_id="t1",
        )
    assert repository.versions == {}
    assert repository.outbox == []


async def test_missing_slot_raises_not_found(repository, actor, membership) -> None:
    service = CanonicalCommitService(repository, _authz())

    with pytest.raises(FactSlotNotFound):
        await service.commit(
            actor,
            [membership],
            _proposal(uuid4(), value={"amount": "1"}, valid_from=dt("2026-01-01")),
            trace_id="t1",
        )


async def test_actor_without_a_matching_membership_is_denied_as_not_found(
    repository, actor
) -> None:
    slot_id = uuid4()
    repository.seed_slot(slot_id)
    service = CanonicalCommitService(repository, _authz())

    with pytest.raises(FactSlotNotFound):
        await service.commit(
            actor,
            [],
            _proposal(slot_id, value={"amount": "1"}, valid_from=dt("2026-01-01")),
            trace_id="t1",
        )
    assert repository.versions == {}
