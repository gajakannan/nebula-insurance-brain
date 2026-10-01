"""Stable verified principal identity (F0002-S0002, ADR-0049/0061).

`external_identity` is the authoritative `(issuer, subject)` alias table. First
verified sight is a unique insert-or-read under a savepoint, so concurrent first
resolutions converge on one principal with no orphan rows. Linking an additional
alias is an explicit operational act with an approval reference; histories are
never merged and email is never an identity.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import UUID, uuid4

from brain_domain.authx import AuthenticationEvent
from brain_domain.principal import Principal, PrincipalKind, PrincipalStatus
from brain_security.principals import AliasConflict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session

from brain_persistence.authx import append_authentication_event, principal_from_row
from brain_persistence.models import ExternalIdentityRow, PrincipalAuthorityRow, PrincipalRow
from brain_persistence.tenancy import record_operational_event

T = TypeVar("T")


def find_by_alias(session: Session, issuer: str, subject: str) -> Principal | None:
    row = session.execute(
        select(PrincipalRow)
        .join(ExternalIdentityRow, ExternalIdentityRow.principal_id == PrincipalRow.id)
        .where(ExternalIdentityRow.issuer == issuer, ExternalIdentityRow.subject == subject)
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()
    return principal_from_row(row) if row is not None else None


def _insert_principal(
    session: Session,
    *,
    issuer: str,
    subject: str,
    kind: PrincipalKind,
    at: datetime,
    linked_by: UUID | None,
    approval_ref: str | None,
) -> Principal:
    principal_id = uuid4()
    session.add(
        PrincipalRow(
            id=principal_id,
            kind=kind.value,
            issuer=issuer,
            subject=subject,
            status=PrincipalStatus.ACTIVE.value,
        )
    )
    session.flush()
    session.add(
        ExternalIdentityRow(
            issuer=issuer,
            subject=subject,
            principal_id=principal_id,
            linked_at=at,
            linked_by=linked_by,
            approval_ref=approval_ref,
        )
    )
    session.add(PrincipalAuthorityRow(principal_id=principal_id, revision=1))
    session.flush()
    return Principal(principal_id, kind, issuer, subject, PrincipalStatus.ACTIVE)


def resolve_or_create(
    session: Session, issuer: str, subject: str, kind: PrincipalKind, *, at: datetime
) -> Principal:
    """First verified self-provisioning: principal + alias + authority revision 1,
    no grants. A concurrent winner's row is returned; the loser's savepoint rolls
    back so no orphan principal survives (S0002 AC1)."""
    existing = find_by_alias(session, issuer, subject)
    if existing is not None:
        return existing
    try:
        with session.begin_nested():
            created = _insert_principal(
                session,
                issuer=issuer,
                subject=subject,
                kind=kind,
                at=at,
                linked_by=None,
                approval_ref=None,
            )
    except IntegrityError:
        winner = find_by_alias(session, issuer, subject)
        if winner is None:
            raise
        return winner
    record_operational_event(
        session,
        event_type="principal_resolved",
        actor_id=created.id,
        resource_type="principal",
        resource_id=created.id,
        at=at,
    )
    return created


def provision_principal(
    session: Session,
    *,
    issuer: str,
    subject: str,
    kind: PrincipalKind,
    operator_id: UUID,
    approval_ref: str,
    at: datetime,
) -> Principal:
    """Explicit provisioning of a service/agent (or pre-provisioned user) identity to
    its trusted kind. Re-provisioning the same alias with the same kind is a no-op;
    a different kind is refused (kind is registry state, never inferred)."""
    if not approval_ref:
        raise ValueError("explicit provisioning requires an approval reference")
    existing = find_by_alias(session, issuer, subject)
    if existing is not None:
        if existing.kind != kind:
            raise AliasConflict("identity is already provisioned with a different kind")
        return existing
    created = _insert_principal(
        session,
        issuer=issuer,
        subject=subject,
        kind=kind,
        at=at,
        linked_by=operator_id,
        approval_ref=approval_ref,
    )
    record_operational_event(
        session,
        event_type="principal_provisioned",
        actor_id=operator_id,
        resource_type="principal",
        resource_id=created.id,
        at=at,
        approval_ref=approval_ref,
    )
    return created


def link_identity(
    session: Session,
    principal_id: UUID,
    issuer: str,
    subject: str,
    *,
    approval_ref: str,
    operator_id: UUID,
    at: datetime,
) -> None:
    """Approved identity-provider migration or additional alias (S0002 AC6). Locks the
    principal; refuses a pair already linked elsewhere; never merges histories."""
    if not approval_ref:
        raise ValueError("linking an identity requires an approval reference")
    principal = session.execute(
        select(PrincipalRow).where(PrincipalRow.id == principal_id).with_for_update()
    ).scalar_one_or_none()
    if principal is None:
        raise AliasConflict("principal does not exist")
    current = session.get(ExternalIdentityRow, (issuer, subject))
    if current is not None:
        if current.principal_id != principal_id:
            raise AliasConflict("identity is already linked to a different principal")
        return
    session.add(
        ExternalIdentityRow(
            issuer=issuer,
            subject=subject,
            principal_id=principal_id,
            linked_at=at,
            linked_by=operator_id,
            approval_ref=approval_ref,
        )
    )
    session.flush()
    record_operational_event(
        session,
        event_type="identity_linked",
        actor_id=operator_id,
        resource_type="principal",
        resource_id=principal_id,
        at=at,
        approval_ref=approval_ref,
    )


def set_principal_status(
    session: Session,
    principal_id: UUID,
    status: PrincipalStatus,
    *,
    operator_id: UUID,
    approval_ref: str,
    at: datetime,
) -> int:
    """Disable/re-enable under the authority lock so the next operation observes it."""
    authority = session.execute(
        select(PrincipalAuthorityRow)
        .where(PrincipalAuthorityRow.principal_id == principal_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one()
    principal = session.get(PrincipalRow, principal_id, populate_existing=True)
    assert principal is not None
    before = authority.revision
    principal.status = status.value
    authority.revision = before + 1
    session.flush()
    record_operational_event(
        session,
        event_type=f"principal_{status.value}",
        actor_id=operator_id,
        resource_type="principal",
        resource_id=principal_id,
        at=at,
        before_revision=before,
        after_revision=authority.revision,
        approval_ref=approval_ref,
    )
    return authority.revision


class SqlAlchemyIdentityRepository:
    """`brain_security.principals.IdentityRepository` over the request's AsyncSession."""

    def __init__(
        self, session: AsyncSession, *, clock: Callable[[], datetime] | None = None
    ) -> None:
        self._session = session
        self._clock = clock or (lambda: datetime.now(UTC))

    async def _run(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        return await self._session.run_sync(lambda s: fn(s, *args, **kwargs))

    async def find_by_alias(self, issuer: str, subject: str) -> Principal | None:
        return await self._run(find_by_alias, issuer, subject)

    async def resolve_or_create(self, issuer: str, subject: str, kind: PrincipalKind) -> Principal:
        return await self._run(resolve_or_create, issuer, subject, kind, at=self._clock())

    async def link_identity(
        self, principal_id: UUID, issuer: str, subject: str, approval_ref: str, operator_id: UUID
    ) -> None:
        await self._run(
            link_identity,
            principal_id,
            issuer,
            subject,
            approval_ref=approval_ref,
            operator_id=operator_id,
            at=self._clock(),
        )


class SqlAlchemyAuthenticationEventSink:
    """Write-only durable sink for rejected credentials, in its own session so it
    never shares a transaction (or a read) with protected storage."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def record(self, event: AuthenticationEvent) -> None:
        async with self._session_factory() as session:
            await session.run_sync(append_authentication_event, event)
            await session.commit()
