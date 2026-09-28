from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """One append-only `audit_event` row.

    The first twelve fields are the F0001 columns and keep their meaning. F0002 adds
    the v1 decision reference: `decision_id` correlates an authorization decision
    with its terminal outcome and with the mutation it authorized, `event_type`
    distinguishes authorization decisions from review/operational events, and
    `payload` carries the schema `Decision` (or operational event) JSON. Existing
    rows are never rewritten; the new fields are null on them."""

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
    decision_id: UUID | None = None
    event_type: str | None = None
    operation_outcome: str | None = None
    payload: dict[str, object] | None = None
