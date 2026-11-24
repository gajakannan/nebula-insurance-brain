from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from brain_api.errors import BrainError, install_problem_details_handlers


class _NotFoundError(BrainError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    title = "Not Found"


def _build_test_app() -> FastAPI:
    app = FastAPI()
    install_problem_details_handlers(app)

    @app.get("/boom")
    async def boom() -> None:
        raise _NotFoundError("thing does not exist")

    @app.get("/needs-query")
    async def needs_query(required: str) -> dict[str, str]:
        return {"required": required}

    return app


def test_brain_error_is_mapped_to_problem_details() -> None:
    client = TestClient(_build_test_app())

    response = client.get("/boom")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["code"] == "not_found"
    assert body["status"] == 404
    assert body["detail"] == "thing does not exist"
    assert body["traceId"]


def test_validation_error_is_mapped_to_problem_details() -> None:
    client = TestClient(_build_test_app())

    response = client.get("/needs-query")

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["traceId"]


def _build_failing_app() -> FastAPI:
    from brain_contracts.schema_runtime import ContractError

    app = FastAPI()
    install_problem_details_handlers(app)

    @app.get("/contract-invariant")
    async def contract_invariant() -> None:
        raise ContractError("CONTRACT_MODEL_MISMATCH", "fact-version-read-v1", "/properties/value")

    @app.get("/unexpected")
    async def unexpected() -> None:
        raise RuntimeError("row (secret-value) violates constraint")

    return app


def _single_record(caplog: pytest.LogCaptureFixture, message: str) -> logging.LogRecord:
    records = [
        r for r in caplog.records if r.name == "brain_api.errors" and r.getMessage() == message
    ]
    assert len(records) == 1
    return records[0]


def test_contract_invariant_failure_is_logged_with_the_client_trace_id(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = TestClient(_build_failing_app(), raise_server_exceptions=False)

    with caplog.at_level("ERROR", logger="brain_api.errors"):
        response = client.get("/contract-invariant")

    body = response.json()
    assert response.status_code == 500
    assert body["code"] == "contract_invariant_failed"
    assert body["detail"] is None and body["instance"] is None
    record = _single_record(caplog, "contract_invariant_failed")
    assert record.trace_id == body["traceId"]
    assert record.contract_code == "CONTRACT_MODEL_MISMATCH"
    assert record.contract_id == "fact-version-read-v1"
    assert record.schema_pointer == "/properties/value"
    assert record.path == "/contract-invariant"
    assert "schema_pointer" not in response.text and "fact-version-read-v1" not in response.text


def test_unexpected_failure_logs_class_and_trace_id_but_never_exception_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = TestClient(_build_failing_app(), raise_server_exceptions=False)

    with caplog.at_level("ERROR", logger="brain_api.errors"):
        response = client.get("/unexpected")

    body = response.json()
    assert response.status_code == 500
    assert body["code"] == "internal_error"
    record = _single_record(caplog, "internal_error")
    assert record.trace_id == body["traceId"]
    assert record.error_type == "RuntimeError"
    assert record.exc_info is None
    assert "secret-value" not in caplog.text and "secret-value" not in response.text
