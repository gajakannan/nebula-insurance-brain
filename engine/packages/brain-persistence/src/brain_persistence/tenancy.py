"""Trusted operational provisioning of ownership, identity and restrictions (F0002-S0001).

These functions are operational authority (scripts, the reviewed reconciliation
batch, trusted submitters and test fixtures), not a public runtime permission and
not a business role. Each validates the Tenant -> Workspace -> KnowledgeBase
hierarchy before writing, runs inside the caller's transaction (so a rejected
change leaves no partial write), and records an append-only operational event.
Nothing here creates a membership or grant as a side effect.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Sequence
from datetime import datetime
from uuid import UUID, uuid4

from brain_domain.audit import AuditEvent
from brain_domain.authx import ResourceKey, ResourceType, ScopedId
from brain_domain.tenancy import OwnershipConflict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from brain_persistence.authx import append_audit_event
from brain_persistence.models import (
    ContentArtifact,
    EntityIdentityRow,
    EntityKnowledgeBaseRow,
    FactSlotRow,
    KnowledgeBaseRow,
    ResourceAccessRow,
    ReviewItemRow,
    TenantRow,
    WorkspaceRow,
)

NOT_AN_AUTHORIZATION = "n/a"


def record_operational_event(
    session: Session,
    *,
    event_type: str,
    actor_id: UUID,
    resource_type: str,
    resource_id: UUID,
    at: datetime,
    applied: bool = True,
    reason_code: str = "applied",
    before_revision: int | None = None,
    after_revision: int = 1,
    approval_ref: str | None = None,
    input_digest: str | None = None,
    affected_ids: Iterable[UUID] = (),
) -> None:
    """Operational event payload (assembly plan "Mutation traceability"): IDs,
    revisions, approval reference and input digest only — never tokens or content."""
    event_id = uuid4()
    append_audit_event(
        session,
        AuditEvent(
            id=event_id,
            occurred_at=at,
            actor_principal_id=actor_id,
            delegate_principal_id=None,
            resource_type=resource_type,
            resource_id=resource_id,
            action=event_type,
            decision=applied,
            reason_code=reason_code,
            policy_hash=NOT_AN_AUTHORIZATION,
            grant_revision=max(after_revision, 1),
            trace_id=str(event_id),
            event_type=event_type,
            operation_outcome="succeeded" if applied else "denied",
            payload={
                "event_id": str(event_id),
                "event_type": event_type,
                "occurred_at": at.isoformat(),
                "operational_actor": str(actor_id),
                "affected_ids": sorted(str(i) for i in {resource_id, *affected_ids}),
                "before_revision": before_revision,
                "after_revision": after_revision,
                "approval_ref": approval_ref,
                "input_digest": input_digest,
                "description": f"{event_type} for {resource_type}/{resource_id} by {actor_id}",
            },
        ),
    )


def provision_tenant(session: Session, tenant_id: UUID, *, actor_id: UUID, at: datetime) -> None:
    existing = session.get(TenantRow, tenant_id)
    if existing is not None:
        return
    session.add(TenantRow(id=tenant_id, created_at=at, created_by=actor_id))
    session.flush()
    record_operational_event(
        session,
        event_type="tenant_provisioned",
        actor_id=actor_id,
        resource_type="tenant",
        resource_id=tenant_id,
        at=at,
    )


def provision_workspace(
    session: Session, workspace_id: UUID, tenant_id: UUID, *, actor_id: UUID, at: datetime
) -> None:
    if session.get(TenantRow, tenant_id) is None:
        raise OwnershipConflict("tenant is not provisioned")
    existing = session.get(WorkspaceRow, workspace_id)
    if existing is not None:
        if existing.tenant_id != tenant_id:
            raise OwnershipConflict("workspace belongs to a different tenant")
        return
    session.add(
        WorkspaceRow(id=workspace_id, tenant_id=tenant_id, created_at=at, created_by=actor_id)
    )
    session.flush()
    record_operational_event(
        session,
        event_type="workspace_provisioned",
        actor_id=actor_id,
        resource_type="workspace",
        resource_id=workspace_id,
        at=at,
        affected_ids=[tenant_id],
    )


def provision_knowledge_base(
    session: Session,
    knowledge_base_id: UUID,
    workspace_id: UUID,
    tenant_id: UUID,
    *,
    actor_id: UUID,
    at: datetime,
) -> None:
    """A KB resolves to exactly one workspace and tenant; a workspace from another
    tenant is rejected before any row is written (S0001 AC1)."""
    workspace = session.get(WorkspaceRow, workspace_id)
    if workspace is None or workspace.tenant_id != tenant_id:
        raise OwnershipConflict("workspace does not belong to the supplied tenant")
    existing = session.get(KnowledgeBaseRow, knowledge_base_id)
    if existing is not None:
        if (existing.workspace_id, existing.tenant_id) != (workspace_id, tenant_id):
            raise OwnershipConflict("knowledge base belongs to a different owner")
        return
    session.add(
        KnowledgeBaseRow(
            id=knowledge_base_id,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            created_at=at,
            created_by=actor_id,
        )
    )
    session.flush()
    record_operational_event(
        session,
        event_type="knowledge_base_provisioned",
        actor_id=actor_id,
        resource_type="knowledge_base",
        resource_id=knowledge_base_id,
        at=at,
        affected_ids=[workspace_id, tenant_id],
    )


def provision_scope(
    session: Session,
    *,
    tenant_id: UUID,
    workspace_id: UUID,
    knowledge_base_id: UUID,
    actor_id: UUID,
    at: datetime,
) -> None:
    """Convenience: the full hierarchy in one call (idempotent, all-or-nothing)."""
    provision_tenant(session, tenant_id, actor_id=actor_id, at=at)
    provision_workspace(session, workspace_id, tenant_id, actor_id=actor_id, at=at)
    provision_knowledge_base(
        session, knowledge_base_id, workspace_id, tenant_id, actor_id=actor_id, at=at
    )


def resolve_entity(
    session: Session,
    tenant_id: UUID,
    *,
    namespace: str,
    external_key: str,
    actor_id: UUID,
    at: datetime,
) -> UUID:
    """Tenant-scoped insert-or-read. The lookup is constrained to `tenant_id`, so an
    identical external identifier in another tenant is never selected or revealed
    (S0001 AC4). Deterministic matching/merge is F0017; this is exact-key only."""
    if not namespace or not external_key:
        raise ValueError("an external entity identifier needs a namespace and key")
    if session.get(TenantRow, tenant_id) is None:
        raise OwnershipConflict("tenant is not provisioned")

    def lookup() -> UUID | None:
        return session.execute(
            select(EntityIdentityRow.id).where(
                EntityIdentityRow.tenant_id == tenant_id,
                EntityIdentityRow.external_namespace == namespace,
                EntityIdentityRow.external_key == external_key,
            )
        ).scalar_one_or_none()

    found = lookup()
    if found is not None:
        return found
    entity_id = uuid4()
    try:
        with session.begin_nested():
            session.add(
                EntityIdentityRow(
                    id=entity_id,
                    tenant_id=tenant_id,
                    external_namespace=namespace,
                    external_key=external_key,
                    created_at=at,
                    created_by=actor_id,
                )
            )
    except IntegrityError:
        winner = lookup()
        if winner is None:
            raise
        return winner
    record_operational_event(
        session,
        event_type="entity_identity_created",
        actor_id=actor_id,
        resource_type="entity_identity",
        resource_id=entity_id,
        at=at,
        affected_ids=[tenant_id],
    )
    return entity_id


def associate_entity(
    session: Session,
    entity_id: UUID,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    *,
    actor_id: UUID,
    at: datetime,
) -> None:
    """Explicit entity-to-KB association within the entity's own tenant (S0001 AC3).
    Creates no membership; a rejected cross-tenant attempt is audited without
    returning another tenant's identifiers (S0001 AC6)."""
    entity = session.get(EntityIdentityRow, (entity_id, tenant_id))
    kb = session.get(KnowledgeBaseRow, knowledge_base_id)
    if entity is None or kb is None or kb.tenant_id != tenant_id:
        raise OwnershipConflict("entity and knowledge base do not share a tenant")
    if session.get(EntityKnowledgeBaseRow, (entity_id, tenant_id, knowledge_base_id)) is not None:
        return
    session.add(
        EntityKnowledgeBaseRow(
            entity_id=entity_id,
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
            created_at=at,
            created_by=actor_id,
        )
    )
    session.flush()
    record_operational_event(
        session,
        event_type="entity_knowledge_base_associated",
        actor_id=actor_id,
        resource_type="entity_identity",
        resource_id=entity_id,
        at=at,
        affected_ids=[knowledge_base_id],
    )


def record_rejected_ownership(
    session: Session,
    *,
    event_type: str,
    actor_id: UUID,
    resource_type: str,
    resource_id: UUID,
    at: datetime,
) -> None:
    """Audit a rejected ownership mutation in its own (fresh) transaction. Only the
    requested resource ID is recorded — never the conflicting owner's identifiers."""
    record_operational_event(
        session,
        event_type=event_type,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        at=at,
        applied=False,
        reason_code="owner_conflict",
    )


def _key_json(key: ResourceKey) -> dict[str, str]:
    return key.to_json()


def _record_owner(session: Session, key: ResourceKey) -> tuple[UUID, UUID] | None:
    row: ContentArtifact | ReviewItemRow | FactSlotRow | None
    if key.type == ResourceType.CONTENT_ARTIFACT:
        row = session.get(ContentArtifact, key.id)
    elif key.type == ResourceType.REVIEW_TASK:
        row = session.get(ReviewItemRow, key.id)
    else:
        row = session.get(FactSlotRow, key.id)
    return (row.tenant_id, row.knowledge_base_id) if row is not None else None


def provision_resource_access(
    session: Session,
    key: ResourceKey,
    *,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    classifications: Iterable[str],
    source_acl_ids: Iterable[str] = (),
    parent_chain: Iterable[ScopedId] = (),
    dependency_keys: Iterable[ResourceKey] = (),
    actor_id: UUID,
    at: datetime,
    allow_before_record: bool = False,
) -> None:
    """Insert, or verify an identical existing row (idempotent trusted replay).

    Classifications are required: there is no default label that silently implies
    enforcement. The owner must agree with the KB registry and, when it exists, the
    protected record itself. `allow_before_record` is only for a trusted submitter
    pre-registering an artifact ID before the worker creates the record."""
    classifications = sorted(set(classifications))
    if not classifications:
        raise ValueError("a protected resource declares at least one classification")
    kb = session.get(KnowledgeBaseRow, knowledge_base_id)
    if kb is None or kb.tenant_id != tenant_id:
        raise OwnershipConflict("knowledge base does not belong to the supplied tenant")
    owner = _record_owner(session, key)
    if owner is None and not allow_before_record:
        raise OwnershipConflict("protected record does not exist")
    if owner is not None and owner != (tenant_id, knowledge_base_id):
        raise OwnershipConflict("protected record belongs to a different owner")
    values = {
        "tenant_id": tenant_id,
        "knowledge_base_id": knowledge_base_id,
        "parent_chain": [p.to_json() for p in sorted(set(parent_chain))],
        "classifications": classifications,
        "source_acl_ids": sorted(set(source_acl_ids)),
        "dependency_keys": [_key_json(d) for d in sorted(set(dependency_keys))],
    }
    existing = session.get(ResourceAccessRow, (key.type.value, key.id))
    if existing is not None:
        current = {name: getattr(existing, name) for name in values}
        if current != values:
            raise OwnershipConflict("resource security metadata differs from the trusted record")
        return
    session.add(
        ResourceAccessRow(
            resource_type=key.type.value,
            resource_id=key.id,
            revision=1,
            created_at=at,
            created_by=actor_id,
            **values,
        )
    )
    session.flush()
    record_operational_event(
        session,
        event_type="resource_access_provisioned",
        actor_id=actor_id,
        resource_type=key.type.value,
        resource_id=key.id,
        at=at,
        input_digest=hashlib.sha256(
            json.dumps(values, default=str, sort_keys=True).encode()
        ).hexdigest(),
    )


def change_resource_restrictions(
    session: Session,
    key: ResourceKey,
    *,
    expected_revision: int,
    actor_id: UUID,
    at: datetime,
    classifications: Iterable[str] | None = None,
    source_acl_ids: Iterable[str] | None = None,
    parent_chain: Sequence[ScopedId] | None = None,
    approval_ref: str,
) -> int:
    """Trusted restriction change under FOR UPDATE with an expected revision; the
    next protected operation observes it (S0004 AC6)."""
    row = session.execute(
        select(ResourceAccessRow)
        .where(
            ResourceAccessRow.resource_type == key.type.value,
            ResourceAccessRow.resource_id == key.id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()
    if row is None:
        raise OwnershipConflict("protected resource has no security metadata")
    if row.revision != expected_revision:
        raise RevisionConflict("resource restriction revision changed")
    if classifications is not None:
        labels_ = sorted(set(classifications))
        if not labels_:
            raise ValueError("a protected resource declares at least one classification")
        row.classifications = labels_
    if source_acl_ids is not None:
        row.source_acl_ids = sorted(set(source_acl_ids))
    if parent_chain is not None:
        row.parent_chain = [p.to_json() for p in sorted(set(parent_chain))]
    row.revision = expected_revision + 1
    session.flush()
    record_operational_event(
        session,
        event_type="resource_restrictions_changed",
        actor_id=actor_id,
        resource_type=key.type.value,
        resource_id=key.id,
        at=at,
        before_revision=expected_revision,
        after_revision=row.revision,
        approval_ref=approval_ref,
    )
    return row.revision


class RevisionConflict(ValueError):
    """An expected revision no longer matches; nothing was written."""


def inherit_resource_access(
    session: Session,
    source: ResourceKey,
    target: ResourceKey,
    *,
    actor_id: UUID,
    at: datetime,
    add_dependency_on_source: bool = False,
) -> None:
    """Provision a derived record's security metadata from its trusted source record
    (same owner, classifications, source ACL and parents). Used when the engine
    itself creates a protected record: a review task derived from an artifact (which
    then also depends on that artifact as evidence), or a re-opened review task for
    a newer assertion version. Missing source metadata fails closed."""
    access = session.get(ResourceAccessRow, (source.type.value, source.id), populate_existing=True)
    if access is None:
        raise OwnershipConflict("source record has no security metadata")
    dependencies = {ResourceKey(d["type"], UUID(d["id"])) for d in access.dependency_keys}
    if add_dependency_on_source:
        dependencies.add(source)
    provision_resource_access(
        session,
        target,
        tenant_id=access.tenant_id,
        knowledge_base_id=access.knowledge_base_id,
        classifications=access.classifications,
        source_acl_ids=access.source_acl_ids,
        parent_chain=[ScopedId(p["kind"], UUID(p["id"])) for p in access.parent_chain],
        dependency_keys=dependencies - {target},
        actor_id=actor_id,
        at=at,
    )
