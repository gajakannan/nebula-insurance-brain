"""F0011 source-owned OpenAPI, installed resources and existing HTTP carriers."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

import httpx2 as httpx
import pytest
from brain_contracts.schema_runtime import ContractError
from fastapi.routing import APIRoute

from brain_api.app import create_app
from brain_api.contract_guards import guard_commit_response, guard_fact_response
from brain_api.schemas.facts import CommitResponseOut, FactVersionOut


def _path(path: str) -> str:
    # OpenAPI uses camelCase parameter labels; implementation uses snake_case.
    # The path converter on the file resource still denotes one catch-all path.
    return re.sub(r"\{[^}]+\}", "{}", path)


def _actual_routes(app):
    for route in app.routes:
        if isinstance(route, APIRoute):
            yield route
        elif callable(getattr(route, "effective_route_contexts", None)):
            # Current FastAPI composes include_router lazily. Effective contexts
            # include all nested routers and their actual mounted prefixes.
            for context in route.effective_route_contexts():
                if isinstance(context.original_route, APIRoute):
                    yield context


def test_installed_openapi_matches_every_actual_route_including_file_path():
    app = create_app()
    snapshot = app.openapi()
    assert snapshot is app.openapi()
    assert snapshot["openapi"] == "3.1.0"
    routes = list(_actual_routes(app))
    assert routes, "Application routes must be enumerated, including lazy include contexts"
    actual = {
        (method.lower(), _path(route.path))
        for route in routes
        if route.include_in_schema
        for method in route.methods
    }
    declared = {
        (method, _path(path))
        for path, item in snapshot["paths"].items()
        for method in item
        if method in {"get", "post", "put", "patch", "delete", "head", "options"}
    }
    assert actual == declared
    assert ("get", "/content/{}/files/{}") in actual
    for route in routes:
        if not route.include_in_schema:
            continue
        path = next(path for path in snapshot["paths"] if _path(path) == _path(route.path))
        for method in route.methods:
            responses = snapshot["paths"][path][method.lower()]["responses"]
            assert str(route.status_code or 200) in responses


def test_openapi_has_no_external_schema_retrieval():
    root = create_app().openapi()

    def visit(value):
        if isinstance(value, dict):
            if "$ref" in value:
                assert value["$ref"].startswith("#/")
                current = root
                for token in value["$ref"][2:].split("/"):
                    current = current[token.replace("~1", "/").replace("~0", "~")]
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(root)


def _legacy_version():
    now = datetime(2026, 11, 22, tzinfo=UTC)
    return FactVersionOut(
        id=uuid4(),
        fact_slot_id=uuid4(),
        value={"pilot": "legacy"},
        valid_start=now,
        valid_end=None,
        recorded_start=now,
        recorded_end=None,
        change_reason=None,
        evidence_refs=[],
        commit_id=uuid4(),
        canonical_accepted_at=now,
    )


def test_flat_legacy_response_and_commit_shape_are_native_compatible():
    version = _legacy_version()
    payload = version.model_dump(mode="json")
    assert "temporal" not in payload
    assert "valid_start" in payload and "recorded_start" in payload
    assert "valid" not in payload and "recorded" not in payload
    guard_fact_response(payload)
    commit = CommitResponseOut(
        commit_id=uuid4(),
        fact_version_ids=[version.id],
        canonical_accepted_at=version.canonical_accepted_at,
    ).model_dump(mode="json")
    assert "versions" not in commit
    guard_commit_response(commit)


@pytest.mark.parametrize(
    ("field", "invalid"), [("valid_start", "not-a-date"), ("id", "not-a-uuid")]
)
def test_adopted_response_formats_are_required_without_portable_number_tightening(field, invalid):
    payload = _legacy_version().model_dump(mode="json")
    payload["value"] = {"legacy_large_integer": 9007199254740993}
    guard_fact_response(payload)
    payload[field] = invalid
    with pytest.raises(ContractError, match="CONTRACT_INSTANCE_INVALID"):
        guard_fact_response(payload)


def test_adopted_commit_response_datetime_format_is_required():
    payload = CommitResponseOut(
        commit_id=uuid4(),
        fact_version_ids=[uuid4()],
        canonical_accepted_at=datetime(2026, 11, 22, tzinfo=UTC),
    ).model_dump(mode="json")
    payload["canonical_accepted_at"] = "not-a-date"
    with pytest.raises(ContractError, match="CONTRACT_INSTANCE_INVALID"):
        guard_commit_response(payload)


async def test_invariant_failure_is_a_generic_problem_without_payload_or_pointer():
    app = create_app()

    @app.get("/_test/contract-invariant", include_in_schema=False)
    async def invariant():
        raise ContractError("CONTRACT_INSTANCE_INVALID")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        result = await client.get("/_test/contract-invariant")
    assert result.status_code == 500
    assert result.headers["content-type"] == "application/problem+json"
    body = result.json()
    assert body["code"] == "contract_invariant_failed"
    assert body["detail"] is None and body["instance"] is None
    assert "CONTRACT_INSTANCE_INVALID" not in result.text
    assert "schema_pointer" not in result.text
