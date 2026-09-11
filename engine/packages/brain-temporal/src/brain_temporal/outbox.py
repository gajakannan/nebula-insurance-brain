from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class OutboxEvent:
    id: UUID
    commit_id: UUID
    payload: dict
    created_at: datetime
    processed_at: datetime | None


class OutboxReader(Protocol):
    """Read side used by the projector (F0001-S0005: 'the worker is killed after
    the transaction commits and before the projector runs -> outbox replay
    processes the event once')."""

    async def unprocessed(self, limit: int = 100) -> tuple[OutboxEvent, ...]: ...

    async def mark_processed(self, event_id: UUID, *, processed_at: datetime) -> None: ...


class OutboxProjector:
    """Records processed events; no graph or vector projection yet (F0033/F0034 own
    that). Idempotent: replaying an already-processed event is a no-op because
    `mark_processed` is the only state change and `unprocessed()` excludes it —
    the projector never reprocesses a watermarked event."""

    def __init__(self, reader: OutboxReader) -> None:
        self._reader = reader

    async def run_once(self, *, now: datetime, limit: int = 100) -> int:
        events = await self._reader.unprocessed(limit=limit)
        for event in events:
            await self._reader.mark_processed(event.id, processed_at=now)
        return len(events)
