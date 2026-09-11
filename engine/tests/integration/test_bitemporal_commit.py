"""Live-Postgres proof for F0001-S0005: the section 87 query matrix answered
after a real reload from `canonical_fact_version`, including its `tstzrange`
columns and `EXCLUDE USING gist` constraint — none of which sqlite can express,
so unlike brain-temporal's algorithmic unit tests, this exercises the real
`SqlAlchemyFactCommitRepository` against a live compose Postgres.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from brain_domain.facts import ChangeReason, CommitProposal
from brain_domain.principal import Membership, Principal
from brain_persistence.repositories import SqlAlchemyFactCommitRepository
from brain_security.authorization import AuthorizationService
from brain_temporal.commit import CanonicalCommitService
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def _proposal(
    slot_id: UUID,
    *,
    value: dict,
    valid_from: datetime,
    expected_current_version_id: UUID | None = None,
    change_reason: ChangeReason | None = None,
) -> CommitProposal:
    return CommitProposal(
        slot_id=slot_id,
        value=value,
        valid_from=valid_from,
        valid_to=None,
        change_reason=change_reason,
        evidence_refs=(uuid4(),),
        review_decision_id=None,
        source_received_at=dt("2026-01-10"),
        artifact_created_at=dt("2026-01-10"),
        assertion_created_at=dt("2026-01-10"),
        expected_current_version_id=expected_current_version_id,
        idempotency_key=f"commit-{uuid4()}",
    )


async def test_section_87_matrix_answered_after_reload_from_postgres(
    pg_session_factory: async_sessionmaker[AsyncSession],
    authz: AuthorizationService,
    actor: Principal,
    membership: Membership,
    slot_id: UUID,
) -> None:
    # `recorded` is stamped from the wall clock inside CanonicalCommitService, not
    # from any business-time field on the proposal — so the "known as of" probes
    # below bracket real commit instants, while "valid as of" uses the business
    # dates the proposals declare.
    async with pg_session_factory() as session:
        repository = SqlAlchemyFactCommitRepository(session)
        service = CanonicalCommitService(repository, authz)
        first = await service.commit(
            actor,
            [membership],
            _proposal(slot_id, value={"amount": "2000000.00"}, valid_from=dt("2026-01-01")),
            trace_id="t1",
        )
        await session.commit()
    original_version_id = first.fact_version_ids[0]
    known_after_first_commit = datetime.now(UTC)

    async with pg_session_factory() as session:
        repository = SqlAlchemyFactCommitRepository(session)
        service = CanonicalCommitService(repository, authz)
        second = await service.commit(
            actor,
            [membership],
            _proposal(
                slot_id,
                value={"amount": "5000000.00"},
                valid_from=dt("2026-06-01"),
                expected_current_version_id=original_version_id,
                change_reason=ChangeReason.SUPERSEDED,
            ),
            trace_id="t2",
        )
        await session.commit()
    known_after_second_commit = datetime.now(UTC)

    # Reload entirely from Postgres — a fresh session, fresh repository reads —
    # to prove the constraint and the stored ranges, not just in-process state.
    async with pg_session_factory() as session:
        repository = SqlAlchemyFactCommitRepository(session)

        # Known before the endorsement was ever recorded: only the original
        # $2,000,000 version exists at that recorded coordinate.
        before_endorsement = await repository.resolve_at(
            slot_id, valid_as_of=dt("2026-03-01"), known_as_of=known_after_first_commit
        )
        assert before_endorsement is not None
        assert before_endorsement.value == {"amount": "2000000.00"}
        assert before_endorsement.id == original_version_id
        assert before_endorsement.change_reason is None  # the very first version

        # Known after the endorsement, asking about a date before the
        # endorsement's own effective date: the SPLIT remainder answers.
        known_after_valid_before = await repository.resolve_at(
            slot_id, valid_as_of=dt("2026-03-01"), known_as_of=known_after_second_commit
        )
        assert known_after_valid_before is not None
        assert known_after_valid_before.value == {"amount": "2000000.00"}
        assert known_after_valid_before.change_reason == ChangeReason.SPLIT
        assert known_after_valid_before.id != original_version_id

        # Known after, valid after the endorsement's effective date: $5,000,000.
        known_and_valid_after = await repository.resolve_at(
            slot_id, valid_as_of=dt("2026-07-01"), known_as_of=known_after_second_commit
        )
        assert known_and_valid_after is not None
        assert known_and_valid_after.value == {"amount": "5000000.00"}
        assert known_and_valid_after.id == second.fact_version_ids[-1]

        # The original row is still readable, unmutated, at its own original
        # recorded coordinates — it was superseded going forward, never rewritten.
        current_versions = await repository.current_versions(slot_id)
        current_ids = {v.id for v in current_versions}
        assert original_version_id not in current_ids  # no longer current
        assert known_after_valid_before.id in current_ids  # the split remainder is
        assert second.fact_version_ids[-1] in current_ids  # ...and the new version
