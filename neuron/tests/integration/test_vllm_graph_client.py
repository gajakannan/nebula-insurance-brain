"""Real SDK and Graph, deterministic HTTP transport; no live inference claimed."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path
from threading import BoundedSemaphore, Event, Thread
from typing import Any

import httpx
import pytest
from brain_extraction.docling_graph_pipeline import DoclingGraphPipelineAdapter
from brain_extraction.vllm_graph_client import (
    InferenceLimits,
    InferenceRejected,
    VllmGraphClient,
    cached_model_token_counter,
)
from docling_core.types.doc import DocItemLabel, DoclingDocument
from docling_graph.exceptions import PipelineError
from pydantic import BaseModel

SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {"limit": {"type": "string"}},
        "required": ["limit"],
        "additionalProperties": False,
    }
)
LIMITS = InferenceLimits(
    context_tokens=256,
    output_tokens=32,
    max_calls=3,
    total_reserved_tokens=384,
    request_timeout_seconds=1,
    run_timeout_seconds=5,
)


def completion(content: str = '{"limit":"$1,000,000"}', finish: str = "stop") -> dict[str, Any]:
    return {
        "id": "recorded-1",
        "object": "chat.completion",
        "created": 1,
        "model": "fixture",
        "choices": [
            {
                "index": 0,
                "finish_reason": finish,
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": {"prompt_tokens": 40, "completion_tokens": 12, "total_tokens": 52},
    }


@pytest.fixture
def make_client() -> Iterator[Callable[..., VllmGraphClient]]:
    clients = []

    def make(handler: Callable[[httpx.Request], httpx.Response], **kwargs: Any) -> VllmGraphClient:
        client = VllmGraphClient(
            base_url="http://127.0.0.1:8000/v1",
            api_key="private-test-key",
            model_id="fixture",
            model_revision="a" * 40,
            token_counter=kwargs.pop("token_counter", lambda messages, schema: 64),
            slots=kwargs.pop("slots", BoundedSemaphore(1)),
            limits=kwargs.pop("limits", LIMITS),
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
            **kwargs,
        )
        clients.append(client)
        return client

    yield make
    for client in clients:
        client.close()


def test_request_uses_only_configured_endpoint_and_records_safe_diagnostics(
    make_client: Any,
) -> None:
    requests = []
    inputs = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=completion())

    def count(messages: list[dict[str, str]], schema: str) -> int:
        inputs.append((messages, schema))
        return 64

    client = make_client(handler, token_counter=count)
    assert client.get_json_response({"system": "instructions", "user": "private source"}, SCHEMA)
    request = requests[0]
    assert str(request.url) == "http://127.0.0.1:8000/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer private-test-key"
    body = json.loads(request.content)
    assert body["messages"] == inputs[0][0]
    assert body["response_format"]["json_schema"]["schema"] == json.loads(inputs[0][1])
    assert body["max_tokens"] == 32
    assert body["temperature"] == 0
    diagnostics = client.diagnostics()
    assert diagnostics["model_revision"] == "a" * 40
    assert diagnostics["calls"][0]["prompt_tokens"] == 40
    assert diagnostics["calls"][0]["outcome"] == "complete"
    for secret in ("private source", "private-test-key", "$1,000,000", "instructions"):
        assert secret not in json.dumps(diagnostics)


@pytest.mark.parametrize("failure", ["context", "cancelled", "external_ref"])
def test_preflight_rejection_never_sends_http(make_client: Any, failure: str) -> None:
    requests = []
    cancelled = Event()
    if failure == "cancelled":
        cancelled.set()
    client = make_client(
        lambda request: requests.append(request),
        cancelled=cancelled,
        token_counter=lambda messages, schema: 4096 if failure == "context" else 64,
    )
    schema = '{"$ref":"https://untrusted.example/schema"}' if failure == "external_ref" else SCHEMA
    with pytest.raises(InferenceRejected):
        client.get_json_response("source", schema)
    assert requests == []


@pytest.mark.parametrize(
    ("content", "finish", "code"),
    [
        ('{"limit":"ok"}', "length", "incomplete_response"),
        ('{"limit":', "stop", "invalid_response"),
        ('{"limit":42}', "stop", "invalid_response"),
        ('{"limit":"first","limit":"second"}', "stop", "invalid_response"),
        ('{"limit":NaN}', "stop", "invalid_response"),
        ("[]", "stop", "invalid_response_type"),
    ],
)
def test_invalid_or_truncated_results_are_rejected(
    make_client: Any,
    content: str,
    finish: str,
    code: str,
) -> None:
    client = make_client(lambda request: httpx.Response(200, json=completion(content, finish)))
    with pytest.raises(InferenceRejected, match=code):
        client.get_json_response("source", SCHEMA)
    assert client.diagnostics()["calls"][0]["outcome"] == code


@pytest.mark.parametrize("kind", ["timeout", "server"])
def test_transport_failure_is_not_retried_or_exposed(make_client: Any, kind: str) -> None:
    requests = []

    def fail(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if kind == "timeout":
            raise httpx.ReadTimeout("private-test-key private source", request=request)
        return httpx.Response(500, json={"error": {"message": "private source"}})

    client = make_client(fail)
    with pytest.raises(InferenceRejected) as error:
        client.get_json_response("source", SCHEMA)
    assert len(requests) == 1
    assert "private" not in str(error.value)
    assert "private" not in json.dumps(client.diagnostics())


@pytest.mark.parametrize(
    ("limits", "reason"),
    [
        (replace(LIMITS, max_calls=1), "call_budget_exceeded"),
        (replace(LIMITS, total_reserved_tokens=100), "token_budget_exceeded"),
    ],
)
def test_repair_requests_share_the_attempt_budget(
    make_client: Any,
    limits: InferenceLimits,
    reason: str,
) -> None:
    requests = []

    def fail(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=completion('{"wrong":"value"}'))

    client = make_client(fail, limits=limits)
    with pytest.raises(InferenceRejected, match="invalid_response"):
        client.get_json_response("source", SCHEMA)
    with pytest.raises(InferenceRejected, match=reason):
        client.get_json_response("repair source", SCHEMA)
    assert len(requests) == 1
    assert client.diagnostics()["reserved_tokens"] == 96


def test_queued_cancellation_stops_before_http(make_client: Any) -> None:
    slots = BoundedSemaphore(1)
    slots.acquire()
    cancelled = Event()
    requests = []
    errors = []
    client = make_client(lambda request: requests.append(request), slots=slots, cancelled=cancelled)

    def invoke() -> None:
        try:
            client.get_json_response("source", SCHEMA)
        except InferenceRejected as exc:
            errors.append(exc.code)

    thread = Thread(target=invoke)
    thread.start()
    cancelled.set()
    thread.join(timeout=2)
    slots.release()
    assert not thread.is_alive()
    assert errors == ["cancelled"]
    assert requests == []


def test_shared_slot_is_released_after_failure(make_client: Any) -> None:
    slots = BoundedSemaphore(1)
    first = make_client(lambda request: httpx.Response(500), slots=slots)
    second = make_client(lambda request: httpx.Response(200, json=completion()), slots=slots)
    with pytest.raises(InferenceRejected):
        first.get_json_response("source", SCHEMA)
    assert second.get_json_response("source", SCHEMA) == {"limit": "$1,000,000"}


def test_real_graph_uses_the_bounded_sdk_client(make_client: Any, tmp_path: Path) -> None:
    class Limit(BaseModel):
        limit: str

    document = DoclingDocument(name="recorded-transport")
    document.add_text(label=DocItemLabel.TEXT, text="Each occurrence limit: $1,000,000")
    source = tmp_path / "docling-document.json"
    source.write_text(document.model_dump_json())
    client = make_client(lambda request: httpx.Response(200, json=completion()))
    result = DoclingGraphPipelineAdapter(llm_client=client, model_id=client.model).run(
        source=source,
        template=Limit,
    )
    assert result.extracted_models[0].model_dump() == {"limit": "$1,000,000"}
    assert client.diagnostics()["calls"][0]["outcome"] == "complete"


def test_graph_repair_cannot_bypass_http_call_budget(make_client: Any, tmp_path: Path) -> None:
    class Limit(BaseModel):
        limit: str

    document = DoclingDocument(name="failed-transport")
    document.add_text(label=DocItemLabel.TEXT, text="Each occurrence limit: $1,000,000")
    source = tmp_path / "docling-document.json"
    source.write_text(document.model_dump_json())
    requests = []

    def invalid(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=completion('{"limit":42}'))

    client = make_client(invalid, limits=replace(LIMITS, max_calls=1))
    with pytest.raises(PipelineError):
        DoclingGraphPipelineAdapter(llm_client=client, model_id=client.model).run(
            source=source,
            template=Limit,
        )
    assert len(requests) == 1
    assert client.diagnostics()["calls"][0]["outcome"] == "invalid_response"


def test_run_deadline_includes_time_waiting_for_model_slot(make_client: Any) -> None:
    slots = BoundedSemaphore(1)
    slots.acquire()
    requests = []
    client = make_client(
        lambda request: requests.append(request),
        slots=slots,
        limits=replace(LIMITS, run_timeout_seconds=0.02),
    )
    try:
        with pytest.raises(InferenceRejected, match="run_deadline_exceeded"):
            client.get_json_response("source", SCHEMA)
    finally:
        slots.release()
    assert requests == []


def test_redirect_is_not_followed(make_client: Any) -> None:
    requests = []

    def redirect(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(307, headers={"Location": "https://elsewhere.example/v1"})

    client = make_client(redirect)
    with pytest.raises(InferenceRejected, match="provider_error"):
        client.get_json_response("source", SCHEMA)
    assert len(requests) == 1


def test_cached_serving_tokenizer_counts_tokens_instead_of_mapping_keys() -> None:
    try:
        count = cached_model_token_counter(
            "microsoft/Phi-4-mini-instruct", "cfbefacb99257ffa30c83adab238a50856ac3083"
        )
    except OSError:
        pytest.skip("pinned Phi tokenizer assets are not cached")
    short = count([{"role": "user", "content": "short"}], SCHEMA)
    long = count([{"role": "user", "content": "policy limit " * 1000}], SCHEMA)
    assert long > short + 1000


def test_serving_tokenizer_drift_blocks_further_requests(make_client: Any) -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        result = completion()
        result["usage"]["prompt_tokens"] = 120
        return httpx.Response(200, json=result)

    client = make_client(handler)
    for _ in range(2):
        with pytest.raises(InferenceRejected, match="usage_exceeds_reservation"):
            client.get_json_response("source", SCHEMA)
    assert len(requests) == 1
    assert client.diagnostics()["reserved_tokens"] == 132


def test_two_clients_share_one_inflight_slot(make_client: Any) -> None:
    entered = Event()
    release = Event()
    second_entered = Event()
    second_started = Event()
    errors = []
    slots = BoundedSemaphore(1)

    def first_handler(request: httpx.Request) -> httpx.Response:
        entered.set()
        assert release.wait(timeout=2)
        return httpx.Response(200, json=completion())

    def second_handler(request: httpx.Request) -> httpx.Response:
        second_entered.set()
        return httpx.Response(200, json=completion())

    first = make_client(first_handler, slots=slots)
    second = make_client(second_handler, slots=slots)

    def invoke(client: VllmGraphClient, started: Event | None = None) -> None:
        if started is not None:
            started.set()
        try:
            client.get_json_response("source", SCHEMA)
        except Exception as exc:
            errors.append(exc)

    a = Thread(target=invoke, args=(first,))
    b = Thread(target=invoke, args=(second, second_started))
    a.start()
    try:
        assert entered.wait(timeout=1)
        b.start()
        assert second_started.wait(timeout=1)
        assert not second_entered.wait(timeout=0.1)
    finally:
        release.set()
        a.join(timeout=2)
        if b.ident is not None:
            b.join(timeout=2)
    assert not a.is_alive() and not b.is_alive()
    assert second_entered.is_set()
    assert not errors
