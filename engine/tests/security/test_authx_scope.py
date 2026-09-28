"""F0002-S0001/S0003 on PostgreSQL through trusted services and existing consumers.

EX-AUTHX-001 (owned association / swapped parent), -002 (entity shared by sibling
KBs grants nothing), -003 (tenant-scoped identity spaces), -007 (union then
filter), -008 (revocation/expiry and business time), -009 (role scoped to its KB),
plus S0003 AC6 (unavailable grants fail closed) and AC7 (revision and outcome move
together, audited).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from brain_domain.authx import (
    Action,
    RequestedScope,
    ResourceKey,
    ResourceType,
    ScopedId,
    ScopedKind,
    Selector,
    SelectorMode,
    unrestricted_selectors,
)
from brain_domain.tenancy import OwnershipConflict
from brain_persistence.authx import SqlAlchemyAuthorityStore
from brain_persistence.grants import revoke_membership
from brain_persistence.identity import find_by_alias
from brain_persistence.models import (
    EntityKnowledgeBaseRow,
    KnowledgeBaseRow,
    MembershipRow,
    WorkspaceRow,
)
from brain_persistence.tenancy import (
    associate_entity,
    provision_knowledge_base,
    provision_scope,
    record_rejected_ownership,
    resolve_entity,
)
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_security.execution import AuthorizationDenied, AuthorizationExecution
from brain_testing import fixtures
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import event, func, select, text

from .conftest import (
    ISSUER,
    POLICIES,
    FailOn,
    bearer,
    decisions_for,
    run_sync,
    seed_content_artifact,
    seed_fact_slot,
    seed_grant,
    seed_principal,
    seed_review_item_in_batch,
    sync_engine_of,
)

OPERATOR = fixtures.SYNTHETIC_OPERATOR


def _now() -> datetime:
    return datetime.now(UTC)


async def test_ownership_hierarchy_rejects_cross_tenant_parents_without_partial_writes(
    client,
) -> None:
    """EX-AUTHX-001 / S0001 AC1/AC6."""
    tenant_a, tenant_b, ws_a, ws_b = uuid4(), uuid4(), uuid4(), uuid4()
    kb_a1, kb_a2 = uuid4(), uuid4()
    await run_sync(
        client.session_factory,
        lambda s: provision_scope(
            s,
            tenant_id=tenant_a,
            workspace_id=ws_a,
            knowledge_base_id=kb_a1,
            actor_id=OPERATOR,
            at=_now(),
        ),
    )
    await run_sync(
        client.session_factory,
        lambda s: provision_scope(
            s,
            tenant_id=tenant_b,
            workspace_id=ws_b,
            knowledge_base_id=uuid4(),
            actor_id=OPERATOR,
            at=_now(),
        ),
    )
    await run_sync(
        client.session_factory,
        lambda s: provision_knowledge_base(s, kb_a2, ws_a, tenant_a, actor_id=OPERATOR, at=_now()),
    )
    rogue_kb = uuid4()
    with pytest.raises(OwnershipConflict):  # workspace B under tenant A
        await run_sync(
            client.session_factory,
            lambda s: provision_knowledge_base(
                s, rogue_kb, ws_b, tenant_a, actor_id=OPERATOR, at=_now()
            ),
        )
    await run_sync(
        client.session_factory,
        lambda s: record_rejected_ownership(
            s,
            event_type="knowledge_base_rejected",
            actor_id=OPERATOR,
            resource_type="knowledge_base",
            resource_id=rogue_kb,
            at=_now(),
        ),
    )
    async with client.session_factory() as session:
        assert await session.get(KnowledgeBaseRow, rogue_kb) is None
        kb = await session.get(KnowledgeBaseRow, kb_a2)
        workspace = await session.get(WorkspaceRow, kb.workspace_id)
        assert (kb.tenant_id, workspace.tenant_id) == (tenant_a, tenant_a)
        audit = (
            await session.execute(
                text(
                    "SELECT reason_code, payload FROM audit_event "
                    "WHERE event_type = 'knowledge_base_rejected' AND resource_id = :r"
                ),
                {"r": rogue_kb},
            )
        ).one()
    assert audit.reason_code == "owner_conflict"
    assert str(ws_b) not in str(audit.payload) and str(tenant_b) not in str(audit.payload)


async def test_entity_identity_is_tenant_scoped_and_grants_nothing(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """EX-AUTHX-002/003 / S0001 AC3/AC4, S0003 AC2."""
    tenant_a, tenant_b = uuid4(), uuid4()
    kb_a1, kb_a2, kb_b = uuid4(), uuid4(), uuid4()
    for tenant, kb in ((tenant_a, kb_a1), (tenant_a, kb_a2), (tenant_b, kb_b)):
        await run_sync(
            client.session_factory, lambda s, t=tenant, k=kb: fixtures.seed_scope(s, t, k)
        )

    def resolve(tenant):
        return lambda s: resolve_entity(
            s, tenant, namespace="account", external_key="ACME-001", actor_id=OPERATOR, at=_now()
        )

    entity_a = await run_sync(client.session_factory, resolve(tenant_a))
    assert await run_sync(client.session_factory, resolve(tenant_a)) == entity_a
    entity_b = await run_sync(client.session_factory, resolve(tenant_b))
    assert entity_a != entity_b  # identical external key, separate identity spaces

    for kb in (kb_a1, kb_a2):
        await run_sync(
            client.session_factory,
            lambda s, k=kb: associate_entity(
                s, entity_a, tenant_a, k, actor_id=OPERATOR, at=_now()
            ),
        )
    with pytest.raises(OwnershipConflict):  # A's entity cannot join B's KB
        await run_sync(
            client.session_factory,
            lambda s: associate_entity(s, entity_a, tenant_a, kb_b, actor_id=OPERATOR, at=_now()),
        )

    reader = await seed_principal(client.session_factory, subject="a1-reader")
    await seed_grant(client.session_factory, reader, tenant_id=tenant_a, knowledge_base_id=kb_a1)
    in_a1 = await seed_content_artifact(
        client.session_factory, tenant_id=tenant_a, knowledge_base_id=kb_a1
    )
    in_a2 = await seed_content_artifact(
        client.session_factory, tenant_id=tenant_a, knowledge_base_id=kb_a2
    )
    headers = bearer(rsa_key, "a1-reader")
    assert (await client.get(f"/content/{in_a1}", headers=headers)).status_code == 200
    assert (await client.get(f"/content/{in_a2}", headers=headers)).status_code == 404
    async with client.session_factory() as session:
        memberships = await session.scalar(
            select(func.count())
            .select_from(MembershipRow)
            .where(MembershipRow.principal_id == reader)
        )
        associations = await session.scalar(
            select(func.count())
            .select_from(EntityKnowledgeBaseRow)
            .where(EntityKnowledgeBaseRow.entity_id == entity_a)
        )
    assert memberships == 1 and associations == 2  # association created no grant


async def test_union_of_grants_then_request_filter_intersection(client) -> None:
    """EX-AUTHX-007 through the facade over the PostgreSQL store (bounded consumer)."""
    tenant, kb = uuid4(), uuid4()
    account_x, account_y, account_z = uuid4(), uuid4(), uuid4()
    principal = await seed_principal(client.session_factory, subject="union-reader")

    def only(kind, *ids):
        return Selector(kind, SelectorMode.ONLY, frozenset(ids))

    def with_account(account):
        return tuple(
            only(ScopedKind.ACCOUNT, account) if s.kind == ScopedKind.ACCOUNT else s
            for s in unrestricted_selectors()
        )

    for account in (account_x, account_y):
        await seed_grant(
            client.session_factory,
            principal,
            tenant_id=tenant,
            knowledge_base_id=kb,
            selectors=with_account(account),
        )
    artifacts = {
        account: await seed_content_artifact(
            client.session_factory,
            tenant_id=tenant,
            knowledge_base_id=kb,
            parent_chain=[ScopedId(ScopedKind.ACCOUNT, account)],
        )
        for account in (account_x, account_y, account_z)
    }
    adapter = CasbinAuthorizationAdapter(POLICIES / "model.conf", POLICIES / "policy.csv")
    subject_principal = await run_sync(
        client.session_factory, lambda s: find_by_alias(s, ISSUER, "union-reader")
    )

    async def read(artifact, requested):
        async with client.session_factory() as session:
            execution = AuthorizationExecution(
                SqlAlchemyAuthorityStore(session), adapter, adapter.release
            )

            async def load(decision):
                return decision

            return await execution.read(
                subject_principal,
                ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact),
                Action.READ,
                trace_id="ex-007",
                load=load,
                requested=requested,
            )

    unfiltered = RequestedScope(None, (), None, None)
    assert (await read(artifacts[account_x], unfiltered)).allowed  # union: X
    assert (await read(artifacts[account_y], unfiltered)).allowed  # union: Y
    with pytest.raises(AuthorizationDenied):
        await read(artifacts[account_z], unfiltered)  # never granted
    narrowed = RequestedScope(None, (only(ScopedKind.ACCOUNT, account_x),), None, None)
    with pytest.raises(AuthorizationDenied) as exc:
        await read(artifacts[account_y], narrowed)  # filter only narrows
    assert exc.value.decision.reason_code.value == "scope_denied"
    widen = RequestedScope(None, (only(ScopedKind.ACCOUNT, account_z),), None, None)
    with pytest.raises(AuthorizationDenied):
        await read(artifacts[account_z], widen)  # a filter never adds authority
    other_kb = RequestedScope(frozenset({uuid4()}), (), None, None)
    with pytest.raises(AuthorizationDenied):
        await read(artifacts[account_x], other_kb)


async def test_revocation_and_expiry_deny_the_next_operation(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """EX-AUTHX-008 / S0003 AC4/AC7: revision and outcome change together; a past
    business coordinate never reinstates a revoked grant."""
    tenant, kb = uuid4(), uuid4()
    principal = await seed_principal(client.session_factory, subject="revocable")
    membership = await seed_grant(
        client.session_factory, principal, tenant_id=tenant, knowledge_base_id=kb
    )
    slot = await seed_fact_slot(client.session_factory, tenant_id=tenant, knowledge_base_id=kb)
    artifact = await seed_content_artifact(
        client.session_factory, tenant_id=tenant, knowledge_base_id=kb
    )
    headers = bearer(rsa_key, "revocable")
    assert (await client.get(f"/content/{artifact}", headers=headers)).status_code == 200
    before = (await decisions_for(client.session_factory, artifact))[-1]["grant_revision"]

    new_revision = await run_sync(
        client.session_factory,
        lambda s: revoke_membership(
            s, membership, operator_id=OPERATOR, approval_ref="REV-1", at=_now()
        ),
    )
    assert new_revision == before + 1
    assert (await client.get(f"/content/{artifact}", headers=headers)).status_code == 404
    past = {"validAsOf": "2026-01-01T00:00:00Z", "knownAsOf": "2026-01-01T00:00:00Z"}
    assert (await client.get(f"/facts/{slot}", headers=headers, params=past)).status_code == 404
    last = (await decisions_for(client.session_factory, artifact))[-1]
    assert (last["allowed"], last["reason_code"], last["grant_revision"]) == (
        False,
        "no_membership",
        new_revision,
    )
    async with client.session_factory() as session:
        change = (
            await session.execute(
                text(
                    "SELECT actor_principal_id, payload FROM audit_event "
                    "WHERE event_type = 'membership_revoked' AND resource_id = :m"
                ),
                {"m": membership},
            )
        ).one()
    assert change.actor_principal_id == OPERATOR
    assert (change.payload["before_revision"], change.payload["after_revision"]) == (
        new_revision - 1,
        new_revision,
    )
    assert str(kb) in change.payload["affected_ids"]

    expiring = await seed_principal(client.session_factory, subject="expiring")
    await seed_grant(
        client.session_factory,
        expiring,
        tenant_id=tenant,
        knowledge_base_id=kb,
        valid_from=_now() - timedelta(days=2),
        expires_at=_now() - timedelta(seconds=1),
    )
    assert (
        await client.get(f"/content/{artifact}", headers=bearer(rsa_key, "expiring"))
    ).status_code == 404
    assert (await decisions_for(client.session_factory, artifact))[-1]["reason_code"] == (
        "membership_expired"
    )


async def test_role_applies_only_in_its_granting_kb(client, rsa_key: rsa.RSAPrivateKey) -> None:
    """EX-AUTHX-009 / S0003 AC5."""
    tenant, kb_a1, kb_a2 = uuid4(), uuid4(), uuid4()
    principal = await seed_principal(client.session_factory, subject="mixed-roles")
    await seed_grant(
        client.session_factory,
        principal,
        tenant_id=tenant,
        knowledge_base_id=kb_a1,
        role="Reviewer",
    )
    await seed_grant(
        client.session_factory,
        principal,
        tenant_id=tenant,
        knowledge_base_id=kb_a2,
        role="TenantMember",
    )
    item_a1, batch_a1 = await seed_review_item_in_batch(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb_a1,
        assembling_principal_id=principal,
    )
    item_a2, batch_a2 = await seed_review_item_in_batch(
        client.session_factory,
        tenant_id=tenant,
        knowledge_base_id=kb_a2,
        assembling_principal_id=principal,
    )
    headers = bearer(rsa_key, "mixed-roles")

    def body(item):
        return {
            "decisions": [{"review_item_id": str(item), "action": "ACCEPT", "assertion_version": 1}]
        }

    denied = await client.post(
        f"/reviews/batches/{batch_a2}/decisions", headers=headers, json=body(item_a2)
    )
    assert denied.status_code == 404
    allowed = await client.post(
        f"/reviews/batches/{batch_a1}/decisions", headers=headers, json=body(item_a1)
    )
    assert allowed.status_code == 200 and allowed.json()["applied"] == 1
    assert (await client.get(f"/reviews/{item_a2}", headers=headers)).status_code == 200


async def test_unavailable_grant_state_fails_closed_with_503(
    client, rsa_key: rsa.RSAPrivateKey
) -> None:
    """S0003 AC6: no fallback to an unrestricted scope and no protected content."""
    tenant, kb = uuid4(), uuid4()
    principal = await seed_principal(client.session_factory, subject="grant-outage")
    await seed_grant(client.session_factory, principal, tenant_id=tenant, knowledge_base_id=kb)
    artifact = await seed_content_artifact(
        client.session_factory, tenant_id=tenant, knowledge_base_id=kb
    )
    hook = FailOn("select membership")
    engine = sync_engine_of(client.session_factory)
    event.listen(engine, "before_cursor_execute", hook)
    try:
        response = await client.get(
            f"/content/{artifact}/files/source.pdf", headers=bearer(rsa_key, "grant-outage")
        )
    finally:
        event.remove(engine, "before_cursor_execute", hook)
    assert response.status_code == 503 and response.json()["code"] == "unavailable"
    assert client.content_store.file_reads == []
