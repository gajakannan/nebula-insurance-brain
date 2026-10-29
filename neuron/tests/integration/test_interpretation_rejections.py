"""F0005 Code Review H1: no Graph-dense run completes around a rejected or fallback call.

Real Graph 1.9.1 and the real bounded SDK client over a recorded HTTP transport.
Graph swallows per-call exceptions, and when dense yields no model it falls back
to one direct call. Both used to leave the run `complete` under dense identity.
"""

from __future__ import annotations

import importlib.util
import json
import runpy
import sys
from dataclasses import replace
from pathlib import Path
from threading import BoundedSemaphore, Event
from typing import Any
from uuid import uuid4

import httpx
import pytest
from brain_content.validation import ArtifactKey
from brain_extraction.graph_interpretation import GraphInterpretationService, Pipeline
from brain_extraction.profiles import ExtractionProfile, load_profile
from brain_extraction.vllm_graph_client import InferenceLimits, VllmGraphClient


def _load_probe() -> type:
    # Loaded by path under a fixed module name, like the fault proxy support module.
    name = "f0005_relationship_probe"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            name, Path(__file__).parents[1] / "support/relationship_probe.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name].RelationshipProbe


RelationshipProbe = _load_probe()

LIMITS = InferenceLimits(
    context_tokens=4096,
    output_tokens=512,
    max_calls=16,
    total_reserved_tokens=60_000,
    request_timeout_seconds=5,
    run_timeout_seconds=30,
)


def _published(tmp_path: Path) -> tuple[Any, ArtifactKey]:
    helpers = runpy.run_path(str(Path(__file__).parent / "test_document_delivery.py"))
    store, manifest, files = helpers["bundle"](tmp_path)
    key = ArtifactKey(manifest.artifact_id, manifest.tenant_id, manifest.knowledge_base_id, 1)
    store.verified.publish(key, manifest.model_dump_json().encode(), files)
    return store, key


def _client(
    skeleton: dict[str, Any],
    limits: InferenceLimits = LIMITS,
    answer: dict[str, Any] | None = None,
) -> VllmGraphClient:
    def respond(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        name = body["response_format"]["json_schema"]["name"]
        schema = body["response_format"]["json_schema"]["schema"]
        content = (
            skeleton
            if name == "dense_skeleton"
            else answer
            if answer is not None
            else dict.fromkeys(schema["properties"])
        )
        return httpx.Response(
            200,
            json={
                "id": "recorded",
                "object": "chat.completion",
                "created": 1,
                "model": "fixture",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": json.dumps(content)},
                    }
                ],
                "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
            },
        )

    return VllmGraphClient(
        base_url="http://127.0.0.1:8000/v1",
        api_key="synthetic",
        model_id="fixture",
        model_revision="a" * 40,
        token_counter=lambda *_: 200,
        slots=BoundedSemaphore(1),
        cancelled=Event(),
        limits=limits,
        http_client=httpx.Client(transport=httpx.MockTransport(respond)),
    )


def _interpret(
    tmp_path: Path,
    client: VllmGraphClient,
    pipeline: Pipeline,
    profile: ExtractionProfile | None = None,
) -> Any:
    store, key = _published(tmp_path)
    try:
        return GraphInterpretationService(store, lambda *_: None).interpret(
            tenant_id=key.tenant_id,
            knowledge_base_id=key.knowledge_base_id,
            artifact_id=key.artifact_id,
            artifact_key=key,
            run_id=uuid4(),
            profile=profile or load_profile("gl-limits-a"),
            client=client,
            output_contract_version=2,
            pipeline=pipeline,
        )
    finally:
        client.close()


def test_dense_fallback_to_a_direct_call_is_never_accepted_as_dense(tmp_path: Path) -> None:
    client = _client({"nodes": []})
    result = _interpret(tmp_path, client, "graph-dense")

    phases = [call["phase"] for call in client.diagnostics()["calls"]]
    assert phases == ["dense_skeleton", "direct_extraction"]  # every call "complete"
    assert result.status == "failed"
    assert "dense_contract_fallback" in result.warnings
    assert result.assertions == []


def test_a_budget_rejection_before_dispatch_fails_the_run(tmp_path: Path) -> None:
    client = _client({"nodes": []}, replace(LIMITS, max_calls=1))
    result = _interpret(tmp_path, client, "graph-dense")

    diagnostics = client.diagnostics()
    assert [call["outcome"] for call in diagnostics["calls"]] == ["complete"]
    assert diagnostics["rejections"] == [
        {"phase": "direct_extraction", "outcome": "call_budget_exceeded", "failure_class": "budget"}
    ]
    assert result.status == "failed"
    assert "model_call_failures" in result.warnings


@pytest.mark.parametrize("pipeline", ["graph-direct", "direct-baseline"])
def test_direct_contracts_are_unaffected_by_the_dense_fallback_rule(
    tmp_path: Path, pipeline: Pipeline
) -> None:
    result = _interpret(tmp_path, _client({"nodes": []}), pipeline)

    assert result.status != "failed"
    assert "dense_contract_fallback" not in result.warnings


@pytest.mark.parametrize("pipeline", ["direct-baseline", "graph-direct"])
def test_relationship_output_fails_closed_with_no_assertions(
    tmp_path: Path, pipeline: Pipeline
) -> None:
    # S0003-AC4, deterministically: the model returns the related entity, and the
    # whole result is rejected as unsupported rather than partially imported.
    probe = ExtractionProfile("gl-relationship-probe", "1", RelationshipProbe, "test-only")
    answer = {
        "each_occurrence_limit": "$1,000,000",
        "insured": {"name": "Acme LLC", "address": "1 Main St"},
    }
    result = _interpret(tmp_path, _client({"nodes": []}, answer=answer), pipeline, probe)

    assert result.status == "failed"
    assert "unsupported_output" in result.warnings
    assert result.assertions == [] and result.relationships == [] and result.entities == []


def test_direct_baseline_sends_exactly_the_f0001_prompt(tmp_path: Path) -> None:
    # Code Review L2 / Architect: one prompt source, so the baseline cannot drift.
    from brain_extraction.openai_compatible_adapter import baseline_prompt
    from docling_core.types.doc import DoclingDocument

    sent: list[str] = []
    client = _client({"nodes": []})
    original = client._provider.chat.completions.create

    def capture(**kwargs: Any) -> Any:
        sent.append(kwargs["messages"][0]["content"])
        return original(**kwargs)

    client._provider.chat.completions.create = capture  # type: ignore[method-assign]
    store, key = _published(tmp_path)
    bundle = store.load_verified(key)
    document = DoclingDocument.model_validate_json(
        bundle.files[bundle.manifest.docling_document.path]
    )
    GraphInterpretationService(store, lambda *_: None).interpret(
        tenant_id=key.tenant_id,
        knowledge_base_id=key.knowledge_base_id,
        artifact_id=key.artifact_id,
        artifact_key=key,
        run_id=uuid4(),
        profile=load_profile("gl-limits-a"),
        client=client,
        output_contract_version=2,
        pipeline="direct-baseline",
    )
    client.close()
    assert sent == [baseline_prompt(document)]


def test_legacy_runs_record_their_effective_pipeline_explicitly(tmp_path: Path) -> None:
    # Delta review gap: legacy metadata says graph-direct, sourced from the default.
    store, key = _published(tmp_path)
    client = _client({"nodes": []})
    run_id = uuid4()
    GraphInterpretationService(store, lambda *_: None).interpret(
        tenant_id=key.tenant_id,
        knowledge_base_id=key.knowledge_base_id,
        artifact_id=key.artifact_id,
        artifact_key=key,
        run_id=run_id,
        profile=load_profile("gl-limits-a"),
        client=client,
        output_contract_version=2,
        pipeline=None,
    )
    client.close()
    run = store.load_run_bundle(
        tenant_id=key.tenant_id,
        knowledge_base_id=key.knowledge_base_id,
        artifact_id=key.artifact_id,
        run_id=run_id,
        artifact_key=key,
    )
    metadata = json.loads(run.files["metadata.json"])
    assert metadata["pipeline"] == "graph-direct"
    assert metadata["pipeline_source"] == "legacy_default"
