"""Worker/importer process-crash proof with real Graph and recorded model responses.

SQLite runs offline. PostgreSQL uses an isolated schema when BRAIN_TEST_POSTGRES_URL
is set; a configured but unavailable service fails instead of skipping.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from threading import BoundedSemaphore
from uuid import uuid4

import httpx
import pytest
from brain_content.checkpoints import CheckpointStore
from brain_content.config import LocalObjectStoreConfig
from brain_content.object_store import LocalFilesystemObjectStore
from brain_extraction.profiles import load_profile
from brain_extraction.vllm_graph_client import VllmGraphClient
from brain_ingestion.document_worker import DocumentTask, DocumentWorker
from brain_interpretation.parsed_content import ParseResult
from brain_jobs.queue import DocumentJobQueue, jobs, metadata, outbox
from brain_persistence.base import Base
from brain_persistence.models import (
    Assertion,
    AssertionEvidence,
    AuditEventRow,
    ContentArtifact,
    MembershipRow,
    PrincipalRow,
    ReviewItemRow,
    SemanticInterpretationRun,
)
from brain_worker.document_delivery import (
    DocumentJobAuthorization,
    DocumentResultImporter,
    register_document_artifact,
)
from docling_core.types.doc import DocItemLabel, DoclingDocument
from docling_core.types.doc.base import BoundingBox, CoordOrigin, Size
from docling_core.types.doc.document import ProvenanceItem
from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[3]
EXIT_CODE = 29


def database(url, schema):
    options = {"options": f"-csearch_path={schema},public"} if schema else {}
    return create_engine(url, connect_args=options)


@pytest.fixture(params=["sqlite", "postgresql"])
def recovery_database(request, tmp_path):
    schema = None
    admin = None
    if request.param == "postgresql":
        url = os.environ.get("BRAIN_TEST_POSTGRES_URL")
        if not url:
            pytest.skip("set BRAIN_TEST_POSTGRES_URL for PostgreSQL process recovery")
        if not url.startswith("postgresql+psycopg://"):
            pytest.fail("BRAIN_TEST_POSTGRES_URL must use postgresql+psycopg")
        schema = f"delivery_proof_{uuid4().hex}"
        admin = create_engine(url)
        with admin.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    else:
        url = f"sqlite:///{tmp_path / 'recovery.db'}"
    engine = database(url, schema)
    try:
        metadata.create_all(engine)
        # Canonical promotion is outside this importer and has PG-only range types.
        excluded = {"fact_slot", "canonical_fact_version", "canonical_fact_change", "outbox_event"}
        Base.metadata.create_all(
            engine, tables=[t for t in Base.metadata.sorted_tables if t.name not in excluded]
        )
        yield engine, url, schema
    finally:
        engine.dispose()
        if admin:
            with admin.begin() as conn:
                conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin.dispose()


def components(engine, root, crash_at=None):
    def record(name):
        with (root / name).open("a") as log:
            log.write("called\n")

    def crash(stage):
        if crash_at == stage:
            os._exit(EXIT_CODE)

    class CrashingStore(CheckpointStore):
        def publish(self, manifest, files):
            result = super().publish(manifest, files)
            crash("bundle")
            return result

        def publish_run(self, **kwargs):
            result = super().publish_run(**kwargs)
            crash("run")
            return result

    class CrashingQueue(DocumentJobQueue):
        def finish(self, lease, result_ref):
            super().finish(lease, result_ref)
            crash("completion")

    store = CrashingStore(
        LocalFilesystemObjectStore(LocalObjectStoreConfig("filesystem", root / "objects", True))
    )
    queue = CrashingQueue(engine, lease_seconds=2)
    policy = ROOT / "planning-mds/security/policies"
    authorization = DocumentJobAuthorization(engine, policy / "model.conf", policy / "policy.csv")

    def convert(_path):
        # A second physical conversion is an immediate proof failure.
        if (root / "conversions").exists():
            raise AssertionError("reconverted an already-published artifact")
        record("conversions")
        doc = DoclingDocument(name="synthetic-policy")
        doc.add_page(page_no=1, size=Size(width=600, height=800))
        value = "Each Occurrence Limit: $1,000,000."
        doc.add_text(
            label=DocItemLabel.TEXT,
            text=value,
            prov=ProvenanceItem(
                page_no=1,
                charspan=(0, len(value)),
                bbox=BoundingBox(l=10, t=10, r=500, b=80, coord_origin=CoordOrigin.TOPLEFT),
            ),
        )
        return ParseResult(doc, 1, [], 0, "complete", [])

    def response(_request):
        # Likewise, successful published output must never cause another model call.
        if (root / "model_calls").exists():
            raise AssertionError("repeated a completed extraction")
        record("model_calls")
        return httpx.Response(
            200,
            json={
                "id": "recorded-recovery-proof",
                "object": "chat.completion",
                "created": 1,
                "model": "fixture",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(
                                {
                                    "each_occurrence_limit": "$1,000,000",
                                    "general_aggregate_limit": None,
                                }
                            ),
                        },
                    }
                ],
                "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
            },
        )

    def client(cancelled):
        return VllmGraphClient(
            base_url="http://127.0.0.1:8000/v1",
            api_key="recorded-test",
            model_id="fixture",
            model_revision="a" * 40,
            token_counter=lambda _messages, _schema: 200,
            slots=BoundedSemaphore(1),
            cancelled=cancelled,
            http_client=httpx.Client(transport=httpx.MockTransport(response)),
        )

    worker = DocumentWorker(
        queue=queue,
        store=store,
        authorize_for_job=authorization.for_job,
        client_factory=client,
        converter=convert,
        record_artifact=register_document_artifact,
    )
    importer = DocumentResultImporter(engine, store, authorization.for_job)
    return worker, importer, store


@pytest.mark.parametrize("crash_at", ["bundle", "run", "completion", "import", "imported"])
def test_process_recovery_delivers_one_reviewed_assertion(recovery_database, tmp_path, crash_at):
    engine, url, schema = recovery_database
    actor, tenant, kb, artifact = uuid4(), uuid4(), uuid4(), uuid4()
    with Session(engine) as session, session.begin():
        session.add(
            PrincipalRow(
                id=actor, kind="service", issuer="local", subject="worker", status="active"
            )
        )
        session.flush()
        session.add(
            MembershipRow(
                principal_id=actor,
                tenant_id=tenant,
                knowledge_base_id=kb,
                role="ServicePrincipal",
                grant_revision=1,
            )
        )
    source = b"synthetic source; converter returns native fixture"
    task = DocumentTask(
        document_id=uuid4(),
        version_id=uuid4(),
        source_sha256=hashlib.sha256(source).hexdigest(),
        recipe_sha256="b" * 64,
        profile_id="gl-limits-a",
        profile_version="1",
        schema_sha256=load_profile("gl-limits-a").schema_sha256,
        actor_id=actor,
        correlation_id=uuid4(),
    )
    worker, importer, store = components(engine, tmp_path)
    store.objects.create_exclusive(f"sources/{tenant}/{kb}/{task.source_sha256}.pdf", source)
    worker.queue.enqueue(
        tenant_id=tenant,
        knowledge_base_id=kb,
        artifact_id=artifact,
        request_key="crash-proof",
        payload=task.model_dump(mode="json"),
    )
    # The database credential stays in the child environment, not argv or fixture files.
    env = os.environ | {"RECOVERY_PROOF_DATABASE_URL": url}
    child = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), str(tmp_path), schema or "", crash_at],
        env=env,
        timeout=90,
        capture_output=True,
    )
    assert child.returncode == EXIT_CODE, child.stderr.decode()
    store.load(artifact, tenant, kb)
    with engine.connect() as conn:
        if crash_at == "import":
            # Abrupt exit mid-import rolls back all inserted assertions and the ack.
            assert conn.scalar(select(func.count()).select_from(Assertion)) == 0
            assert conn.scalar(select(func.count()).select_from(SemanticInterpretationRun)) == 0
            assert conn.scalar(select(outbox.c.delivered_at)) is None
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        worker.run_one()
        with engine.connect() as conn:
            if conn.scalar(select(jobs.c.state)) == "complete":
                break
        time.sleep(0.1)
    else:
        pytest.fail("worker did not recover within 15 seconds")
    assert importer.run_one() == (crash_at != "imported")
    assert not importer.run_one()
    assert not worker.run_one()
    assert (tmp_path / "conversions").read_text().splitlines() == ["called"]
    assert (tmp_path / "model_calls").read_text().splitlines() == ["called"]
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(ContentArtifact)) == 1
        assert session.scalar(select(func.count()).select_from(SemanticInterpretationRun)) == 1
        assertion = session.scalars(select(Assertion)).one()
        assert assertion.value == {"value": "$1,000,000"}
        assert session.scalar(select(func.count()).select_from(AssertionEvidence)) == 1
        review = session.scalars(select(ReviewItemRow)).one()
        assert review.assertion_id == assertion.id and review.status == "open"
        assert session.scalar(select(func.count()).select_from(outbox)) == 1
        assert session.scalar(select(outbox.c.delivered_at)) is not None
        audits = session.scalars(select(AuditEventRow)).all()
        assert audits and all(row.decision and row.actor_principal_id == actor for row in audits)


def child_main():
    root, schema, crash_at = Path(sys.argv[1]), sys.argv[2] or None, sys.argv[3]
    engine = database(os.environ["RECOVERY_PROOF_DATABASE_URL"], schema)
    worker, importer, _ = components(engine, root, crash_at)
    if crash_at == "import":

        def crash_review(_conn, _cursor, statement, _parameters, _context, _many):
            if statement.startswith("INSERT INTO review_item"):
                os._exit(EXIT_CODE)

        event.listen(engine, "before_cursor_execute", crash_review)
    assert worker.run_one()
    assert importer.run_one()
    if crash_at == "imported":
        os._exit(EXIT_CODE)
    raise AssertionError("crash injection point was not reached")


if __name__ == "__main__":
    child_main()
