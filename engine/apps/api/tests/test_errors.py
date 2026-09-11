from __future__ import annotations

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
