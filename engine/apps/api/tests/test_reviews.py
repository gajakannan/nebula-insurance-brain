from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import jwt
import pytest
import pytest_asyncio
from brain_domain.authx import PilotRole
from brain_domain.principal import PrincipalKind
from brain_persistence import fixtures
from brain_persistence.base import Base, sqlite_test_tables
from brain_persistence.session import make_engine, make_session_factory, session_scope
from brain_security.identity_profile import IdentityProfile, IssuerProfile
from brain_security.verification import VerifiedCredential, decode_verified
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jwt import PyJWK

from brain_api.app import create_app
from brain_api.deps import (
    get_credential_verifier,
    get_db_session,
    get_identity_profile,
    get_session_factory,
)

ISSUER = "https://authentik.local/application/o/brain/"
AUDIENCE = "brain"
ISSUER_PROFILE = IssuerProfile(
    issuer=ISSUER, audiences=frozenset({AUDIENCE}), human_clients=frozenset({"brain"})
)
IDENTITY_PROFILE = IdentityProfile((ISSUER_PROFILE,))
POLICIES = Path(__file__).resolve().parents[4] / "planning-mds" / "security" / "policies"


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
        "azp": "brain",
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
        return decode_verified(bearer_token, signing_key.key, ISSUER_PROFILE, key_id="test-key-1")


@pytest_asyncio.fixture
async def client(rsa_key: rsa.RSAPrivateKey):
    engine = make_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all, tables=sqlite_test_tables())
    session_factory = make_session_factory(engine)
    async with session_scope(session_factory) as session:
        await session.run_sync(
            fixtures.activate_policy, POLICIES / "model.conf", POLICIES / "policy.csv"
        )

    app = create_app()

    async def override_get_db_session():
        async with session_scope(session_factory) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_credential_verifier] = lambda: _FakeVerifier(rsa_key)
    app.dependency_overrides[get_identity_profile] = lambda: IDENTITY_PROFILE
    app.dependency_overrides[get_session_factory] = lambda: session_factory

    with TestClient(app) as test_client:
        test_client.session_factory = session_factory  # type: ignore[attr-defined]
        yield test_client

    await engine.dispose()


async def _seed_user(session_factory, *, subject, tenant_id, kb_id, role, kind=PrincipalKind.USER):
    async with session_scope(session_factory) as session:

        def seed(s):
            principal = fixtures.seed_principal(s, issuer=ISSUER, subject=subject, kind=kind)
            fixtures.seed_grant(s, principal.id, tenant_id, kb_id, PilotRole(role))
            return principal.id

        return await session.run_sync(seed)


async def _seed_review_item(session_factory, *, tenant_id, kb_id, role: str, subject: str) -> tuple:
    principal_id = await _seed_user(
        session_factory, subject=subject, tenant_id=tenant_id, kb_id=kb_id, role=role
    )
    async with session_scope(session_factory) as session:

        def seed(s):
            artifact_id = fixtures.seed_content_artifact(s, tenant_id, kb_id)
            item_id, batch_id = fixtures.seed_review_item(
                s, tenant_id, kb_id, assembling_principal_id=principal_id
            )
            return item_id, batch_id, artifact_id

        return await session.run_sync(seed)


async def test_get_review_item_requires_authentication(client) -> None:
    response = client.get(f"/reviews/{uuid4()}")

    assert response.status_code == 401
    assert response.json()["code"] == "unauthenticated"


async def test_get_review_item_returns_404_for_reviewer_without_membership(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    item_id, _batch_id, _artifact_id = await _seed_review_item(
        client.session_factory,
        tenant_id=tenant_id,
        kb_id=kb_id,
        role="Reviewer",
        subject="stranger",
    )
    other_token = _make_token(rsa_key, subject="someone-else")

    response = client.get(f"/reviews/{item_id}", headers={"Authorization": f"Bearer {other_token}"})

    assert response.status_code == 404


async def test_reviewer_can_read_and_correct_their_review_item(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    item_id, batch_id, artifact_id = await _seed_review_item(
        client.session_factory, tenant_id=tenant_id, kb_id=kb_id, role="Reviewer", subject="rosa"
    )
    token = _make_token(rsa_key, subject="rosa")
    headers = {"Authorization": f"Bearer {token}"}

    get_response = client.get(f"/reviews/{item_id}", headers=headers)
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["status"] == "open"
    assert body["decision"] is None

    submit_response = client.post(
        f"/reviews/batches/{batch_id}/decisions",
        headers=headers,
        json={
            "decisions": [
                {
                    "review_item_id": str(item_id),
                    "action": "CORRECT",
                    "assertion_version": 1,
                    "reason_code": "MISREAD_VALUE",
                    "corrected_value": {"value": "$2,000,000"},
                    "evidence": {"source": str(artifact_id), "precision": "exact-span"},
                }
            ]
        },
    )
    assert submit_response.status_code == 200
    receipt = submit_response.json()
    assert receipt["applied"] == 1
    assert receipt["duplicate"] is False
    assert receipt["stale"] == 0
    assert receipt["blocked"] == 0

    reget_response = client.get(f"/reviews/{item_id}", headers=headers)
    assert reget_response.json()["status"] == "decided"
    assert reget_response.json()["decision"]["action"] == "CORRECT"


async def test_resubmitting_the_same_decision_is_a_duplicate_no_op(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    item_id, batch_id, artifact_id = await _seed_review_item(
        client.session_factory, tenant_id=tenant_id, kb_id=kb_id, role="Reviewer", subject="rosa2"
    )
    token = _make_token(rsa_key, subject="rosa2")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "decisions": [
            {
                "review_item_id": str(item_id),
                "action": "ACCEPT",
                "assertion_version": 1,
            }
        ]
    }

    first = client.post(f"/reviews/batches/{batch_id}/decisions", headers=headers, json=payload)
    second = client.post(f"/reviews/batches/{batch_id}/decisions", headers=headers, json=payload)

    assert first.json()["applied"] == 1
    assert second.json()["duplicate"] is True


async def test_tenant_member_without_annotate_permission_cannot_submit_a_decision(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    item_id, batch_id, _artifact_id = await _seed_review_item(
        client.session_factory,
        tenant_id=tenant_id,
        kb_id=kb_id,
        role="TenantMember",  # can read, not annotate
        subject="viewer-only",
    )
    token = _make_token(rsa_key, subject="viewer-only")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        f"/reviews/batches/{batch_id}/decisions",
        headers=headers,
        json={
            "decisions": [
                {"review_item_id": str(item_id), "action": "ACCEPT", "assertion_version": 1}
            ]
        },
    )

    assert response.status_code == 404
