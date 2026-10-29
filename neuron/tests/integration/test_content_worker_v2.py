"""Authorized v2/fallback publication and parser-free cross-profile reuse on PostgreSQL."""

from __future__ import annotations

import json
import runpy
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier, BoundedSemaphore, Event
from unittest.mock import patch
from uuid import UUID

import httpx
import pytest
from brain_content.checkpoints import CheckpointStore
from brain_content.config import LocalObjectStoreConfig
from brain_content.identities import fallback_key
from brain_content.object_store import LocalFilesystemObjectStore
from brain_content.outputs import RunManifestV2
from brain_content.validation import ArtifactIntegrityError, ArtifactKey
from brain_extraction.vllm_graph_client import VllmGraphClient
from brain_ingestion.docling_adapter import DoclingAdapter
from brain_ingestion.document_worker import DocumentWorker
from brain_ingestion.submission import enqueue_document
from brain_interpretation.parsed_content import ParseResult
from brain_jobs.queue import DocumentJobQueue, jobs
from brain_persistence.content_models import content_block
from brain_persistence.models import AuditEventRow, ContentArtifact, SemanticInterpretationRun
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_worker.content_access import SourceContentAccess
from brain_worker.content_publication import AuthorizedContentPublisher
from brain_worker.document_delivery import DocumentJobAuthorization, DocumentResultImporter
from docling.document_converter import DocumentConverter
from docling_core.types.doc import DoclingDocument
from docling_graph.exceptions import PipelineError
from rapidocr import RapidOCR
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

_enqueue_helpers = runpy.run_path(str(Path(__file__).with_name("test_worker_cli_enqueue.py")))
ROOT, POLICY = _enqueue_helpers["ROOT"], _enqueue_helpers["POLICY"]
database, _seed = _enqueue_helpers["database"], _enqueue_helpers["_seed"]


@pytest.fixture(scope="module")
def native(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, ParseResult[DoclingDocument]]:
    folder = tmp_path_factory.mktemp("native-receipts")
    helpers = runpy.run_path(
        str(ROOT / "neuron/packages/brain-ingestion/tests/spikes/test_item_provenance.py")
    )
    path = helpers["create_fixtures"](folder)["native"]
    parsed = DoclingAdapter(capture_provenance=True).parse(path)
    assert parsed.provenance and not parsed.origin_unavailable
    return path, parsed


def components(
    database: tuple[Engine, str], tmp_path: Path
) -> tuple[
    Engine,
    DocumentJobQueue,
    CheckpointStore,
    DocumentJobAuthorization,
    SourceContentAccess,
    AuthorizedContentPublisher,
    Callable[..., UUID],
]:
    engine, _ = database
    tenant, kb, actor = _seed(engine)
    queue = DocumentJobQueue(engine, lease_seconds=30)
    store = CheckpointStore(
        LocalFilesystemObjectStore(LocalObjectStoreConfig("filesystem", tmp_path / "objects", True))
    )
    policy = CasbinAuthorizationAdapter(POLICY / "model.conf", POLICY / "policy.csv")
    authorization = DocumentJobAuthorization(engine, POLICY / "model.conf", POLICY / "policy.csv")
    access = SourceContentAccess(engine, store.verified, policy)
    publisher = AuthorizedContentPublisher(queue, store.verified, policy, objects=store.objects)

    def enqueue(
        path: Path,
        profile: str = "gl-limits-a",
        enabled: bool = True,
        classifications: list[str] | None = None,
    ) -> UUID:
        return enqueue_document(
            engine,
            queue,
            store,
            authorization,
            access,
            source_path=path,
            tenant_id=tenant,
            knowledge_base_id=kb,
            actor_id=actor,
            profile_id=profile,
            classifications=classifications or ["internal"],
            source_acl_ids=[],
            v2_writer_enabled=enabled,
            pipeline="graph-direct",
        )

    return engine, queue, store, authorization, access, publisher, enqueue


def client_factory(calls: list[httpx.Request]) -> Callable[[Event], VllmGraphClient]:
    def factory(cancelled: Event) -> VllmGraphClient:
        def response(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return httpx.Response(
                200,
                json={
                    "id": "recorded-content-worker",
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
                                        "each_occurrence_limit": "NATIVE ALPHA POLICY",
                                        "general_aggregate_limit": None,
                                        "named_insured": "NATIVE ALPHA POLICY",
                                        "policy_period_start": None,
                                        "policy_period_end": None,
                                    }
                                ),
                            },
                        }
                    ],
                    "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
                },
            )

        return VllmGraphClient(
            base_url="http://127.0.0.1:8000/v1",
            api_key="recorded",
            model_id="fixture",
            model_revision="a" * 40,
            token_counter=lambda *_: 200,
            slots=BoundedSemaphore(1),
            cancelled=cancelled,
            http_client=httpx.Client(transport=httpx.MockTransport(response)),
        )

    return factory


@pytest.mark.parametrize("fallback", [False, True])
def test_publication_import_and_second_profile_reuse(
    database: tuple[Engine, str],
    tmp_path: Path,
    native: tuple[Path, ParseResult[DoclingDocument]],
    fallback: bool,
) -> None:
    engine, queue, store, authorization, access, publisher, enqueue = components(database, tmp_path)
    path, parsed = native
    if fallback:
        parsed = replace(parsed, provenance={}, origin_unavailable=("#/texts/0", "#/texts/1"))
    job = enqueue(path)
    lease = queue.claim()
    assert lease is not None and lease.job_id == job
    calls: list[httpx.Request] = []
    conversions: list[Path] = []

    def convert(_path: Path) -> ParseResult[DoclingDocument]:
        conversions.append(_path)
        return parsed

    worker = DocumentWorker(
        queue=queue,
        store=store,
        authorize_for_job=authorization.for_job,
        client_factory=client_factory(calls),
        converter=convert,
        publish_content=publisher.publish_manifest,
        load_accepted=access.resolve,
        v2_writer_enabled=True,
    )
    worker._execute(lease, Event())
    with Session(engine) as session:
        row = session.scalars(select(ContentArtifact)).one()
        assert row.publication_state == "ready"
        assert row.artifact_contract_version == (1 if fallback else 2)
        assert row.writer_fallback_reason == ("ORIGIN_UNAVAILABLE" if fallback else None)
        published = session.scalars(
            select(AuditEventRow).where(AuditEventRow.event_type == "content_artifact_published")
        ).one()
        assert published.payload is not None
        assert published.payload["unattributed_item_count"] == (2 if fallback else 0)
        assert session.scalar(select(func.count()).select_from(content_block)) == (
            0 if fallback else 2
        )
        key = ArtifactKey(row.id, row.tenant_id, row.knowledge_base_id, 1 if fallback else 2)
        if fallback:
            assert key == fallback_key(
                row.document_version_id, row.tenant_id, row.knowledge_base_id
            )
        assert session.scalar(select(jobs.c.state).where(jobs.c.id == str(job))) == "complete"
    importer = DocumentResultImporter(
        engine, store, authorization.for_job, read_artifact=access.read
    )
    assert importer.run_one()
    first = store.load_verified(key)
    # A changed writer flag/installed recipe cannot replace an accepted source.
    with (
        patch(
            "brain_ingestion.submission.physical_recipe", side_effect=AssertionError("new recipe")
        ),
        patch.object(DoclingAdapter, "parse", side_effect=AssertionError("parser forbidden")),
        patch.object(DocumentConverter, "convert", side_effect=AssertionError("convert forbidden")),
        patch.object(
            DocumentConverter, "convert_all", side_effect=AssertionError("convert_all forbidden")
        ),
        patch.object(RapidOCR, "__call__", side_effect=AssertionError("OCR forbidden")),
    ):
        second_job = enqueue(path, profile="gl-limits-b", enabled=False)
        worker.converter = lambda _: (_ for _ in ()).throw(AssertionError("converter forbidden"))
        worker.v2_writer_enabled = False
        assert worker.run_one()
        assert importer.run_one()
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(ContentArtifact)) == 1
        assert session.scalar(select(func.count()).select_from(SemanticInterpretationRun)) == 2
        result_ref = session.scalar(select(jobs.c.result_ref).where(jobs.c.id == str(second_job)))
        assert result_ref is not None
        marker = store.objects.read(result_ref)
        assert json.loads(marker)["artifact_id"] == str(key.artifact_id)
        assert isinstance(RunManifestV2.model_validate_json(marker), RunManifestV2)
    assert len(conversions) == 1
    assert store.load_verified(key).manifest_bytes == first.manifest_bytes
    assert dict(store.load_verified(key).files) == dict(first.files)


def test_concurrent_profiles_share_pending_identity_and_preserve_restrictions(
    database: tuple[Engine, str],
    tmp_path: Path,
    native: tuple[Path, ParseResult[DoclingDocument]],
) -> None:
    engine, _, _, _, _, _, enqueue = components(database, tmp_path)
    path, _ = native
    barrier = Barrier(2)

    def submit(profile: str) -> UUID:
        barrier.wait(timeout=10)
        return enqueue(path, profile=profile)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, ["gl-limits-a", "gl-limits-b"]))
    assert len(set(results)) == 2
    with Session(engine) as session:
        rows = session.execute(select(jobs)).mappings().all()
        assert len({row["artifact_id"] for row in rows}) == 1
        assert len({row["payload"]["version_id"] for row in rows}) == 1
        assert all(row["payload"]["content_contract_version"] == 2 for row in rows)
    assert enqueue(path, enabled=False) == results[0]
    with pytest.raises(PermissionError, match="governed change"):
        enqueue(path, classifications=["restricted"])
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(jobs)) == 2


def test_missing_producer_is_hard_failure_without_ready_or_fallback(
    database: tuple[Engine, str], tmp_path: Path, native: tuple[Path, ParseResult[DoclingDocument]]
) -> None:
    engine, queue, store, authorization, access, publisher, enqueue = components(database, tmp_path)
    path, parsed = native
    bad = {
        # Deliberately violate the producer contract to exercise rejection.
        ref: tuple(replace(origin, producer=None) for origin in origins)  # type: ignore[arg-type]
        for ref, origins in parsed.provenance.items()
    }
    enqueue(path)
    lease = queue.claim()
    assert lease is not None
    worker = DocumentWorker(
        queue=queue,
        store=store,
        authorize_for_job=authorization.for_job,
        client_factory=client_factory([]),
        converter=lambda _: replace(parsed, provenance=bad),
        publish_content=publisher.publish_manifest,
        load_accepted=access.resolve,
        v2_writer_enabled=True,
    )
    with pytest.raises(PipelineError) as failure:
        worker._execute(lease, Event())
    assert isinstance(failure.value.__cause__, (TypeError, ValueError))
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(ContentArtifact)) == 0
    assert not list((tmp_path / "objects").glob("**/manifest.json"))


def test_corrupt_accepted_marker_never_becomes_conversion_miss(
    database: tuple[Engine, str], tmp_path: Path, native: tuple[Path, ParseResult[DoclingDocument]]
) -> None:
    engine, queue, store, authorization, access, publisher, enqueue = components(database, tmp_path)
    path, parsed = native
    enqueue(path)
    worker = DocumentWorker(
        queue=queue,
        store=store,
        authorize_for_job=authorization.for_job,
        client_factory=client_factory([]),
        converter=lambda _: parsed,
        publish_content=publisher.publish_manifest,
        load_accepted=access.resolve,
        v2_writer_enabled=True,
    )
    assert worker.run_one()
    with Session(engine) as session:
        row = session.scalars(select(ContentArtifact)).one()
        key = ArtifactKey(row.id, row.tenant_id, row.knowledge_base_id, 2)
    marker = tmp_path / "objects" / key.prefix / "manifest.json"
    marker.unlink()
    with (
        patch.object(DoclingAdapter, "parse", side_effect=AssertionError("parser forbidden")),
        pytest.raises(ArtifactIntegrityError, match="marker is missing"),
    ):
        enqueue(path, profile="gl-limits-b")
