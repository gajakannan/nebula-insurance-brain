from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from brain_domain.principal import Membership, Principal


@dataclass(frozen=True, slots=True)
class ResourceRef:
    type: str  # "content_artifact" | "review_task" | "fact_slot"
    id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID
    classification: str = "internal"


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    reason_code: str
    policy_hash: str
    grant_revision: int
    trace_id: str


class CasbinEnforcer(Protocol):
    def enforce(
        self,
        role: str,
        sub_knowledge_base_id: str,
        resource_type: str,
        obj_knowledge_base_id: str,
        action: str,
    ) -> bool: ...

    @property
    def policy_hash(self) -> str: ...


class AuditSink(Protocol):
    async def record(
        self,
        *,
        actor_principal_id: UUID,
        delegate_principal_id: UUID | None,
        resource: ResourceRef,
        action: str,
        decision: Decision,
    ) -> None: ...


class AuthorizationService:
    """1 memberships -> 2 structural tenancy conjunction -> 3 Casbin evaluate ->
    4 audit -> 5 return (F0001-S0006 logic flow)."""

    def __init__(self, enforcer: CasbinEnforcer, audit: AuditSink) -> None:
        self._enforcer = enforcer
        self._audit = audit

    async def authorize(
        self,
        principal: Principal,
        memberships: Sequence[Membership],
        resource: ResourceRef,
        action: str,
        *,
        trace_id: str,
    ) -> Decision:
        matching = [
            m
            for m in memberships
            if m.tenant_id == resource.tenant_id
            and m.knowledge_base_id == resource.knowledge_base_id
        ]
        if not matching:
            decision = Decision(
                allowed=False,
                reason_code="no_membership",
                policy_hash=self._enforcer.policy_hash,
                grant_revision=0,
                trace_id=trace_id,
            )
        else:
            membership = matching[0]
            allowed = self._enforcer.enforce(
                membership.role,
                str(membership.knowledge_base_id),
                resource.type,
                str(resource.knowledge_base_id),
                action,
            )
            decision = Decision(
                allowed=allowed,
                reason_code="allowed" if allowed else "policy_denied",
                policy_hash=self._enforcer.policy_hash,
                grant_revision=membership.grant_revision,
                trace_id=trace_id,
            )

        await self._audit.record(
            actor_principal_id=principal.id,
            delegate_principal_id=None,
            resource=resource,
            action=action,
            decision=decision,
        )
        return decision
