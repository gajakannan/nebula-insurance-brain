"""Baseline response headers for every API response (SEC-03, F0004 SEC-L2).

`X-Content-Type-Options: nosniff` stops browsers from reinterpreting JSON,
problem details or stored content as another type; `Cross-Origin-Resource-Policy:
same-origin` stops other origins from embedding responses. The middleware is pure
ASGI so streamed and error responses are covered too, and it never overrides a
header a route set deliberately. Unhandled exceptions are answered outside user
middleware by Starlette, so the 500 handler in `errors.py` sets these headers
itself.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send

SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "Cross-Origin-Resource-Policy": "same-origin",
}
_ENCODED = [
    (name.lower().encode("latin-1"), value.encode("latin-1"))
    for name, value in SECURITY_HEADERS.items()
]


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                _add_missing(message)
            await send(message)

        await self.app(scope, receive, send_with_headers)


def _add_missing(message: MutableMapping[str, Any]) -> None:
    headers = list(message.get("headers", []))
    present = {name.lower() for name, _ in headers}
    headers.extend((name, value) for name, value in _ENCODED if name not in present)
    message["headers"] = headers
