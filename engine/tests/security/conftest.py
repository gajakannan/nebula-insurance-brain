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
from types import SimpleNamespace
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import httpx2 as httpx
import jwt
import pytest
import pytest_asyncio
from brain_persistence.models import (
    Assertion,
    ContentArtifact,
    DocumentVersion,
    FactSlotRow,
    MembershipRow,
    PrincipalRow,
    ReviewBatchRow,
    ReviewItemRow,
    SourceDocument,
)
from brain_persistence.session import make_engine, make_session_factory, session_scope
from brain_security.verification import VerifiedCredential
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWK
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from brain_api.app import create_app
from brain_api.deps import get_content_store, get_credential_verifier, get_db_session

ISSUER = "https://authentik.local/application/o/brain/"
AUDIENCE = "brain"


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
    }
    claims.update(claim_overrides)
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
        from brain_security.verification import CredentialError

        try:
            signing_key = self._signing_key()
            payload = jwt.decode(
                bearer_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=AUDIENCE,
                issuer=ISSUER,
            )
        except jwt.ExpiredSignatureError as exc:
            raise CredentialError("expired", str(exc)) from exc
        except jwt.InvalidAudienceError as exc:
            raise CredentialError("wrong_audience", str(exc)) from exc
        except jwt.InvalidIssuerError as exc:
            raise CredentialError("wrong_issuer", str(exc)) from exc
        except jwt.ImmatureSignatureError as exc:
            raise CredentialError("not_yet_valid", str(exc)) from exc
        except jwt.InvalidTokenError as exc:
            raise CredentialError("invalid_signature", str(exc)) from exc
        return VerifiedCredential(
            issuer=payload["iss"],
            subject=payload["sub"],
            audience=AUDIENCE,
            expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
            not_before=None,
            key_id="test-key-1",
        )


class FakeContentStore:
    """Enough of `ContentArtifactStore` to prove a 200/404 without touching a
    real filesystem — the object-store adapter itself is proven in S0002/S0004."""

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {"source.pdf": b"%PDF-1.4 fake bytes"}

    async def get_manifest(self, artifact_id: UUID) -> SimpleNamespace:
        return SimpleNamespace(files=[SimpleNamespace(path=path) for path in self._files])

    async def open_file(self, artifact_id: UUID, path: str) -> bytes:
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
    yield session_factory

    async with session_factory() as session:
        await session.execute(
            text(
                "TRUNCATE TABLE outbox_event, canonical_fact_change, canonical_fact_version, "
                "fact_slot, review_decision, review_item, review_batch, content_artifact, "
                "document_version, source_document, membership, principal CASCADE"
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
    app.dependency_overrides[get_credential_verifier] = lambda: FakeVerifier(rsa_key)
    app.dependency_overrides[get_content_store] = lambda: FakeContentStore()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as test_client:
        test_client.session_factory = pg_session_factory  # type: ignore[attr-defined]
        yield test_client


async def seed_principal_and_membership(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    issuer: str = ISSUER,
    subject: str,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    role: str = "TenantMember",
) -> UUID:
    async with session_scope(session_factory) as session:
        principal_row = PrincipalRow(
            id=uuid4(), kind="user", issuer=issuer, subject=subject, status="active"
        )
        session.add(principal_row)
        await session.flush()
        session.add(
            MembershipRow(
                id=uuid4(),
                principal_id=principal_row.id,
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                role=role,
                grant_revision=1,
                revoked_at=None,
            )
        )
        return principal_row.id


async def seed_content_artifact(
    session_factory: async_sessionmaker[AsyncSession], *, tenant_id: UUID, knowledge_base_id: UUID
) -> UUID:
    async with session_scope(session_factory) as session:
        source = SourceDocument(
            tenant_id=tenant_id, knowledge_base_id=knowledge_base_id, source_sha256=uuid4().hex
        )
        session.add(source)
        await session.flush()
        version = DocumentVersion(source_document_id=source.id)
        session.add(version)
        await session.flush()
        artifact = ContentArtifact(
            id=uuid4(),
            document_version_id=version.id,
            artifact_sha256=uuid4().hex,
            page_count=1,
            extraction_status="complete",
        )
        session.add(artifact)
        await session.flush()
        return artifact.id


async def seed_review_item(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    assembling_principal_id: UUID,
) -> UUID:
    async with session_scope(session_factory) as session:
        assertion = Assertion(
            id=uuid4(),
            run_id=None,
            origin="MACHINE_EXTRACTION",
            subject_type="Policy",
            slot_type="each_occurrence_limit",
            value={"value": "$20,000,000"},
            model_confidence=0.41,
            interpretation_basis="EXPLICIT",
        )
        session.add(assertion)
        await session.flush()
        batch = ReviewBatchRow(id=uuid4(), assembling_principal_id=assembling_principal_id)
        session.add(batch)
        await session.flush()
        item = ReviewItemRow(
            id=uuid4(),
            type="LOW_CONFIDENCE_ASSERTION",
            status="open",
            assertion_id=assertion.id,
            assertion_version=1,
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
            review_batch_id=batch.id,
        )
        session.add(item)
        await session.flush()
        return item.id


async def seed_fact_slot(
    session_factory: async_sessionmaker[AsyncSession], *, tenant_id: UUID, knowledge_base_id: UUID
) -> UUID:
    async with session_scope(session_factory) as session:
        slot = FactSlotRow(
            id=uuid4(),
            entity_id=uuid4(),
            slot_type="each_occurrence_limit",
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
        )
        session.add(slot)
        await session.flush()
        return slot.id
