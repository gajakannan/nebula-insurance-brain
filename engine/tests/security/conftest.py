"""Shared fixtures for F0001-S0006's access-boundary proof. These tests exercise
the real HTTP layer (`brain_api`) against the live compose Postgres — skipped,
not failed, when it isn't reachable — using a real RSA-signed JWT verified by a
fake-JWKS-but-real-crypto verifier (the same pattern `apps/api/tests/*.py`
established at S0004), and `httpx.AsyncClient`/ASGI transport rather than
FastAPI's synchronous `TestClient`, because `asyncpg` connections are bound to
the event loop that created them and break across `TestClient`'s worker-thread
portal (found at S0005, see `apps/api/tests/test_facts.py`).
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit
from uuid import UUID

import httpx2 as httpx
import jwt
import pytest
import pytest_asyncio
from brain_domain.authx import PilotRole
from brain_domain.principal import PrincipalKind
from brain_persistence import fixtures
from brain_persistence.session import make_engine, make_session_factory, session_scope
from brain_security.identity_profile import IdentityProfile, IssuerProfile
from brain_security.verification import VerifiedCredential, decode_verified
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWK
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from brain_api.app import create_app
from brain_api.deps import (
    get_content_store,
    get_credential_verifier,
    get_db_session,
    get_identity_profile,
    get_session_factory,
)

ISSUER = "https://authentik.local/application/o/brain/"
AUDIENCE = "brain"
HUMAN_CLIENT = "brain"
REPO_ROOT = Path(__file__).resolve().parents[3]
POLICIES = REPO_ROOT / "planning-mds" / "security" / "policies"
ISSUER_PROFILE = IssuerProfile(
    issuer=ISSUER, audiences=frozenset({AUDIENCE}), human_clients=frozenset({HUMAN_CLIENT})
)
IDENTITY_PROFILE = IdentityProfile((ISSUER_PROFILE,))


def _database_url() -> str:
    return os.environ.get(
        "BRAIN_DATABASE_URL", "postgresql+asyncpg://brain:brain@localhost:5432/brain"
    )


def make_token(rsa_key: rsa.RSAPrivateKey, subject: str, **claim_overrides: object) -> str:
    now = datetime.now(UTC)
    claims: dict[str, object] = {
        "iss": ISSUER,
        "sub": subject,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "azp": HUMAN_CLIENT,
    }
    claims.update(claim_overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, rsa_key, algorithm="RS256", headers={"kid": "test-key-1"})


class FakeVerifier:
    """A real `OidcJwksVerifier`-shaped verifier that trusts a fixed test key
    instead of fetching JWKS over the network — same crypto path (`jwt.decode`
    with issuer/audience/expiry/not-before checks), no live authentik dependency."""

    def __init__(self, rsa_key: rsa.RSAPrivateKey) -> None:
        self._rsa_key = rsa_key

    def _signing_key(self) -> PyJWK:
        return PyJWK.from_json(
            json.dumps(
                {
                    "kty": "RSA",
                    "kid": "test-key-1",
                    "n": jwt.utils.to_base64url_uint(
                        self._rsa_key.public_key().public_numbers().n
                    ).decode(),
                    "e": jwt.utils.to_base64url_uint(
                        self._rsa_key.public_key().public_numbers().e
                    ).decode(),
                }
            ),
            algorithm="RS256",
        )

    async def verify(self, bearer_token: str) -> VerifiedCredential:
        # Real signature/issuer/audience/time/required-claim checks via the same
        # `decode_verified` the production verifier uses; only JWKS fetch is faked.
        return decode_verified(
            bearer_token, self._signing_key().key, ISSUER_PROFILE, key_id="test-key-1"
        )


class FakeContentStore:
    """Enough of `ContentArtifactStore` to prove a 200/404 without touching a
    real filesystem — the object-store adapter itself is proven in S0002/S0004.
    Records every manifest/byte access so tests can prove nothing protected is
    opened before an allow decision (F0002-S0004 AC7)."""

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {"source.pdf": b"%PDF-1.4 fake bytes"}
        self.manifest_reads: list[UUID] = []
        self.file_reads: list[tuple[UUID, str]] = []

    async def get_manifest(self, artifact_id: UUID) -> SimpleNamespace:
        self.manifest_reads.append(artifact_id)
        files = [SimpleNamespace(path=path) for path in self._files]
        body = json.dumps({"artifact_id": str(artifact_id), "files": sorted(self._files)})
        return SimpleNamespace(files=files, model_dump_json=lambda: body)

    async def open_file(self, artifact_id: UUID, path: str) -> bytes:
        self.file_reads.append((artifact_id, path))
        return self._files[path]


@pytest.fixture(scope="module")
def rsa_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest_asyncio.fixture
async def pg_session_factory() -> async_sessionmaker[AsyncSession]:
    parsed_url = urlsplit(_database_url())
    try:
        with socket.create_connection(
            (parsed_url.hostname or "localhost", parsed_url.port or 5432), timeout=2
        ):
            pass
    except OSError as exc:
        pytest.skip(f"Postgres not reachable at {_database_url()}: {exc}")

    engine = make_engine(_database_url())
    try:
        connection = await asyncio.wait_for(engine.connect(), timeout=5)
        try:
            await asyncio.wait_for(connection.execute(text("SELECT 1")), timeout=5)
        finally:
            await connection.close()
    except Exception as exc:  # noqa: BLE001 - any connection failure means "skip"
        with suppress(TimeoutError):
            await asyncio.wait_for(engine.dispose(), timeout=5)
        pytest.skip(f"Postgres not reachable at {_database_url()}: {exc}")
    session_factory = make_session_factory(engine)
    async with session_scope(session_factory) as session:
        await session.run_sync(
            fixtures.activate_policy, POLICIES / "model.conf", POLICIES / "policy.csv"
        )
    yield session_factory

    async with session_factory() as session:
        await session.execute(
            text(
                "TRUNCATE TABLE outbox_event, canonical_fact_change, canonical_fact_version, "
                "canonical_commit, fact_slot, review_decision, review_item, review_batch, "
                "assertion_evidence, assertion, semantic_interpretation_run, content_artifact, "
                "document_version, source_document, resource_access, delegation, membership, "
                "entity_knowledge_base, entity_identity, external_identity, principal_authority, "
                "principal, knowledge_base, workspace, tenant, authentication_event, "
                "policy_release_pointer, policy_release CASCADE"
            )
        )
        await session.commit()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(rsa_key: rsa.RSAPrivateKey, pg_session_factory: async_sessionmaker[AsyncSession]):
    app = create_app()

    async def override_get_db_session():
        async with session_scope(pg_session_factory) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_session_factory] = lambda: pg_session_factory
    app.dependency_overrides[get_credential_verifier] = lambda: FakeVerifier(rsa_key)
    app.dependency_overrides[get_identity_profile] = lambda: IDENTITY_PROFILE
    content_store = FakeContentStore()
    app.dependency_overrides[get_content_store] = lambda: content_store

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as test_client:
        test_client.session_factory = pg_session_factory  # type: ignore[attr-defined]
        test_client.content_store = content_store  # type: ignore[attr-defined]
        test_client.app = app  # type: ignore[attr-defined]
        yield test_client


async def seed_principal(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    issuer: str = ISSUER,
    subject: str,
    kind: PrincipalKind = PrincipalKind.USER,
) -> UUID:
    async with session_scope(session_factory) as session:
        principal = await session.run_sync(
            lambda s: fixtures.seed_principal(s, issuer=issuer, subject=subject, kind=kind)
        )
        return principal.id


async def seed_grant(
    session_factory: async_sessionmaker[AsyncSession],
    principal_id: UUID,
    *,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    role: str = "TenantMember",
    **slice_fields: object,
) -> UUID:
    async with session_scope(session_factory) as session:
        return await session.run_sync(
            lambda s: fixtures.seed_grant(
                s, principal_id, tenant_id, knowledge_base_id, PilotRole(role), **slice_fields
            )
        )


async def seed_principal_and_membership(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    issuer: str = ISSUER,
    subject: str,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    role: str = "TenantMember",
    kind: PrincipalKind = PrincipalKind.USER,
) -> UUID:
    principal_id = await seed_principal(session_factory, issuer=issuer, subject=subject, kind=kind)
    await seed_grant(
        session_factory,
        principal_id,
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
        role=role,
    )
    return principal_id


async def seed_content_artifact(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    **restrictions: object,
) -> UUID:
    async with session_scope(session_factory) as session:
        return await session.run_sync(
            lambda s: fixtures.seed_content_artifact(
                s, tenant_id, knowledge_base_id, **restrictions
            )
        )


async def seed_review_item(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    assembling_principal_id: UUID,
    **restrictions: object,
) -> UUID:
    item_id, _ = await seed_review_item_in_batch(
        session_factory,
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
        assembling_principal_id=assembling_principal_id,
        **restrictions,
    )
    return item_id


async def seed_review_item_in_batch(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    assembling_principal_id: UUID,
    batch_id: UUID | None = None,
    **restrictions: object,
) -> tuple[UUID, UUID]:
    async with session_scope(session_factory) as session:
        return await session.run_sync(
            lambda s: fixtures.seed_review_item(
                s,
                tenant_id,
                knowledge_base_id,
                assembling_principal_id=assembling_principal_id,
                batch_id=batch_id,
                **restrictions,
            )
        )


async def seed_fact_slot(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    **restrictions: object,
) -> UUID:
    async with session_scope(session_factory) as session:
        return await session.run_sync(
            lambda s: fixtures.seed_fact_slot(s, tenant_id, knowledge_base_id, **restrictions)
        )


def bearer(rsa_key: rsa.RSAPrivateKey, subject: str, **claims: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(rsa_key, subject, **claims)}"}


async def run_sync(session_factory: async_sessionmaker[AsyncSession], fn):  # noqa: ANN001, ANN201
    """Run a trusted operational function in its own committed transaction."""
    async with session_scope(session_factory) as session:
        return await session.run_sync(fn)


async def decisions_for(
    session_factory: async_sessionmaker[AsyncSession], resource_id: UUID
) -> list[dict]:
    """Durable v1 authorization decisions for one resource, oldest first."""
    async with session_factory() as session:
        rows = await session.execute(
            text(
                "SELECT payload FROM audit_event WHERE event_type = 'authorization_decision' "
                "AND resource_id = :rid ORDER BY occurred_at, payload->>'decision_id'"
            ),
            {"rid": resource_id},
        )
        return [row.payload for row in rows]


class StatementLog:
    """Captures SQL issued on the test engine (instrumented repository proof)."""

    def __init__(self) -> None:
        self.statements: list[str] = []

    def __call__(self, conn, cursor, statement, parameters, context, executemany) -> None:  # noqa: ANN001
        self.statements.append(" ".join(statement.split()).lower())

    def touching(self, *tables: str) -> list[str]:
        return [s for s in self.statements if any(f" {t}" in s for t in tables)]


def sync_engine_of(session_factory: async_sessionmaker[AsyncSession]):  # noqa: ANN201
    return session_factory.kw["bind"].sync_engine


class FailOn:
    """`before_cursor_execute` hook that raises for statements starting with a prefix
    (failure injection for audit/authority storage)."""

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix.lower()
        self.armed = True

    def __call__(self, conn, cursor, statement, parameters, context, executemany) -> None:  # noqa: ANN001
        if self.armed and " ".join(statement.split()).lower().startswith(self.prefix):
            raise RuntimeError(f"injected failure: {self.prefix}")
