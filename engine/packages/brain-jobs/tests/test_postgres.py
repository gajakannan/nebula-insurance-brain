"""Real PostgreSQL qualification; each invocation owns only a fresh random schema."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from brain_jobs.queue import DocumentJobQueue, LeaseLost, jobs, leases, metadata, outbox
from sqlalchemy import create_engine, select, text, update


@pytest.fixture
def pg_queue():
    url = os.environ.get("BRAIN_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("set BRAIN_TEST_POSTGRES_URL to a PostgreSQL psycopg test database")
    if not url.startswith("postgresql+psycopg://"):
        pytest.fail("BRAIN_TEST_POSTGRES_URL must use postgresql+psycopg")
    admin = create_engine(url)
    schema = f"graph_proof_{uuid4().hex}"
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    try:
        metadata.create_all(engine)
        yield DocumentJobQueue(engine, lease_seconds=30)
    finally:
        engine.dispose()
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def test_postgres_competing_profiles_claim_one_artifact(pg_queue):
    queue = pg_queue
    tenant, kb, artifact = uuid4(), uuid4(), uuid4()
    for request in ("profile-a", "profile-b"):
        queue.enqueue(
            tenant_id=tenant,
            knowledge_base_id=kb,
            artifact_id=artifact,
            request_key=request,
            payload={},
        )
    barrier = Barrier(2)

    def claim():
        barrier.wait(timeout=10)
        return queue.claim()

    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda _: claim(), range(2)))
    accepted = [lease for lease in claims if lease is not None]
    assert len(accepted) == 1
    first = accepted[0]
    queue.finish(first, "proof/first")
    second = queue.claim()
    assert second is not None and second.job_id != first.job_id
    queue.finish(second, "proof/second")
    with queue.engine.connect() as conn:
        assert len(conn.execute(select(outbox)).all()) == 2


def test_postgres_expired_lease_fences_old_worker(pg_queue):
    queue = pg_queue
    queue.enqueue(
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        artifact_id=uuid4(),
        request_key="expiry",
        payload={},
    )
    old = queue.claim()
    assert old
    with queue.engine.begin() as conn:
        conn.execute(update(jobs).where(jobs.c.id == str(old.job_id)).values(leased_until=0))
        conn.execute(
            update(leases)
            .where(leases.c.artifact_id == str(old.artifact_id))
            .values(leased_until=0)
        )
    current = queue.claim()
    assert current and current.generation > old.generation
    written = []
    with pytest.raises(LeaseLost):
        queue.publish(old, lambda: written.append(True))
    assert not written
    queue.finish(current, "proof/recovered")
