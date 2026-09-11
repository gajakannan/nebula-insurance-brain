"""HTTP-layer proof for F0001-S0005's `/facts` routes. `canonical_fact_version`
only exists against real Postgres (`tstzrange` + gist exclusion constraint), so
unlike `test_reviews.py`/`test_content.py`'s sqlite fixture, this runs against
the live compose Postgres — skipped, not failed, when it isn't reachable.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx2 as httpx
import jwt
import pytest
import pytest_asyncio
from brain_persistence.models import FactSlotRow
from brain_persistence.session import make_engine, make_session_factory, session_scope
from brain_security.verification import VerifiedCredential
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWK
from sqlalchemy import text

from brain_api.app import create_app
from brain_api.deps import get_credential_verifier, get_db_session

ISSUER = "https://authentik.local/application/o/brain/"
AUDIENCE = "brain"


def _database_url() -> str:
    return os.environ.get(
        "BRAIN_DATABASE_URL", "postgresql+asyncpg://brain:brain@localhost:5432/brain"
    )


@pytest.fixture(scope="module")
def rsa_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _make_token(rsa_key: rsa.RSAPrivateKey, subject: str) -> str:
    now = datetime.now(UTC)
    claims = {
        "iss": ISSUER,
        "sub": subject,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    return jwt.encode(claims, rsa_key, algorithm="RS256", headers={"kid": "test-key-1"})


class _FakeVerifier:
    def __init__(self, rsa_key: rsa.RSAPrivateKey) -> None:
        self._rsa_key = rsa_key

    async def verify(self, bearer_token: str) -> VerifiedCredential:
        import json

        signing_key = PyJWK.from_json(
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
        payload = jwt.decode(
            bearer_token, signing_key.key, algorithms=["RS256"], audience=AUDIENCE, issuer=ISSUER
        )
        return VerifiedCredential(
            issuer=payload["iss"],
            subject=payload["sub"],
            audience=AUDIENCE,
            expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
            not_before=None,
            key_id="test-key-1",
        )


@pytest_asyncio.fixture
async def client(rsa_key: rsa.RSAPrivateKey):
    engine = make_engine(_database_url())
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - any connection failure means "skip"
        await engine.dispose()
        pytest.skip(f"Postgres not reachable at {_database_url()}: {exc}")
    session_factory = make_session_factory(engine)

    app = create_app()

    async def override_get_db_session():
        # `brain_api.deps` builds its own module-level engine bound to whatever
        # event loop was running at import time; TestClient gives each test a
        # fresh loop, so reusing that shared engine here would hand asyncpg
        # connections across loops. Route through this test's own engine instead.
        async with session_scope(session_factory) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_credential_verifier] = lambda: _FakeVerifier(rsa_key)

    # A synchronous `TestClient` runs the ASGI app on a separate thread's event
    # loop (via an anyio portal); asyncpg's connections are bound tightly to the
    # loop that created them and break across that thread boundary. An async
    # httpx client run on this same test's event loop avoids that entirely.
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as test_client:
        test_client.session_factory = session_factory  # type: ignore[attr-defined]
        yield test_client

    async with session_factory() as session:
        await session.execute(
            text(
                "TRUNCATE TABLE outbox_event, canonical_fact_change, canonical_fact_version, "
                "fact_slot, membership, principal CASCADE"
            )
        )
        await session.commit()
    await engine.dispose()


async def _seed_fact_slot(session_factory, *, tenant_id, kb_id) -> object:
    slot_id = uuid4()
    async with session_scope(session_factory) as session:
        session.add(
            FactSlotRow(
                id=slot_id,
                entity_id=uuid4(),
                slot_type="each_occurrence_limit",
                tenant_id=tenant_id,
                knowledge_base_id=kb_id,
            )
        )
    return slot_id


async def _seed_service_principal(session_factory, *, tenant_id, kb_id, subject: str) -> None:
    from brain_persistence.models import MembershipRow, PrincipalRow

    async with session_scope(session_factory) as session:
        principal_row = PrincipalRow(
            id=uuid4(), kind="service", issuer=ISSUER, subject=subject, status="active"
        )
        session.add(principal_row)
        await session.flush()
        session.add(
            MembershipRow(
                id=uuid4(),
                principal_id=principal_row.id,
                tenant_id=tenant_id,
                knowledge_base_id=kb_id,
                role="ServicePrincipal",
                grant_revision=1,
                revoked_at=None,
            )
        )


async def test_commit_then_get_round_trips_through_http(client, rsa_key: rsa.RSAPrivateKey) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    slot_id = await _seed_fact_slot(client.session_factory, tenant_id=tenant_id, kb_id=kb_id)
    await _seed_service_principal(
        client.session_factory, tenant_id=tenant_id, kb_id=kb_id, subject="svc-http"
    )
    token = _make_token(rsa_key, subject="svc-http")
    headers = {"Authorization": f"Bearer {token}"}

    commit_response = await client.post(
        f"/facts/{slot_id}/commits",
        headers=headers,
        json={
            "value": {"amount": "2000000.00"},
            "valid_from": "2026-01-01T00:00:00Z",
            "evidence_refs": [str(uuid4())],
            "source_received_at": "2026-01-10T00:00:00Z",
            "artifact_created_at": "2026-01-10T00:00:00Z",
            "assertion_created_at": "2026-01-10T00:00:00Z",
            "idempotency_key": "commit-http-0001",
        },
    )
    assert commit_response.status_code == 201
    body = commit_response.json()
    assert len(body["fact_version_ids"]) == 1

    get_response = await client.get(
        f"/facts/{slot_id}", headers=headers, params={"validAsOf": "2026-06-01T00:00:00Z"}
    )
    assert get_response.status_code == 200
    assert get_response.json()["value"] == {"amount": "2000000.00"}


async def test_commit_with_empty_range_returns_400(client, rsa_key: rsa.RSAPrivateKey) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    slot_id = await _seed_fact_slot(client.session_factory, tenant_id=tenant_id, kb_id=kb_id)
    await _seed_service_principal(
        client.session_factory, tenant_id=tenant_id, kb_id=kb_id, subject="svc-invalid-range"
    )
    token = _make_token(rsa_key, subject="svc-invalid-range")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        f"/facts/{slot_id}/commits",
        headers=headers,
        json={
            "value": {"amount": "1"},
            "valid_from": "2026-06-01T00:00:00Z",
            "valid_to": "2026-06-01T00:00:00Z",
            "evidence_refs": [str(uuid4())],
            "source_received_at": "2026-01-10T00:00:00Z",
            "artifact_created_at": "2026-01-10T00:00:00Z",
            "assertion_created_at": "2026-01-10T00:00:00Z",
            "idempotency_key": "commit-http-0002",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_range"


async def test_commit_with_stale_expected_version_returns_409(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    slot_id = await _seed_fact_slot(client.session_factory, tenant_id=tenant_id, kb_id=kb_id)
    await _seed_service_principal(
        client.session_factory, tenant_id=tenant_id, kb_id=kb_id, subject="svc-stale"
    )
    token = _make_token(rsa_key, subject="svc-stale")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        f"/facts/{slot_id}/commits",
        headers=headers,
        json={
            "value": {"amount": "1"},
            "valid_from": "2026-01-01T00:00:00Z",
            "evidence_refs": [str(uuid4())],
            "source_received_at": "2026-01-10T00:00:00Z",
            "artifact_created_at": "2026-01-10T00:00:00Z",
            "assertion_created_at": "2026-01-10T00:00:00Z",
            "expected_current_version_id": str(uuid4()),
            "idempotency_key": "commit-http-0003",
        },
    )

    assert response.status_code == 409
    assert response.json()["code"] == "stale_version"


async def test_get_fact_for_slot_without_membership_is_404(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    slot_id = await _seed_fact_slot(client.session_factory, tenant_id=tenant_id, kb_id=kb_id)
    token = _make_token(rsa_key, subject="stranger")

    response = await client.get(f"/facts/{slot_id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
