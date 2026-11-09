"""SEC-03 / F0004 SEC-L2: baseline security headers on every response class."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.testclient import TestClient

from brain_api.app import create_app
from brain_api.errors import BrainError, install_problem_details_handlers
from brain_api.security_headers import SECURITY_HEADERS, SecurityHeadersMiddleware


def _assert_headers(response) -> None:  # type: ignore[no-untyped-def]
    for name, value in SECURITY_HEADERS.items():
        assert response.headers.get_list(name) == [value], name


class _Conflict(BrainError):
    status_code = 409
    code = "conflict"
    title = "Conflict"


def _app() -> FastAPI:
    app = FastAPI()
    install_problem_details_handlers(app)
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/ok")
    async def ok() -> dict[str, str]:
        return {"ok": "yes"}

    @app.get("/brain-error")
    async def brain_error() -> None:
        raise _Conflict("conflict")

    @app.get("/needs-query")
    async def needs_query(required: str) -> dict[str, str]:
        return {"required": required}

    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("secret detail that must not leak")

    @app.get("/own-header")
    async def own_header() -> Response:
        return Response("x", headers={"X-Content-Type-Options": "nosniff"})

    return app


def test_public_health_response_carries_security_headers() -> None:
    _assert_headers(TestClient(create_app()).get("/health"))


@pytest.mark.parametrize(
    ("path", "status"),
    [("/ok", 200), ("/brain-error", 409), ("/needs-query", 422), ("/missing-route", 404)],
)
def test_success_problem_and_framework_errors_carry_security_headers(
    path: str, status: int
) -> None:
    response = TestClient(_app()).get(path)
    assert response.status_code == status
    _assert_headers(response)


def test_unhandled_exception_returns_problem_details_with_headers_and_no_leak() -> None:
    response = TestClient(_app(), raise_server_exceptions=False).get("/crash")
    assert response.status_code == 500
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "internal_error"
    assert "secret detail" not in response.text
    _assert_headers(response)


def test_a_route_header_is_not_duplicated() -> None:
    _assert_headers(TestClient(_app()).get("/own-header"))


def test_protected_route_without_credentials_carries_security_headers() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.get("/content/00000000-0000-0000-0000-000000000000")
    assert response.status_code >= 400
    _assert_headers(response)
