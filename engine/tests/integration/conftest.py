from __future__ import annotations

import os
from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from brain_persistence.session import make_engine, make_session_factory, session_scope
from brain_testing import fixtures
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def _database_url() -> str:
    return os.environ.get(
        "BRAIN_DATABASE_URL", "postgresql+asyncpg://brain:brain@localhost:5432/brain"
    )


@pytest.fixture
async def pg_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Skips the test (not a failure) when the compose Postgres isn't reachable —
    same "skip, don't fail" convention as F0001-S0003's live vLLM proof, since
    these tables (`canonical_fact_version`'s `tstzrange` + gist exclusion
    constraint) only exist against real Postgres, never sqlite. Function-scoped:
    pytest-asyncio gives each test its own event loop, and an asyncpg engine
    can't be reused across loops."""
    engine = make_engine(_database_url())
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - any connection failure means "skip"
        pytest.skip(f"Postgres not reachable at {_database_url()}: {exc}")
    yield make_session_factory(engine)
    await engine.dispose()


@pytest.fixture(autouse=True)
async def _clean_fact_tables(
    pg_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[None]:
    yield
    async with pg_session_factory() as session:
        await session.execute(
            text(
                "TRUNCATE TABLE outbox_event, canonical_fact_change, canonical_fact_version, "
                "canonical_commit, resource_access, fact_slot CASCADE"
            )
        )
        await session.commit()


@pytest.fixture
def tenant_id() -> UUID:
    return uuid4()


@pytest.fixture
def knowledge_base_id() -> UUID:
    return uuid4()


@pytest.fixture
def owner(tenant_id: UUID, knowledge_base_id: UUID) -> tuple[UUID, UUID]:
    """The scope `CanonicalCommitService` is told was authorized (F0002: the facade
    authorizes; these tests prove the temporal algorithm on real PostgreSQL)."""
    return (tenant_id, knowledge_base_id)


@pytest.fixture
async def slot_id(
    pg_session_factory: async_sessionmaker[AsyncSession],
    tenant_id: UUID,
    knowledge_base_id: UUID,
) -> UUID:
    async with session_scope(pg_session_factory) as session:
        return await session.run_sync(
            lambda s: fixtures.seed_fact_slot(s, tenant_id, knowledge_base_id)
        )
