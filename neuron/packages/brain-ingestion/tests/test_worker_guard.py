"""F0005 Step 0a: host singleton, durable in-flight marker and confirmed quiescence."""

from __future__ import annotations

import contextlib
import json
import os
import signal
import socket
import stat
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from threading import BoundedSemaphore

import httpx
import pytest
from brain_extraction.vllm_graph_client import InferenceRejected, VllmGraphClient
from brain_ingestion import provider_supervisor
from brain_ingestion import worker_guard as wg
from brain_ingestion.worker_guard import (
    GuardError,
    HostInferenceGuard,
    ProviderRecord,
    canonical_endpoint,
    control_directory,
    group_members,
    load_provider,
    record_provider,
)

LOCAL = "http://127.0.0.1:8000/v1"


def guard_in(tmp_path: Path, url: str = LOCAL) -> HostInferenceGuard:
    directory = tmp_path / "guard"
    return HostInferenceGuard(url, directory=directory)


def test_aliases_and_paths_resolve_to_one_canonical_identity():
    resolve = {"localhost": {"127.0.0.1"}, "127.0.0.1": {"127.0.0.1"}}.get
    a = canonical_endpoint("http://localhost:8000/v1/", resolve=resolve)
    b = canonical_endpoint("http://127.0.0.1:8000//v1", resolve=resolve)
    assert a == b and a.canonical == "http://127.0.0.1:8000/v1"
    assert a.key == b.key and "secret" not in a.canonical
    # Default port is the effective port, not a different slot.
    assert canonical_endpoint("http://127.0.0.1/v1", resolve=resolve).port == 80


@pytest.mark.parametrize(
    ("url", "addresses", "code"),
    [
        ("http://localhost:8000/v1", {"127.0.0.1", "::1"}, "inference_endpoint_ambiguous"),
        ("http://inference.example:8000/v1", {"10.0.0.5"}, "inference_endpoint_not_allowlisted"),
        ("http://user:pw@127.0.0.1:8000/v1", {"127.0.0.1"}, "inference_endpoint_invalid"),
        ("ftp://127.0.0.1/v1", {"127.0.0.1"}, "inference_endpoint_invalid"),
        ("http://127.0.0.1:8000/v1/../admin", {"127.0.0.1"}, "inference_endpoint_invalid"),
    ],
)
def test_ambiguous_remote_or_malformed_endpoints_are_refused(url, addresses, code):
    with pytest.raises(GuardError, match=code):
        canonical_endpoint(url, resolve=lambda _host: addresses)


def test_control_directory_is_fixed_by_uid_and_ignores_environment(monkeypatch):
    monkeypatch.setenv("TMPDIR", "/somewhere/else")
    assert control_directory() == Path(f"/tmp/nebula-brain-inference-{os.getuid()}")


def test_unsafe_control_directories_are_rejected(tmp_path):
    loose = tmp_path / "loose"
    loose.mkdir(mode=0o755)
    loose.chmod(0o755)
    with pytest.raises(GuardError, match="directory_invalid"):
        HostInferenceGuard(LOCAL, directory=loose).acquire()
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    (tmp_path / "link").symlink_to(target)
    with pytest.raises(GuardError, match="directory_invalid"):
        HostInferenceGuard(LOCAL, directory=tmp_path / "link").acquire()


_HOLDER = textwrap.dedent(
    """
    import sys, time
    from pathlib import Path
    from brain_ingestion.worker_guard import HostInferenceGuard, GuardError
    directory = None if sys.argv[1] == "host" else Path(sys.argv[1])
    guard = HostInferenceGuard(sys.argv[2], directory=directory)
    try:
        guard.acquire()
        guard.require_quiescent()
    except GuardError as exc:
        print(exc.code, flush=True)
        sys.exit(2)
    print("acquired", flush=True)
    if sys.argv[3] == "inflight":
        with guard.inflight("request-1"):
            print("dispatched", flush=True)
            time.sleep(600)
    time.sleep(float(sys.argv[3]) if sys.argv[3] != "inflight" else 0)
    """
)


def holder(directory: str, url: str, mode: str, cwd: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-c", _HOLDER, directory, url, mode],
        cwd=cwd,
        stdout=subprocess.PIPE,
        text=True,
    )


def test_second_process_on_real_host_directory_is_refused_before_work(tmp_path):
    """Two independent processes, different working/content directories, the actual
    fixed host directory: the loser exits inference_guard_busy."""
    url = "http://127.0.0.1:65431/v1"  # a dedicated test key; never the live provider's
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    first = holder("host", url, "30", tmp_path / "a")
    try:
        assert first.stdout.readline().strip() == "acquired"
        second = holder("host", url, "0", tmp_path / "b")
        assert second.stdout.readline().strip() == "inference_guard_busy"
        assert second.wait(10) == 2
    finally:
        first.kill()
        first.wait()
    released = holder("host", url, "0", tmp_path / "b")
    assert released.stdout.readline().strip() == "acquired"
    released.wait(10)


def test_lock_descriptor_is_not_inherited_and_child_exit_cannot_release(tmp_path):
    guard = guard_in(tmp_path)
    guard.acquire()
    try:
        assert not os.get_inheritable(guard._fd)
        child = subprocess.Popen(
            [sys.executable, "-c", f"import os; os.fstat({guard._fd})"],
            close_fds=False,
            stderr=subprocess.DEVNULL,
        )
        assert child.wait(10) != 0  # descriptor absent in the child
        competitor = holder(str(guard.directory), LOCAL, "0", tmp_path)
        assert competitor.stdout.readline().strip() == "inference_guard_busy"
        competitor.wait(10)
    finally:
        guard.release()


def test_confirmed_request_clears_marker_and_uncertain_request_blocks_replacement(tmp_path):
    guard = guard_in(tmp_path)
    guard.acquire()
    with guard.inflight("one") as handle:
        assert json.loads(guard.marker_path.read_text())["correlation_sha256"] != "one"
        handle.confirm()
    assert not guard.marker_path.exists() and not guard.uncertain
    with guard.inflight("two"):
        pass  # timeout/disconnect: never confirmed
    assert guard.uncertain and guard.marker_path.exists()
    with (
        pytest.raises(GuardError, match="provider_quiescence_required"),
        guard.inflight("three"),
    ):
        pass
    guard.release()
    replacement = guard_in(tmp_path)
    replacement.acquire()
    with pytest.raises(GuardError, match="provider_quiescence_required"):
        replacement.require_quiescent()
    replacement.release()


def test_sigkill_during_held_request_lets_lock_go_but_marker_blocks_claims(tmp_path):
    directory = tmp_path / "guard"
    worker_a = holder(str(directory), LOCAL, "inflight", tmp_path)
    assert worker_a.stdout.readline().strip() == "acquired"
    assert worker_a.stdout.readline().strip() == "dispatched"
    worker_a.send_signal(signal.SIGKILL)
    worker_a.wait()
    worker_b = holder(str(directory), LOCAL, "0", tmp_path)
    # B acquires the OS-released lock but must not claim: the marker is dirty.
    assert worker_b.stdout.readline().strip() == "provider_quiescence_required"
    assert worker_b.wait(10) == 2


def _client(guard: HostInferenceGuard, transport: httpx.MockTransport) -> VllmGraphClient:
    return VllmGraphClient(
        base_url=LOCAL,
        api_key="test",
        model_id="fixture",
        model_revision="a" * 40,
        token_counter=lambda *_: 10,
        slots=BoundedSemaphore(1),
        http_client=httpx.Client(transport=transport),
        dispatch_guard=guard.inflight,
    )


def test_marker_fsync_failure_sends_nothing(tmp_path, monkeypatch):
    guard = guard_in(tmp_path)
    guard.acquire()
    requests: list[httpx.Request] = []
    transport = httpx.MockTransport(lambda request: requests.append(request) or httpx.Response(500))

    def failing_fsync(_path: Path) -> None:
        raise OSError("fsync failed")

    monkeypatch.setattr(wg, "_fsync_directory", failing_fsync)
    client = _client(guard, transport)
    with pytest.raises(InferenceRejected, match="inflight_marker_not_durable"):
        client.get_json_response("prompt", '{"type": "object"}')
    assert requests == []
    assert client.diagnostics()["calls"][0]["failure_class"] == "unavailable"
    client.close()
    guard.release()


@pytest.mark.parametrize(
    ("response", "uncertain"),
    [
        (lambda request: httpx.Response(503, json={"error": "busy"}), False),
        (
            lambda request: (_ for _ in ()).throw(httpx.ConnectError("refused", request=request)),
            False,
        ),
        (lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("slow", request=request)), True),
        (
            lambda request: (_ for _ in ()).throw(
                httpx.RemoteProtocolError("cut", request=request)
            ),
            True,
        ),
    ],
)
def test_only_terminal_or_refused_outcomes_clear_the_marker(tmp_path, response, uncertain):
    guard = guard_in(tmp_path)
    guard.acquire()
    client = _client(guard, httpx.MockTransport(response))
    with pytest.raises(InferenceRejected):
        client.get_json_response("prompt", '{"type": "object"}')
    assert guard.uncertain is uncertain
    assert guard.marker_path.exists() is uncertain
    client.close()
    guard.release()


def test_receipt_must_confirm_exit_before_clearing(tmp_path):
    guard = guard_in(tmp_path)
    guard.acquire()
    with guard.inflight("x"):
        pass
    with pytest.raises(GuardError, match="receipt_incomplete"):
        guard.clear_after_quiescence(
            {"old_provider": {}, "new_provider": {}, "pins": {}, "confirmed_exit": False}
        )
    assert guard.marker_path.exists()
    guard.release()


_FAKE_PROVIDER = textwrap.dedent(
    """
    import json, os, sys, subprocess
    from http.server import BaseHTTPRequestHandler, HTTPServer
    # An extra group member stands in for vLLM's EngineCore worker.
    subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
    port = int(sys.argv[sys.argv.index("--port") + 1])
    model = sys.argv[sys.argv.index("serve") + 1]
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            if self.path == "/health":
                body = b"{}"
            elif self.path == "/v1/models" and (
                self.headers.get("Authorization") == "Bearer " + os.environ["FAKE_KEY"]
                or os.environ.get("FAKE_UNAUTHENTICATED") == "1"
            ):
                body = json.dumps({"data": [{"id": model}]}).encode()
            else:
                self.send_response(401); self.end_headers(); return
            self.send_response(200); self.end_headers(); self.wfile.write(body)
    HTTPServer(("127.0.0.1", port), H).serve_forever()
    """
)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _fake_vllm(tmp_path: Path, port: int) -> list[str]:
    # Named `vllm` and bound like the real server: only such a record is accepted.
    script = tmp_path / "bin" / "vllm"
    script.parent.mkdir(exist_ok=True)
    script.write_text(_FAKE_PROVIDER)
    # Like a virtual environment: the interpreter sits beside its `vllm` script.
    python = script.parent / "python"
    if not python.exists():
        python.symlink_to(sys.executable)
    return [
        str(python),
        str(script),
        "serve",
        "fake/model",
        "--revision",
        "r" * 40,
        "--tokenizer-revision",
        "r" * 40,
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--max-model-len",
        "4096",
    ]


def test_quiescence_stops_whole_group_restarts_pinned_command_then_clears(tmp_path, monkeypatch):
    port = _free_port()
    url = f"http://127.0.0.1:{port}/v1"
    argv = _fake_vllm(tmp_path, port)
    monkeypatch.setenv("FAKE_KEY", "k")
    old = subprocess.Popen(argv, start_new_session=True, cwd=tmp_path)
    try:
        provider_supervisor.wait_ready(url, api_key="k", model="fake/model", timeout=20)
        guard = HostInferenceGuard(url, directory=tmp_path / "guard")
        record_provider(guard, ProviderRecord.capture(old.pid, guard.identity))
        assert len(group_members(old.pid)) == 2
        guard.acquire()
        with guard.inflight("held-when-worker-died"):
            pass
        guard.release()
        started = time.monotonic()
        receipt_path = provider_supervisor.quiesce_and_restart(
            url,
            api_key="k",
            stop_timeout=5,
            ready_timeout=30,
            guard=HostInferenceGuard(url, directory=tmp_path / "guard"),
        )
        elapsed = time.monotonic() - started
        old.wait(5)
        assert group_members(old.pid) == []
        receipt = json.loads(receipt_path.read_text())
        assert receipt["confirmed_exit"] is True
        assert receipt["old_provider"]["pid"] == old.pid
        assert receipt["new_provider"]["pid"] != old.pid
        assert receipt["pins"]["revision"] == "r" * 40
        assert "k" not in json.dumps({k: v for k, v in receipt.items() if k != "marker"}).split('"')
        assert not guard.marker_path.exists()
        new_pid = receipt["new_provider"]["pid"]
        assert elapsed < 30
        fresh = HostInferenceGuard(url, directory=tmp_path / "guard")
        fresh.acquire()
        fresh.require_quiescent()
        fresh.release()
    finally:
        for pid in (old.pid, locals().get("new_pid")):
            if pid:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(pid, signal.SIGKILL)


def test_quiescence_fails_closed_when_pid_was_reused(tmp_path):
    guard = HostInferenceGuard(LOCAL, directory=tmp_path / "guard")
    other = subprocess.Popen(["sleep", "60"], start_new_session=True)
    try:
        # A well-formed record whose PID now names a different process.
        argv = _fake_vllm(tmp_path, guard.identity.port)
        record = ProviderRecord(other.pid, other.pid, 1, argv, "/", guard.identity.canonical)
        record_provider(guard, record)
        guard.acquire()
        with guard.inflight("x"):
            pass
        with pytest.raises(GuardError, match="provider_ownership_unconfirmed"):
            provider_supervisor.quiesce_and_restart(LOCAL, api_key="k", guard=guard)
        assert other.poll() is None  # nothing was signalled
        assert guard.marker_path.exists()  # never cleared on a guess
        guard.release()
    finally:
        other.kill()
        other.wait()


@pytest.mark.parametrize(
    "tamper",
    [
        "other_program",
        "vllm_named_argument",
        "foreign_interpreter",
        "api_key_in_argv",
        "other_port",
        "not_group_leader",
        "other_host",
    ],
)
def test_tampered_or_mistaken_provider_records_are_refused(tmp_path, tamper):
    guard = HostInferenceGuard(LOCAL, directory=tmp_path / "guard")
    argv = _fake_vllm(tmp_path, guard.identity.port)
    pid = pgid = 4242
    if tamper == "other_program":
        argv[1] = "/usr/bin/curl"
    elif tamper == "vllm_named_argument":
        argv[0], argv[1] = "/tmp/evil", "vllm"
    elif tamper == "foreign_interpreter":
        argv[0] = "/bin/sh"
    elif tamper == "api_key_in_argv":
        argv += ["--api-key", "secret"]
    elif tamper == "other_port":
        argv[argv.index("--port") + 1] = "9999"
    elif tamper == "other_host":
        argv[argv.index("--host") + 1] = "0.0.0.0"
    else:
        pgid = 1
    record = ProviderRecord(pid, pgid, 1, argv, "/", guard.identity.canonical)
    with pytest.raises(GuardError, match="provider_record_invalid"):
        record_provider(guard, record)
    # A record written behind the guard's back is refused at use.
    guard._prepare_directory()
    guard.provider_path.write_bytes(record.to_json())
    with pytest.raises(GuardError, match="provider_record_invalid"):
        load_provider(guard)


def test_a_restart_that_accepts_unauthenticated_requests_is_never_ready(tmp_path, monkeypatch):
    port = _free_port()
    monkeypatch.setenv("FAKE_KEY", "k")
    monkeypatch.setenv("FAKE_UNAUTHENTICATED", "1")
    server = subprocess.Popen(_fake_vllm(tmp_path, port), start_new_session=True)
    try:
        with pytest.raises(GuardError, match="provider_restart_unauthenticated"):
            provider_supervisor.wait_ready(
                f"http://127.0.0.1:{port}/v1", api_key="k", model="fake/model", timeout=20
            )
    finally:
        os.killpg(server.pid, signal.SIGKILL)
        server.wait()


def test_a_refused_restart_stops_the_server_it_started(tmp_path, monkeypatch):
    # SEC-F5-L5: a restart that would accept unauthenticated requests is refused
    # and its process group is stopped; the marker stays dirty.
    port = _free_port()
    url = f"http://127.0.0.1:{port}/v1"
    monkeypatch.setenv("FAKE_KEY", "k")
    old = subprocess.Popen(_fake_vllm(tmp_path, port), start_new_session=True, cwd=tmp_path)
    started: list[int] = []
    real_popen = subprocess.Popen

    def popen(*args, **kwargs):  # type: ignore[no-untyped-def]
        process = real_popen(*args, **kwargs)
        started.append(process.pid)
        return process

    try:
        provider_supervisor.wait_ready(url, api_key="k", model="fake/model", timeout=20)
        guard = HostInferenceGuard(url, directory=tmp_path / "guard")
        record_provider(guard, ProviderRecord.capture(old.pid, guard.identity))
        guard.acquire()
        with guard.inflight("held"):
            pass
        guard.release()
        # The restarted server comes back without authentication.
        monkeypatch.setenv("FAKE_UNAUTHENTICATED", "1")
        monkeypatch.setattr(provider_supervisor.subprocess, "Popen", popen)
        with pytest.raises(GuardError, match="provider_restart_unauthenticated"):
            provider_supervisor.quiesce_and_restart(
                url,
                api_key="k",
                stop_timeout=5,
                ready_timeout=30,
                guard=HostInferenceGuard(url, directory=tmp_path / "guard"),
            )
        assert started and group_members(started[0]) == []
        assert guard.marker_path.exists()
        assert (
            stat.S_IMODE(os.stat(guard.directory / f"{guard.identity.key}.provider.log").st_mode)
            == 0o600
        )
    finally:
        for pid in (old.pid, *started):
            with contextlib.suppress(ProcessLookupError):
                os.killpg(pid, signal.SIGKILL)


def test_a_record_whose_port_is_served_by_another_process_is_refused(tmp_path):
    guard = HostInferenceGuard(LOCAL, directory=tmp_path / "guard")
    sleeper = subprocess.Popen(["sleep", "60"], start_new_session=True)
    try:
        argv = _fake_vllm(tmp_path, guard.identity.port)
        record = ProviderRecord(sleeper.pid, sleeper.pid, 1, argv, "/", guard.identity.canonical)
        assert not record.owns_listener(guard.identity)
    finally:
        sleeper.kill()
        sleeper.wait()


def test_a_marker_that_cannot_be_cleared_stops_the_worker(tmp_path, monkeypatch):
    # Code Review L-N3: a stale marker must stop the worker, not fail jobs serially.
    guard = guard_in(tmp_path)
    guard.acquire()
    real_unlink = Path.unlink

    def failing_unlink(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        if self == guard.marker_path:
            raise OSError("read-only")
        return real_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", failing_unlink)
    with guard.inflight("confirmed") as handle:
        handle.confirm()
    assert guard.uncertain and guard.marker_path.exists()
    guard.release()


def test_a_leftover_marker_marks_the_guard_uncertain(tmp_path):
    guard = guard_in(tmp_path)
    guard.acquire()
    guard.marker_path.write_text("{}")
    with (
        pytest.raises(GuardError, match="provider_quiescence_required"),
        guard.inflight("next"),
    ):
        pass
    assert guard.uncertain
    guard.release()


def test_the_credential_is_not_sent_to_a_listener_another_group_owns(tmp_path, monkeypatch):
    # Delta review D-4: with owner_pgid, wait_ready refuses before the authenticated call.
    port = _free_port()
    monkeypatch.setenv("FAKE_KEY", "k")
    server = subprocess.Popen(_fake_vllm(tmp_path, port), start_new_session=True)
    other = subprocess.Popen(["sleep", "60"], start_new_session=True)
    try:
        provider_supervisor.wait_ready(
            f"http://127.0.0.1:{port}/v1", api_key="k", model="fake/model", timeout=20
        )
        with pytest.raises(GuardError, match="provider_listener_unowned"):
            provider_supervisor.wait_ready(
                f"http://127.0.0.1:{port}/v1",
                api_key="k",
                model="fake/model",
                timeout=5,
                owner_pgid=other.pid,
            )
    finally:
        os.killpg(server.pid, signal.SIGKILL)
        server.wait()
        other.kill()
        other.wait()
