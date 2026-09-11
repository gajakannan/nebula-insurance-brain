"""Live-Postgres proof for F0001-S0005: two concurrent commits on the same
`FactSlot` leave exactly one winner. `lock_slot`'s `SELECT ... FOR UPDATE` is
what actually serializes the race — the loser's `SELECT ... FOR UPDATE` blocks
until the winner's transaction commits, then observes the slot's current
version has moved and rejects on `expected_current_version_id`. This can only
be proven against real Postgres row locking, not the in-memory fake.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from brain_domain.facts import CommitProposal
from brain_domain.principal import Membership, Principal
from brain_persistence.repositories import SqlAlchemyFactCommitRepository
from brain_security.authorization import AuthorizationService
from brain_temporal.commit import CanonicalCommitService, StaleVersionError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def _proposal(slot_id: UUID, *, value: dict, expected_current_version_id: UUID) -> CommitProposal:
    return CommitProposal(
        slot_id=slot_id,
        value=value,
        valid_from=dt("2026-06-01"),
        valid_to=None,
        change_reason=None,
        evidence_refs=(uuid4(),),
        review_decision_id=None,
        source_received_at=dt("2026-01-10"),
        artifact_created_at=dt("2026-01-10"),
        assertion_created_at=dt("2026-01-10"),
        expected_current_version_id=expected_current_version_id,
        idempotency_key=f"commit-{uuid4()}",
    )


async def test_two_concurrent_commits_on_the_same_slot_leave_exactly_one_winner(
    pg_session_factory: async_sessionmaker[AsyncSession],
    authz: AuthorizationService,
    actor: Principal,
    membership: Membership,
    slot_id: UUID,
) -> None:
    async with pg_session_factory() as session:
        repository = SqlAlchemyFactCommitRepository(session)
        service = CanonicalCommitService(repository, authz)
        first = await service.commit(
            actor,
            [membership],
            CommitProposal(
                slot_id=slot_id,
                value={"amount": "1000000.00"},
                valid_from=dt("2026-01-01"),
                valid_to=None,
                change_reason=None,
                evidence_refs=(uuid4(),),
                review_decision_id=None,
                source_received_at=dt("2026-01-10"),
                artifact_created_at=dt("2026-01-10"),
                assertion_created_at=dt("2026-01-10"),
                expected_current_version_id=None,
                idempotency_key=f"commit-{uuid4()}",
            ),
            trace_id="t0",
        )
        await session.commit()
    original_version_id = first.fact_version_ids[0]

    async def attempt(value: str) -> object:
        try:
            async with pg_session_factory() as session:
                repository = SqlAlchemyFactCommitRepository(session)
                service = CanonicalCommitService(repository, authz)
                result = await service.commit(
                    actor,
                    [membership],
                    _proposal(
                        slot_id,
                        value={"amount": value},
                        expected_current_version_id=original_version_id,
                    ),
                    trace_id=f"race-{value}",
                )
                await session.commit()
                return result
        except StaleVersionError as exc:
            return exc

    outcomes = await asyncio.gather(attempt("2000000.00"), attempt("3000000.00"))

    winners = [o for o in outcomes if not isinstance(o, StaleVersionError)]
    losers = [o for o in outcomes if isinstance(o, StaleVersionError)]
    assert len(winners) == 1, f"expected exactly one winner, got {outcomes}"
    assert len(losers) == 1

    async with pg_session_factory() as session:
        repository = SqlAlchemyFactCommitRepository(session)
        current = await repository.current_versions(slot_id)
        current_ids = {v.id for v in current}
        # The winner's commit produces two current rows: the SPLIT remainder
        # covering [2026-01-01, 2026-06-01) with the original's value, and the
        # winner's own new version from 2026-06-01 onward — the original,
        # first-seeded version is superseded and no longer current.
        assert len(current) == 2
        winning_result = winners[0]
        assert winning_result.fact_version_ids[-1] in current_ids  # type: ignore[attr-defined]
        assert original_version_id not in current_ids
