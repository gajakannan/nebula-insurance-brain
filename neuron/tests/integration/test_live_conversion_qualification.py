"""F0005-S0001 live conversion qualification (opt-in: BRAIN_RUN_LIVE_QUALIFICATION=1).

Every corpus document converts through the supervised child with real Docling and
OCR, publishes a verified bundle before any model request, and the job records the
model failure (provider stopped) without discarding or reconverting the bundle.
Assertions read the persisted bundle through a fresh composition (restart).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest
from brain_ingestion.conversion_process import ConversionError, SupervisedConverter
from brain_ingestion.worker_cli import compose
from brain_jobs.queue import events, jobs
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent))
from f0005_live_support import (  # type: ignore[import-not-found]
    CORPUS,
    corpus_documents,
    fault_proxy,
    qualification,
    require_live,
    upstream,
)

PINNED_RAPIDOCR = "docling.models.stages.ocr.rapid_ocr_model.RapidOcrModel"


def test_every_corpus_document_publishes_before_the_first_model_request(tmp_path):
    url, settings = require_live()
    proxy = fault_proxy.FaultProxy(upstream(settings)).start()
    proxy.stop_listening()  # provider "stopped": connection refused
    documents = corpus_documents()
    rows = []
    try:
        with qualification.isolated(url, "graph-dense", v2_writer_enabled=True) as env:
            with qualification.live_session(env, settings, transport_url=proxy.base_url) as live:
                submitted = [(d, live.submit(CORPUS / d["file"], "gl-limits-a")) for d in documents]
                for _ in submitted:
                    started = time.monotonic()
                    assert live.worker.run_one()
                    rows.append(time.monotonic() - started)
                assert live.converter.launches == len(documents)
            # Restart: a fresh composition reads only persisted state.
            parts = compose(env.engine, qualification.POLICY)
            with env.engine.connect() as conn:
                reasons = {
                    row.job_id: row.reason
                    for row in conn.execute(
                        select(events.c.job_id, events.c.reason).where(events.c.reason.is_not(None))
                    )
                }
                states = dict(conn.execute(select(jobs.c.id, jobs.c.state)).all())
            report = []
            for document, job in submitted:
                # AC3: model failure recorded; bundle retained and registered ready.
                assert reasons[str(job)] == "model_unavailable"
                assert states[str(job)] == "retry"
                key = qualification._accepted_key(env, _payload(env, job)["version_id"])
                bundle = parts.store.load_verified(key)
                manifest = bundle.manifest
                raw = (CORPUS / document["file"]).read_bytes()
                # AC2: parser/OCR identity, quality and source hash from the bundle.
                assert manifest.source_sha256 == hashlib.sha256(raw).hexdigest()
                quality = manifest.extraction_quality
                execution = manifest.execution
                assert execution.parser_package_version == "docling==2.126.0"
                assert manifest.page_count == document["pages"]
                # AC2: OCR page count and engine, on both contracts (ADR-0073 amendment).
                ocr = quality.ocr
                assert ocr is not None
                assert ocr.page_count == len(ocr.pages)
                assert ocr.engine is not None and ocr.engine.name == PINNED_RAPIDOCR
                assert len(execution.model_artifact_digests) == 3
                # Observed, not estimated: Docling also OCRs bitmap regions (logos,
                # stamps) on pages that have a text layer, so a native page may count.
                assert set(ocr.pages) <= set(range(1, document["pages"] + 1))
                if document["kind"] == "scanned":
                    assert ocr.pages == list(range(1, document["pages"] + 1))
                ocr_pages: set[int] = set()
                producers: set[tuple[str, str, str | None]] = set()
                if key.contract_version == 2:
                    assert len(execution.model_artifact_digests) == 3
                    for line in bundle.files["blocks.jsonl"].splitlines():
                        block = json.loads(line)
                        if block.get("text_origin") == "OCR":
                            producer = block["producer"]
                            producers.add(
                                (producer["engine"], producer["engine_version"], producer["model"])
                            )
                            for region in block["origin_anchor"].get("regions", []):
                                ocr_pages.add(region["page"])
                    if document["kind"] == "scanned":
                        # OCR engine and exact asset identity on every scanned page.
                        assert ocr_pages == set(range(1, document["pages"] + 1))
                        assert {p[0] for p in producers} == {PINNED_RAPIDOCR}
                if document["kind"] == "partial" or document["damaged_pages"]:
                    # AC4: supported content published with failed pages, never complete.
                    assert quality.status == "partial"
                    assert set(document["damaged_pages"]) <= set(quality.failed_pages)
                else:
                    assert quality.status == "complete"
                report.append(
                    {
                        "document": document["id"],
                        "kind": document["kind"],
                        "contract": key.contract_version,
                        "status": quality.status,
                        "pages": manifest.page_count,
                        "failed_pages": list(quality.failed_pages),
                        "ocr_page_count": ocr.page_count,
                        "ocr_pages": list(ocr.pages),
                        "ocr_engine": [ocr.engine.name, ocr.engine.version],
                        "ocr_pages_from_records": sorted(ocr_pages),
                        "ocr_producers": sorted(map(list, producers)),
                        "warnings": len(quality.warnings),
                        "ocr_assets": list(execution.model_artifact_digests),
                    }
                )
            assert max(rows) < 300
            # No model request reached the provider: the proxy refused every connection.
            assert proxy.records == []
            print(json.dumps({"conversion_rows": report, "max_attempt_seconds": max(rows)}))
    finally:
        proxy.close()


def _payload(env, job) -> dict:
    with env.engine.connect() as conn:
        return conn.execute(select(jobs.c.payload).where(jobs.c.id == str(job))).scalar_one()


_STAGE_MISMATCH = textwrap.dedent(
    """
    import sys
    from pathlib import Path
    from docling_graph.pipeline import orchestrator
    from docling_graph.pipeline.stages import ExtractionStage
    from brain_extraction.docling_graph_pipeline import (
        DoclingGraphPipelineAdapter, StageLayoutMismatch)
    from brain_extraction.profiles import load_profile
    original = orchestrator.PipelineOrchestrator.__init__
    def patched(self, *args, **kwargs):
        original(self, *args, **kwargs)
        self.stages.append(ExtractionStage())  # installed layout differs from the pin
    orchestrator.PipelineOrchestrator.__init__ = patched
    published = []
    class NoModel:
        def get_json_response(self, *a, **k): raise AssertionError("model called")
    try:
        DoclingGraphPipelineAdapter(llm_client=NoModel(), model_id="none").run(
            source=Path(sys.argv[1]), template=load_profile("gl-limits-a").template,
            converter=lambda path: (_ for _ in ()).throw(AssertionError("converted")),
            publish=published.append, conversion_only=True)
    except StageLayoutMismatch:
        print("stage_guard_mismatch", len(published))
    """
)


def test_installed_stage_layout_mismatch_raises_before_extraction_and_registers_nothing():
    require_live()
    out = subprocess.run(
        [sys.executable, "-c", _STAGE_MISMATCH, str(CORPUS / "documents/gl-q-001.pdf")],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert out.stdout.strip().splitlines()[-1] == "stage_guard_mismatch 0", out.stderr[-2000:]


def test_production_300_second_deadline_with_a_real_hung_child(tmp_path):
    """Real subprocess at the production setting; decision separate from cleanup."""
    require_live()
    supervisor = SupervisedConverter(
        tmp_path / "staging",
        child_args=("--converter", "fixture", "--fixture-behavior", "helper_ignores_term"),
        load_document=json.loads,
    )
    assert supervisor.deadline_seconds == 300.0
    with pytest.raises(ConversionError) as raised:
        supervisor.convert(
            b"%PDF-1.4\n", attempt_id="production-deadline", capture_provenance=False
        )
    diagnostics = raised.value.diagnostics
    print(json.dumps({"production_deadline": diagnostics}))
    assert raised.value.code == "conversion_timeout"
    assert 300.0 <= diagnostics["decision_seconds"] < 300.5
    assert diagnostics["cleanup_seconds"] <= 5.5
    assert diagnostics["group_confirmed_gone"] is True
    assert list((tmp_path / "staging").iterdir()) == []
