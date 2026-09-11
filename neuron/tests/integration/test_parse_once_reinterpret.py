"""F0001-S0003 proof harness: parse once, reinterpret twice, evidence resolves.

Requires a live local vLLM endpoint serving `microsoft/Phi-4-mini-instruct`
(`docker/local-inference-runbook.md`) at `BRAIN_INFERENCE_BASE_URL`
(default `http://127.0.0.1:8000/v1`) with `BRAIN_INFERENCE_API_KEY` set. Skipped
automatically when that endpoint is unreachable — this is a runtime-bearing
integration test, not a unit test (see `agents/actions/feature.md` Runtime Preflight).
"""

from __future__ import annotations

import asyncio
import os
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4

import pytest
from brain_content.config import LocalObjectStoreConfig
from brain_content.object_store import LocalFilesystemObjectStore
from brain_content.store import LocalContentArtifactStore
from brain_extraction.docling_graph_adapter import DoclingGraphAdapter
from brain_extraction.profiles import load_profile
from brain_ingestion.bundle_writer import build_bundle
from brain_ingestion.docling_adapter import DoclingAdapter
from brain_interpretation.counters import assert_no_reparse

NEURON_ROOT = Path(__file__).resolve().parents[2]
BASE_URL = os.environ.get("BRAIN_INFERENCE_BASE_URL", "http://127.0.0.1:8000/v1")
API_KEY = os.environ.get("BRAIN_INFERENCE_API_KEY", "")


def _vllm_reachable() -> bool:
    if not API_KEY:
        return False
    try:
        request = urllib.request.Request(
            f"{BASE_URL}/models", headers={"Authorization": f"Bearer {API_KEY}"}
        )
        with urllib.request.urlopen(request, timeout=3):  # noqa: S310
            return True
    except (urllib.error.URLError, TimeoutError):
        return False


pytestmark = pytest.mark.skipif(
    not _vllm_reachable(),
    reason="local vLLM endpoint not reachable; see docker/local-inference-runbook.md",
)


def test_parse_once_reinterpret_twice_evidence_resolves(tmp_path: Path) -> None:
    config = LocalObjectStoreConfig(
        provider="filesystem", root=tmp_path / "content", immutable=True
    )
    store = LocalContentArtifactStore(LocalFilesystemObjectStore(config))
    artifact_id = uuid4()

    # --- Step 1: parse once ---------------------------------------------------
    parse_result = DoclingAdapter().parse(NEURON_ROOT / "fixtures" / "gl-policy-declarations.pdf")
    assert parse_result.status == "complete"
    conversion_calls_from_parse = 1  # DoclingAdapter.parse() called exactly once, above

    manifest, files = build_bundle(
        parse_result,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        document_id=uuid4(),
        version_id=uuid4(),
        artifact_id=artifact_id,
        source_sha256="a" * 64,
        configuration_hash="b" * 64,
    )
    asyncio.run(store.put_bundle(manifest, files))

    # --- Step 2: reinterpret twice, from the persisted artifact only ---------
    adapter = DoclingGraphAdapter(
        base_url=BASE_URL, api_key=API_KEY, model_id="microsoft/Phi-4-mini-instruct"
    )

    result_a = asyncio.run(
        adapter.interpret(store=store, artifact_id=artifact_id, profile=load_profile("gl-limits-a"))
    )
    result_b = asyncio.run(
        adapter.interpret(store=store, artifact_id=artifact_id, profile=load_profile("gl-limits-b"))
    )

    # Interpretation never re-parses: its own counters carry no conversion/OCR calls,
    # and the artifact bytes are untouched (still readable, same hash) after both runs.
    assert_no_reparse(result_a.counters)
    assert_no_reparse(result_b.counters)
    refetched = asyncio.run(store.get_manifest(artifact_id))
    assert refetched.artifact_sha256 == manifest.artifact_sha256
    assert conversion_calls_from_parse == 1  # documents intent: exactly one parse happened, ever

    # --- Step 3: every extracted value carries evidence with declared precision
    assert result_a.status == "complete"
    by_slot_a = {a.slot_type: a for a in result_a.assertions}
    assert "1,000,000" in by_slot_a["each_occurrence_limit"].value["value"]
    each_occurrence_evidence = by_slot_a["each_occurrence_limit"].evidence[0]
    assert each_occurrence_evidence.precision in ("span", "block", "page", "unresolved")
    if each_occurrence_evidence.precision == "span":
        assert each_occurrence_evidence.page == 1
        assert each_occurrence_evidence.block_id is not None
        assert each_occurrence_evidence.char_start is not None
        assert each_occurrence_evidence.char_end is not None
        assert each_occurrence_evidence.bbox is not None

    assert result_b.status == "complete"
    by_slot_b = {a.slot_type: a for a in result_b.assertions}
    assert "Meridian" in (by_slot_b["named_insured"].value["value"] or "")

    # --- Step 4: model calls, prompt/completion tokens recorded per run ------
    assert result_a.counters.model_calls == 1
    assert result_a.counters.prompt_tokens > 0
    assert result_b.counters.model_calls == 1


def test_reinterpretation_over_context_limit_is_rejected_client_side(tmp_path: Path) -> None:
    """A context limit tight enough that even this tiny fixture cannot fit forces the
    client-side rejection path (F0001-S0003 acceptance criterion 4 / edge case)."""
    config = LocalObjectStoreConfig(
        provider="filesystem", root=tmp_path / "content", immutable=True
    )
    store = LocalContentArtifactStore(LocalFilesystemObjectStore(config))
    artifact_id = uuid4()

    parse_result = DoclingAdapter().parse(NEURON_ROOT / "fixtures" / "gl-policy-declarations.pdf")
    manifest, files = build_bundle(
        parse_result,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        document_id=uuid4(),
        version_id=uuid4(),
        artifact_id=artifact_id,
        source_sha256="a" * 64,
        configuration_hash="b" * 64,
    )
    asyncio.run(store.put_bundle(manifest, files))

    tiny_context_adapter = DoclingGraphAdapter(
        base_url=BASE_URL,
        api_key=API_KEY,
        model_id="microsoft/Phi-4-mini-instruct",
        context_limit=32,
        max_output_tokens=16,
    )

    result = asyncio.run(
        tiny_context_adapter.interpret(
            store=store, artifact_id=artifact_id, profile=load_profile("gl-limits-a")
        )
    )

    assert result.status == "failed"
    assert result.counters.model_calls == 0  # rejected before the call, never truncated
    assert any("exceeds budget" in w for w in result.warnings)
