"""F0007 PostgreSQL harness: an owned database per test, migrated to head.

Never touches the shared development database. Requires
`BRAIN_MIGRATION_ADMIN_URL` (skips without it, like the F0006 suites).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import httpx2 as httpx
import psycopg
import pytest
from alembic import command
from brain_domain.authx import ResourceKey, ResourceType
from brain_domain.principal import Principal, PrincipalKind
from brain_factslots.answers import FactAnswerReader
from brain_factslots.names import NameFactReader
from brain_factslots.resolution import FactSlotResolver
from brain_factslots.service import AuthorizedFactSlots
from brain_persistence.authx import SqlAlchemyAuthorityStore
from brain_persistence.fact_slots import SqlAlchemyFactSlotStore
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_security.execution import AuthorizationExecution
from brain_testing import fixtures
from brain_testing.factslots import seed_subject, slot_key, test_registry
from engine.tests.fixtures.assertions import harness as f0006
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session

from brain_api.app import create_app
from brain_api.deps import current_principal, get_db_session, get_predicate_registry

PRODUCT = Path(__file__).resolve().parents[4]
POLICIES = PRODUCT / "planning-mds/security/policies"
FIXTURES = Path(__file__).resolve().parent

_clean_fact_tables = f0006._clean_fact_tables
database = f0006.database
configuration = f0006.configuration


@dataclass
class Owner:
    tenant_id: UUID
    knowledge_base_id: UUID
    artifact_id: UUID

    @property
    def scope(self) -> tuple[UUID, UUID]:
        return (self.tenant_id, self.knowledge_base_id)


class FactSlotWorld:
    """Tenant T with KB A and KB B; entity E associated with both."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.sync_engine = create_engine(url.replace("postgresql://", "postgresql+psycopg://"))
        self.engine = create_async_engine(url.replace("postgresql://", "postgresql+asyncpg://"))
        self.policy = CasbinAuthorizationAdapter(POLICIES / "model.conf", POLICIES / "policy.csv")
        self.registry = test_registry()
        tenant = uuid4()
        with Session(self.sync_engine) as session, session.begin():
            fixtures.activate_policy(session, POLICIES / "model.conf", POLICIES / "policy.csv")
            kb_a, kb_b = uuid4(), uuid4()
            fixtures.seed_scope(session, tenant, kb_a)
            fixtures.seed_scope(session, tenant, kb_b)
            self.a = Owner(tenant, kb_a, fixtures.seed_content_artifact(session, tenant, kb_a))
            self.b = Owner(tenant, kb_b, fixtures.seed_content_artifact(session, tenant, kb_b))
            self.subject = seed_subject(session, tenant, [kb_a, kb_b])
            self.service = self._principal(session, "service", PrincipalKind.SERVICE, [self.a])
            self.service_b = self._principal(session, "service-b", PrincipalKind.SERVICE, [self.b])
            self.reader_b = self._principal(
                session, "reader-b", PrincipalKind.USER, [self.b], roles=("TenantMember",)
            )

    def _principal(
        self,
        session: Session,
        name: str,
        kind: PrincipalKind,
        owners: list[Owner],
        roles: tuple[str, ...] = ("ServicePrincipal", "TenantMember"),
    ) -> Principal:
        principal = fixtures.seed_principal(
            session, issuer="urn:f0007:test", subject=f"{name}-{uuid4()}", kind=kind
        )
        for owner in owners:
            for role in roles:
                fixtures.seed_grant(session, principal.id, *owner.scope, role)
        return principal

    def entity(self, *owners: Owner) -> UUID:
        with Session(self.sync_engine) as session, session.begin():
            return seed_subject(session, self.a.tenant_id, [o.knowledge_base_id for o in owners])

    def artifact(self, owner: Owner, **restrictions: object) -> UUID:
        with Session(self.sync_engine) as session, session.begin():
            return fixtures.seed_content_artifact(
                session, owner.tenant_id, owner.knowledge_base_id, **restrictions
            )

    def key(self, owner: Owner, predicate, subject: UUID | None = None, **kwargs):  # type: ignore[no-untyped-def]
        return slot_key(owner.knowledge_base_id, subject or self.subject, predicate, **kwargs)

    @asynccontextmanager
    async def slots(self, *, fingerprint=None, registry=None):  # type: ignore[no-untyped-def]
        async with AsyncSession(self.engine, expire_on_commit=False) as session:
            store = SqlAlchemyFactSlotStore(session)
            kwargs = {"fingerprint": fingerprint} if fingerprint else {}
            resolver = FactSlotResolver(registry or self.registry, store, **kwargs)
            execution = AuthorizationExecution(
                SqlAlchemyAuthorityStore(session), self.policy, self.policy.release
            )
            yield AuthorizedFactSlots(
                execution, resolver, NameFactReader(store), FactAnswerReader(store)
            )

    async def resolve(  # type: ignore[no-untyped-def]
        self, key, *, principal=None, sources=None, owner=None, fingerprint=None, registry=None
    ):
        owner = owner or self.a
        async with self.slots(fingerprint=fingerprint, registry=registry) as service:
            return await service.resolve(
                principal or self.service,
                key,
                source_artifact_ids=sources or [owner.artifact_id],
                trace_id="f0007-test",
            )

    def client(self, principal: Principal):  # type: ignore[no-untyped-def]
        app = create_app()

        async def session_override():  # type: ignore[no-untyped-def]
            async with AsyncSession(self.engine, expire_on_commit=False) as session:
                yield session

        app.dependency_overrides[get_db_session] = session_override
        app.dependency_overrides[current_principal] = lambda: principal
        app.dependency_overrides[get_predicate_registry] = lambda: self.registry
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")

    async def commit(self, slot_id: UUID, value: dict, *, principal=None, valid_from=None):  # type: ignore[no-untyped-def]
        now = datetime.now(UTC)
        start = valid_from or now - timedelta(days=1)
        body = {
            "value": value,
            "valid_from": start.isoformat(),
            "valid_to": None,
            "change_reason": None,
            "evidence_refs": [],
            "review_decision_id": None,
            "source_received_at": now.isoformat(),
            "artifact_created_at": now.isoformat(),
            "assertion_created_at": now.isoformat(),
            "expected_current_version_id": None,
            "idempotency_key": f"f0007-{uuid4()}",
        }
        async with self.client(principal or self.service) as client:
            return await client.post(f"/facts/{slot_id}/commits", json=body)

    async def get(self, slot_id: UUID, *, principal=None):  # type: ignore[no-untyped-def]
        async with self.client(principal or self.service) as client:
            return await client.get(f"/facts/{slot_id}")

    def scalar(self, sql: str, *params: object):  # type: ignore[no-untyped-def]
        with psycopg.connect(self.url) as connection:
            row = connection.execute(sql, params).fetchone()
            return row[0] if row else None

    def rows(self, sql: str, *params: object) -> list[tuple]:
        with psycopg.connect(self.url) as connection:
            return list(connection.execute(sql, params).fetchall())

    def counts(self) -> dict[str, int]:
        return {
            t: self.scalar(f"SELECT count(*) FROM {t}")
            for t in (
                "fact_slot",
                "fact_slot_qualifier",
                "canonical_fact_version",
                "canonical_commit",
            )
        }

    def access(self, slot_id: UUID) -> tuple:
        return self.rows(
            "SELECT classifications, source_acl_ids, dependency_keys FROM resource_access "
            "WHERE resource_type = 'fact_slot' AND resource_id = %s",
            slot_id,
        )[0]

    async def close(self) -> None:
        await self.engine.dispose()
        self.sync_engine.dispose()


def artifact_key(artifact_id: UUID) -> ResourceKey:
    return ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact_id)


@pytest.fixture
async def slot_world(database):  # type: ignore[no-untyped-def]
    command.upgrade(configuration(), "head")
    world = FactSlotWorld(database)
    try:
        yield world
    finally:
        await world.close()
