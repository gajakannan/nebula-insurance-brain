"""Bounded self-hosted model transport for Docling-Graph's client protocol.

Create one client per interpretation attempt and share its concurrency semaphore
across the worker. Graph owns extraction/repair; every resulting model request
must cross this boundary. Neither prompts nor responses belong in diagnostics.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from threading import BoundedSemaphore, Event, Lock
from typing import Any, Literal, cast
from urllib.parse import urlsplit

import httpx
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError
from openai import APIError, APITimeoutError, OpenAI
from openai.types.chat import ChatCompletionMessageParam

TokenCounter = Callable[[list[dict[str, str]], str], int]


class InferenceRejected(RuntimeError):
    """Stable reason code, deliberately excluding SDK errors and source text."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class InferenceLimits:
    context_tokens: int = 4096
    output_tokens: int = 512
    max_calls: int = 16
    total_reserved_tokens: int = 32768
    request_timeout_seconds: float = 60
    run_timeout_seconds: float = 300

    def __post_init__(self) -> None:
        counts = (
            self.context_tokens,
            self.output_tokens,
            self.max_calls,
            self.total_reserved_tokens,
        )
        if any(type(value) is not int or value <= 0 for value in counts):
            raise ValueError("inference token and call limits must be positive integers")
        if self.output_tokens >= self.context_tokens:
            raise ValueError("output reservation must leave room for input")
        for value in (self.request_timeout_seconds, self.run_timeout_seconds):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("inference timeouts must be finite and positive")


DEFAULT_LIMITS = InferenceLimits()


def cached_model_token_counter(model_id: str, model_revision: str) -> TokenCounter:
    """Count with the pinned serving tokenizer, never a different model's encoding.

    Includes chat framing and a conservative reservation for the response schema.
    The server must use this same tokenizer/revision; live qualification checks it.
    Missing local assets fail instead of downloading during document processing.
    """
    from transformers import AutoTokenizer

    if not re.fullmatch(r"[0-9a-f]{40}", model_revision):
        raise ValueError("model_revision must be an immutable Hugging Face commit SHA")
    tokenizer = AutoTokenizer.from_pretrained(
        model_id, revision=model_revision, local_files_only=True, trust_remote_code=False
    )

    def count(messages: list[dict[str, str]], schema_json: str) -> int:
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True, return_dict=False
        )
        if not isinstance(prompt, list) or any(type(token) is not int for token in prompt):
            raise ValueError("tokenizer must return one flat token sequence")
        schema = tokenizer.encode(schema_json, add_special_tokens=False)
        return len(prompt) + len(schema) + 32

    return count


def _local_schema(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in ("$ref", "$dynamicRef") and (
                not isinstance(child, str) or not child.startswith("#")
            ):
                raise InferenceRejected("external_schema_reference")
            _local_schema(child)
    elif isinstance(value, list):
        for child in value:
            _local_schema(child)


def _json_value(raw: str) -> Any:
    def reject_constant(_value: str) -> None:
        raise ValueError("non-finite JSON number")

    def unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    return json.loads(raw, parse_constant=reject_constant, object_pairs_hook=unique_keys)


class VllmGraphClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model_id: str,
        model_revision: str,
        token_counter: TokenCounter,
        slots: BoundedSemaphore,
        limits: InferenceLimits = DEFAULT_LIMITS,
        cancelled: Event | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        endpoint = urlsplit(base_url)
        if (
            endpoint.scheme not in ("http", "https")
            or not endpoint.hostname
            or endpoint.username
            or endpoint.password
            or endpoint.query
            or endpoint.fragment
        ):
            raise ValueError("base_url must be a configured service URL without credentials")
        if not api_key or not model_id or not re.fullmatch(r"[0-9a-f]{40}", model_revision):
            raise ValueError("model, immutable revision, and inference credential are required")
        self.model = model_id
        self._revision = model_revision
        self._endpoint_hash = hashlib.sha256(base_url.encode()).hexdigest()
        self._limits = limits
        self._counter = token_counter
        self._slots = slots
        self._cancelled = cancelled if cancelled is not None else Event()
        self._lock = Lock()
        self._deadline = time.monotonic() + limits.run_timeout_seconds
        self._calls: list[dict[str, Any]] = []
        self._reserved = 0
        self._fatal_reason: str | None = None
        if http_client is not None and http_client.follow_redirects:
            raise ValueError("inference transport must not follow redirects")
        self._provider = OpenAI(
            base_url=base_url,
            api_key=api_key,
            max_retries=0,
            timeout=limits.request_timeout_seconds,
            http_client=http_client or httpx.Client(follow_redirects=False, trust_env=False),
        )

    def close(self) -> None:
        self._provider.close()

    def _check_active(self) -> float:
        if self._fatal_reason is not None:
            raise InferenceRejected(self._fatal_reason)
        if self._cancelled.is_set():
            raise InferenceRejected("cancelled")
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise InferenceRejected("run_deadline_exceeded")
        return remaining

    def diagnostics(self) -> dict[str, Any]:
        with self._lock:
            return {
                "model_id": self.model,
                "model_revision": self._revision,
                "endpoint_hash": self._endpoint_hash,
                "reserved_tokens": self._reserved,
                "calls": [dict(call) for call in self._calls],
            }

    def get_json_response(
        self,
        prompt: str | Mapping[str, str],
        schema_json: str,
        structured_output: bool = True,
        response_top_level: Literal["object", "array"] = "object",
        response_schema_name: str = "extraction_result",
    ) -> dict[str, Any] | list[Any]:
        self._check_active()
        if not structured_output:
            raise InferenceRejected("structured_output_required")
        if response_top_level not in ("object", "array"):
            raise InferenceRejected("invalid_response_type")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", response_schema_name):
            raise InferenceRejected("invalid_schema_name")
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            if set(prompt) - {"system", "user"} or not prompt:
                raise InferenceRejected("invalid_prompt_roles")
            messages = [
                {"role": role, "content": prompt[role]}
                for role in ("system", "user")
                if role in prompt
            ]
        if any(not isinstance(message["content"], str) for message in messages):
            raise InferenceRejected("invalid_prompt_content")
        try:
            schema = _json_value(schema_json)
            _local_schema(schema)
            Draft202012Validator.check_schema(schema)
        except (ValueError, SchemaError):
            raise InferenceRejected("invalid_schema") from None
        validator = Draft202012Validator(schema)
        tokens = self._counter(messages, schema_json)
        if type(tokens) is not int or tokens < 0:
            raise InferenceRejected("invalid_token_estimate")
        reservation = tokens + self._limits.output_tokens
        if reservation > self._limits.context_tokens:
            raise InferenceRejected("context_limit_exceeded")
        # Poll while queued so cancellation does not wait for a busy model slot.
        while not self._slots.acquire(timeout=min(0.1, self._check_active())):
            pass
        try:
            self._check_active()
            with self._lock:
                if len(self._calls) >= self._limits.max_calls:
                    raise InferenceRejected("call_budget_exceeded")
                if self._reserved + reservation > self._limits.total_reserved_tokens:
                    raise InferenceRejected("token_budget_exceeded")
                self._reserved += reservation
                call: dict[str, Any] = {
                    "prompt_hash": hashlib.sha256(json.dumps(messages).encode()).hexdigest(),
                    "schema_hash": hashlib.sha256(schema_json.encode()).hexdigest(),
                    "estimated_input_tokens": tokens,
                    "reserved_tokens": reservation,
                    "prompt_tokens": None,
                    "completion_tokens": None,
                    "outcome": "started",
                }
                self._calls.append(call)
            try:
                response = self._provider.chat.completions.create(
                    model=self.model,
                    messages=cast(list[ChatCompletionMessageParam], messages),
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": response_schema_name,
                            "schema": schema,
                            "strict": False,
                        },
                    },
                    # Preserve Graph's optional-field schema semantics; independently
                    # validate the response below rather than changing required fields.
                    max_tokens=self._limits.output_tokens,
                    temperature=0,
                    timeout=min(self._limits.request_timeout_seconds, self._check_active()),
                )
                if response.usage is not None:
                    with self._lock:
                        call.update(
                            prompt_tokens=response.usage.prompt_tokens,
                            completion_tokens=response.usage.completion_tokens,
                        )
                        actual = response.usage.prompt_tokens + response.usage.completion_tokens
                        self._reserved += max(0, actual - reservation)
                        if (
                            response.usage.prompt_tokens > tokens
                            or response.usage.completion_tokens > self._limits.output_tokens
                        ):
                            # Detect a changed serving tokenizer or ignored output cap.
                            # The incurred usage is retained; no later call is allowed.
                            self._fatal_reason = "usage_exceeds_reservation"
                self._check_active()
                if len(response.choices) != 1 or response.choices[0].finish_reason != "stop":
                    raise InferenceRejected("incomplete_response")
                message = response.choices[0].message
                if message.refusal or message.content is None:
                    raise InferenceRejected("refused_or_empty_response")
                value = _json_value(message.content)
                if not isinstance(value, dict if response_top_level == "object" else list):
                    raise InferenceRejected("invalid_response_type")
                validator.validate(value)
            except APITimeoutError:
                with self._lock:
                    call["outcome"] = "provider_timeout"
                raise InferenceRejected("provider_timeout") from None
            except APIError:
                with self._lock:
                    call["outcome"] = "provider_error"
                raise InferenceRejected("provider_error") from None
            except (ValueError, ValidationError):
                with self._lock:
                    call["outcome"] = "invalid_response"
                raise InferenceRejected("invalid_response") from None
            except InferenceRejected as exc:
                with self._lock:
                    call["outcome"] = exc.code
                raise
            with self._lock:
                call["outcome"] = "complete"
            return cast(dict[str, Any] | list[Any], value)
        finally:
            self._slots.release()

    def get_json_response_stream(
        self,
        prompt: str | Mapping[str, str],
        schema_json: str,
        structured_output: bool = True,
        response_top_level: Literal["object", "array"] = "object",
        response_schema_name: str = "extraction_result",
    ) -> Iterator[dict[str, Any] | list[Any]]:
        # A partial JSON stream is never exposed as accepted extraction output.
        yield self.get_json_response(
            prompt, schema_json, structured_output, response_top_level, response_schema_name
        )
