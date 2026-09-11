from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from brain_domain.audit import AuditEvent


def test_audit_event_construction() -> None:
    event = AuditEvent(
        id=uuid4(),
        occurred_at=datetime.now(UTC),
        actor_principal_id=uuid4(),
        delegate_principal_id=None,
        resource_type="review_task",
        resource_id=uuid4(),
        action="annotate",
        decision=True,
        reason_code="allowed",
        policy_hash="a" * 64,
        grant_revision=1,
        trace_id="trace-1",
    )

    assert event.decision is True
    assert event.delegate_principal_id is None
