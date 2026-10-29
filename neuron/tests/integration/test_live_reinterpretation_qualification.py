"""F0005-S0003 live reinterpretation over saved JSON (opt-in: BRAIN_RUN_LIVE_QUALIFICATION=1).

Assembly plan Step 5, kept beside the original F0005 smoke proof
(`test_graph_live_inference.py`, its own opt-in gate) rather than mixed into it.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from threading import BoundedSemaphore
from typing import Any
from uuid import uuid4

import pytest
from brain_extraction import profiles
from brain_extraction.graph_interpretation import GraphInterpretationService
from brain_extraction.profiles import ExtractionProfile
from brain_extraction.vllm_graph_client import VllmGraphClient, cached_model_token_counter
from brain_ingestion import docling_adapter
from brain_ingestion.conversion_process import SupervisedConverter
from brain_jobs.queue import jobs
from brain_persistence.models import Assertion, ReviewItemRow
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent))
from f0005_live_support import (  # type: ignore[import-not-found]  # noqa: E402
    CORPUS,
    corpus_documents,
    fault_proxy,
    qualification,
    require_live,
    upstream,
)


def _forbid(*_args, **_kwargs):  # type: ignore[no-untyped-def]
    raise AssertionError("conversion/OCR entry point called after publication")


def _bundle_digest(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((root / "bundles").rglob("*"))
        if p.is_file()
    }


def test_both_profiles_reinterpret_saved_json_with_zero_conversion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url, settings = require_live()
    proxy = fault_proxy.FaultProxy(upstream(settings)).start()
    port = proxy.port
    proxy.stop_listening()
    documents = corpus_documents()
    try:
        with qualification.isolated(url, "graph-dense", v2_writer_enabled=True) as env:
            with qualification.live_session(env, settings, transport_url=proxy.base_url) as live:
                submitted = [
                    (d["id"], profile, live.submit(CORPUS / d["file"], profile))
                    for d in documents
                    for profile in ("gl-limits-a", "gl-limits-b")
                ]
                # One claim per job: publish every bundle; the stopped provider fails each
                # first model call (queued jobs are claimed before any retry is due).
                for _ in submitted:
                    assert live.worker.run_one()
                published = live.converter.launches
            before = _bundle_digest(env.content_root)
            # Restart with every conversion/OCR entry point instrumented to fail.
            monkeypatch.setattr(SupervisedConverter, "convert", _forbid)
            monkeypatch.setattr(docling_adapter.DoclingAdapter, "parse", _forbid)
            from docling.models.stages.ocr.rapid_ocr_model import RapidOcrModel

            monkeypatch.setattr(RapidOcrModel, "__call__", _forbid)
            proxy.port = port
            proxy.start()
            with qualification.live_session(env, settings, transport_url=proxy.base_url) as live:
                live.drain(timeout=3600)
                assert live.converter.launches == 0
            assert _bundle_digest(env.content_root) == before
            rows = []
            for document_id, profile, job in submitted:
                expected = json.loads((CORPUS / f"expectations/{document_id}.json").read_text())
                case = qualification.score_case(env, job, profile, expected["profiles"][profile])
                rows.append(
                    {
                        "document": document_id,
                        "profile": profile,
                        "state": case["job_state"],
                        "reasons": case["failure_reasons"],
                        "fabricated": sum(f.get("fabricated", 0) for f in case["fields"].values()),
                        "max_reserved_tokens": case.get("max_reserved_tokens"),
                    }
                )
                if case["job_state"] != "complete":
                    continue
                requested = case["requested_configuration"]
                assert requested["extraction_contract"] == "dense"
                assert requested["pipeline"] == "graph-dense"
                assert requested["model_revision"] == settings.revision
                # Budget: every call's reservation fits the serving context.
                assert case["max_reserved_tokens"] <= qualification.CONTEXT_TOKENS
                assert case["over_budget_calls"] == 0
                # Evidence: no resolved selector contradicts the bundle text.
                assert rows[-1]["fabricated"] == 0
                # AC3: ledger and graph retained as run outputs; its native item
                # references resolve in the saved DoclingDocument they came from.
                assert {"provenance.json", "graph.json", "metadata.json"} <= set(case["run_files"])
                assert case["ledger_ref"].endswith("/provenance.json")
                assert case["ledger_item_refs"]
                native = _native_refs(env, job)
                assert set(case["ledger_item_refs"]) <= native, case["ledger_item_refs"]
            identities = {
                (
                    row["profile"],
                    json.dumps(
                        qualification.score_case(
                            env,
                            job,
                            profile,
                            json.loads((CORPUS / f"expectations/{d}.json").read_text())["profiles"][
                                profile
                            ],
                        ).get("pipeline_identity"),
                        sort_keys=True,
                    ),
                )
                for (d, profile, job), row in zip(submitted, rows, strict=True)
            }
            # Distinct profile/schema identities produce distinct run configurations.
            # Failed attempts publish their run identity too, so this is unconditional.
            by_profile: dict[str, set[str]] = {}
            for profile, identity in identities:
                if identity != "null":
                    by_profile.setdefault(profile, set()).add(identity)
            assert set(by_profile) == {"gl-limits-a", "gl-limits-b"}
            assert not (by_profile["gl-limits-a"] & by_profile["gl-limits-b"])
            print(
                json.dumps({"reinterpretation": {"published_conversions": published, "rows": rows}})
            )
            assert published == len(documents)
    finally:
        proxy.close()


def _native_refs(env: Any, job: Any) -> set[str]:
    with env.engine.connect() as conn:
        payload = conn.execute(select(jobs.c.payload).where(jobs.c.id == str(job))).scalar_one()
    bundle = env.parts.store.load_verified(qualification._accepted_key(env, payload["version_id"]))
    native = json.loads(bundle.files[bundle.manifest.docling_document.path])
    return {
        item["self_ref"]
        for kind in ("texts", "tables", "pictures", "groups")
        for item in native.get(kind, [])
    }


class _Insured(BaseModel):
    name: str | None = Field(None, description="Named Insured, verbatim")
    address: str | None = Field(None, description="Mailing address, verbatim")


class _RelationshipProbe(BaseModel):
    """Template variant with an entity relationship that has no downstream mapping."""

    each_occurrence_limit: str | None = Field(None, description="Each Occurrence Limit, verbatim")
    insured: _Insured | None = Field(None, description="The named insured party and its address")


def test_relationship_output_fails_closed_with_no_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    url, settings = require_live()
    probe = ExtractionProfile("gl-relationship-probe", "1", _RelationshipProbe, "test-only")
    monkeypatch.setitem(profiles.PROFILES, probe.profile_id, probe)
    with qualification.isolated(url, "graph-dense", v2_writer_enabled=True) as env:
        with qualification.live_session(env, settings) as live:
            job = live.submit(CORPUS / "documents/gl-q-007.pdf", probe.profile_id)
            live.drain(timeout=900)
        reasons = qualification.score_case(env, job, probe.profile_id, {})["failure_reasons"]
        with Session(env.engine) as session:
            assertions = session.scalar(select(func.count()).select_from(Assertion))
            reviews = session.scalar(select(func.count()).select_from(ReviewItemRow))
            state = session.scalar(select(jobs.c.state).where(jobs.c.id == str(job)))
        print(json.dumps({"relationship_probe": {"state": state, "reasons": reasons}}))
        assert assertions == 0 and reviews == 0
        assert state == "failed"
        # Explicit unsupported output, or an explicit model failure; never partial rows.
        assert reasons[-1] in (
            "unsupported_output",
            "model_malformed_output",
            "model_schema_invalid",
        )


def test_targeted_request_fails_before_any_model_call(tmp_path: Path) -> None:
    _url, settings = require_live()
    requests: list[object] = []
    import httpx

    client = VllmGraphClient(
        base_url=settings.provider_url,
        api_key=settings.api_key,
        model_id=settings.model,
        model_revision=settings.revision,
        token_counter=cached_model_token_counter(settings.model, settings.revision),
        slots=BoundedSemaphore(1),
        http_client=httpx.Client(
            transport=httpx.MockTransport(
                lambda r: requests.append(r) or httpx.Response(500)  # type: ignore[func-returns-value]
            )
        ),
    )
    service = GraphInterpretationService(store=None, authorize=lambda *_: None)  # type: ignore[arg-type]
    with pytest.raises(NotImplementedError):
        service.interpret(
            tenant_id=uuid4(),
            knowledge_base_id=uuid4(),
            artifact_id=uuid4(),
            run_id=uuid4(),
            profile=profiles.load_profile("gl-limits-a"),
            client=client,
            selected_refs=("#/texts/0",),
            pipeline="graph-dense",
        )
    assert requests == [] and client.diagnostics()["calls"] == []
    from brain_ingestion.document_worker import classify

    assert classify(NotImplementedError()) == "unsupported_targeting"
