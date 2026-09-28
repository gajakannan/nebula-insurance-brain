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
    get_content_store,
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


class _FakeContentStore:
    def __init__(self) -> None:
        self._files: dict[str, bytes] = {"source.pdf": b"%PDF-1.4 fake bytes"}

    async def get_manifest(self, artifact_id):
        from types import SimpleNamespace

        return SimpleNamespace(files=[SimpleNamespace(path=path) for path in self._files])

    async def open_file(self, artifact_id, path: str) -> bytes:
        return self._files[path]


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
    app.dependency_overrides[get_content_store] = lambda: _FakeContentStore()

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


async def _seed_artifact(session_factory, *, tenant_id, kb_id, role: str, subject: str) -> str:
    await _seed_user(session_factory, subject=subject, tenant_id=tenant_id, kb_id=kb_id, role=role)
    async with session_scope(session_factory) as session:
        artifact_id = await session.run_sync(
            lambda s: fixtures.seed_content_artifact(s, tenant_id, kb_id)
        )
        return str(artifact_id)


async def test_member_can_stream_a_retained_source_file(client, rsa_key: rsa.RSAPrivateKey) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    artifact_id = await _seed_artifact(
        client.session_factory,
        tenant_id=tenant_id,
        kb_id=kb_id,
        role="TenantMember",
        subject="alice",
    )
    token = _make_token(rsa_key, subject="alice")

    response = client.get(
        f"/content/{artifact_id}/files/source.pdf", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 fake bytes"


async def test_non_member_gets_404_not_403(client, rsa_key: rsa.RSAPrivateKey) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    artifact_id = await _seed_artifact(
        client.session_factory, tenant_id=tenant_id, kb_id=kb_id, role="TenantMember", subject="bob"
    )
    token = _make_token(rsa_key, subject="someone-else")

    response = client.get(
        f"/content/{artifact_id}/files/source.pdf", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


async def test_path_not_in_manifest_is_404(client, rsa_key: rsa.RSAPrivateKey) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    artifact_id = await _seed_artifact(
        client.session_factory,
        tenant_id=tenant_id,
        kb_id=kb_id,
        role="TenantMember",
        subject="carol",
    )
    token = _make_token(rsa_key, subject="carol")

    response = client.get(
        f"/content/{artifact_id}/files/../../etc/passwd",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
