"""Opt-in Graph/vLLM smoke proof, separate from offline recorded-response tests.

This exercises model transport and native JSON reuse, not evidence translation,
durable jobs, or Golden Corpus release qualification.
"""

from __future__ import annotations

import os
from pathlib import Path
from threading import BoundedSemaphore
from unittest.mock import patch

import pytest
from brain_extraction.docling_graph_pipeline import DoclingGraphPipelineAdapter
from brain_extraction.profiles import load_profile
from brain_extraction.vllm_graph_client import VllmGraphClient, cached_model_token_counter
from brain_ingestion.docling_adapter import DoclingAdapter
from docling.document_converter import DocumentConverter

pytestmark = pytest.mark.skipif(
    os.environ.get("BRAIN_RUN_LIVE_GRAPH_PROOF") != "1",
    reason="opt-in live Graph/vLLM proof; see F0005 GETTING-STARTED",
)


def test_live_graph_two_profiles_from_saved_json(tmp_path: Path) -> None:
    model = os.environ.get("BRAIN_INFERENCE_MODEL", "microsoft/Phi-4-mini-instruct")
    revision = os.environ["BRAIN_INFERENCE_MODEL_REVISION"]
    key = os.environ["BRAIN_INFERENCE_API_KEY"]
    endpoint = os.environ.get("BRAIN_INFERENCE_BASE_URL", "http://127.0.0.1:8000/v1")
    count = cached_model_token_counter(model, revision)
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "gl-policy-declarations.pdf"
    parsed = DoclingAdapter().parse(fixture)
    assert parsed.status == "complete"
    saved = tmp_path / "docling-document.json"
    saved.write_text(parsed.document.model_dump_json())
    original = saved.read_bytes()
    slots = BoundedSemaphore(1)
    for profile_id, field, expected in [
        ("gl-limits-a", "each_occurrence_limit", "1,000,000"),
        ("gl-limits-b", "named_insured", "Meridian"),
    ]:
        client = VllmGraphClient(
            base_url=endpoint,
            api_key=key,
            model_id=model,
            model_revision=revision,
            token_counter=count,
            slots=slots,
        )
        try:
            with patch.object(DocumentConverter, "convert", side_effect=AssertionError("reparse")):
                result = DoclingGraphPipelineAdapter(llm_client=client, model_id=model).run(
                    source=saved,
                    template=load_profile(profile_id).template,
                )
            assert result.extracted_models
            assert expected in result.extracted_models[0].model_dump()[field]
            calls = client.diagnostics()["calls"]
            assert calls and any(call["outcome"] == "complete" for call in calls)
            assert all(call["prompt_tokens"] is not None for call in calls)
            assert saved.read_bytes() == original
        finally:
            client.close()
