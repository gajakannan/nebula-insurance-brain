"""F0001-S0006: revocation propagation timing. `PrincipalResolver.memberships()`
excludes any row with `revoked_at IS NOT NULL` on every call — there is no
membership cache in this feature (see STATUS.md's Deferred Non-Blocking
Follow-ups for why `BRAIN_GRANT_CACHE_SECONDS` documents an upper bound with no
cache behind it yet), so propagation is bounded only by transaction visibility.
This measures that real elapsed time end to end through the HTTP layer and
records it against the configured 30s window.
"""

from __future__ import annotations

import os
import time
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import text

from .conftest import (
    ISSUER,
    make_token,
    seed_content_artifact,
    seed_fact_slot,
    seed_principal_and_membership,
)

GRANT_CACHE_SECONDS = int(os.environ.get("BRAIN_GRANT_CACHE_SECONDS", "30"))


async def _revoke(
    session_factory, *, issuer: str, subject: str, tenant_id, knowledge_base_id
) -> None:
    async with session_factory() as session:
        await session.execute(
            text(
                """
                UPDATE membership
                SET revoked_at = now(), grant_revision = grant_revision + 1
                WHERE principal_id = (
                    SELECT id FROM principal WHERE issuer = :issuer AND subject = :subject
                )
                AND tenant_id = :tenant_id
                AND knowledge_base_id = :knowledge_base_id
                """
            ),
            {
                "issuer": issuer,
                "subject": subject,
                "tenant_id": tenant_id,
                "knowledge_base_id": knowledge_base_id,
            },
        )
        await session.commit()


async def test_revocation_is_enforced_on_the_first_request_after_the_write(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    tenant_id, kb_id = uuid4(), uuid4()
    await seed_principal_and_membership(
        client.session_factory,
        subject="soon-to-be-revoked",
        tenant_id=tenant_id,
        knowledge_base_id=kb_id,
    )
    artifact_id = await seed_content_artifact(
        client.session_factory, tenant_id=tenant_id, knowledge_base_id=kb_id
    )
    headers = {"Authorization": f"Bearer {make_token(rsa_key, 'soon-to-be-revoked')}"}

    before = await client.get(f"/content/{artifact_id}/files/source.pdf", headers=headers)
    assert before.status_code == 200

    revoked_at = time.monotonic()
    await _revoke(
        client.session_factory,
        issuer=ISSUER,
        subject="soon-to-be-revoked",
        tenant_id=tenant_id,
        knowledge_base_id=kb_id,
    )

    after = await client.get(f"/content/{artifact_id}/files/source.pdf", headers=headers)
    propagation_seconds = time.monotonic() - revoked_at

    assert after.status_code == 404  # denial-as-404, never 403
    assert propagation_seconds < GRANT_CACHE_SECONDS
    print(  # noqa: T201 - the measured value is the point of this proof (S0006 AC)
        f"revocation propagation: {propagation_seconds * 1000:.2f}ms "
        f"(bound: {GRANT_CACHE_SECONDS}s; no membership cache exists in this feature, "
        f"so this measures real transaction-visibility latency, not a cache TTL)"
    )


async def test_a_historical_valid_as_of_date_cannot_reinstate_a_revoked_grant(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """Proposed ADR-0053, business rule 3: a revoked membership stays revoked
    regardless of what business-time coordinate the request's query targets —
    revocation is a fact about *authorization now*, not a bitemporal business
    fact, so it cannot be queried around."""
    tenant_id, kb_id = uuid4(), uuid4()
    await seed_principal_and_membership(
        client.session_factory,
        subject="revoked-cannot-time-travel",
        tenant_id=tenant_id,
        knowledge_base_id=kb_id,
        role="ServicePrincipal",
    )
    fact_slot_id = await seed_fact_slot(
        client.session_factory, tenant_id=tenant_id, knowledge_base_id=kb_id
    )
    headers = {"Authorization": f"Bearer {make_token(rsa_key, 'revoked-cannot-time-travel')}"}

    commit_before_revoke = await client.post(
        f"/facts/{fact_slot_id}/commits",
        headers=headers,
        json={
            "value": {"amount": "1"},
            "valid_from": "2020-01-01T00:00:00Z",
            "evidence_refs": [str(uuid4())],
            "source_received_at": "2020-01-10T00:00:00Z",
            "artifact_created_at": "2020-01-10T00:00:00Z",
            "assertion_created_at": "2020-01-10T00:00:00Z",
            "idempotency_key": f"revocation-time-travel-{uuid4()}",
        },
    )
    assert commit_before_revoke.status_code == 201

    await _revoke(
        client.session_factory,
        issuer=ISSUER,
        subject="revoked-cannot-time-travel",
        tenant_id=tenant_id,
        knowledge_base_id=kb_id,
    )

    # Querying a coordinate from before the grant was ever revoked does not help
    # — authorization is evaluated against *current* membership state, not the
    # business-time coordinate named in the query.
    get_response = await client.get(
        f"/facts/{fact_slot_id}",
        headers=headers,
        params={"validAsOf": "2020-06-01T00:00:00Z", "knownAsOf": "2020-06-01T00:00:00Z"},
    )
    assert get_response.status_code == 404
