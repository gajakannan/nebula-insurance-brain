from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from brain_api.app import create_app


def test_health_returns_200_without_credentials() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200


def test_health_body_reports_pinned_versions_and_git_sha() -> None:
    client = TestClient(create_app())

    body = client.get("/health").json()

    assert body["status"] == "ok"
    assert isinstance(body["git_sha"], str) and body["git_sha"]
    for key in ("fastapi", "sqlalchemy", "docling"):
        assert key in body["versions"]
        assert isinstance(body["versions"][key], str) and body["versions"][key]


def test_health_storage_round_trip_succeeds_against_committed_config() -> None:
    client = TestClient(create_app())

    body = client.get("/health").json()

    assert body["storage"] == "ok"


def test_health_storage_reports_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAIN_LOCAL_CONFIG_PATH", "/does/not/exist.yaml")
    client = TestClient(create_app())

    body = client.get("/health").json()

    assert body["storage"].startswith("error:")


def test_problem_details_handlers_are_registered() -> None:
    from fastapi.exceptions import RequestValidationError

    from brain_api.errors import BrainError

    app = create_app()

    assert RequestValidationError in app.exception_handlers
    assert BrainError in app.exception_handlers
