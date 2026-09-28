"""F0002-S0005 on PostgreSQL: the bounded delegated-read consumer (async facade),
the sync worker adapter, and autonomous service commits through the API.

EX-AUTHX-014 (intersection of current actor grant and ceiling), -015 (revocation or
expiry between job operations), -016 (autonomous ServicePrincipal, no human, no
bypass), plus S0005 AC4 (forged references), AC6 (onward/wider/unregistered
rejected) and AC7 (both identities, delegation and revisions traceable).
"""

from __future__ import annotations

import os
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from brain_domain.authx import (
    Action,
    ActionCeiling,
    Delegation,
    ResourceKey,
    ResourceType,
)
from brain_domain.principal import PrincipalKind
from brain_jobs.queue import JobLease
from brain_persistence import fixtures
from brain_persistence.authx import SqlAlchemyAuthorityStore
from brain_persistence.grants import issue_delegation, revoke_delegation, revoke_membership
from brain_persistence.identity import find_by_alias
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_security.delegation import DelegationRejected
from brain_security.execution import AuthorizationDenied, AuthorizationExecution
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import create_engine

from brain_worker.document_delivery import DocumentJobAuthorization

from .conftest import (
    ISSUER,
    POLICIES,
    bearer,
    decisions_for,
    run_sync,
    seed_content_artifact,
    seed_fact_slot,
    seed_grant,
    seed_principal,
)

ADAPTER = CasbinAuthorizationAdapter(POLICIES / "model.conf", POLICIES / "policy.csv")
OPERATOR = fixtures.SYNTHETIC_OPERATOR


async def _operator(client) -> object:
    """The trusted operational actor who issues delegations is itself a provisioned
    principal (delegation.issued_by is a principal FK)."""
    return await seed_principal(
        client.session_factory,
        subject=f"platform-operator-{uuid4().hex[:6]}",
        kind=PrincipalKind.SERVICE,
    )


def _now() -> datetime:
    return datetime.now(UTC)


def _delegation(
    acting, executor, owned, key, actions, *, minutes=30, not_before=None, issuer=OPERATOR
):
    start = not_before or _now() - timedelta(seconds=5)
    return Delegation(
        id=uuid4(),
        acting_principal_id=acting,
        executor_principal_id=executor,
        issued_by=issuer,
        issued_at=start,
        not_before=start,
        expires_at=start + timedelta(minutes=minutes),
        revoked_at=None,
        revision=1,
        ceilings=(ActionCeiling(owned, key, frozenset(actions)),),
    )


async def _principal(client, subject):
    return await run_sync(client.session_factory, lambda s: find_by_alias(s, ISSUER, subject))


async def _scope_of(client, key):
    from brain_persistence.authx import hydrate

    envelope = await run_sync(client.session_factory, lambda s: hydrate(s, key))
    return envelope.scope


async def _delegated_read(client, executor, key, delegation_id):
    async with client.session_factory() as session:
        execution = AuthorizationExecution(
            SqlAlchemyAuthorityStore(session), ADAPTER, ADAPTER.release
        )

        async def load(decision):
            return decision

        return await execution.read(
            executor, key, Action.READ, trace_id="deleg", load=load, delegation_id=delegation_id
        )


async def test_delegated_authority_is_the_intersection_and_fully_traceable(client) -> None:
    """EX-AUTHX-014 / S0005 AC1/AC2/AC4/AC7."""
    tenant, kb = uuid4(), uuid4()
    user_id = await seed_principal(client.session_factory, subject="deleg-user")
    await seed_grant(client.session_factory, user_id, tenant_id=tenant, knowledge_base_id=kb)
    agent_id = await seed_principal(
        client.session_factory, subject="deleg-agent", kind=PrincipalKind.AGENT
    )
    other_agent_id = await seed_principal(
        client.session_factory, subject="other-agent", kind=PrincipalKind.AGENT
    )
    artifact = await seed_content_artifact(
        client.session_factory, tenant_id=tenant, knowledge_base_id=kb
    )
    outside = await seed_content_artifact(
        client.session_factory, tenant_id=tenant, knowledge_base_id=kb
    )
    key = ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact)
    owned = await _scope_of(client, key)
    issuer = await _operator(client)
    delegation = _delegation(user_id, agent_id, owned, key, {Action.READ}, issuer=issuer)
    await run_sync(
        client.session_factory,
        lambda s: issue_delegation(
            s, delegation, operator_id=issuer, approval_ref="DLG-1", policy=ADAPTER, at=_now()
        ),
    )
    agent = await _principal(client, "deleg-agent")

    decision = await _delegated_read(client, agent, key, delegation.id)
    assert (decision.actor_principal_id, decision.executor_principal_id) == (user_id, agent_id)
    persisted = (await decisions_for(client.session_factory, artifact))[-1]
    assert persisted["delegation_id"] == str(delegation.id)
    assert persisted["delegation_revision"] == 1 and persisted["actor_kind"] == "user"
    assert persisted["policy_release"] == ADAPTER.release.release_id
    assert persisted["grant_revision"] >= 1

    with pytest.raises(AuthorizationDenied) as exc:  # outside the ceiling
        await _delegated_read(
            client, agent, ResourceKey(ResourceType.CONTENT_ARTIFACT, outside), delegation.id
        )
    assert exc.value.decision.reason_code.value == "delegation_denied"
    other = await _principal(client, "other-agent")
    for forged in (delegation.id, uuid4()):  # bound to another executor / unknown
        with pytest.raises(AuthorizationDenied) as exc:
            await _delegated_read(client, other, key, forged)
        assert exc.value.decision.reason_code.value == "delegation_denied"
        assert exc.value.decision.actor_principal_id == other_agent_id
    with pytest.raises(AuthorizationDenied):  # agent alone has no implied grant
        await _delegated_read(client, agent, key, None)

    # Revoking the acting user's grant denies the next delegated operation.
    await run_sync(client.session_factory, _revoke_all(user_id))
    with pytest.raises(AuthorizationDenied) as exc:
        await _delegated_read(client, agent, key, delegation.id)
    assert exc.value.decision.reason_code.value == "no_membership"


async def test_issuance_refuses_wider_onward_expired_or_unregistered_ceilings(client) -> None:
    """S0005 AC6: no widening, onward delegation, expired window or unknown action."""
    tenant, kb = uuid4(), uuid4()
    user_id = await seed_principal(client.session_factory, subject="issuer-user")
    await seed_grant(client.session_factory, user_id, tenant_id=tenant, knowledge_base_id=kb)
    agent_id = await seed_principal(
        client.session_factory, subject="issuer-agent", kind=PrincipalKind.AGENT
    )
    human_executor = await seed_principal(client.session_factory, subject="human-exec")
    slot = await seed_fact_slot(client.session_factory, tenant_id=tenant, knowledge_base_id=kb)
    key = ResourceKey(ResourceType.FACT_SLOT, slot)
    owned = await _scope_of(client, key)
    issuer = await _operator(client)
    rejected = [
        _delegation(user_id, agent_id, owned, key, {Action.READ, Action.COMMIT}),  # wider
        _delegation(agent_id, user_id, owned, key, {Action.READ}),  # onward via agent
        _delegation(user_id, human_executor, owned, key, {Action.READ}),  # USER executor
        _delegation(
            user_id,
            agent_id,
            owned,
            key,
            {Action.READ},
            minutes=1,
            not_before=_now() - timedelta(minutes=5),
        ),  # already expired
    ]
    for delegation in rejected:
        with pytest.raises(DelegationRejected):
            await run_sync(
                client.session_factory,
                lambda s, d=delegation: issue_delegation(
                    s,
                    replace(d, issued_by=issuer),
                    operator_id=issuer,
                    approval_ref="DLG-X",
                    policy=ADAPTER,
                    at=_now(),
                ),
            )
    with pytest.raises(ValueError):
        ActionCeiling(owned, key, frozenset({"delete"}))
    async with client.session_factory() as session:
        from sqlalchemy import text

        count = (
            await session.execute(
                text("SELECT count(*) FROM delegation WHERE acting_principal_id = :u"),
                {"u": user_id},
            )
        ).scalar_one()
    assert count == 0


def _sync_engine():
    url = os.environ.get(
        "BRAIN_DATABASE_URL", "postgresql+asyncpg://brain:brain@localhost:5432/brain"
    )
    return create_engine(url.replace("postgresql+asyncpg://", "postgresql+psycopg://"))


async def test_worker_steps_reauthorize_after_delegation_revocation(client) -> None:
    """EX-AUTHX-015 / S0005 AC3: an earlier successful job step confers nothing."""
    tenant, kb = uuid4(), uuid4()
    ingest_service = await seed_principal(
        client.session_factory, subject="ingest-svc", kind=PrincipalKind.SERVICE
    )
    await seed_grant(
        client.session_factory,
        ingest_service,
        tenant_id=tenant,
        knowledge_base_id=kb,
        role="ServicePrincipal",
    )
    worker_agent = await seed_principal(
        client.session_factory, subject="worker-agent", kind=PrincipalKind.AGENT
    )
    artifact = uuid4()
    key = ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact)
    await run_sync(
        client.session_factory, lambda s: fixtures.protect(s, key, tenant, kb, before_record=True)
    )
    owned = await _scope_of_prepared(client, key)
    issuer = await _operator(client)
    delegation = _delegation(
        ingest_service, worker_agent, owned, key, {Action.INGEST, Action.INTERPRET}, issuer=issuer
    )
    await run_sync(
        client.session_factory,
        lambda s: issue_delegation(
            s, delegation, operator_id=issuer, approval_ref="DLG-W", policy=ADAPTER, at=_now()
        ),
    )
    engine = _sync_engine()
    try:
        authorization = DocumentJobAuthorization(
            engine, POLICIES / "model.conf", POLICIES / "policy.csv"
        )
        lease = JobLease(
            uuid4(),
            tenant,
            kb,
            artifact,
            1,
            1,
            {
                "actor_id": str(worker_agent),
                "delegation_id": str(delegation.id),
                "correlation_id": str(uuid4()),
            },
        )
        authorize = authorization.for_job(lease)
        authorize(tenant, kb, artifact, "ingest")
        await run_sync(
            client.session_factory,
            lambda s: revoke_delegation(
                s, delegation.id, operator_id=OPERATOR, approval_ref="DLG-W-REV", at=_now()
            ),
        )
        with pytest.raises(PermissionError):
            authorize(tenant, kb, artifact, "interpret")
        # A lease payload cannot name a different acting principal: acting comes from
        # the trusted delegation row, and a forged delegation reference denies.
        forged = authorization.for_job(
            JobLease(
                uuid4(),
                tenant,
                kb,
                artifact,
                1,
                1,
                {
                    "actor_id": str(worker_agent),
                    "delegation_id": str(uuid4()),
                    "correlation_id": str(uuid4()),
                    "acting_principal_id": str(ingest_service),
                },
            )
        )
        with pytest.raises(PermissionError):
            forged(tenant, kb, artifact, "ingest")
    finally:
        engine.dispose()
    outcomes = [
        (d["allowed"], d["reason_code"])
        for d in await decisions_for(client.session_factory, artifact)
    ]
    assert (True, "allowed") in outcomes
    assert (False, "delegation_expired") in outcomes
    assert (False, "delegation_denied") in outcomes


async def _scope_of_prepared(client, key):
    from brain_persistence.authx import hydrate

    envelope = await run_sync(
        client.session_factory, lambda s: hydrate(s, key, require_record=False)
    )
    return envelope.scope


async def test_autonomous_service_commits_under_its_own_grant_only(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """EX-AUTHX-016 / S0005 AC5: audited as a service; no human, no bypass."""
    tenant, kb = uuid4(), uuid4()
    service = await seed_principal(
        client.session_factory, subject="svc-committer", kind=PrincipalKind.SERVICE
    )
    await seed_grant(
        client.session_factory,
        service,
        tenant_id=tenant,
        knowledge_base_id=kb,
        role="ServicePrincipal",
    )
    await seed_principal(client.session_factory, subject="bare-agent", kind=PrincipalKind.AGENT)
    slot = await seed_fact_slot(client.session_factory, tenant_id=tenant, knowledge_base_id=kb)
    other_slot = await seed_fact_slot(
        client.session_factory, tenant_id=uuid4(), knowledge_base_id=uuid4()
    )
    proposal = {
        "value": {"amount": "5000000.00"},
        "valid_from": "2026-06-01T00:00:00Z",
        "evidence_refs": [str(uuid4())],
        "source_received_at": "2026-06-10T00:00:00Z",
        "artifact_created_at": "2026-06-10T00:00:00Z",
        "assertion_created_at": "2026-06-10T00:00:00Z",
        "idempotency_key": "svc-commit-0001",
    }
    headers = bearer(rsa_key, "svc-committer")
    response = await client.post(f"/facts/{slot}/commits", headers=headers, json=proposal)
    assert response.status_code == 201
    decision = (await decisions_for(client.session_factory, slot))[-1]
    assert decision["actor_kind"] == "service" and decision["actor_principal_id"] == str(service)
    assert decision["delegation_id"] is None and decision["executor_principal_id"] is None
    # No implicit tenant-wide privilege: another tenant's slot is a 404.
    assert (
        await client.post(
            f"/facts/{other_slot}/commits",
            headers=headers,
            json={**proposal, "idempotency_key": "svc-commit-0002"},
        )
    ).status_code == 404
    # An agent without delegation or grant commits nothing.
    assert (
        await client.post(
            f"/facts/{slot}/commits",
            headers=bearer(rsa_key, "bare-agent"),
            json={**proposal, "idempotency_key": "agent-commit"},
        )
    ).status_code == 404


def _revoke_all(principal_id):
    def revoke(session):
        from brain_persistence.models import MembershipRow
        from sqlalchemy import select

        ids = session.scalars(
            select(MembershipRow.id).where(
                MembershipRow.principal_id == principal_id, MembershipRow.revoked_at.is_(None)
            )
        ).all()
        for membership_id in ids:
            revoke_membership(
                session, membership_id, operator_id=OPERATOR, approval_ref="REV-ALL", at=_now()
            )

    return revoke
