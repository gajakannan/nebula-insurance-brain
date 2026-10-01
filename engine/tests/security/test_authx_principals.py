"""F0002-S0002 through the real HTTP boundary on PostgreSQL.

EX-AUTHX-004 (stable identity under concurrency/restart), EX-AUTHX-005 (every
invalid credential is a generic 401 with a durable authentication event and NO
principal, membership or protected-resource lookup), EX-AUTHX-006 (disabled,
forged and unapproved identities).
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from brain_domain.principal import PrincipalKind, PrincipalStatus
from brain_persistence.identity import (
    find_by_alias,
    link_identity,
    resolve_or_create,
    set_principal_status,
)
from brain_security.principals import AliasConflict
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import event, text

from brain_api.deps import get_authentication_event_sink

from .conftest import (
    ISSUER,
    StatementLog,
    bearer,
    make_token,
    run_sync,
    seed_content_artifact,
    seed_principal_and_membership,
    sync_engine_of,
)

OPERATOR = uuid4()
PROTECTED = ("principal", "external_identity", "membership", "resource_access", "content_artifact")


async def _count(session_factory, sql: str, **params) -> int:
    async with session_factory() as session:
        return (await session.execute(text(sql), params)).scalar_one()


async def test_concurrent_first_sight_yields_one_principal_that_survives_restart(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """EX-AUTHX-004: repeated/concurrent verified resolution -> one durable ID."""
    subject = f"first-sight-{uuid4().hex[:8]}"
    headers = bearer(rsa_key, subject)
    responses = await asyncio.gather(
        *(client.get(f"/reviews/{uuid4()}", headers=headers) for _ in range(8))
    )
    assert {r.status_code for r in responses} == {404}  # identity grants nothing
    count = await _count(
        client.session_factory,
        "SELECT count(*) FROM external_identity WHERE issuer = :i AND subject = :s",
        i=ISSUER,
        s=subject,
    )
    principals = await _count(
        client.session_factory,
        "SELECT count(*) FROM principal WHERE issuer = :i AND subject = :s",
        i=ISSUER,
        s=subject,
    )
    assert (count, principals) == (1, 1)
    first = await run_sync(client.session_factory, lambda s: find_by_alias(s, ISSUER, subject))
    # A new process/session resolves the same ID (process restart = fresh session).
    await client.get(f"/reviews/{uuid4()}", headers=headers)
    again = await run_sync(client.session_factory, lambda s: find_by_alias(s, ISSUER, subject))
    assert first.id == again.id and first.kind == PrincipalKind.USER
    grants = await _count(
        client.session_factory,
        "SELECT count(*) FROM membership WHERE principal_id = :p",
        p=first.id,
    )
    assert grants == 0


async def test_same_subject_at_another_issuer_is_a_distinct_principal(client) -> None:
    """EX-AUTHX-004 boundary: issuer-namespaced identity; no email/subject merge."""
    at = datetime.now(UTC)
    x = await run_sync(
        client.session_factory,
        lambda s: resolve_or_create(s, "https://issuer-x", "same", PrincipalKind.USER, at=at),
    )
    y = await run_sync(
        client.session_factory,
        lambda s: resolve_or_create(s, "https://issuer-y", "same", PrincipalKind.USER, at=at),
    )
    assert x.id != y.id


def _other_key_token(subject: str) -> str:
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return make_token(other, subject)


@pytest.mark.parametrize(
    ("label", "reason"),
    [
        ("missing", "malformed"),
        ("scheme", "malformed"),
        ("garbage", "malformed"),
        ("expired", "expired"),
        ("not_yet_valid", "not_yet_valid"),
        ("wrong_signature", "invalid_signature"),
        ("wrong_issuer", "wrong_issuer"),
        ("wrong_audience", "wrong_audience"),
        ("missing_claim", "invalid_claims"),
        ("token_type", "unsupported_token_type"),
    ],
)
async def test_invalid_credentials_never_touch_protected_storage(
    client, rsa_key: rsa.RSAPrivateKey, label: str, reason: str, caplog
) -> None:
    """EX-AUTHX-005 / S0002 AC3 / S0006 AC2 with an instrumented database."""
    caplog.set_level(logging.WARNING, logger="brain_api.deps")
    tenant, kb = uuid4(), uuid4()
    await seed_principal_and_membership(
        client.session_factory, subject="victim", tenant_id=tenant, knowledge_base_id=kb
    )
    artifact = await seed_content_artifact(
        client.session_factory, tenant_id=tenant, knowledge_base_id=kb
    )
    now = datetime.now(UTC)
    tokens = {
        "expired": make_token(
            rsa_key, "victim", iat=now - timedelta(hours=1), exp=now - timedelta(minutes=1)
        ),
        "not_yet_valid": make_token(rsa_key, "victim", nbf=now + timedelta(minutes=10)),
        "wrong_signature": _other_key_token("victim"),
        "wrong_issuer": make_token(rsa_key, "victim", iss="https://evil.example/"),
        "wrong_audience": make_token(rsa_key, "victim", aud="someone-else"),
        "missing_claim": make_token(rsa_key, "victim", iat=None),
        "token_type": jwt.encode(
            {
                "iss": ISSUER,
                "sub": "victim",
                "aud": "brain",
                "iat": now,
                "exp": now + timedelta(minutes=5),
            },
            rsa_key,
            algorithm="RS256",
            headers={"kid": "test-key-1", "typ": "logout+jwt"},
        ),
    }
    special = {
        "missing": {},
        "scheme": {"Authorization": "Basic dXNlcjpwYXNz"},
        "garbage": {"Authorization": "Bearer not-a-real-jwt"},
    }
    headers = special[label] if label in special else {"Authorization": f"Bearer {tokens[label]}"}

    log = StatementLog()
    engine = sync_engine_of(client.session_factory)
    event.listen(engine, "before_cursor_execute", log)
    try:
        response = await client.get(f"/content/{artifact}/files/source.pdf", headers=headers)
    finally:
        event.remove(engine, "before_cursor_execute", log)

    assert response.status_code == 401
    assert response.json()["code"] == "unauthenticated" and reason not in response.text
    assert log.touching(*PROTECTED) == []  # no principal/membership/resource lookup
    assert all(s.startswith("insert into authentication_event") for s in log.statements)
    assert client.content_store.file_reads == []
    async with client.session_factory() as session:
        row = (
            await session.execute(
                text(
                    "SELECT reason_code, route_template, trace_id, payload "
                    "FROM authentication_event ORDER BY occurred_at DESC LIMIT 1"
                )
            )
        ).one()
    assert row.reason_code == reason
    assert row.route_template == "/content/{artifact_id}/files/{path:path}"
    assert row.payload["principal_id"] is None
    logged = [r for r in caplog.records if r.name == "brain_api.deps"][-1]
    assert logged.event_trace_id == row.trace_id  # log line correlates with the durable event
    credential = headers.get("Authorization", "").partition(" ")[2]
    if credential:
        assert credential not in json.dumps(row.payload)


async def test_authentication_sink_failure_is_a_sanitized_503(client) -> None:
    class Broken:
        async def record(self, _event) -> None:
            raise OSError("audit store down")

    client.app.dependency_overrides[get_authentication_event_sink] = lambda: Broken()
    response = await client.get(f"/reviews/{uuid4()}")
    assert response.status_code == 503
    assert response.json()["code"] == "unavailable" and response.json()["detail"] is None


async def test_disabled_principal_gets_the_generic_401_and_an_audited_reason(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """EX-AUTHX-006 / S0002 AC4: no resource existence is disclosed."""
    tenant, kb = uuid4(), uuid4()
    principal_id = await seed_principal_and_membership(
        client.session_factory, subject="to-disable", tenant_id=tenant, knowledge_base_id=kb
    )
    artifact = await seed_content_artifact(
        client.session_factory, tenant_id=tenant, knowledge_base_id=kb
    )
    headers = bearer(rsa_key, "to-disable")
    assert (await client.get(f"/content/{artifact}", headers=headers)).status_code == 200
    await run_sync(
        client.session_factory,
        lambda s: set_principal_status(
            s,
            principal_id,
            PrincipalStatus.DISABLED,
            operator_id=OPERATOR,
            approval_ref="SEC-1",
            at=datetime.now(UTC),
        ),
    )
    for path in (f"/content/{artifact}", f"/content/{uuid4()}"):
        response = await client.get(path, headers=headers)
        assert response.status_code == 401 and response.json()["code"] == "unauthenticated"
    reason = await _count(
        client.session_factory,
        "SELECT count(*) FROM authentication_event WHERE reason_code = 'disabled_principal'",
    )
    assert reason >= 2


async def test_forged_identity_and_role_fields_are_ignored(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """S0002 AC5/AC7: headers, query and body cannot replace verified identity."""
    tenant, kb = uuid4(), uuid4()
    victim = await seed_principal_and_membership(
        client.session_factory,
        subject="victim-2",
        tenant_id=tenant,
        knowledge_base_id=kb,
        role="ServicePrincipal",
        kind=PrincipalKind.SERVICE,
    )
    artifact = await seed_content_artifact(
        client.session_factory, tenant_id=tenant, knowledge_base_id=kb
    )
    forged = {
        **bearer(rsa_key, "attacker"),
        "X-Principal-Id": str(victim),
        "X-Acting-Principal": str(victim),
        "X-Role": "ServicePrincipal",
    }
    response = await client.get(
        f"/content/{artifact}",
        headers=forged,
        params={"principal_id": str(victim), "kind": "service", "role": "ServicePrincipal"},
    )
    assert response.status_code == 404
    decisions = [
        d for d in await _decisions(client, artifact) if d["actor_principal_id"] != str(victim)
    ]
    assert decisions and all(d["actor_kind"] == "user" for d in decisions)


async def _decisions(client, resource_id):
    from .conftest import decisions_for

    return await decisions_for(client.session_factory, resource_id)


async def test_identity_links_need_approval_and_never_merge_histories(client) -> None:
    """EX-AUTHX-006 / S0002 AC6: an approved link keeps the existing principal ID;
    a pair already linked elsewhere is refused; nothing is rewritten."""
    at = datetime.now(UTC)
    alice = await run_sync(
        client.session_factory,
        lambda s: resolve_or_create(s, ISSUER, "alice-old", PrincipalKind.USER, at=at),
    )
    bob = await run_sync(
        client.session_factory,
        lambda s: resolve_or_create(s, ISSUER, "bob", PrincipalKind.USER, at=at),
    )
    with pytest.raises(ValueError):
        await run_sync(
            client.session_factory,
            lambda s: link_identity(
                s,
                alice.id,
                "https://new-idp",
                "alice",
                approval_ref="",
                operator_id=OPERATOR,
                at=at,
            ),
        )
    await run_sync(
        client.session_factory,
        lambda s: link_identity(
            s,
            alice.id,
            "https://new-idp",
            "alice",
            approval_ref="IDP-9",
            operator_id=OPERATOR,
            at=at,
        ),
    )
    migrated = await run_sync(
        client.session_factory, lambda s: find_by_alias(s, "https://new-idp", "alice")
    )
    assert migrated.id == alice.id
    with pytest.raises(AliasConflict):
        await run_sync(
            client.session_factory,
            lambda s: link_identity(
                s,
                bob.id,
                "https://new-idp",
                "alice",
                approval_ref="IDP-10",
                operator_id=OPERATOR,
                at=at,
            ),
        )
    still = await run_sync(
        client.session_factory, lambda s: find_by_alias(s, "https://new-idp", "alice")
    )
    assert still.id == alice.id


async def test_unprovisioned_service_client_cannot_become_a_user(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """Assembly plan Step 2.4 / S0002 AC7: kind is trusted registry state."""
    response = await client.get(
        f"/reviews/{uuid4()}", headers=bearer(rsa_key, "rogue-svc", azp="brain-service")
    )
    assert response.status_code == 401
    created = await _count(
        client.session_factory,
        "SELECT count(*) FROM principal WHERE subject = 'rogue-svc'",
    )
    assert created == 0
