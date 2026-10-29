"""Test-only model fault proxy (F0005 Step 4); never part of the production worker.

Forwards the guarded worker's requests to the dedicated vLLM server and injects a
fault selected per request number, so a retry can succeed. It is a transport
between one owner and the provider, not a second model client. Request bodies
and responses are never recorded; only timestamps, modes and status codes.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Literal

import httpx

Mode = Literal["pass", "timeout", "http_5xx", "malformed_json", "schema_invalid"]

# `timeout` keeps the provider genuinely busy past the client's deadline (Code
# Review M4): the forwarded request asks for a long fixed generation instead of
# the original prompt, which the timed-out client never receives anyway.
BUSY_TOKENS = 3800
BUSY_PROMPT = "Write the whole numbers from 1 upward, one per line."


@dataclass
class ProxyRecord:
    number: int
    mode: str
    started: float
    finished: float | None = None
    status: int | None = None
    # When the provider itself was working on this request (forwarding only).
    upstream_started: float | None = None
    upstream_finished: float | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "number": self.number,
            "mode": self.mode,
            "status": self.status,
            "started": self.started,
            "finished": self.finished,
            "upstream": [self.upstream_started, self.upstream_finished],
        }


@dataclass
class FaultProxy:
    upstream: str  # e.g. http://127.0.0.1:8000
    hold_seconds: float = 90.0
    schedule: dict[int, Mode] = field(default_factory=dict)
    records: list[ProxyRecord] = field(default_factory=list)
    # Called (outside the proxy lock) after each request is recorded, before forwarding.
    on_record: Callable[[ProxyRecord], None] | None = None

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._count = 0
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.port = 0
        self._client = httpx.Client(trust_env=False, follow_redirects=False, timeout=600)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/v1"

    def start(self) -> FaultProxy:
        proxy = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_args: object) -> None:
                return None

            def _forward(self, method: str) -> None:
                body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
                with proxy._lock:
                    proxy._count += 1
                    number = proxy._count
                    mode = (
                        proxy.schedule.get(number, "pass")
                        if self.path.endswith("/chat/completions")
                        else "pass"
                    )
                    record = ProxyRecord(number, mode, time.monotonic())
                    proxy.records.append(record)
                if proxy.on_record is not None:
                    proxy.on_record(record)
                if mode == "http_5xx":
                    return self._reply(record, 503, b'{"error":{"message":"injected"}}')
                headers = {
                    k.lower(): v
                    for k, v in self.headers.items()
                    if k.lower() in ("authorization", "content-type")
                }
                if mode == "timeout":
                    original = json.loads(body)
                    body = json.dumps(
                        {
                            "model": original["model"],
                            "messages": [{"role": "user", "content": BUSY_PROMPT}],
                            "max_tokens": BUSY_TOKENS,
                            "ignore_eos": True,
                            "temperature": 0,
                        }
                    ).encode()
                    headers["content-type"] = "application/json"
                record.upstream_started = time.monotonic()
                try:
                    upstream = proxy._client.request(
                        method, proxy.upstream + self.path, content=body, headers=headers
                    )
                except httpx.HTTPError:
                    # Provider unreachable (for example mid-restart): close the record.
                    return self._reply(record, 599, b'{"error":{"message":"upstream"}}')
                finally:
                    record.upstream_finished = time.monotonic()
                payload = upstream.content
                if mode == "timeout":
                    # The client gave up while the provider was still generating.
                    time.sleep(proxy.hold_seconds)
                elif mode in ("malformed_json", "schema_invalid") and upstream.status_code == 200:
                    data = json.loads(payload)
                    data["choices"][0]["message"]["content"] = (
                        '{"truncated": '
                        if mode == "malformed_json"
                        else json.dumps({"each_occurrence_limit": 42, "named_insured": 7})
                    )
                    payload = json.dumps(data).encode()
                self._reply(record, upstream.status_code, payload)

            def _reply(self, record: ProxyRecord, status: int, payload: bytes) -> None:
                try:
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    record.finished, record.status = time.monotonic(), status

            def do_POST(self) -> None:
                self._forward("POST")

            def do_GET(self) -> None:
                self._forward("GET")

        self._server = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        self._server.daemon_threads = True
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop_listening(self) -> None:
        """`stopped` mode: the port refuses connections until `start()` again."""
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    def close(self) -> None:
        self.stop_listening()
        self._client.close()

    def max_concurrency(self) -> int:
        """Peak number of model requests the provider was working on at once.

        Measured on the forwarded (upstream) interval, not on the proxy's reply:
        a `timeout` hold keeps the client waiting after the provider finished.
        """
        events = []
        for record in self.records:
            if record.upstream_started is None:
                continue  # injected 5xx: never reached the provider
            end = record.upstream_finished if record.upstream_finished is not None else float("inf")
            events.append((record.upstream_started, 1))
            events.append((end, -1))
        peak = current = 0
        for _time, delta in sorted(events, key=lambda event: (event[0], event[1])):
            current += delta
            peak = max(peak, current)
        return peak

    def busy_at(self, moment: float) -> bool:
        """True when a `timeout` request was inside the provider at `moment`."""
        return any(
            record.mode == "timeout"
            and record.upstream_started is not None
            and record.upstream_started <= moment
            and (record.upstream_finished is None or record.upstream_finished > moment)
            for record in self.records
        )

    def timeline(self) -> list[dict[str, object]]:
        return [record.as_dict() for record in self.records]
