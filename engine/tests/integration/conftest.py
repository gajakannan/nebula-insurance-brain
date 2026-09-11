from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from brain_domain.principal import Membership, Principal, PrincipalKind, PrincipalStatus
from brain_persistence.models import (
    CanonicalFactChangeRow,
    CanonicalFactVersionRow,
    FactSlotRow,
    OutboxEventRow,
)
from brain_persistence.session import make_engine, make_session_factory
from brain_security.audit import InMemoryAuditEventRepository, RepositoryAuditSink
from brain_security.authorization import AuthorizationService
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = REPO_ROOT / "planning-mds" / "security" / "policies" / "model.conf"
POLICY_PATH = REPO_ROOT / "planning-mds" / "security" / "policies" / "policy.csv"


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
        for row in (OutboxEventRow, CanonicalFactChangeRow, CanonicalFactVersionRow, FactSlotRow):
            await session.execute(text(f"TRUNCATE TABLE {row.__tablename__} CASCADE"))
        await session.commit()


@pytest.fixture
def authz() -> AuthorizationService:
    return AuthorizationService(
        CasbinAuthorizationAdapter(MODEL_PATH, POLICY_PATH),
        RepositoryAuditSink(InMemoryAuditEventRepository()),
    )


@pytest.fixture
def tenant_id() -> UUID:
    return uuid4()


@pytest.fixture
def knowledge_base_id() -> UUID:
    return uuid4()


@pytest.fixture
def actor() -> Principal:
    return Principal(
        id=uuid4(),
        kind=PrincipalKind.SERVICE,
        issuer="authentik",
        subject="svc",
        status=PrincipalStatus.ACTIVE,
    )


@pytest.fixture
def membership(actor: Principal, tenant_id: UUID, knowledge_base_id: UUID) -> Membership:
    return Membership(
        principal_id=actor.id,
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
        role="ServicePrincipal",
        grant_revision=1,
        revoked_at=None,
    )


@pytest.fixture
async def slot_id(
    pg_session_factory: async_sessionmaker[AsyncSession],
    tenant_id: UUID,
    knowledge_base_id: UUID,
) -> UUID:
    new_slot_id = uuid4()
    async with pg_session_factory() as session:
        session.add(
            FactSlotRow(
                id=new_slot_id,
                entity_id=uuid4(),
                slot_type="each_occurrence_limit",
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
            )
        )
        await session.commit()
    return new_slot_id
