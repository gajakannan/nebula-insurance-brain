from __future__ import annotations

import json
import runpy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import jwt
import pytest
import pytest_asyncio
from brain_content.config import LocalObjectStoreConfig
from brain_content.object_store import LocalFilesystemObjectStore
from brain_content.store import LocalContentArtifactStore
from brain_content.validation import verify_bundle
from brain_domain.authx import PilotRole, ResourceKey, ResourceType
from brain_domain.principal import PrincipalKind
from brain_persistence import content_models
from brain_persistence.base import Base, sqlite_test_tables
from brain_persistence.content_repository import ContentArtifactRepository
from brain_persistence.grants import revoke_membership
from brain_persistence.models import (
    AuditEventRow,
    ContentArtifact,
    DocumentVersion,
    MembershipRow,
    SourceDocument,
)
from brain_persistence.session import make_engine, make_session_factory, session_scope
from brain_security.identity_profile import IdentityProfile, IssuerProfile
from brain_security.verification import VerifiedCredential, decode_verified
from brain_testing import fixtures
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jwt import PyJWK
from sqlalchemy import select, update

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


@pytest_asyncio.fixture
async def client(rsa_key: rsa.RSAPrivateKey, tmp_path):
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
    content = LocalContentArtifactStore(
        LocalFilesystemObjectStore(LocalObjectStoreConfig("filesystem", tmp_path / "content", True))
    )
    app.dependency_overrides[get_content_store] = lambda: content

    with TestClient(app) as test_client:
        test_client.session_factory = session_factory  # type: ignore[attr-defined]
        test_client.content_store = content
        test_client.bundles = {}
        yield test_client
    await engine.dispose()


async def _seed_user(session_factory, *, subject, tenant_id, kb_id, role, kind=PrincipalKind.USER):
    async with session_scope(session_factory) as session:

        def seed(s):
            principal = fixtures.seed_principal(s, issuer=ISSUER, subject=subject, kind=kind)
            fixtures.seed_grant(s, principal.id, tenant_id, kb_id, PilotRole(role))
            return principal.id

        return await session.run_sync(seed)


async def _seed_artifact(client, *, tenant_id, kb_id, role: str, subject: str, version=2) -> str:
    actor = await _seed_user(
        client.session_factory, subject=subject, tenant_id=tenant_id, kb_id=kb_id, role=role
    )
    helpers = runpy.run_path(
        str(POLICIES.parents[2] / "engine/packages/brain-content/tests/test_versioned_content.py")
    )
    manifest, files = helpers["bundle_fixture"]()
    manifest.update(tenant_id=str(tenant_id), knowledge_base_id=str(kb_id))
    if version == 1:
        for name in (
            "source_file",
            "recipe_sha256",
            "bundle_hash_algorithm",
            "record_contract_version",
            "page_number_base",
            "coordinate_units",
            "text_normalization_version",
        ):
            manifest.pop(name)
        manifest["execution"].pop("parser_name")
        manifest["execution"].pop("projection_version")
        manifest["artifact_contract_version"] = 1
    key, raw, files = helpers["seal"](manifest, files)
    # Whitespace and member order must survive the HTTP manifest response.
    raw = json.dumps(json.loads(raw), indent=2, ensure_ascii=False).encode() + b"\n"
    bundle = verify_bundle(key, raw, files)
    await client.content_store.publish_verified(key, raw, files)
    async with session_scope(client.session_factory) as session:

        def seed(s):
            owner = dict(tenant_id=tenant_id, knowledge_base_id=kb_id)
            s.add(
                SourceDocument(
                    id=bundle.manifest.document_id,
                    source_sha256=bundle.manifest.source_sha256,
                    **owner,
                )
            )
            s.flush()
            s.add(
                DocumentVersion(
                    id=bundle.manifest.version_id,
                    source_document_id=bundle.manifest.document_id,
                    **owner,
                )
            )
            s.flush()
            s.add(
                ContentArtifact(
                    id=key.artifact_id,
                    document_version_id=bundle.manifest.version_id,
                    artifact_sha256=bundle.manifest.artifact_sha256,
                    page_count=1,
                    extraction_status="complete",
                    artifact_contract_version=version if version == 2 else None,
                    recipe_sha256=getattr(bundle.manifest, "recipe_sha256", None),
                    manifest_sha256=bundle.manifest_sha256 if version == 2 else None,
                    publication_state="ready" if version == 2 else "legacy_unverified",
                    **owner,
                )
            )
            s.flush()
            fixtures.protect(
                s, ResourceKey(ResourceType.CONTENT_ARTIFACT, key.artifact_id), tenant_id, kb_id
            )
            ContentArtifactRepository(s)._insert_indexes(bundle, actor)

        await session.run_sync(seed)
    client.bundles[str(key.artifact_id)] = bundle
    return str(key.artifact_id)


async def test_member_can_stream_a_retained_source_file(client, rsa_key: rsa.RSAPrivateKey) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    artifact_id = await _seed_artifact(
        client,
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
    assert response.content == client.bundles[artifact_id].files["source.pdf"]


async def test_non_member_gets_404_not_403(client, rsa_key: rsa.RSAPrivateKey) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    artifact_id = await _seed_artifact(
        client, tenant_id=tenant_id, kb_id=kb_id, role="TenantMember", subject="bob"
    )
    token = _make_token(rsa_key, subject="someone-else")

    response = client.get(
        f"/content/{artifact_id}/files/source.pdf", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


async def test_path_not_in_manifest_is_404(client, rsa_key: rsa.RSAPrivateKey) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    artifact_id = await _seed_artifact(
        client,
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


@pytest.mark.parametrize("version", [1, 2])
async def test_manifest_and_declared_files_return_exact_persisted_bytes(client, rsa_key, version):
    artifact_id = await _seed_artifact(
        client,
        tenant_id=uuid4(),
        kb_id=uuid4(),
        role="TenantMember",
        subject="reader",
        version=version,
    )
    headers = {"Authorization": f"Bearer {_make_token(rsa_key, 'reader')}"}
    bundle = client.bundles[artifact_id]
    response = client.get(f"/content/{artifact_id}", headers=headers)
    assert response.status_code == 200
    assert response.content == bundle.manifest_bytes
    assert response.headers["cache-control"] == "private, no-store"
    for path, raw in bundle.files.items():
        response = client.get(f"/content/{artifact_id}/files/{path}", headers=headers)
        assert response.status_code == 200 and response.content == raw
        assert response.headers["cache-control"] == "private, no-store"


@pytest.mark.parametrize(
    "fault,code,status",
    [
        ("missing", "ARTIFACT_INTEGRITY", 409),
        ("bytes", "ARTIFACT_INTEGRITY", 409),
        ("manifest", "ARTIFACT_INTEGRITY", 409),
        ("scope", "ARTIFACT_INTEGRITY", 409),
        ("version", "ARTIFACT_VERSION_UNSUPPORTED", 409),
        ("indexes", "ARTIFACT_INTEGRITY", 409),
        ("quarantine", "ARTIFACT_INTEGRITY", 409),
        ("transient", "CONTENT_UNAVAILABLE", 503),
    ],
)
async def test_failed_content_read_only_writes_failed_authorization_audit(
    client, rsa_key, monkeypatch, fault, code, status
):
    artifact_id = await _seed_artifact(
        client, tenant_id=uuid4(), kb_id=uuid4(), role="TenantMember", subject="reader"
    )
    bundle = client.bundles[artifact_id]
    objects = client.content_store._object_store
    root = objects._root / bundle.key.prefix
    if fault == "missing":
        (root / "normalized.md").unlink()
    elif fault == "bytes":
        (root / "source.pdf").write_bytes(b"changed source")
    elif fault == "manifest":
        (root / "manifest.json").write_bytes(b"{invalid")
    elif fault == "version":
        data = json.loads(bundle.manifest_bytes)
        data["artifact_contract_version"] = 99
        (root / "manifest.json").write_text(json.dumps(data))
    elif fault == "scope":
        data = json.loads(bundle.manifest_bytes)
        data["tenant_id"] = str(uuid4())
        (root / "manifest.json").write_text(json.dumps(data))
    elif fault == "indexes":
        async with session_scope(client.session_factory) as session:
            await session.execute(content_models.content_block.delete())
    elif fault == "quarantine":
        # SQLite fixture exercises the API response. PostgreSQL separately
        # proves that only witnessed state transitions can produce this row.
        async with session_scope(client.session_factory) as session:
            await session.execute(update(ContentArtifact).values(publication_state="quarantined"))
    elif fault == "transient":

        async def unavailable(_key):
            raise OSError("synthetic protected filesystem path")

        monkeypatch.setattr(client.content_store, "load_verified", unavailable)
    async with session_scope(client.session_factory) as session:
        before = (await session.execute(select(ContentArtifact.__table__))).mappings().one()
        baseline = len((await session.scalars(select(AuditEventRow))).all())
    headers = {"Authorization": f"Bearer {_make_token(rsa_key, 'reader')}"}
    for _ in range(2):
        response = client.get(f"/content/{artifact_id}", headers=headers)
        assert response.status_code == status
        assert response.headers["content-type"].startswith("application/problem+json")
        assert response.json()["code"] == code and response.json()["traceId"]
        assert "synthetic protected" not in response.text
    async with session_scope(client.session_factory) as session:
        after = (await session.execute(select(ContentArtifact.__table__))).mappings().one()
        assert dict(after) == dict(before)
        events = (await session.scalars(select(AuditEventRow))).all()
        assert len(events) == baseline + 2
        reads = [row for row in events if row.event_type == "authorization_decision"]
        assert len(reads) == 2
        assert all(row.action == "read" and row.operation_outcome == "failed" for row in reads)
        for table in (
            content_models.content_repair_record,
            content_models.content_artifact_state_event,
        ):
            assert (await session.execute(select(table))).first() is None


async def test_reviewer_without_member_grant_is_denied_before_any_object_read(
    client, rsa_key, monkeypatch
):
    artifact_id = await _seed_artifact(
        client, tenant_id=uuid4(), kb_id=uuid4(), role="Reviewer", subject="reviewer"
    )

    async def forbidden(_key):
        pytest.fail("denied content must not open object storage")

    monkeypatch.setattr(client.content_store, "load_verified", forbidden)
    headers = {"Authorization": f"Bearer {_make_token(rsa_key, 'reviewer')}"}
    for suffix in ("", "/files/source.pdf"):
        assert client.get(f"/content/{artifact_id}{suffix}", headers=headers).status_code == 404


@pytest.mark.parametrize("same_tenant", [True, False])
async def test_cross_kb_and_cross_tenant_content_is_denied(client, rsa_key, same_tenant):
    tenant = uuid4()
    await _seed_user(
        client.session_factory,
        subject="alice",
        tenant_id=tenant,
        kb_id=uuid4(),
        role="TenantMember",
    )
    artifact_id = await _seed_artifact(
        client,
        tenant_id=tenant if same_tenant else uuid4(),
        kb_id=uuid4(),
        role="TenantMember",
        subject="other-reader",
    )
    headers = {"Authorization": f"Bearer {_make_token(rsa_key, 'alice')}"}
    for suffix in ("", "/files/source.pdf"):
        assert client.get(f"/content/{artifact_id}{suffix}", headers=headers).status_code == 404


async def test_revoked_grant_is_reloaded_on_every_content_read(client, rsa_key):
    artifact_id = await _seed_artifact(
        client, tenant_id=uuid4(), kb_id=uuid4(), role="TenantMember", subject="reader"
    )
    headers = {"Authorization": f"Bearer {_make_token(rsa_key, 'reader')}"}
    assert client.get(f"/content/{artifact_id}", headers=headers).status_code == 200
    async with session_scope(client.session_factory) as session:
        membership = (await session.scalars(select(MembershipRow))).one()
        await session.run_sync(
            lambda s: revoke_membership(
                s,
                membership.id,
                operator_id=fixtures.SYNTHETIC_OPERATOR,
                approval_ref="controlled-revocation",
                at=datetime.now(UTC),
            )
        )
    for suffix in ("", "/files/source.pdf"):
        assert client.get(f"/content/{artifact_id}{suffix}", headers=headers).status_code == 404


async def test_malformed_content_id_returns_sanitized_400(client, rsa_key):
    response = client.get(
        "/content/invalid-uuid",
        headers={"Authorization": f"Bearer {_make_token(rsa_key, 'reader')}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] is None
