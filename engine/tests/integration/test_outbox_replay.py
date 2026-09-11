"""Live-Postgres proof for F0001-S0005: outbox replay after a simulated worker
kill processes each event exactly once. The commit transaction itself (fact
version + `canonical_fact_change` + `audit_event` + `outbox_event`) is proven
elsewhere; this proves the read side — `SqlAlchemyOutboxReader` +
`OutboxProjector` — against the real `outbox_event` table.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from brain_domain.facts import CommitProposal
from brain_domain.principal import Membership, Principal
from brain_persistence.repositories import SqlAlchemyFactCommitRepository, SqlAlchemyOutboxReader
from brain_security.authorization import AuthorizationService
from brain_temporal.commit import CanonicalCommitService
from brain_temporal.outbox import OutboxProjector
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


async def test_replay_after_a_simulated_worker_kill_processes_each_event_once(
    pg_session_factory: async_sessionmaker[AsyncSession],
    authz: AuthorizationService,
    actor: Principal,
    membership: Membership,
    slot_id: UUID,
) -> None:
    async with pg_session_factory() as session:
        repository = SqlAlchemyFactCommitRepository(session)
        service = CanonicalCommitService(repository, authz)
        result = await service.commit(
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
        # Commits the fact version, the change record, the audit event, and the
        # outbox event together — simulating the worker being killed right after
        # this point, before any projector ever ran.
        await session.commit()

    # First run: processes the one outbox event the commit above produced.
    async with pg_session_factory() as session:
        reader = SqlAlchemyOutboxReader(session)
        projector = OutboxProjector(reader)
        first_run = await projector.run_once(now=datetime.now(UTC))
        await session.commit()
    assert first_run == 1

    # Replay (the worker restarts and polls again): the event is already
    # watermarked, so it is not reprocessed.
    async with pg_session_factory() as session:
        reader = SqlAlchemyOutboxReader(session)
        projector = OutboxProjector(reader)
        second_run = await projector.run_once(now=datetime.now(UTC))
    assert second_run == 0

    async with pg_session_factory() as session:
        reader = SqlAlchemyOutboxReader(session)
        unprocessed = await reader.unprocessed()
        assert unprocessed == ()

    assert result.fact_version_ids  # sanity: the commit that produced the event
