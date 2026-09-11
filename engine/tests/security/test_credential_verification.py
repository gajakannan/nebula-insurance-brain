"""F0001-S0006: no protected storage is read before verification completes, the
internal failure reason is recorded but never disclosed, and a malformed bearer
is rejected the same as any other unverifiable credential. `OidcJwksVerifier`
itself (expired/wrong-audience/wrong-issuer/wrong-signature/not-yet-valid) is
unit-tested directly in `packages/brain-security/tests/test_verification.py`;
this proves the HTTP-layer ordering and disclosure contract on top of it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric import rsa

from .conftest import make_token, seed_content_artifact, seed_principal_and_membership


async def test_missing_bearer_header_is_401_before_any_route_logic_runs(client) -> None:
    response = await client.get(f"/reviews/{uuid4()}")

    assert response.status_code == 401
    assert response.json()["code"] == "unauthenticated"
    # The internal reason ("malformed") is never in the response body.
    assert "malformed" not in response.text


async def test_malformed_bearer_scheme_is_401(client) -> None:
    response = await client.get(
        f"/reviews/{uuid4()}", headers={"Authorization": "Basic dXNlcjpwYXNz"}
    )

    assert response.status_code == 401
    assert response.json()["code"] == "unauthenticated"


async def test_garbage_token_is_401_and_reason_not_disclosed(client) -> None:
    response = await client.get(
        f"/reviews/{uuid4()}", headers={"Authorization": "Bearer not-a-real-jwt"}
    )

    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "unauthenticated"
    assert "invalid_signature" not in response.text
    assert "signature" not in (body.get("detail") or "")


async def test_expired_token_is_401_without_reading_storage(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    await seed_principal_and_membership(
        client.session_factory, subject="expired-user", tenant_id=tenant_id, knowledge_base_id=kb_id
    )
    artifact_id = await seed_content_artifact(
        client.session_factory, tenant_id=tenant_id, knowledge_base_id=kb_id
    )
    now = datetime.now(UTC)
    expired_token = make_token(
        rsa_key,
        "expired-user",
        iat=now - timedelta(hours=1),
        exp=now - timedelta(minutes=1),
    )

    response = await client.get(
        f"/content/{artifact_id}/files/source.pdf",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    # 401, not 404/200 — proves the request never got far enough to resolve the
    # artifact, let alone read it (F0001-S0006 logic flow: verify before read).
    assert response.status_code == 401
    assert response.json()["code"] == "unauthenticated"


async def test_wrong_audience_token_is_401(client, rsa_key: rsa.RSAPrivateKey) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    await seed_principal_and_membership(
        client.session_factory,
        subject="wrong-aud-user",
        tenant_id=tenant_id,
        knowledge_base_id=kb_id,
    )
    token = make_token(rsa_key, "wrong-aud-user", aud="someone-else")

    response = await client.get(f"/reviews/{uuid4()}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["code"] == "unauthenticated"
