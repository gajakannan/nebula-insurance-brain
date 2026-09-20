from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from brain_jobs.queue import DocumentJobQueue, LeaseLost, events, jobs, metadata, outbox
from sqlalchemy import create_engine, select


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
    queue.retry(lease, delay_seconds=2)
    assert queue.claim() is None
    clock[0] += 3
    reopened = DocumentJobQueue(queue.engine, clock=lambda: clock[0])
    second = reopened.claim()
    assert second.attempt == 2
    reopened.retry(second)
    assert reopened.claim() is None
    with queue.engine.connect() as conn:
        assert conn.scalar(select(jobs.c.state)) == "failed"
        assert len(conn.execute(select(events)).all()) == 5
