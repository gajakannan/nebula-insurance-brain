"""Durable, non-secret audit projections (F0002-S0006, ADR-0062)."""

from __future__ import annotations

from typing import Protocol
from uuid import uuid4

from brain_domain.audit import AuditEvent
from brain_domain.authx import AuthenticationEvent, AuthorizationDecision

AUTHORIZATION_DECISION = "authorization_decision"


class AuditEventRepository(Protocol):
    async def append(self, event: AuditEvent) -> None: ...


class AuthenticationEventSink(Protocol):
    """Write-only sink for rejected credentials. It never reads principal or
    protected-resource storage to enrich the event (S0006 AC2)."""

    async def record(self, event: AuthenticationEvent) -> None: ...


def decision_audit_event(decision: AuthorizationDecision) -> AuditEvent:
    """Project a schema `Decision` onto one append-only `audit_event` row.

    Legacy columns stay meaningful for F0001 readers: `actor_principal_id` is the
    accountable (acting) principal and `delegate_principal_id` the executor when a
    delegation applies. The full v1 decision rides in `payload`; it contains no
    token, request body or protected payload by construction."""
    return AuditEvent(
        id=uuid4(),
        occurred_at=decision.occurred_at,
        actor_principal_id=decision.actor_principal_id,
        delegate_principal_id=decision.executor_principal_id,
        resource_type=decision.resource.type.value,
        resource_id=decision.resource.id,
        action=decision.action,
        decision=decision.allowed,
        reason_code=decision.reason_code.value,
        policy_hash=decision.policy_hash,
        grant_revision=decision.grant_revision,
        trace_id=decision.trace_id,
        decision_id=decision.decision_id,
        event_type=AUTHORIZATION_DECISION,
        operation_outcome=decision.operation_outcome.value,
        payload=decision.to_json(),
    )


class InMemoryAuditEventRepository:
    """Test/harness `AuditEventRepository`; the real one lives in `brain_persistence`."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    async def append(self, event: AuditEvent) -> None:
        self.events.append(event)
