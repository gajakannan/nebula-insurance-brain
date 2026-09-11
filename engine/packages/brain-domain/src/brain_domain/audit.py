from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuditEvent:
    id: UUID
    occurred_at: datetime
    actor_principal_id: UUID
    delegate_principal_id: UUID | None
    resource_type: str
    resource_id: UUID
    action: str
    decision: bool
    reason_code: str
    policy_hash: str
    grant_revision: int
    trace_id: str
