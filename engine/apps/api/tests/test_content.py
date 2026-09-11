from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
import pytest_asyncio
from brain_persistence.base import Base, sqlite_test_tables
from brain_persistence.models import (
    ContentArtifact,
    DocumentVersion,
    MembershipRow,
    PrincipalRow,
    SourceDocument,
)
from brain_persistence.session import make_engine, make_session_factory, session_scope
from brain_security.verification import VerifiedCredential
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jwt import PyJWK

from brain_api.app import create_app
from brain_api.deps import get_content_store, get_credential_verifier, get_db_session

ISSUER = "https://authentik.local/application/o/brain/"
AUDIENCE = "brain"


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
    app = create_app()

    async def override_get_db_session():
        async with session_scope(session_factory) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_credential_verifier] = lambda: _FakeVerifier(rsa_key)
    app.dependency_overrides[get_content_store] = lambda: _FakeContentStore()

    with TestClient(app) as test_client:
        test_client.session_factory = session_factory  # type: ignore[attr-defined]
        yield test_client
    await engine.dispose()


async def _seed_artifact(session_factory, *, tenant_id, kb_id, role: str, subject: str) -> str:
    async with session_scope(session_factory) as session:
        principal_row = PrincipalRow(
            id=uuid4(), kind="user", issuer=ISSUER, subject=subject, status="active"
        )
        session.add(principal_row)
        await session.flush()
        session.add(
            MembershipRow(
                id=uuid4(),
                principal_id=principal_row.id,
                tenant_id=tenant_id,
                knowledge_base_id=kb_id,
                role=role,
                grant_revision=1,
                revoked_at=None,
            )
        )
        source = SourceDocument(
            tenant_id=tenant_id, knowledge_base_id=kb_id, source_sha256="a" * 64
        )
        session.add(source)
        await session.flush()
        version = DocumentVersion(source_document_id=source.id)
        session.add(version)
        await session.flush()
        artifact = ContentArtifact(
            id=uuid4(),
            document_version_id=version.id,
            artifact_sha256="b" * 64,
            page_count=1,
            extraction_status="complete",
        )
        session.add(artifact)
        await session.flush()
        return str(artifact.id)


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
