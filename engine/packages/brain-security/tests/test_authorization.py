from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from brain_domain.principal import Membership, Principal, PrincipalKind, PrincipalStatus
from brain_security.audit import InMemoryAuditEventRepository, RepositoryAuditSink
from brain_security.authorization import AuthorizationService, ResourceRef
from brain_security.casbin_adapter import CasbinAuthorizationAdapter


def _principal() -> Principal:
    return Principal(
        id=uuid4(),
        kind=PrincipalKind.USER,
        issuer="authentik",
        subject="rosa",
        status=PrincipalStatus.ACTIVE,
    )


async def test_reviewer_with_matching_membership_is_allowed_to_annotate(
    model_path: Path, policy_path: Path
) -> None:
    principal = _principal()
    tenant_id, kb_id = uuid4(), uuid4()
    membership = Membership(
        principal_id=principal.id,
        tenant_id=tenant_id,
        knowledge_base_id=kb_id,
        role="Reviewer",
        grant_revision=3,
        revoked_at=None,
    )
    audit_repo = InMemoryAuditEventRepository()
    service = AuthorizationService(
        CasbinAuthorizationAdapter(model_path, policy_path), RepositoryAuditSink(audit_repo)
    )
    resource = ResourceRef(
        type="review_task", id=uuid4(), tenant_id=tenant_id, knowledge_base_id=kb_id
    )

    decision = await service.authorize(principal, [membership], resource, "annotate", trace_id="t1")

    assert decision.allowed is True
    assert decision.grant_revision == 3
    assert len(audit_repo.events) == 1
    assert audit_repo.events[0].decision is True
    assert audit_repo.events[0].actor_principal_id == principal.id


async def test_no_membership_for_resource_tenant_is_denied_without_calling_casbin(
    model_path: Path, policy_path: Path
) -> None:
    principal = _principal()
    audit_repo = InMemoryAuditEventRepository()
    service = AuthorizationService(
        CasbinAuthorizationAdapter(model_path, policy_path), RepositoryAuditSink(audit_repo)
    )
    resource = ResourceRef(
        type="review_task", id=uuid4(), tenant_id=uuid4(), knowledge_base_id=uuid4()
    )

    decision = await service.authorize(principal, [], resource, "annotate", trace_id="t2")

    assert decision.allowed is False
    assert decision.reason_code == "no_membership"
    assert audit_repo.events[0].decision is False


async def test_membership_role_lacking_the_action_is_denied(
    model_path: Path, policy_path: Path
) -> None:
    principal = _principal()
    tenant_id, kb_id = uuid4(), uuid4()
    membership = Membership(
        principal_id=principal.id,
        tenant_id=tenant_id,
        knowledge_base_id=kb_id,
        role="TenantMember",
        grant_revision=1,
        revoked_at=None,
    )
    service = AuthorizationService(
        CasbinAuthorizationAdapter(model_path, policy_path),
        RepositoryAuditSink(InMemoryAuditEventRepository()),
    )
    resource = ResourceRef(
        type="review_task", id=uuid4(), tenant_id=tenant_id, knowledge_base_id=kb_id
    )

    decision = await service.authorize(principal, [membership], resource, "annotate", trace_id="t3")

    assert decision.allowed is False
    assert decision.reason_code == "policy_denied"


async def test_every_decision_carries_the_policy_hash(model_path: Path, policy_path: Path) -> None:
    principal = _principal()
    tenant_id, kb_id = uuid4(), uuid4()
    adapter = CasbinAuthorizationAdapter(model_path, policy_path)
    service = AuthorizationService(adapter, RepositoryAuditSink(InMemoryAuditEventRepository()))
    resource = ResourceRef(
        type="review_task", id=uuid4(), tenant_id=tenant_id, knowledge_base_id=kb_id
    )

    decision = await service.authorize(principal, [], resource, "annotate", trace_id="t4")

    assert decision.policy_hash == adapter.policy_hash
