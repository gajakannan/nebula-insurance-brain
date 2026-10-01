"""F0002-S0006 audit contract on PostgreSQL through the existing consumers.

EX-AUTHX-017 (allowed and denied calls: outcome and audit agree; policy/grant
versions and trace recorded; no token or protected payload; denied mutations leave
no state) and EX-AUTHX-018 (audit persistence failure: no success response, no
payload, no committed mutation), plus S0006 AC1-AC3.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest
from brain_domain.principal import PrincipalKind
from cryptography.hazmat.primitives.asymmetric import rsa
from jsonschema import Draft202012Validator, FormatChecker
from sqlalchemy import event, text

from .conftest import (
    FailOn,
    bearer,
    decisions_for,
    make_token,
    seed_content_artifact,
    seed_fact_slot,
    seed_grant,
    seed_principal,
    seed_review_item_in_batch,
    sync_engine_of,
)

SCHEMA = json.loads(
    (
        Path(__file__).resolve().parents[3] / "planning-mds/schemas/authx-kernel.schema.json"
    ).read_text()
)
DECISION = Draft202012Validator(
    {"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": "#/$defs/Decision"},
    format_checker=FormatChecker(),
)
PROPOSAL = {
    "value": {"amount": "2000000.00"},
    "valid_from": "2026-01-01T00:00:00Z",
    "evidence_refs": [],
    "source_received_at": "2026-01-10T00:00:00Z",
    "artifact_created_at": "2026-01-10T00:00:00Z",
    "assertion_created_at": "2026-01-10T00:00:00Z",
}


async def _count(client, sql, **params):
    async with client.session_factory() as session:
        return (await session.execute(text(sql), params)).scalar_one()


async def _world(client):
    tenant, kb = uuid4(), uuid4()
    service = await seed_principal(
        client.session_factory, subject=f"svc-{uuid4().hex[:6]}", kind=PrincipalKind.SERVICE
    )
    await seed_grant(
        client.session_factory,
        service,
        tenant_id=tenant,
        knowledge_base_id=kb,
        role="ServicePrincipal",
    )
    reviewer = await seed_principal(client.session_factory, subject=f"rev-{uuid4().hex[:6]}")
    await seed_grant(
        client.session_factory, reviewer, tenant_id=tenant, knowledge_base_id=kb, role="Reviewer"
    )
    artifact = await seed_content_artifact(
        client.session_factory, tenant_id=tenant, knowledge_base_id=kb
    )
    slot = await seed_fact_slot(client.session_factory, tenant_id=tenant, knowledge_base_id=kb)
    item, batch = await seed_review_item_in_batch(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb,
        assembling_principal_id=reviewer,
    )
    return tenant, kb, service, reviewer, artifact, slot, item, batch


async def _subject(client, principal_id):
    async with client.session_factory() as session:
        return (
            await session.execute(
                text("SELECT subject FROM principal WHERE id = :p"), {"p": principal_id}
            )
        ).scalar_one()


async def test_allowed_and_denied_calls_leave_matching_non_secret_audit(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """EX-AUTHX-017 / S0006 AC1/AC3/AC4 across content, fact and review consumers."""
    _t, _kb, service, reviewer, artifact, slot, item, batch = await _world(client)
    service_token = make_token(rsa_key, await _subject(client, service))
    reviewer_token = make_token(rsa_key, await _subject(client, reviewer))
    service_h = {"Authorization": f"Bearer {service_token}"}
    reviewer_h = {"Authorization": f"Bearer {reviewer_token}"}

    async def check(response, resource_id, allowed):
        assert (response.status_code < 300) == allowed, response.text
        decision = (await decisions_for(client.session_factory, resource_id))[-1]
        assert decision["allowed"] is allowed
        assert decision["operation_outcome"] == ("succeeded" if allowed else "denied")
        assert list(DECISION.iter_errors(decision)) == []
        assert len(decision["policy_hash"]) == 64
        assert decision["policy_release"].startswith("sha256:")
        assert decision["grant_revision"] >= 1 and decision["trace_id"]
        serialized = json.dumps(decision)
        for secret in (service_token, reviewer_token, "PDF-1.4", "2000000.00"):
            assert secret not in serialized

    review_body = {
        "decisions": [{"review_item_id": str(item), "action": "ACCEPT", "assertion_version": 1}]
    }
    await check(await client.get(f"/content/{artifact}", headers=service_h), artifact, True)
    await check(await client.get(f"/content/{artifact}", headers=reviewer_h), artifact, False)
    await check(
        await client.post(
            f"/facts/{slot}/commits", headers=service_h, json={**PROPOSAL, "idempotency_key": "a1"}
        ),
        slot,
        True,
    )
    await check(
        await client.post(
            f"/facts/{slot}/commits", headers=reviewer_h, json={**PROPOSAL, "idempotency_key": "a2"}
        ),
        slot,
        False,
    )
    await check(await client.get(f"/reviews/{item}", headers=reviewer_h), item, True)
    await check(
        await client.post(
            f"/reviews/batches/{batch}/decisions", headers=service_h, json=review_body
        ),
        item,
        False,
    )

    # The allowed commit references its decision; the denied one left no state.
    decisions = await decisions_for(client.session_factory, slot)
    allowed_commit = next(d for d in decisions if d["allowed"])
    assert (
        await _count(
            client,
            "SELECT count(*) FROM canonical_commit WHERE authorization_decision_id = :d",
            d=allowed_commit["decision_id"],
        )
        == 1
    )
    assert (
        await _count(
            client, "SELECT count(*) FROM canonical_fact_version WHERE slot_id = :s", s=slot
        )
        == 1
    )
    assert (
        await _count(
            client, "SELECT count(*) FROM review_decision WHERE review_item_id = :i", i=item
        )
        == 0
    )


@pytest.mark.parametrize("consumer", ["content", "commit", "review"])
async def test_audit_persistence_failure_never_yields_an_unaudited_success(
    client, rsa_key: rsa.RSAPrivateKey, consumer: str
) -> None:
    """EX-AUTHX-018 / S0006 AC3: sanitized 503, no payload, no committed mutation."""
    _t, _kb, service, reviewer, artifact, slot, item, batch = await _world(client)
    service_h = bearer(rsa_key, await _subject(client, service))
    reviewer_h = bearer(rsa_key, await _subject(client, reviewer))
    hook = FailOn("insert into audit_event")
    engine = sync_engine_of(client.session_factory)
    event.listen(engine, "before_cursor_execute", hook)
    try:
        if consumer == "content":
            response = await client.get(f"/content/{artifact}/files/source.pdf", headers=service_h)
        elif consumer == "commit":
            response = await client.post(
                f"/facts/{slot}/commits",
                headers=service_h,
                json={**PROPOSAL, "idempotency_key": "fail-audit"},
            )
        else:
            response = await client.post(
                f"/reviews/batches/{batch}/decisions",
                headers=reviewer_h,
                json={
                    "decisions": [
                        {"review_item_id": str(item), "action": "ACCEPT", "assertion_version": 1}
                    ]
                },
            )
    finally:
        event.remove(engine, "before_cursor_execute", hook)
    assert response.status_code == 503
    assert response.json() == {**response.json(), "code": "unavailable", "detail": None}
    assert b"PDF" not in response.content
    for table, column, rid in (
        ("canonical_fact_version", "slot_id", slot),
        (
            "outbox_event o JOIN canonical_commit c ON c.id = o.commit_id "
            "JOIN canonical_fact_version v ON v.commit_id = c.id",
            "v.slot_id",
            slot,
        ),
        ("review_decision", "review_item_id", item),
    ):
        assert (
            await _count(client, f"SELECT count(*) FROM {table} WHERE {column} = :r", r=rid) == 0
        ), table
    for resource_id in (artifact, slot, item):
        assert await decisions_for(client.session_factory, resource_id) == []
