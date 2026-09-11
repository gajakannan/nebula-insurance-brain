from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from brain_temporal.outbox import OutboxEvent, OutboxProjector


class FakeOutboxReader:
    def __init__(self) -> None:
        self.events: dict[UUID, OutboxEvent] = {}

    def seed(self, commit_id: UUID, payload: dict) -> UUID:
        event_id = uuid4()
        self.events[event_id] = OutboxEvent(
            id=event_id,
            commit_id=commit_id,
            payload=payload,
            created_at=datetime.now(UTC),
            processed_at=None,
        )
        return event_id

    async def unprocessed(self, limit: int = 100) -> tuple[OutboxEvent, ...]:
        return tuple(e for e in self.events.values() if e.processed_at is None)[:limit]

    async def mark_processed(self, event_id: UUID, *, processed_at: datetime) -> None:
        event = self.events[event_id]
        self.events[event_id] = OutboxEvent(
            id=event.id,
            commit_id=event.commit_id,
            payload=event.payload,
            created_at=event.created_at,
            processed_at=processed_at,
        )


async def test_run_once_processes_all_unprocessed_events() -> None:
    reader = FakeOutboxReader()
    reader.seed(uuid4(), {"a": 1})
    reader.seed(uuid4(), {"b": 2})
    projector = OutboxProjector(reader)

    processed_count = await projector.run_once(now=datetime.now(UTC))

    assert processed_count == 2
    assert all(e.processed_at is not None for e in reader.events.values())


async def test_replay_after_a_partial_run_only_processes_what_remains_unprocessed() -> None:
    """F0001-S0005 edge case: the worker is killed after the commit transaction and
    before the projector runs — outbox replay must process each event exactly once."""
    reader = FakeOutboxReader()
    reader.seed(uuid4(), {"a": 1})
    projector = OutboxProjector(reader)

    first_run = await projector.run_once(now=datetime.now(UTC))
    second_run = await projector.run_once(now=datetime.now(UTC))  # simulates a replay

    assert first_run == 1
    assert second_run == 0  # already-processed event is not reprocessed


async def test_run_once_respects_the_limit() -> None:
    reader = FakeOutboxReader()
    for _ in range(5):
        reader.seed(uuid4(), {})
    projector = OutboxProjector(reader)

    processed_count = await projector.run_once(now=datetime.now(UTC), limit=2)

    assert processed_count == 2
