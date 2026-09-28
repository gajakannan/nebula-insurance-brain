"""SQLAlchemy adapters for the AuthX kernel (F0002, ADR-0061/0062).

Every query is written once against a synchronous `Session`. The sync worker uses
`SyncAuthorityStore` directly; the async API uses `SqlAlchemyAuthorityStore`, which
runs the same functions through `AsyncSession.run_sync` — so both adapters read,
lock and hydrate identically and hand identical inputs to the shared evaluator.

Lock order (never violated): policy pointer -> principal_authority rows by
principal ID -> delegation row -> resource_access rows by (type, id) -> the
operation's own semantic rows. Reads take FOR SHARE; changes take FOR UPDATE.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import UUID

from brain_domain.authx import (
    ActionCeiling,
    AuthenticationEvent,
    AuthorizationDecision,
    Delegation,
    PilotRole,
    ResourceEnvelope,
    ResourceKey,
    ResourceType,
    ScopedId,
    ScopeSlice,
    Selector,
    labels,
)
from brain_domain.principal import Principal, PrincipalKind, PrincipalStatus
from brain_domain.tenancy import OwnedScope
from brain_security.audit import decision_audit_event
from brain_security.execution import PrincipalAuthority
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from brain_persistence.models import (
    AuditEventRow,
    AuthenticationEventRow,
    ContentArtifact,
    DelegationRow,
    FactSlotRow,
    KnowledgeBaseRow,
    MembershipRow,
    PolicyReleasePointerRow,
    PrincipalAuthorityRow,
    PrincipalRow,
    ResourceAccessRow,
    ReviewItemRow,
)

T = TypeVar("T")

POINTER_ID = 1


# --- row <-> domain mapping ---------------------------------------------------------


def principal_from_row(row: PrincipalRow) -> Principal:
    return Principal(
        id=row.id,
        kind=PrincipalKind(row.kind),
        issuer=row.issuer,
        subject=row.subject,
        status=PrincipalStatus(row.status),
    )


def selectors_from_json(data: Sequence[dict[str, Any]]) -> tuple[Selector, ...]:
    return tuple(
        Selector(kind=item["kind"], mode=item["mode"], ids=frozenset(UUID(i) for i in item["ids"]))
        for item in data
    )


def selectors_to_json(selectors: Sequence[Selector]) -> list[dict[str, object]]:
    return [s.to_json() for s in sorted(selectors, key=lambda s: s.kind.value)]


def labels_to_json(value: object) -> object:
    normalized = labels(value)  # type: ignore[arg-type]
    return normalized if isinstance(normalized, str) else sorted(normalized)


def ceilings_from_json(data: Sequence[dict[str, Any]]) -> tuple[ActionCeiling, ...]:
    return tuple(
        ActionCeiling(
            scope=OwnedScope(
                UUID(c["scope"]["tenant_id"]),
                UUID(c["scope"]["workspace_id"]),
                UUID(c["scope"]["knowledge_base_id"]),
            ),
            resource=ResourceKey(ResourceType(c["resource"]["type"]), UUID(c["resource"]["id"])),
            actions=frozenset(c["actions"]),
        )
        for c in data
    )


def delegation_from_row(row: DelegationRow) -> Delegation:
    return Delegation(
        id=row.id,
        acting_principal_id=row.acting_principal_id,
        executor_principal_id=row.executor_principal_id,
        issued_by=row.issued_by,
        issued_at=_aware(row.issued_at),
        not_before=_aware(row.not_before),
        expires_at=_aware(row.expires_at),
        revoked_at=_aware(row.revoked_at) if row.revoked_at else None,
        revision=row.revision,
        ceilings=ceilings_from_json(row.ceilings),
    )


def _aware(value: datetime) -> datetime:
    """SQLite drops tzinfo; every stored instant is UTC by construction."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def resource_key_from_json(item: dict[str, str]) -> ResourceKey:
    return ResourceKey(ResourceType(item["type"]), UUID(item["id"]))


# --- the shared synchronous queries ----------------------------------------------------


def current_policy_release(session: Session) -> str | None:
    row = session.execute(
        select(PolicyReleasePointerRow.release_id)
        .where(PolicyReleasePointerRow.id == POINTER_ID)
        .with_for_update(read=True)
    ).first()
    return row.release_id if row is not None else None


def peek_delegation(session: Session, delegation_id: UUID) -> Delegation | None:
    row = session.get(DelegationRow, delegation_id, populate_existing=True)
    return delegation_from_row(row) if row is not None else None


def lock_delegation(session: Session, delegation_id: UUID) -> Delegation | None:
    row = session.execute(
        select(DelegationRow)
        .where(DelegationRow.id == delegation_id)
        .with_for_update(read=True)
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()
    return delegation_from_row(row) if row is not None else None


def lock_authority(
    session: Session, principal_ids: Sequence[UUID]
) -> dict[UUID, PrincipalAuthority]:
    result: dict[UUID, PrincipalAuthority] = {}
    for principal_id in sorted(set(principal_ids), key=str):
        authority = session.execute(
            select(PrincipalAuthorityRow.revision)
            .where(PrincipalAuthorityRow.principal_id == principal_id)
            .with_for_update(read=True)
        ).first()
        principal = session.execute(
            select(PrincipalRow)
            .where(PrincipalRow.id == principal_id)
            .execution_options(populate_existing=True)
        ).scalar_one_or_none()
        if authority is None or principal is None:
            continue
        result[principal_id] = PrincipalAuthority(principal_from_row(principal), authority.revision)
    return result


def scope_slices(session: Session, principal_id: UUID) -> tuple[ScopeSlice, ...]:
    rows = session.execute(
        select(MembershipRow, KnowledgeBaseRow.workspace_id)
        .join(
            KnowledgeBaseRow,
            (KnowledgeBaseRow.id == MembershipRow.knowledge_base_id)
            & (KnowledgeBaseRow.tenant_id == MembershipRow.tenant_id),
        )
        .where(MembershipRow.principal_id == principal_id, MembershipRow.revoked_at.is_(None))
        .order_by(MembershipRow.id)
        .execution_options(populate_existing=True)
    ).all()
    slices: list[ScopeSlice] = []
    for membership, workspace_id in rows:
        slices.append(
            ScopeSlice(
                membership_id=membership.id,
                scope=OwnedScope(membership.tenant_id, workspace_id, membership.knowledge_base_id),
                role=PilotRole(membership.role),
                valid_from=_aware(membership.valid_from),
                expires_at=_aware(membership.expires_at) if membership.expires_at else None,
                revoked_at=None,
                grant_revision=membership.grant_revision,
                selectors=selectors_from_json(membership.selectors),
                classifications=labels(membership.classifications),
                source_acl_ids=labels(membership.source_acl_ids),
            )
        )
    return tuple(slices)


def _semantic_owner(session: Session, key: ResourceKey) -> tuple[tuple[UUID, UUID], int] | None:
    """The protected record's own (tenant, kb) and resource revision, or None."""
    if key.type == ResourceType.CONTENT_ARTIFACT:
        artifact = session.get(ContentArtifact, key.id, populate_existing=True)
        return ((artifact.tenant_id, artifact.knowledge_base_id), 1) if artifact else None
    if key.type == ResourceType.REVIEW_TASK:
        item = session.get(ReviewItemRow, key.id, populate_existing=True)
        return ((item.tenant_id, item.knowledge_base_id), item.assertion_version) if item else None
    slot = session.get(FactSlotRow, key.id, populate_existing=True)
    return ((slot.tenant_id, slot.knowledge_base_id), 1) if slot else None


def hydrate(
    session: Session, key: ResourceKey, *, require_record: bool = True
) -> ResourceEnvelope | None:
    """Security metadata only — never content bytes, fact values, reviewer comments
    or evidence payloads. Missing or inconsistent metadata returns None (deny).

    `require_record=False` is used only by the worker for `ingest`/`interpret` on an
    artifact whose trusted submitter provisioned its metadata before the record
    exists; if the record does exist its ownership must still agree."""
    access = session.execute(
        select(ResourceAccessRow)
        .where(
            ResourceAccessRow.resource_type == key.type.value,
            ResourceAccessRow.resource_id == key.id,
        )
        .with_for_update(read=True)
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()
    if access is None:
        return None
    kb = session.get(KnowledgeBaseRow, access.knowledge_base_id)
    if kb is None or kb.tenant_id != access.tenant_id:
        return None
    owner = _semantic_owner(session, key)
    if owner is None and require_record:
        return None
    if owner is not None and owner[0] != (access.tenant_id, access.knowledge_base_id):
        return None
    try:
        return ResourceEnvelope(
            key=key,
            scope=OwnedScope(access.tenant_id, kb.workspace_id, access.knowledge_base_id),
            parent_chain=frozenset(ScopedId(p["kind"], UUID(p["id"])) for p in access.parent_chain),
            classifications=frozenset(access.classifications),
            source_acl_ids=frozenset(access.source_acl_ids),
            dependency_keys=frozenset(resource_key_from_json(d) for d in access.dependency_keys),
            resource_revision=owner[1] if owner else 1,
            restriction_revision=access.revision,
        )
    except (ValueError, KeyError, TypeError):
        return None  # malformed trusted metadata fails closed


def append_decision(session: Session, decision: AuthorizationDecision) -> None:
    append_audit_event(session, decision_audit_event(decision))


def audit_timestamp(value: datetime) -> datetime:
    """`audit_event.occurred_at` is the F0001 `timestamp without time zone` column;
    it is kept (existing rows are never rewritten) and stores the UTC instant."""
    return value.astimezone(UTC).replace(tzinfo=None) if value.tzinfo else value


def append_audit_event(session: Session, event: Any) -> None:
    session.add(
        AuditEventRow(
            id=event.id,
            occurred_at=audit_timestamp(event.occurred_at),
            actor_principal_id=event.actor_principal_id,
            delegate_principal_id=event.delegate_principal_id,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            action=event.action,
            decision=event.decision,
            reason_code=event.reason_code,
            policy_hash=event.policy_hash,
            grant_revision=event.grant_revision,
            trace_id=event.trace_id,
            decision_id=event.decision_id,
            event_type=event.event_type,
            operation_outcome=event.operation_outcome,
            payload=event.payload,
        )
    )
    session.flush()


def append_authentication_event(session: Session, event: AuthenticationEvent) -> None:
    session.add(
        AuthenticationEventRow(
            event_id=event.event_id,
            occurred_at=event.occurred_at,
            reason_code=event.reason_code.value,
            route_template=event.route_template,
            trace_id=event.trace_id,
            payload=event.to_json(),
        )
    )
    session.flush()


# --- adapters ------------------------------------------------------------------------------


class SyncAuthorityStore:
    """`brain_security.execution.AuthorityStore` semantics over a sync `Session`
    (the worker's transaction); methods are plain calls, not coroutines."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def current_policy_release(self) -> str | None:
        return current_policy_release(self.session)

    def peek_delegation(self, delegation_id: UUID) -> Delegation | None:
        return peek_delegation(self.session, delegation_id)

    def lock_authority(self, principal_ids: Sequence[UUID]) -> dict[UUID, PrincipalAuthority]:
        return lock_authority(self.session, principal_ids)

    def lock_delegation(self, delegation_id: UUID) -> Delegation | None:
        return lock_delegation(self.session, delegation_id)

    def scope_slices(self, principal_id: UUID) -> tuple[ScopeSlice, ...]:
        return scope_slices(self.session, principal_id)

    def hydrate(self, key: ResourceKey, *, require_record: bool = True) -> ResourceEnvelope | None:
        return hydrate(self.session, key, require_record=require_record)

    def append_decision(self, decision: AuthorizationDecision) -> None:
        append_decision(self.session, decision)


class SqlAlchemyAuthorityStore:
    """Async `AuthorityStore` bound to the request's unit of work."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _run(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        return await self._session.run_sync(lambda s: fn(s, *args, **kwargs))

    async def current_policy_release(self) -> str | None:
        return await self._run(current_policy_release)

    async def peek_delegation(self, delegation_id: UUID) -> Delegation | None:
        return await self._run(peek_delegation, delegation_id)

    async def lock_authority(self, principal_ids: Sequence[UUID]) -> dict[UUID, PrincipalAuthority]:
        return await self._run(lock_authority, principal_ids)

    async def lock_delegation(self, delegation_id: UUID) -> Delegation | None:
        return await self._run(lock_delegation, delegation_id)

    async def scope_slices(self, principal_id: UUID) -> tuple[ScopeSlice, ...]:
        return await self._run(scope_slices, principal_id)

    async def hydrate(self, key: ResourceKey) -> ResourceEnvelope | None:
        return await self._run(hydrate, key)

    async def append_decision(self, decision: AuthorizationDecision) -> None:
        await self._run(append_decision, decision)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
