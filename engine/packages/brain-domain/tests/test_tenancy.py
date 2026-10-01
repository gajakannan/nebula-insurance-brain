"""F0002-S0001 ownership invariants (no I/O)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from brain_domain.tenancy import (
    KnowledgeBase,
    OwnedScope,
    OwnershipConflict,
    TenancyIdentity,
    Tenant,
    Workspace,
    require_knowledge_base_in_workspace,
    require_same_owner,
)

NOW = datetime(2026, 9, 27, tzinfo=UTC)


def test_knowledge_base_resolves_to_exactly_one_workspace_and_tenant() -> None:
    tenant = Tenant(uuid4(), NOW, uuid4())
    workspace = Workspace(uuid4(), tenant.id, NOW, uuid4())
    kb = KnowledgeBase(uuid4(), workspace.id, tenant.id, NOW, uuid4())
    require_knowledge_base_in_workspace(workspace, kb)
    assert kb.scope == OwnedScope(tenant.id, workspace.id, kb.id)
    foreign = Workspace(uuid4(), uuid4(), NOW, uuid4())
    with pytest.raises(OwnershipConflict):
        require_knowledge_base_in_workspace(foreign, kb)
    with pytest.raises(OwnershipConflict):
        require_knowledge_base_in_workspace(
            workspace, KnowledgeBase(uuid4(), workspace.id, uuid4(), NOW, uuid4())
        )


def test_children_must_match_their_parent_owner() -> None:
    scope = OwnedScope(uuid4(), uuid4(), uuid4())
    require_same_owner(scope, scope)
    with pytest.raises(OwnershipConflict) as exc:
        require_same_owner(OwnedScope(uuid4(), scope.workspace_id, scope.knowledge_base_id), scope)
    assert str(scope.tenant_id) not in str(exc.value)  # no foreign identifiers disclosed


def test_entity_identity_associations_stay_in_the_tenant() -> None:
    tenant = uuid4()
    a1 = OwnedScope(tenant, uuid4(), uuid4())
    a2 = OwnedScope(tenant, a1.workspace_id, uuid4())
    identity = TenancyIdentity(tenant, uuid4(), (a1, a2), NOW, uuid4())
    assert len(identity.to_json()["kb_scopes"]) == 2
    with pytest.raises(OwnershipConflict):
        TenancyIdentity(tenant, uuid4(), (OwnedScope(uuid4(), uuid4(), uuid4()),), NOW, uuid4())
    with pytest.raises(ValueError):
        TenancyIdentity(tenant, uuid4(), (a1, a1), NOW, uuid4())
    with pytest.raises(ValueError):
        Tenant(uuid4(), datetime(2026, 1, 1), uuid4())  # noqa: DTZ001 - naive rejected
