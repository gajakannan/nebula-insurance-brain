from __future__ import annotations

import hashlib
import json
from pathlib import Path
from threading import BoundedSemaphore, Event
from uuid import uuid4

import httpx
import pytest
from brain_content.checkpoints import ArtifactIntegrityError, CheckpointStore
from brain_content.config import LocalObjectStoreConfig
from brain_content.manifest import ArtifactManifest
from brain_content.object_store import LocalFilesystemObjectStore
from brain_extraction.graph_evidence import ground_value
from brain_extraction.profiles import load_profile
from brain_extraction.vllm_graph_client import VllmGraphClient
from brain_ingestion.bundle_writer import build_bundle
from brain_ingestion.document_worker import DocumentTask, DocumentWorker
from brain_interpretation.parsed_content import ParseResult
from brain_jobs.queue import DocumentJobQueue, jobs, metadata, outbox
from brain_worker.document_delivery import register_document_artifact
from docling_core.types.doc import DocItemLabel, DoclingDocument
from docling_core.types.doc.base import BoundingBox, CoordOrigin, Size
from docling_core.types.doc.document import ProvenanceItem
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine


def document() -> DoclingDocument:
    doc = DoclingDocument(name="synthetic-policy")
    doc.add_page(page_no=1, size=Size(width=600, height=800))
    text = (
        "Each Occurrence Limit: $1,000,000. Currency USD. "
        "Basis per occurrence. Effective 2026-01-01."
    )
    doc.add_text(
        label=DocItemLabel.TEXT,
        text=text,
        prov=ProvenanceItem(
            page_no=1,
            charspan=(0, len(text)),
            bbox=BoundingBox(l=10, t=10, r=500, b=80, coord_origin=CoordOrigin.TOPLEFT),
        ),
    )
    return doc


def bundle(tmp_path: Path) -> tuple[CheckpointStore, ArtifactManifest, dict[str, bytes]]:
    doc = document()
    manifest, files = build_bundle(
        ParseResult(doc, 1, [], 0, "complete", []),
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        document_id=uuid4(),
        version_id=uuid4(),
        artifact_id=uuid4(),
        source_sha256=hashlib.sha256(b"source").hexdigest(),
        configuration_hash="b" * 64,
        source_bytes=b"source",
        source_filename="source.pdf",
    )
    objects = LocalFilesystemObjectStore(
        LocalObjectStoreConfig(provider="filesystem", root=tmp_path / "objects", immutable=True)
    )
    return CheckpointStore(objects), manifest, files


def test_bundle_retry_completes_partial_publication_and_verifies_hashes(tmp_path: Path) -> None:
    store, manifest, files = bundle(tmp_path)
    store.objects.create_exclusive(
        f"bundles/{manifest.artifact_id}/docling-document.json", files["docling-document.json"]
    )
    store.publish(manifest, files)
    assert store.publish(manifest, files) == manifest
    with pytest.raises(PermissionError):
        store.load(manifest.artifact_id, uuid4(), manifest.knowledge_base_id)
    native = tmp_path / "objects" / "bundles" / str(manifest.artifact_id) / "docling-document.json"
    native.write_bytes(b"corrupted")
    with pytest.raises(ArtifactIntegrityError):
        store.load(manifest.artifact_id, manifest.tenant_id, manifest.knowledge_base_id)
    native.unlink()
    with pytest.raises(ArtifactIntegrityError, match="missing a file"):
        store.load(manifest.artifact_id, manifest.tenant_id, manifest.knowledge_base_id)


@pytest.mark.parametrize("value", ["$1,000,000", "USD", "per occurrence", "2026-01-01"])
def test_each_property_gets_its_own_native_selector(value: str) -> None:
    doc = document()
    ledger = {"version": 2, "chunks": {"0": {"doc_item_refs": ["#/texts/0"]}}}
    binding = ground_value(doc, ledger, uuid4(), value)[0]
    assert binding.precision == "span"
    assert doc.texts[0].text[binding.char_start : binding.char_end] == value
    assert binding.block_id == "text-0" and binding.page == 1


def test_node_anchor_does_not_ground_missing_or_ambiguous_properties() -> None:
    doc = document()
    ledger = {
        "version": 2,
        "chunks": {"0": {"doc_item_refs": ["#/texts/0"]}},
        "nodes": {"root": {"anchors": [{"chunk_id": 0, "span": [0, 2]}]}},
    }
    assert ground_value(doc, ledger, uuid4(), "$2,000,000")[0].precision == "unresolved"
    assert ground_value(doc, None, uuid4(), "$1,000,000")[0].precision == "unresolved"
    doc.texts[0].text += " USD"
    assert ground_value(doc, ledger, uuid4(), "USD")[0].precision == "unresolved"


def test_worker_restart_after_model_failure_reuses_bundle_and_emits_one_completion(
    tmp_path: Path,
) -> None:
    store, manifest, files = bundle(tmp_path)
    clock = [100.0]
    engine = create_engine(f"sqlite:///{tmp_path / 'queue.db'}")
    metadata.create_all(engine)
    _engine_schema(engine)
    queue = DocumentJobQueue(engine, clock=lambda: clock[0])
    source = b"source"
    store.objects.create_exclusive(
        f"sources/{manifest.tenant_id}/{manifest.knowledge_base_id}/{manifest.source_sha256}.pdf",
        source,
    )
    task = DocumentTask(
        document_id=manifest.document_id,
        version_id=manifest.version_id,
        source_sha256=manifest.source_sha256,
        recipe_sha256=manifest.execution.configuration_hash,
        profile_id="gl-limits-a",
        profile_version="1",
        schema_sha256=load_profile("gl-limits-a").schema_sha256,
        actor_id=uuid4(),
        correlation_id=uuid4(),
    )
    queue.enqueue(
        tenant_id=manifest.tenant_id,
        knowledge_base_id=manifest.knowledge_base_id,
        artifact_id=manifest.artifact_id,
        request_key="first-profile",
        payload=task.model_dump(mode="json"),
    )
    conversions = []
    fail = [True]
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if fail[0]:
            return httpx.Response(500)
        return httpx.Response(
            200,
            json={
                "id": "test",
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

    def client_factory(cancelled: Event) -> VllmGraphClient:
        return VllmGraphClient(
            base_url="http://127.0.0.1:8000/v1",
            api_key="test",
            model_id="fixture",
            model_revision="a" * 40,
            token_counter=lambda m, s: 200,
            slots=BoundedSemaphore(1),
            cancelled=cancelled,
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        )

    def convert(path: Path) -> ParseResult[DoclingDocument]:
        conversions.append(path)
        return ParseResult(document(), 1, [], 0, "complete", [])

    worker = DocumentWorker(
        queue=queue,
        store=store,
        authorize_for_job=lambda lease: lambda *args: None,
        client_factory=client_factory,
        record_artifact=register_document_artifact,
        converter=convert,
    )
    assert worker.run_one()
    assert len(conversions) == 1
    from brain_persistence.models import ContentArtifact

    with engine.connect() as connection:
        assert connection.scalar(select(ContentArtifact.id)) == manifest.artifact_id
    store.load(manifest.artifact_id, manifest.tenant_id, manifest.knowledge_base_id)
    fail[0] = False
    clock[0] += 6
    restarted = DocumentWorker(
        queue=DocumentJobQueue(engine, clock=lambda: clock[0]),
        store=CheckpointStore(store.objects),
        authorize_for_job=lambda lease: lambda *args: None,
        client_factory=client_factory,
        record_artifact=register_document_artifact,
        converter=lambda path: pytest.fail("reparse"),
    )
    assert restarted.run_one()
    with engine.connect() as conn:
        assert conn.scalar(select(jobs.c.state)) == "complete"
        result_ref = conn.scalar(select(outbox.c.result_ref))
        assert result_ref
        assert len(conn.execute(select(outbox)).all()) == 1
    previous_calls = len(calls)
    assert not restarted.run_one()
    assert len(calls) == previous_calls
    engine.dispose()


def test_run_missing_file_is_corruption_not_a_cache_miss(tmp_path: Path) -> None:
    store, manifest, files = bundle(tmp_path)
    store.publish(manifest, files)
    run_id = uuid4()
    names = {
        name: b"{}" for name in ("result.json", "graph.json", "provenance.json", "metadata.json")
    }
    store.publish_run(
        tenant_id=manifest.tenant_id,
        knowledge_base_id=manifest.knowledge_base_id,
        artifact_id=manifest.artifact_id,
        run_id=run_id,
        files=names,
    )
    store.objects.delete(
        f"runs/{manifest.tenant_id}/{manifest.knowledge_base_id}/{run_id}/result.json"
    )
    with pytest.raises(ArtifactIntegrityError, match="missing a file"):
        store.load_run(
            tenant_id=manifest.tenant_id,
            knowledge_base_id=manifest.knowledge_base_id,
            artifact_id=manifest.artifact_id,
            run_id=run_id,
        )


def test_table_geometry_and_ambiguous_unlocated_cells() -> None:
    from docling_core.types.doc import TableCell, TableData

    doc = document()
    table = doc.add_table(
        data=TableData(
            num_rows=1,
            num_cols=2,
            table_cells=[
                TableCell(
                    text="Limit",
                    start_row_offset_idx=0,
                    end_row_offset_idx=1,
                    start_col_offset_idx=0,
                    end_col_offset_idx=1,
                    column_header=True,
                    bbox=BoundingBox(l=10, t=100, r=100, b=120, coord_origin=CoordOrigin.TOPLEFT),
                ),
                TableCell(
                    text="$7,000",
                    start_row_offset_idx=0,
                    end_row_offset_idx=1,
                    start_col_offset_idx=1,
                    end_col_offset_idx=2,
                    bbox=BoundingBox(l=100, t=100, r=200, b=120, coord_origin=CoordOrigin.TOPLEFT),
                ),
            ],
        ),
        prov=ProvenanceItem(
            page_no=1,
            charspan=(0, 0),
            bbox=BoundingBox(l=10, t=100, r=200, b=120, coord_origin=CoordOrigin.TOPLEFT),
        ),
    )
    ledger = {"version": 2, "chunks": {"0": {"doc_item_refs": [table.self_ref]}}}
    for value in ["Limit", "$7,000"]:
        evidence = ground_value(doc, ledger, uuid4(), value)[0]
        assert evidence.precision == "table_cell" and evidence.block_id == "table-0"
        assert evidence.bbox and evidence.bbox.y0 == 100
    table.data.table_cells.append(
        TableCell(
            text="$7,000",
            start_row_offset_idx=1,
            end_row_offset_idx=2,
            start_col_offset_idx=1,
            end_col_offset_idx=2,
        )
    )
    assert ground_value(doc, ledger, uuid4(), "$7,000")[0].precision == "unresolved"


def _engine_schema(engine: Engine) -> None:
    from brain_persistence import models  # noqa: F401
    from brain_persistence.base import Base

    # PostgreSQL-specific canonical tables are intentionally outside this importer.
    excluded = {"fact_slot", "canonical_fact_version", "canonical_fact_change", "outbox_event"}
    Base.metadata.create_all(
        engine, tables=[t for t in Base.metadata.sorted_tables if t.name not in excluded]
    )


def test_job_authorization_reloads_revocations_and_audits_denials(tmp_path: Path) -> None:
    from datetime import UTC, datetime

    from brain_jobs.queue import JobLease
    from brain_persistence.models import AuditEventRow, MembershipRow, PrincipalRow
    from brain_worker.document_delivery import DocumentJobAuthorization
    from sqlalchemy.orm import Session

    engine = create_engine(f"sqlite:///{tmp_path / 'auth.db'}")
    _engine_schema(engine)
    actor, tenant, kb, artifact = uuid4(), uuid4(), uuid4(), uuid4()
    policy = Path(__file__).resolve().parents[3] / "planning-mds/security/policies"
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
    lease = JobLease(
        uuid4(),
        tenant,
        kb,
        artifact,
        1,
        1,
        {"actor_id": str(actor), "correlation_id": str(uuid4())},
    )
    authorize = DocumentJobAuthorization(
        engine, policy / "model.conf", policy / "policy.csv"
    ).for_job(lease)
    authorize(tenant, kb, artifact, "ingest")
    with Session(engine) as session, session.begin():
        grant = session.scalars(select(MembershipRow)).one()
        grant.revoked_at = datetime.now(UTC)
        grant.grant_revision += 1
    with pytest.raises(PermissionError):
        authorize(tenant, kb, artifact, "interpret")
    with pytest.raises(PermissionError):
        authorize(uuid4(), kb, artifact, "ingest")
    with Session(engine) as session:
        decisions = session.scalars(select(AuditEventRow).order_by(AuditEventRow.occurred_at)).all()
        assert sorted(d.decision for d in decisions) == [False, True]
        assert all(d.actor_principal_id == actor for d in decisions)
    engine.dispose()


def test_outbox_import_is_atomic_idempotent_and_never_commits_facts(tmp_path: Path) -> None:
    from datetime import UTC, datetime

    from brain_contracts.result import (
        CandidateAssertion,
        Counters,
        EvidenceBinding,
        InterpretationResult,
        RunConfiguration,
    )
    from brain_persistence.models import (
        Assertion,
        AssertionEvidence,
        ReviewItemRow,
        SemanticInterpretationRun,
    )
    from brain_worker.document_delivery import DocumentResultImporter
    from sqlalchemy import event, func
    from sqlalchemy.orm import Session

    store, manifest, files = bundle(tmp_path)
    store.publish(manifest, files)
    engine = create_engine(f"sqlite:///{tmp_path / 'import.db'}")
    metadata.create_all(engine)
    _engine_schema(engine)
    queue = DocumentJobQueue(engine, clock=lambda: 100.0)
    queue.enqueue(
        tenant_id=manifest.tenant_id,
        knowledge_base_id=manifest.knowledge_base_id,
        artifact_id=manifest.artifact_id,
        request_key="import",
        payload={
            "document_id": str(manifest.document_id),
            "version_id": str(manifest.version_id),
            "source_sha256": manifest.source_sha256,
            "recipe_sha256": manifest.execution.configuration_hash,
            "profile_id": "gl-limits-a",
            "profile_version": "1",
            "schema_sha256": load_profile("gl-limits-a").schema_sha256,
        },
    )
    lease = queue.claim()
    assert lease
    run_id = uuid4()
    candidate = CandidateAssertion(
        id=uuid4(),
        subject_type="Policy",
        slot_type="limit",
        value={"value": "$7,000"},
        model_confidence=None,
        interpretation_basis="AMBIGUOUS",
        evidence=[EvidenceBinding(artifact_id=manifest.artifact_id, precision="unresolved")],
    )
    result = InterpretationResult(
        run_id=run_id,
        artifact_id=manifest.artifact_id,
        status="partial",
        assertions=[candidate],
        entities=[],
        relationships=[],
        quality_signals={},
        warnings=[],
        failed_chunks=[],
        counters=Counters(model_calls=1),
        created_at=datetime.now(UTC),
        provenance_ledger_ref=None,
        run_configuration=RunConfiguration(
            backend="openai_compatible",
            model_id="fixture",
            model_revision="a" * 40,
            endpoint_hash="b" * 64,
            prompt_hash="c" * 64,
            schema_hash=load_profile("gl-limits-a").schema_sha256,
            context_limit=4096,
            profile_id="gl-limits-a",
            profile_version="1",
        ),
    )
    ref = store.publish_run(
        tenant_id=manifest.tenant_id,
        knowledge_base_id=manifest.knowledge_base_id,
        artifact_id=manifest.artifact_id,
        run_id=run_id,
        files={
            "result.json": result.model_dump_json().encode(),
            "graph.json": b"{}",
            "metadata.json": b"{}",
            "provenance.json": b"{}",
        },
    )
    queue.finish(lease, ref)
    importer = DocumentResultImporter(engine, store, lambda lease: lambda *args: None)
    inject = [True]

    def fail_review(
        connection: object,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: object,
    ) -> None:
        if inject[0] and statement.startswith("INSERT INTO review_item"):
            raise RuntimeError("injected review insertion failure")

    event.listen(engine, "before_cursor_execute", fail_review)
    with pytest.raises(RuntimeError, match="injected"):
        importer.run_one()
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Assertion)) == 0
        assert session.scalar(select(func.count()).select_from(SemanticInterpretationRun)) == 0
        assert session.scalar(select(outbox.c.delivered_at)) is None
    inject[0] = False
    assert importer.run_one()
    assert not importer.run_one()
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Assertion)) == 1
        assert session.scalar(select(func.count()).select_from(AssertionEvidence)) == 1
        item = session.scalars(select(ReviewItemRow)).one()
        assert item.type == "PROVENANCE_CORRECTION" and item.status == "open"
        assert item.evidence and item.evidence["precision"] == "unresolved"
        assert session.scalar(select(outbox.c.delivered_at)) is not None
    event.remove(engine, "before_cursor_execute", fail_review)
    engine.dispose()


def test_process_exit_after_publication_recovers_without_conversion_or_model(
    tmp_path: Path,
) -> None:
    import base64
    import subprocess
    import sys
    from datetime import UTC, datetime
    from uuid import uuid5

    from brain_contracts.result import Counters, InterpretationResult, RunConfiguration

    store, manifest, files = bundle(tmp_path)
    engine = create_engine(f"sqlite:///{tmp_path / 'crash.db'}")
    metadata.create_all(engine)
    queue = DocumentJobQueue(engine, clock=lambda: 100.0, lease_seconds=10)
    task = DocumentTask(
        document_id=manifest.document_id,
        version_id=manifest.version_id,
        source_sha256=manifest.source_sha256,
        recipe_sha256=manifest.execution.configuration_hash,
        profile_id="gl-limits-a",
        profile_version="1",
        schema_sha256=load_profile("gl-limits-a").schema_sha256,
        actor_id=uuid4(),
        correlation_id=uuid4(),
    )
    job_id = queue.enqueue(
        tenant_id=manifest.tenant_id,
        knowledge_base_id=manifest.knowledge_base_id,
        artifact_id=manifest.artifact_id,
        request_key="crash",
        payload=task.model_dump(mode="json"),
    )
    run_id = uuid5(job_id, "attempt:1")
    result = InterpretationResult(
        run_id=run_id,
        artifact_id=manifest.artifact_id,
        status="complete",
        assertions=[],
        entities=[],
        relationships=[],
        quality_signals={},
        warnings=[],
        failed_chunks=[],
        counters=Counters(model_calls=1),
        created_at=datetime.now(UTC),
        provenance_ledger_ref=None,
        run_configuration=RunConfiguration(
            backend="openai_compatible",
            model_id="fixture",
            model_revision="a" * 40,
            endpoint_hash="b" * 64,
            prompt_hash="c" * 64,
            schema_hash=load_profile("gl-limits-a").schema_sha256,
            context_limit=4096,
            profile_id="gl-limits-a",
            profile_version="1",
        ),
    )
    payload = tmp_path / "publication.json"
    payload.write_text(
        json.dumps(
            {
                "manifest": manifest.model_dump(mode="json"),
                "files": {k: base64.b64encode(v).decode() for k, v in files.items()},
                "result": result.model_dump(mode="json"),
            }
        )
    )
    script = """
import base64, json, os, sys
from pathlib import Path
from uuid import UUID
from sqlalchemy import create_engine
from brain_jobs.queue import DocumentJobQueue
from brain_content.config import LocalObjectStoreConfig
from brain_content.object_store import LocalFilesystemObjectStore
from brain_content.checkpoints import CheckpointStore
from brain_content.manifest import ArtifactManifest
root = Path(sys.argv[1])
payload = json.loads((root / "publication.json").read_text())
manifest = ArtifactManifest.model_validate(payload["manifest"])
config = LocalObjectStoreConfig("filesystem", root / "objects", True)
store = CheckpointStore(LocalFilesystemObjectStore(config))
engine = create_engine(f"sqlite:///{root / 'crash.db'}")
queue = DocumentJobQueue(engine, clock=lambda:100.0, lease_seconds=10)
lease = queue.claim()
files = {k:base64.b64decode(v) for k,v in payload["files"].items()}
queue.publish(lease, lambda: store.publish(manifest, files))
queue.publish(lease, lambda: store.publish_run(
    tenant_id=manifest.tenant_id, knowledge_base_id=manifest.knowledge_base_id,
    artifact_id=manifest.artifact_id, run_id=UUID(payload["result"]["run_id"]), files={
    "result.json":json.dumps(payload["result"]).encode(), "metadata.json":b"{}",
    "graph.json":b"{}", "provenance.json":b"{}"}))
os._exit(27)  # no finally, no completion acknowledgement, no clean worker shutdown
"""
    process = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)], timeout=30, capture_output=True
    )
    assert process.returncode == 27, process.stderr.decode()
    restarted = DocumentWorker(
        queue=DocumentJobQueue(engine, clock=lambda: 111.0),
        store=CheckpointStore(store.objects),
        authorize_for_job=lambda lease: lambda *args: None,
        client_factory=lambda _: pytest.fail("model call after published run"),
        record_artifact=lambda _conn, _manifest: None,
        converter=lambda _: pytest.fail("conversion after published artifact"),
    )
    assert restarted.run_one()
    with engine.connect() as conn:
        assert conn.scalar(select(jobs.c.state)) == "complete"
        assert len(conn.execute(select(outbox)).all()) == 1
    engine.dispose()
