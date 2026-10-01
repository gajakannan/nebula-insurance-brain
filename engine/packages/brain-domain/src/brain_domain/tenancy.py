"""Structural tenancy and tenant-scoped entity identity (F0002-S0001, ADR-0061).

Tenant -> Workspace -> KnowledgeBase is the ownership hierarchy. An entity identity
belongs to exactly one tenant and may be *associated* with several knowledge bases in
that tenant; an association is identity, never an access grant. No I/O here — the
persistence layer enforces the same invariants with composite foreign keys.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


class OwnershipConflict(ValueError):
    """A reference crosses the Tenant -> Workspace -> KnowledgeBase hierarchy.

    Carries no foreign identifiers in its message: the caller may only learn that
    the ownership it supplied is inconsistent, never what the other owner is.
    """


def _require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware UTC")


@dataclass(frozen=True, slots=True)
class OwnedScope:
    """The resolved owner of a KB-scoped record (schema `OwnedScope`)."""

    tenant_id: UUID
    workspace_id: UUID
    knowledge_base_id: UUID

    def to_json(self) -> dict[str, str]:
        return {
            "tenant_id": str(self.tenant_id),
            "workspace_id": str(self.workspace_id),
            "knowledge_base_id": str(self.knowledge_base_id),
        }


@dataclass(frozen=True, slots=True)
class Tenant:
    id: UUID
    created_at: datetime
    created_by: UUID

    def __post_init__(self) -> None:
        _require_aware(self.created_at, "created_at")


@dataclass(frozen=True, slots=True)
class Workspace:
    id: UUID
    tenant_id: UUID
    created_at: datetime
    created_by: UUID

    def __post_init__(self) -> None:
        _require_aware(self.created_at, "created_at")


@dataclass(frozen=True, slots=True)
class KnowledgeBase:
    id: UUID
    workspace_id: UUID
    tenant_id: UUID
    created_at: datetime
    created_by: UUID

    def __post_init__(self) -> None:
        _require_aware(self.created_at, "created_at")

    @property
    def scope(self) -> OwnedScope:
        return OwnedScope(self.tenant_id, self.workspace_id, self.id)


def require_knowledge_base_in_workspace(
    workspace: Workspace, knowledge_base: KnowledgeBase
) -> None:
    """A KB resolves to exactly one workspace and that workspace's tenant (S0001 AC1)."""
    if (
        knowledge_base.workspace_id != workspace.id
        or knowledge_base.tenant_id != workspace.tenant_id
    ):
        raise OwnershipConflict("knowledge base does not belong to the supplied workspace")


def require_same_owner(child: OwnedScope, parent: OwnedScope) -> None:
    """A KB-owned record must agree with its parent's owner (S0001 AC2)."""
    if child != parent:
        raise OwnershipConflict("record ownership disagrees with its parent")


@dataclass(frozen=True, slots=True)
class TenancyIdentity:
    """Schema `TenancyIdentity`: one tenant-scoped entity and its KB associations.

    Associations share the entity's tenant (S0001 AC3/AC4). They grant nothing:
    authorization reads memberships, never this record.
    """

    tenant_id: UUID
    entity_id: UUID
    kb_scopes: tuple[OwnedScope, ...]
    created_at: datetime
    created_by: UUID

    def __post_init__(self) -> None:
        _require_aware(self.created_at, "created_at")
        if any(scope.tenant_id != self.tenant_id for scope in self.kb_scopes):
            raise OwnershipConflict("entity association crosses a tenant boundary")
        if len(set(self.kb_scopes)) != len(self.kb_scopes):
            raise ValueError("duplicate knowledge-base association")

    def to_json(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "tenant_id": str(self.tenant_id),
            "entity_id": str(self.entity_id),
            "kb_scopes": [scope.to_json() for scope in self.kb_scopes],
            "created_at": self.created_at.isoformat(),
            "created_by": str(self.created_by),
        }
