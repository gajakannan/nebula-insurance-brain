from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from brain_jobs.queue import DocumentJobQueue, LeaseLost, events, jobs, metadata, outbox
from sqlalchemy import create_engine, func, select


@pytest.fixture
def queue(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'jobs.db'}")
    metadata.create_all(engine)
    clock = [100.0]
    queue = DocumentJobQueue(engine, lease_seconds=10, clock=lambda: clock[0])
    yield queue, clock
    engine.dispose()


def enqueue(queue, **overrides):
    args = dict(
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        artifact_id=uuid4(),
        request_key="request",
        payload={"profile": "limits"},
    )
    args.update(overrides)
    return queue.enqueue(**args), args


def test_duplicate_key_is_idempotent_and_conflicting_payload_is_rejected(queue):
    queue, _ = queue
    job_id, args = enqueue(queue)
    assert queue.enqueue(**args) == job_id
    with pytest.raises(ValueError, match="different request"):
        queue.enqueue(**{**args, "payload": {"profile": "different"}})


def test_artifact_scope_cannot_be_reused_by_another_tenant(queue):
    queue, _ = queue
    _, args = enqueue(queue)
    with pytest.raises(PermissionError):
        enqueue(queue, artifact_id=args["artifact_id"])


def test_two_profiles_share_one_conversion_lease(queue):
    queue, _ = queue
    _, args = enqueue(queue)
    queue.enqueue(**{**args, "request_key": "second", "payload": {"profile": "second"}})
    first = queue.claim()
    assert first is not None
    assert queue.claim() is None
    queue.finish(first, "runs/first/manifest.json")
    second = queue.claim()
    assert second is not None and second.job_id != first.job_id


def test_expired_worker_cannot_publish_after_reclaim(queue):
    queue, clock = queue
    enqueue(queue)
    old = queue.claim()
    clock[0] += 11
    new = queue.claim()
    assert new.generation > old.generation
    published = []
    with pytest.raises(LeaseLost):
        queue.publish(old, lambda: published.append(True))
    assert published == []
    queue.finish(new, "runs/recovered/manifest.json")
    with queue.engine.connect() as conn:
        assert len(conn.execute(select(outbox)).all()) == 1


def test_heartbeat_extends_lease_and_cancellation_fences_publication(queue):
    queue, clock = queue
    job_id, args = enqueue(queue)
    lease = queue.claim()
    clock[0] += 9
    queue.heartbeat(lease)
    clock[0] += 2
    assert queue.claim() is None
    with pytest.raises(PermissionError):
        queue.cancel(job_id, uuid4(), args["knowledge_base_id"])
    queue.cancel(job_id, args["tenant_id"], args["knowledge_base_id"])
    with pytest.raises(LeaseLost):
        queue.finish(lease, "should-not-publish")
    with queue.engine.connect() as conn:
        assert conn.execute(select(outbox)).first() is None


def test_retry_budget_and_event_history_survive_queue_reconstruction(queue):
    queue, clock = queue
    enqueue(queue, max_attempts=2)
    lease = queue.claim()
    queue.retry(lease, reason="model_unavailable", delay_seconds=2)
    assert queue.claim() is None
    clock[0] += 3
    reopened = DocumentJobQueue(queue.engine, clock=lambda: clock[0])
    second = reopened.claim()
    assert second.attempt == 2
    reopened.retry(second, reason="model_timeout")
    assert reopened.claim() is None
    with queue.engine.connect() as conn:
        assert conn.scalar(select(jobs.c.state)) == "failed"
        assert len(conn.execute(select(events)).all()) == 5


def test_lease_expiring_during_publication_rolls_back_database_effects(queue):
    queue, clock = queue
    job_id, _ = enqueue(queue)
    lease = queue.claim()

    def publish(connection):
        # A complete external marker may survive; readiness may not.
        connection.execute(jobs.update().where(jobs.c.id == str(job_id)).values(result_ref="ready"))
        clock[0] += 11

    with pytest.raises(LeaseLost):
        queue.publish_transaction(lease, publish)
    with queue.engine.connect() as connection:
        assert connection.scalar(select(jobs.c.result_ref)) is None
        assert "checkpoint_published" not in connection.scalars(select(events.c.event)).all()


def test_failure_reasons_are_recorded_and_terminal_failure_ends_the_job(queue):
    queue, clock = queue
    job_id, _ = enqueue(queue, max_attempts=3)
    lease = queue.claim()
    queue.retry(lease, reason="model_schema_invalid", delay_seconds=0)
    clock[0] += 1
    second = queue.claim()
    queue.fail(second, reason="unsupported_output")
    clock[0] += 10
    assert queue.claim() is None
    with queue.engine.connect() as conn:
        assert conn.scalar(select(jobs.c.state)) == "failed"
        rows = conn.execute(
            select(events.c.event, events.c.reason).order_by(events.c.occurred_at, events.c.event)
        ).all()
    assert ("retry", "model_schema_invalid") in rows
    assert ("failed", "unsupported_output") in rows
    # Non-failure transitions keep a NULL reason.
    assert {reason for event, reason in rows if event in ("queued", "claimed")} == {None}


def test_unknown_failure_reason_is_rejected_without_changing_state(queue):
    queue, _ = queue
    enqueue(queue)
    lease = queue.claim()
    with pytest.raises(ValueError, match="unknown job failure reason"):
        queue.retry(lease, reason="provider said: secret text")  # type: ignore[arg-type]
    with queue.engine.connect() as conn:
        assert conn.scalar(select(jobs.c.state)) == "running"


def test_cancellation_records_the_cancelled_reason(queue):
    queue, _ = queue
    job_id, args = enqueue(queue)
    queue.cancel(job_id, args["tenant_id"], args["knowledge_base_id"])
    with queue.engine.connect() as conn:
        assert (
            conn.execute(select(events.c.reason).where(events.c.event == "cancelled")).scalar_one()
            == "cancelled"
        )


def test_queue_depth_bound_rejects_new_work_but_keeps_duplicates_idempotent(tmp_path):
    from brain_jobs.queue import QueueFull

    engine = create_engine(f"sqlite:///{tmp_path / 'bounded.db'}")
    metadata.create_all(engine)
    clock = [100.0]
    queue = DocumentJobQueue(engine, lease_seconds=10, clock=lambda: clock[0], max_depth=2)
    first, args = enqueue(queue, request_key="one")
    enqueue(
        queue,
        request_key="two",
        tenant_id=args["tenant_id"],
        knowledge_base_id=args["knowledge_base_id"],
        artifact_id=uuid4(),
    )
    assert queue.depth() == 2
    with pytest.raises(QueueFull, match="queue_depth_exceeded"):
        enqueue(queue, request_key="three")
    # A duplicate of admitted work is not new work: same job, even when full.
    assert queue.enqueue(**args) == first
    with queue.engine.connect() as conn:
        assert conn.scalar(select(func.count()).select_from(jobs)) == 2
    # Terminal jobs free capacity; running work still counts.
    lease = queue.claim()
    queue.finish(lease, "runs/x/manifest.json")
    enqueue(queue, request_key="three")
    assert queue.depth() == 2
    engine.dispose()


def test_queue_depth_bound_must_be_positive(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'x.db'}")
    for bad in (0, -1, 1.5):
        with pytest.raises(ValueError, match="positive integer"):
            DocumentJobQueue(engine, max_depth=bad)  # type: ignore[arg-type]
