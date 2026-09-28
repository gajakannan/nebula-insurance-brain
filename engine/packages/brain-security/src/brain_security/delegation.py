"""Bounded delegation lifecycle rules (F0002-S0005, ADR-0062).

Issuance and revocation are trusted operational commands (no web endpoint, no
implicit role). A delegation never exceeds the acting principal's current
authority at issuance, names exact resources and a finite action set, has a finite
expiry, is bound to one executor, and cannot be delegated onward. At use time the
evaluator re-intersects the ceiling with the acting principal's then-current grants.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from brain_domain.authx import Delegation, ScopeSlice, is_active
from brain_domain.principal import Principal, PrincipalKind

from brain_security.evaluation import PolicyEvaluator


class DelegationRejected(ValueError):
    """Issuance or revocation refused; no state was written."""


def validate_issuance(
    delegation: Delegation,
    *,
    acting: Principal,
    executor: Principal,
    acting_slices: Sequence[ScopeSlice],
    policy: PolicyEvaluator,
    now: datetime,
) -> None:
    if not is_active(acting) or not is_active(executor):
        raise DelegationRejected("acting and executor principals must be active")
    if executor.kind not in {PrincipalKind.AGENT, PrincipalKind.SERVICE}:
        raise DelegationRejected("only an agent or service principal can execute a delegation")
    if acting.kind == PrincipalKind.AGENT:
        raise DelegationRejected("an agent cannot be the acting principal (no onward delegation)")
    if (
        delegation.acting_principal_id != acting.id
        or delegation.executor_principal_id != executor.id
    ):
        raise DelegationRejected("delegation principals do not match")
    if delegation.expires_at <= now:
        raise DelegationRejected("delegation is already expired")
    if delegation.revoked_at is not None:
        raise DelegationRejected("a new delegation cannot be revoked")
    current = [s for s in acting_slices if s.current_at(now)]
    for ceiling in delegation.ceilings:
        for action in ceiling.actions:
            if not any(
                s.scope == ceiling.scope
                and policy.permits(
                    s.role.value, s.scope, ceiling.scope, ceiling.resource, action.value
                )
                for s in current
            ):
                raise DelegationRejected("ceiling exceeds the acting principal's current authority")


class DelegationService(Protocol):
    async def resolve(
        self, delegation_id: UUID, executor_id: UUID, at: datetime
    ) -> Delegation | None: ...

    async def issue(
        self,
        delegation: Delegation,
        operator_id: UUID,
        approval_ref: str,
        expected_authority_revision: int,
    ) -> UUID: ...

    async def revoke(
        self, delegation_id: UUID, operator_id: UUID, approval_ref: str, expected_revision: int
    ) -> None: ...
