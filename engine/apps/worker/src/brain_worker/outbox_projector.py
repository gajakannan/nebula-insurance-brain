from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime

from brain_persistence.repositories import SqlAlchemyOutboxReader
from brain_persistence.session import make_engine, make_session_factory
from brain_temporal.outbox import OutboxProjector

logger = logging.getLogger("brain_worker.outbox_projector")


def _database_url() -> str:
    return os.environ.get(
        "BRAIN_DATABASE_URL", "postgresql+asyncpg://brain:brain@localhost:5432/brain"
    )


async def run_forever(*, poll_interval_seconds: float = 1.0, batch_limit: int = 100) -> None:
    """Poll the outbox and mark events processed (F0001-S0005). If the process is
    killed mid-batch, the next `run_once` call picks up exactly the events still
    unprocessed — `OutboxProjector` is idempotent by construction, so a killed
    worker never double-projects or drops an event."""
    engine = make_engine(_database_url())
    session_factory = make_session_factory(engine)

    while True:
        async with session_factory() as session:
            reader = SqlAlchemyOutboxReader(session)
            projector = OutboxProjector(reader)
            processed = await projector.run_once(now=datetime.now(UTC), limit=batch_limit)
            await session.commit()
        if processed:
            logger.info("processed %d outbox event(s)", processed)
        await asyncio.sleep(poll_interval_seconds)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_forever())


if __name__ == "__main__":
    main()
