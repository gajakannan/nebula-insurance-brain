from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from brain_domain.audit import AuditEvent

from brain_security.authorization import Decision, ResourceRef


class AuditEventRepository(Protocol):
    async def append(self, event: AuditEvent) -> None: ...


class RepositoryAuditSink:
    """`AuditSink` (F0001-S0006) backed by an append-only `AuditEventRepository`.
    Written in the same transaction as the read's request log by the caller."""

    def __init__(self, repository: AuditEventRepository) -> None:
        self._repository = repository

    async def record(
        self,
        *,
        actor_principal_id: UUID,
        delegate_principal_id: UUID | None,
        resource: ResourceRef,
        action: str,
        decision: Decision,
    ) -> None:
        await self._repository.append(
            AuditEvent(
                id=uuid4(),
                occurred_at=datetime.now(UTC),
                actor_principal_id=actor_principal_id,
                delegate_principal_id=delegate_principal_id,
                resource_type=resource.type,
                resource_id=resource.id,
                action=action,
                decision=decision.allowed,
                reason_code=decision.reason_code,
                policy_hash=decision.policy_hash,
                grant_revision=decision.grant_revision,
                trace_id=decision.trace_id,
            )
        )


class InMemoryAuditEventRepository:
    """Test/harness `AuditEventRepository`; the real one lives in `brain_persistence`."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    async def append(self, event: AuditEvent) -> None:
        self.events.append(event)
