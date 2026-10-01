"""Trusted grant, policy-release and delegation lifecycle (F0002-S0003/S0005).

Every change takes the principal's authority row FOR UPDATE and advances its
monotonic revision in the same transaction as the change, so a revocation that
commits before an operation starts is always observed by that operation (its
evaluation holds FOR SHARE on the same row). Each change is audited with the
operational actor, before/after revision and approval reference.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from uuid import UUID, uuid4

from brain_domain.authx import (
    Delegation,
    LabelSet,
    PilotRole,
    PolicyRelease,
    Selector,
    labels,
)
from brain_domain.tenancy import OwnershipConflict
from brain_security.delegation import DelegationRejected, validate_issuance
from brain_security.evaluation import PolicyEvaluator
from sqlalchemy import select
from sqlalchemy.orm import Session

from brain_persistence.authx import (
    delegation_from_row,
    labels_to_json,
    principal_from_row,
    scope_slices,
    selectors_to_json,
)
from brain_persistence.models import (
    DelegationRow,
    KnowledgeBaseRow,
    MembershipRow,
    PolicyReleasePointerRow,
    PolicyReleaseRow,
    PrincipalAuthorityRow,
    PrincipalRow,
)
from brain_persistence.tenancy import RevisionConflict, record_operational_event


def _lock_authority(session: Session, principal_id: UUID) -> PrincipalAuthorityRow:
    row = session.execute(
        select(PrincipalAuthorityRow)
        .where(PrincipalAuthorityRow.principal_id == principal_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()
    if row is None:
        raise OwnershipConflict("principal has no authority record")
    return row


def grant_membership(
    session: Session,
    *,
    principal_id: UUID,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    role: PilotRole | str,
    selectors: Sequence[Selector],
    classifications: LabelSet | Iterable[str],
    source_acl_ids: LabelSet | Iterable[str],
    valid_from: datetime,
    expires_at: datetime | None = None,
    operator_id: UUID,
    approval_ref: str,
    at: datetime,
    expected_authority_revision: int | None = None,
    membership_id: UUID | None = None,
) -> UUID:
    """One complete grant slice in one KB. Restrictions are mandatory arguments —
    `unrestricted_selectors()` and `"*"` must be chosen explicitly."""
    role = PilotRole(role)
    kb = session.get(KnowledgeBaseRow, knowledge_base_id)
    if kb is None or kb.tenant_id != tenant_id:
        raise OwnershipConflict("knowledge base does not belong to the supplied tenant")
    authority = _lock_authority(session, principal_id)
    if (
        expected_authority_revision is not None
        and authority.revision != expected_authority_revision
    ):
        raise RevisionConflict("principal authority revision changed")
    before = authority.revision
    authority.revision = before + 1
    membership_id = membership_id or uuid4()
    session.add(
        MembershipRow(
            id=membership_id,
            principal_id=principal_id,
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
            role=role.value,
            grant_revision=authority.revision,
            revoked_at=None,
            valid_from=valid_from,
            expires_at=expires_at,
            selectors=selectors_to_json(selectors),
            classifications=labels_to_json(labels(classifications)),
            source_acl_ids=labels_to_json(labels(source_acl_ids)),
        )
    )
    session.flush()
    record_operational_event(
        session,
        event_type="membership_granted",
        actor_id=operator_id,
        resource_type="membership",
        resource_id=membership_id,
        at=at,
        before_revision=before,
        after_revision=authority.revision,
        approval_ref=approval_ref,
        affected_ids=[principal_id, knowledge_base_id],
    )
    return membership_id


def revoke_membership(
    session: Session,
    membership_id: UUID,
    *,
    operator_id: UUID,
    approval_ref: str,
    at: datetime,
    expected_grant_revision: int | None = None,
) -> int:
    """Revoke under the authority lock; returns the new authority revision (S0003 AC4/AC7)."""
    membership = session.get(MembershipRow, membership_id, populate_existing=True)
    if membership is None:
        raise OwnershipConflict("membership does not exist")
    authority = _lock_authority(session, membership.principal_id)
    membership = session.execute(
        select(MembershipRow)
        .where(MembershipRow.id == membership_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one()
    if expected_grant_revision is not None and membership.grant_revision != expected_grant_revision:
        raise RevisionConflict("membership revision changed")
    if membership.revoked_at is not None:
        return authority.revision
    before = authority.revision
    authority.revision = before + 1
    membership.revoked_at = at
    membership.grant_revision = authority.revision
    session.flush()
    record_operational_event(
        session,
        event_type="membership_revoked",
        actor_id=operator_id,
        resource_type="membership",
        resource_id=membership_id,
        at=at,
        before_revision=before,
        after_revision=authority.revision,
        approval_ref=approval_ref,
        affected_ids=[membership.principal_id, membership.knowledge_base_id],
    )
    return authority.revision


def register_policy_release(session: Session, release: PolicyRelease, *, at: datetime) -> None:
    """Idempotent: an immutable release row keyed by its content hash."""
    existing = session.get(PolicyReleaseRow, release.release_id)
    if existing is not None:
        if (existing.model_sha256, existing.policy_sha256, existing.contract_version) != (
            release.model_sha256,
            release.policy_sha256,
            release.contract_version,
        ):
            raise ValueError("policy release identity collision")
        return
    session.add(
        PolicyReleaseRow(
            release_id=release.release_id,
            release_sha256=release.release_sha256,
            model_sha256=release.model_sha256,
            policy_sha256=release.policy_sha256,
            contract_version=release.contract_version,
            created_at=at,
        )
    )
    session.flush()


def activate_policy_release(
    session: Session, release: PolicyRelease, *, operator_id: UUID, approval_ref: str, at: datetime
) -> None:
    """Switch the current release under FOR UPDATE on the singleton pointer."""
    register_policy_release(session, release, at=at)
    pointer = session.execute(
        select(PolicyReleasePointerRow)
        .where(PolicyReleasePointerRow.id == 1)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()
    before = pointer.release_id if pointer else None
    if pointer is None:
        session.add(
            PolicyReleasePointerRow(
                id=1, release_id=release.release_id, activated_at=at, activated_by=operator_id
            )
        )
    elif pointer.release_id != release.release_id:
        pointer.release_id = release.release_id
        pointer.activated_at = at
        pointer.activated_by = operator_id
    else:
        return
    session.flush()
    record_operational_event(
        session,
        event_type="policy_release_activated",
        actor_id=operator_id,
        resource_type="policy_release",
        resource_id=operator_id,
        at=at,
        approval_ref=approval_ref,
        input_digest=f"{before}->{release.release_id}",
    )


def issue_delegation(
    session: Session,
    delegation: Delegation,
    *,
    operator_id: UUID,
    approval_ref: str,
    policy: PolicyEvaluator,
    at: datetime,
    expected_authority_revision: int | None = None,
) -> UUID:
    """Trusted issuance: the ceiling cannot exceed the acting principal's current
    authority, the executor must be an explicitly provisioned agent/service, and
    there is no onward delegation or implicit renewal (S0005)."""
    if not approval_ref:
        raise DelegationRejected("issuance requires an approval reference")
    authority = _lock_authority(session, delegation.acting_principal_id)
    if (
        expected_authority_revision is not None
        and authority.revision != expected_authority_revision
    ):
        raise RevisionConflict("acting principal authority revision changed")
    acting = session.get(PrincipalRow, delegation.acting_principal_id, populate_existing=True)
    executor = session.get(PrincipalRow, delegation.executor_principal_id, populate_existing=True)
    if acting is None or executor is None:
        raise DelegationRejected("delegation principals must exist")
    validate_issuance(
        delegation,
        acting=principal_from_row(acting),
        executor=principal_from_row(executor),
        acting_slices=scope_slices(session, delegation.acting_principal_id),
        policy=policy,
        now=at,
    )
    session.add(
        DelegationRow(
            id=delegation.id,
            acting_principal_id=delegation.acting_principal_id,
            executor_principal_id=delegation.executor_principal_id,
            issued_by=delegation.issued_by,
            issued_at=delegation.issued_at,
            not_before=delegation.not_before,
            expires_at=delegation.expires_at,
            revoked_at=None,
            revision=1,
            ceilings=[c.to_json() for c in delegation.ceilings],
            approval_ref=approval_ref,
            created_at=at,
        )
    )
    session.flush()
    record_operational_event(
        session,
        event_type="delegation_issued",
        actor_id=operator_id,
        resource_type="delegation",
        resource_id=delegation.id,
        at=at,
        approval_ref=approval_ref,
        affected_ids=[delegation.acting_principal_id, delegation.executor_principal_id],
    )
    return delegation.id


def revoke_delegation(
    session: Session,
    delegation_id: UUID,
    *,
    operator_id: UUID,
    approval_ref: str,
    at: datetime,
    expected_revision: int | None = None,
) -> Delegation:
    row = session.execute(
        select(DelegationRow)
        .where(DelegationRow.id == delegation_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()
    if row is None:
        raise DelegationRejected("delegation does not exist")
    if expected_revision is not None and row.revision != expected_revision:
        raise RevisionConflict("delegation revision changed")
    if row.revoked_at is None:
        before = row.revision
        row.revoked_at = at
        row.revision = before + 1
        session.flush()
        record_operational_event(
            session,
            event_type="delegation_revoked",
            actor_id=operator_id,
            resource_type="delegation",
            resource_id=delegation_id,
            at=at,
            before_revision=before,
            after_revision=row.revision,
            approval_ref=approval_ref,
        )
    return delegation_from_row(row)
