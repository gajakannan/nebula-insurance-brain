from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from brain_domain.facts import ChangeReason, CommitProposal, CommitResult, FactSlot, FactVersion


def test_fact_slot_construction() -> None:
    slot = FactSlot(
        id=uuid4(),
        entity_id=uuid4(),
        slot_type="each_occurrence_limit",
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
    )

    assert slot.slot_type == "each_occurrence_limit"


def test_change_reason_values() -> None:
    assert ChangeReason.SUPERSEDED == "superseded"
    assert ChangeReason.CORRECTED == "corrected"
    assert ChangeReason.RETRACTED == "retracted"
    assert ChangeReason.EXPIRED == "expired"
    assert ChangeReason.INVALIDATED == "invalidated"
    assert ChangeReason.MERGED == "merged"
    assert ChangeReason.SPLIT == "split"


def test_commit_proposal_construction_and_defaults() -> None:
    now = datetime.now(UTC)
    proposal = CommitProposal(
        slot_id=uuid4(),
        value={"amount": "2000000.00"},
        valid_from=now,
        valid_to=None,
        change_reason=ChangeReason.SUPERSEDED,
        evidence_refs=(uuid4(),),
        review_decision_id=None,
        source_received_at=now,
        artifact_created_at=now,
        assertion_created_at=now,
        expected_current_version_id=None,
        idempotency_key="commit-key-0001",
    )

    assert proposal.valid_to is None
    assert proposal.review_decision_id is None
    assert len(proposal.evidence_refs) == 1


def test_commit_result_construction() -> None:
    result = CommitResult(
        commit_id=uuid4(),
        fact_version_ids=(uuid4(), uuid4()),
        canonical_accepted_at=datetime.now(UTC),
    )

    assert len(result.fact_version_ids) == 2


def test_fact_version_construction_and_optional_fields() -> None:
    now = datetime.now(UTC)
    version = FactVersion(
        id=uuid4(),
        fact_slot_id=uuid4(),
        value={"amount": "2000000.00"},
        valid_start=now,
        valid_end=None,
        recorded_start=now,
        recorded_end=None,
        change_reason=None,
        evidence_refs=(),
        commit_id=uuid4(),
        canonical_accepted_at=now,
    )

    assert version.valid_end is None
    assert version.recorded_end is None
    assert version.change_reason is None
    assert version.evidence_refs == ()
