"""F0002-S0006 consumer integration on PostgreSQL.

AC5: annotation and commit stay independent (no promotion, commit rechecks
authority, outbox stays atomic). Batch semantics: everything authorized and
locked before any write; an inaccessible item or a failed item rolls the whole
batch back and the failure is durably audited. Linearization of a concurrent
revoke against commits. AC7: measured local decision latency (no SLO claimed).
"""

from __future__ import annotations

import asyncio
import json
import os
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from brain_domain.principal import PrincipalKind
from brain_persistence.grants import revoke_membership
from brain_testing import fixtures
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import text

from .conftest import (
    bearer,
    decisions_for,
    run_sync,
    seed_content_artifact,
    seed_fact_slot,
    seed_grant,
    seed_principal,
    seed_review_item_in_batch,
)

PROPOSAL = {
    "value": {"amount": "1000000.00"},
    "valid_from": "2026-01-01T00:00:00Z",
    "evidence_refs": [],
    "source_received_at": "2026-01-10T00:00:00Z",
    "artifact_created_at": "2026-01-10T00:00:00Z",
    "assertion_created_at": "2026-01-10T00:00:00Z",
}


async def _count(client, sql, **params):
    async with client.session_factory() as session:
        return (await session.execute(text(sql), params)).scalar_one()


def _decide(item, action="ACCEPT"):
    return {"review_item_id": str(item), "action": action, "assertion_version": 1}


async def test_annotation_and_commit_are_independent_authorizations(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """S0006 AC5: annotation never promotes to truth or implies commit; the service
    commit independently rechecks authority and keeps its outbox atomic."""
    tenant, kb = uuid4(), uuid4()
    reviewer = await seed_principal(client.session_factory, subject="indep-reviewer")
    await seed_grant(
        client.session_factory, reviewer, tenant_id=tenant, knowledge_base_id=kb, role="Reviewer"
    )
    service = await seed_principal(
        client.session_factory, subject="indep-service", kind=PrincipalKind.SERVICE
    )
    await seed_grant(
        client.session_factory,
        service,
        tenant_id=tenant,
        knowledge_base_id=kb,
        role="ServicePrincipal",
    )
    item, batch = await seed_review_item_in_batch(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb,
        assembling_principal_id=reviewer,
    )
    slot = await seed_fact_slot(client.session_factory, tenant_id=tenant, knowledge_base_id=kb)

    annotated = await client.post(
        f"/reviews/batches/{batch}/decisions",
        headers=bearer(rsa_key, "indep-reviewer"),
        json={"decisions": [_decide(item)]},
    )
    assert annotated.status_code == 200
    assert await _count(client, "SELECT count(*) FROM canonical_fact_version") == 0
    assert (
        await client.post(
            f"/facts/{slot}/commits",
            headers=bearer(rsa_key, "indep-reviewer"),
            json={**PROPOSAL, "idempotency_key": "rev-1"},
        )
    ).status_code == 404

    committed = await client.post(
        f"/facts/{slot}/commits",
        headers=bearer(rsa_key, "indep-service"),
        json={**PROPOSAL, "idempotency_key": "svc-1"},
    )
    assert committed.status_code == 201
    commit_id = committed.json()["commit_id"]
    assert (
        await _count(client, "SELECT count(*) FROM outbox_event WHERE commit_id = :c", c=commit_id)
        == 1
    )
    decision = (await decisions_for(client.session_factory, slot))[-1]
    assert (
        await _count(
            client,
            "SELECT count(*) FROM canonical_commit WHERE id = :c "
            "AND authorization_decision_id = :d",
            c=commit_id,
            d=decision["decision_id"],
        )
        == 1
    )


async def test_batch_with_an_inaccessible_item_writes_nothing(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """All items are authorized and locked before any mutation; an inaccessible item
    is a non-disclosing 404 even when it sits in the same batch."""
    tenant, kb, other_kb = uuid4(), uuid4(), uuid4()
    reviewer = await seed_principal(client.session_factory, subject="batch-reviewer")
    await seed_grant(
        client.session_factory, reviewer, tenant_id=tenant, knowledge_base_id=kb, role="Reviewer"
    )
    mine, batch = await seed_review_item_in_batch(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb,
        assembling_principal_id=reviewer,
    )
    foreign, _ = await seed_review_item_in_batch(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=other_kb,
        assembling_principal_id=reviewer,
    )
    response = await client.post(
        f"/reviews/batches/{batch}/decisions",
        headers=bearer(rsa_key, "batch-reviewer"),
        json={"decisions": [_decide(mine), _decide(foreign)]},
    )
    assert response.status_code == 404
    assert (
        await _count(
            client,
            "SELECT count(*) FROM review_decision WHERE review_item_id IN (:a, :b)",
            a=mine,
            b=foreign,
        )
        == 0
    )
    outcomes = {
        (d["resource"]["id"], d["operation_outcome"])
        for rid in (mine, foreign)
        for d in await decisions_for(client.session_factory, rid)
    }
    assert outcomes == {(str(mine), "failed"), (str(foreign), "denied")}


async def test_failed_item_rolls_back_the_whole_batch_and_is_audited(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """Once independently authorized, a wrong batch reference is the existing
    sanitized 422; every new decision rolls back and the failure is durable."""
    tenant, kb = uuid4(), uuid4()
    reviewer = await seed_principal(client.session_factory, subject="partial-reviewer")
    await seed_grant(
        client.session_factory, reviewer, tenant_id=tenant, knowledge_base_id=kb, role="Reviewer"
    )
    first, batch = await seed_review_item_in_batch(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb,
        assembling_principal_id=reviewer,
    )
    elsewhere, _ = await seed_review_item_in_batch(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb,
        assembling_principal_id=reviewer,
    )
    response = await client.post(
        f"/reviews/batches/{batch}/decisions",
        headers=bearer(rsa_key, "partial-reviewer"),
        json={"decisions": [_decide(first), _decide(elsewhere)]},
    )
    assert response.status_code == 422
    assert (
        await _count(
            client,
            "SELECT count(*) FROM review_decision WHERE review_item_id IN (:a, :b)",
            a=first,
            b=elsewhere,
        )
        == 0
    )
    for rid in (first, elsewhere):
        (decision,) = await decisions_for(client.session_factory, rid)
        assert decision["allowed"] and decision["operation_outcome"] == "failed"


async def test_revocation_linearizes_against_concurrent_commits(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """A revoke that committed before an operation began is always observed; each
    successful commit carries the authority revision it was decided under."""
    tenant, kb = uuid4(), uuid4()
    service = await seed_principal(
        client.session_factory, subject="race-service", kind=PrincipalKind.SERVICE
    )
    membership = await seed_grant(
        client.session_factory,
        service,
        tenant_id=tenant,
        knowledge_base_id=kb,
        role="ServicePrincipal",
    )
    slots = [
        await seed_fact_slot(client.session_factory, tenant_id=tenant, knowledge_base_id=kb)
        for _ in range(6)
    ]
    headers = bearer(rsa_key, "race-service")

    async def commit(slot, key):
        return await client.post(
            f"/facts/{slot}/commits", headers=headers, json={**PROPOSAL, "idempotency_key": key}
        )

    async def revoke():
        await asyncio.sleep(0.01)
        return await run_sync(
            client.session_factory,
            lambda s: revoke_membership(
                s,
                membership,
                operator_id=fixtures.SYNTHETIC_OPERATOR,
                approval_ref="RACE",
                at=datetime.now(UTC),
            ),
        )

    *responses, revoked_revision = await asyncio.gather(
        *(commit(slot, f"race-{i}") for i, slot in enumerate(slots)), revoke()
    )
    for slot, response in zip(slots, responses, strict=True):
        decision = (await decisions_for(client.session_factory, slot))[-1]
        versions = await _count(
            client, "SELECT count(*) FROM canonical_fact_version WHERE slot_id = :s", s=slot
        )
        if response.status_code == 201:
            assert decision["allowed"] and decision["grant_revision"] < revoked_revision
            assert versions == 1
        else:
            assert response.status_code == 404
            assert not decision["allowed"] and decision["grant_revision"] == revoked_revision
            assert versions == 0
    after = await commit(slots[0], "race-after")
    assert after.status_code == 404


async def test_measured_local_decision_latency(client, rsa_key: rsa.RSAPrivateKey) -> None:
    """S0006 AC7: measure, do not claim, a production SLO. The QE run exports the
    sample through BRAIN_AUTHX_LATENCY_OUT."""
    tenant, kb = uuid4(), uuid4()
    reader = await seed_principal(client.session_factory, subject="latency-reader")
    await seed_grant(client.session_factory, reader, tenant_id=tenant, knowledge_base_id=kb)
    artifact = await seed_content_artifact(
        client.session_factory, tenant_id=tenant, knowledge_base_id=kb
    )
    headers = bearer(rsa_key, "latency-reader")
    samples = []
    for _ in range(60):
        started = time.perf_counter()
        response = await client.get(f"/content/{artifact}", headers=headers)
        samples.append((time.perf_counter() - started) * 1000)
        assert response.status_code == 200
    samples.sort()
    result = {
        "measurement": "end-to-end authorized GET /content/{artifact_id} via ASGI + PostgreSQL",
        "includes": [
            "verification",
            "principal resolution",
            "policy/authority/resource locks",
            "evaluation",
            "durable audit commit",
        ],
        "samples": len(samples),
        "p50_ms": round(statistics.median(samples), 2),
        "p95_ms": round(samples[int(len(samples) * 0.95) - 1], 2),
        "max_ms": round(samples[-1], 2),
        "fixture": {"grant_slices": 1, "dependencies": 0},
        "slo_claimed": False,
    }
    out = os.environ.get("BRAIN_AUTHX_LATENCY_OUT")
    if out:
        Path(out).write_text(json.dumps(result, indent=2) + "\n")
    assert result["p50_ms"] > 0
