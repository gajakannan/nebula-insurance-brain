"""Trusted provisioning rejection paths (F0002-S0001/S0003/S0005): each refused
operation raises before writing, and accepted replays are idempotent."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from brain_domain.authx import (
    Action,
    ActionCeiling,
    Delegation,
    PilotRole,
    ResourceKey,
    ResourceType,
    ScopedId,
    ScopedKind,
    unrestricted_selectors,
)
from brain_domain.principal import PrincipalKind, PrincipalStatus
from brain_domain.tenancy import OwnedScope, OwnershipConflict
from brain_persistence import fixtures
from brain_persistence.base import Base, sqlite_test_tables
from brain_persistence.grants import (
    activate_policy_release,
    grant_membership,
    issue_delegation,
    register_policy_release,
    revoke_delegation,
    revoke_membership,
)
from brain_persistence.identity import (
    link_identity,
    provision_principal,
    set_principal_status,
)
from brain_persistence.models import PolicyReleasePointerRow, ResourceAccessRow
from brain_persistence.tenancy import (
    RevisionConflict,
    associate_entity,
    change_resource_restrictions,
    inherit_resource_access,
    provision_knowledge_base,
    provision_resource_access,
    provision_workspace,
    resolve_entity,
)
from brain_security.casbin_adapter import CasbinAuthorizationAdapter, compute_policy_release
from brain_security.delegation import DelegationRejected
from brain_security.principals import AliasConflict
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

POLICIES = Path(__file__).resolve().parents[4] / "planning-mds" / "security" / "policies"
OPERATOR = fixtures.SYNTHETIC_OPERATOR
NOW = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=sqlite_test_tables())
    with Session(engine) as s:
        yield s
    engine.dispose()


def test_hierarchy_provisioning_is_idempotent_and_rejects_conflicts(session) -> None:
    tenant, other, workspace, kb = uuid4(), uuid4(), uuid4(), uuid4()
    fixtures.seed_scope(session, tenant, kb, workspace)
    fixtures.seed_scope(session, tenant, kb, workspace)  # replay: no-op
    fixtures.seed_scope(session, other, uuid4())
    with pytest.raises(OwnershipConflict):
        provision_workspace(session, uuid4(), uuid4(), actor_id=OPERATOR, at=NOW)  # no tenant
    with pytest.raises(OwnershipConflict):
        provision_workspace(session, workspace, other, actor_id=OPERATOR, at=NOW)
    with pytest.raises(OwnershipConflict):
        provision_knowledge_base(
            session, kb, fixtures.workspace_for(other), other, actor_id=OPERATOR, at=NOW
        )


def test_entity_identity_validation(session) -> None:
    tenant, kb = uuid4(), uuid4()
    fixtures.seed_scope(session, tenant, kb)
    with pytest.raises(ValueError):
        resolve_entity(session, tenant, namespace="", external_key="k", actor_id=OPERATOR, at=NOW)
    with pytest.raises(OwnershipConflict):
        resolve_entity(session, uuid4(), namespace="n", external_key="k", actor_id=OPERATOR, at=NOW)
    entity = resolve_entity(
        session, tenant, namespace="n", external_key="k", actor_id=OPERATOR, at=NOW
    )
    associate_entity(session, entity, tenant, kb, actor_id=OPERATOR, at=NOW)
    associate_entity(session, entity, tenant, kb, actor_id=OPERATOR, at=NOW)  # replay
    with pytest.raises(OwnershipConflict):
        associate_entity(session, uuid4(), tenant, kb, actor_id=OPERATOR, at=NOW)


def test_resource_metadata_requires_labels_owner_agreement_and_revision(session) -> None:
    tenant, kb = uuid4(), uuid4()
    artifact = fixtures.seed_content_artifact(session, tenant, kb)
    key = ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact)
    with pytest.raises(ValueError):
        provision_resource_access(
            session,
            ResourceKey(ResourceType.FACT_SLOT, uuid4()),
            tenant_id=tenant,
            knowledge_base_id=kb,
            classifications=[],
            actor_id=OPERATOR,
            at=NOW,
        )
    with pytest.raises(OwnershipConflict):  # KB outside the tenant
        provision_resource_access(
            session,
            key,
            tenant_id=uuid4(),
            knowledge_base_id=kb,
            classifications=["internal"],
            actor_id=OPERATOR,
            at=NOW,
        )
    with pytest.raises(OwnershipConflict):  # record does not exist yet
        provision_resource_access(
            session,
            ResourceKey(ResourceType.FACT_SLOT, uuid4()),
            tenant_id=tenant,
            knowledge_base_id=kb,
            classifications=["internal"],
            actor_id=OPERATOR,
            at=NOW,
        )
    other_kb = uuid4()
    fixtures.seed_scope(session, tenant, other_kb)
    with pytest.raises(OwnershipConflict):  # record belongs to another KB
        provision_resource_access(
            session,
            key,
            tenant_id=tenant,
            knowledge_base_id=other_kb,
            classifications=["internal"],
            actor_id=OPERATOR,
            at=NOW,
        )
    with pytest.raises(OwnershipConflict):  # differs from the trusted row already there
        provision_resource_access(
            session,
            key,
            tenant_id=tenant,
            knowledge_base_id=kb,
            classifications=["secret"],
            actor_id=OPERATOR,
            at=NOW,
        )
    with pytest.raises(RevisionConflict):
        change_resource_restrictions(
            session,
            key,
            expected_revision=7,
            actor_id=OPERATOR,
            at=NOW,
            classifications=["x"],
            approval_ref="A",
        )
    with pytest.raises(ValueError):
        change_resource_restrictions(
            session,
            key,
            expected_revision=1,
            actor_id=OPERATOR,
            at=NOW,
            classifications=[],
            approval_ref="A",
        )
    new = change_resource_restrictions(
        session,
        key,
        expected_revision=1,
        actor_id=OPERATOR,
        at=NOW,
        classifications=["secret"],
        source_acl_ids=["acl"],
        parent_chain=[ScopedId(ScopedKind.ACCOUNT, uuid4())],
        approval_ref="A",
    )
    row = session.get(ResourceAccessRow, (key.type.value, key.id))
    assert new == 2 and row.classifications == ["secret"] and row.source_acl_ids == ["acl"]
    with pytest.raises(OwnershipConflict):
        change_resource_restrictions(
            session,
            ResourceKey(ResourceType.FACT_SLOT, uuid4()),
            expected_revision=1,
            actor_id=OPERATOR,
            at=NOW,
            approval_ref="A",
        )
    with pytest.raises(OwnershipConflict):
        inherit_resource_access(
            session,
            ResourceKey(ResourceType.CONTENT_ARTIFACT, uuid4()),
            ResourceKey(ResourceType.REVIEW_TASK, uuid4()),
            actor_id=OPERATOR,
            at=NOW,
        )


def test_identity_provisioning_rules(session) -> None:
    service = provision_principal(
        session,
        issuer="i",
        subject="svc",
        kind=PrincipalKind.SERVICE,
        operator_id=OPERATOR,
        approval_ref="P-1",
        at=NOW,
    )
    assert (
        provision_principal(
            session,
            issuer="i",
            subject="svc",
            kind=PrincipalKind.SERVICE,
            operator_id=OPERATOR,
            approval_ref="P-1",
            at=NOW,
        )
        == service
    )
    with pytest.raises(AliasConflict):
        provision_principal(
            session,
            issuer="i",
            subject="svc",
            kind=PrincipalKind.USER,
            operator_id=OPERATOR,
            approval_ref="P-2",
            at=NOW,
        )
    with pytest.raises(ValueError):
        provision_principal(
            session,
            issuer="i",
            subject="x",
            kind=PrincipalKind.USER,
            operator_id=OPERATOR,
            approval_ref="",
            at=NOW,
        )
    with pytest.raises(AliasConflict):
        link_identity(session, uuid4(), "i", "new", approval_ref="L", operator_id=OPERATOR, at=NOW)
    link_identity(session, service.id, "j", "svc", approval_ref="L", operator_id=OPERATOR, at=NOW)
    link_identity(session, service.id, "j", "svc", approval_ref="L", operator_id=OPERATOR, at=NOW)
    revision = set_principal_status(
        session,
        service.id,
        PrincipalStatus.DISABLED,
        operator_id=OPERATOR,
        approval_ref="D",
        at=NOW,
    )
    assert revision == 2


def test_grant_revocation_and_policy_release_lifecycle(session) -> None:
    tenant, kb = uuid4(), uuid4()
    fixtures.seed_scope(session, tenant, kb)
    user = fixtures.seed_principal(session, issuer="i", subject="u")
    with pytest.raises(OwnershipConflict):
        grant_membership(
            session,
            principal_id=user.id,
            tenant_id=uuid4(),
            knowledge_base_id=kb,
            role=PilotRole.TENANT_MEMBER,
            selectors=unrestricted_selectors(),
            classifications="*",
            source_acl_ids="*",
            valid_from=NOW,
            operator_id=OPERATOR,
            approval_ref="G",
            at=NOW,
        )
    with pytest.raises(OwnershipConflict):
        grant_membership(
            session,
            principal_id=uuid4(),
            tenant_id=tenant,
            knowledge_base_id=kb,
            role=PilotRole.TENANT_MEMBER,
            selectors=unrestricted_selectors(),
            classifications="*",
            source_acl_ids="*",
            valid_from=NOW,
            operator_id=OPERATOR,
            approval_ref="G",
            at=NOW,
        )
    with pytest.raises(RevisionConflict):
        grant_membership(
            session,
            principal_id=user.id,
            tenant_id=tenant,
            knowledge_base_id=kb,
            role=PilotRole.TENANT_MEMBER,
            selectors=unrestricted_selectors(),
            classifications="*",
            source_acl_ids="*",
            valid_from=NOW,
            operator_id=OPERATOR,
            approval_ref="G",
            at=NOW,
            expected_authority_revision=99,
        )
    membership = fixtures.seed_grant(session, user.id, tenant, kb, PilotRole.TENANT_MEMBER)
    with pytest.raises(RevisionConflict):
        revoke_membership(
            session,
            membership,
            operator_id=OPERATOR,
            approval_ref="R",
            at=NOW,
            expected_grant_revision=99,
        )
    first = revoke_membership(session, membership, operator_id=OPERATOR, approval_ref="R", at=NOW)
    assert (
        revoke_membership(session, membership, operator_id=OPERATOR, approval_ref="R", at=NOW)
        == first
    )  # idempotent
    with pytest.raises(OwnershipConflict):
        revoke_membership(session, uuid4(), operator_id=OPERATOR, approval_ref="R", at=NOW)

    release = compute_policy_release(b"m", b"p")
    activate_policy_release(session, release, operator_id=OPERATOR, approval_ref="P", at=NOW)
    activate_policy_release(session, release, operator_id=OPERATOR, approval_ref="P", at=NOW)
    second = compute_policy_release(b"m2", b"p")
    activate_policy_release(session, second, operator_id=OPERATOR, approval_ref="P", at=NOW)
    assert session.get(PolicyReleasePointerRow, 1).release_id == second.release_id
    with pytest.raises(ValueError):  # a release ID cannot be re-bound to other content
        register_policy_release(
            session,
            release.__class__(
                release.release_id,
                release.release_sha256,
                "x" * 64,
                release.policy_sha256,
                release.contract_version,
            ),
            at=NOW,
        )


def test_delegation_lifecycle_guards(session) -> None:
    tenant, kb = uuid4(), uuid4()
    fixtures.seed_scope(session, tenant, kb)
    policy = CasbinAuthorizationAdapter(POLICIES / "model.conf", POLICIES / "policy.csv")
    user = fixtures.seed_principal(session, issuer="i", subject="u")
    agent = fixtures.seed_principal(session, issuer="i", subject="a", kind=PrincipalKind.AGENT)
    fixtures.seed_grant(session, user.id, tenant, kb, PilotRole.TENANT_MEMBER)
    artifact = fixtures.seed_content_artifact(session, tenant, kb)
    owned = OwnedScope(tenant, fixtures.workspace_for(tenant), kb)
    now = datetime.now(UTC)
    delegation = Delegation(
        id=uuid4(),
        acting_principal_id=user.id,
        executor_principal_id=agent.id,
        issued_by=OPERATOR,
        issued_at=now,
        not_before=now,
        expires_at=now + timedelta(minutes=5),
        revoked_at=None,
        revision=1,
        ceilings=(
            ActionCeiling(
                owned,
                ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact),
                frozenset({Action.READ}),
            ),
        ),
    )
    with pytest.raises(DelegationRejected):
        issue_delegation(
            session, delegation, operator_id=OPERATOR, approval_ref="", policy=policy, at=now
        )
    with pytest.raises(RevisionConflict):
        issue_delegation(
            session,
            delegation,
            operator_id=OPERATOR,
            approval_ref="D",
            policy=policy,
            at=now,
            expected_authority_revision=99,
        )
    issue_delegation(
        session, delegation, operator_id=OPERATOR, approval_ref="D", policy=policy, at=now
    )
    with pytest.raises(RevisionConflict):
        revoke_delegation(
            session,
            delegation.id,
            operator_id=OPERATOR,
            approval_ref="R",
            at=now,
            expected_revision=5,
        )
    revoked = revoke_delegation(
        session, delegation.id, operator_id=OPERATOR, approval_ref="R", at=now
    )
    assert revoked.revoked_at is not None and revoked.revision == 2
    with pytest.raises(DelegationRejected):
        revoke_delegation(session, uuid4(), operator_id=OPERATOR, approval_ref="R", at=now)
