"""DevOps/qualification supervisor for the dedicated local provider (F0005 Step 0a).

`record` captures the preflight identity of the running serving process group.
`quiesce` is the only uncertain-request recovery path: while holding the host
guard it stops that exact process group, confirms every member exited, restarts
the identical recorded serving command, waits for the pinned model, writes a
source-free receipt and only then clears the in-flight marker. If ownership or
exit cannot be established it stays stopped and leaves the marker dirty.

The credential stays in the existing local secret mechanism: the restarted
server inherits this process environment; nothing secret enters the receipt.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import httpx

from brain_ingestion.worker_guard import (
    GuardError,
    HostInferenceGuard,
    ProviderRecord,
    canonical_endpoint,
    group_members,
    load_provider,
    process_start_ticks,
    record_provider,
    terminate_group,
)


def _pins(argv: list[str]) -> dict[str, str | None]:
    def option(name: str) -> str | None:
        return argv[argv.index(name) + 1] if name in argv[:-1] else None

    model = argv[argv.index("serve") + 1] if "serve" in argv[:-1] else None
    return {
        "model": model,
        "revision": option("--revision"),
        "tokenizer_revision": option("--tokenizer-revision"),
        "max_model_len": option("--max-model-len"),
    }


def wait_ready(
    endpoint: str,
    *,
    api_key: str,
    model: str | None,
    timeout: float,
    alive: Any = None,
    owner_pgid: int | None = None,
) -> float:
    """Wait for /health and an authenticated model listing; return the ready time.

    With `owner_pgid`, the credential is sent only once the guarded listener is
    owned by that process group (delta review D-4).
    """
    root = endpoint.rsplit("/v1", 1)[0]
    identity = canonical_endpoint(endpoint)
    deadline = time.monotonic() + timeout
    with httpx.Client(trust_env=False, follow_redirects=False, timeout=5) as client:
        while time.monotonic() < deadline:
            if alive is not None and not alive():
                raise GuardError("provider_restart_exited")
            try:
                if client.get(f"{root}/health").status_code == 200:
                    if owner_pgid is not None and not _group_owns_listener(owner_pgid, identity):
                        raise GuardError("provider_listener_unowned")
                    listed = client.get(
                        f"{endpoint}/models", headers={"Authorization": f"Bearer {api_key}"}
                    )
                    if listed.status_code == 200 and model in {
                        item.get("id") for item in listed.json().get("data", [])
                    }:
                        # The restarted server must still refuse unauthenticated
                        # requests: a restart without its key is never "ready"
                        # (Security SEC-F5-L1).
                        if client.get(f"{endpoint}/models").status_code != 401:
                            raise GuardError("provider_restart_unauthenticated")
                        return time.time()
            except httpx.HTTPError:
                pass
            time.sleep(1)
    raise GuardError("provider_restart_not_ready")


def _group_owns_listener(pgid: int, identity: Any) -> bool:
    record = ProviderRecord(pgid, pgid, 0, [], "/", identity.canonical)
    return record.owns_listener(identity)


def confirm_stopped(record: ProviderRecord, *, stop_timeout: float) -> float:
    """Stop the recorded process group and return when every member has exited."""
    live = process_start_ticks(record.pid)
    if live is not None and not record.is_live():
        # The PID now names another process, group or command: ownership cannot
        # be established, so nothing is signalled.
        raise GuardError("provider_ownership_unconfirmed")
    if live is None and not group_members(record.pgid):
        return time.time()
    if live is not None and not record.owns_listener(canonical_endpoint(record.endpoint)):
        # A different process holds the guarded port: signalling the recorded
        # group cannot make the endpoint quiescent (SEC-F5-L4).
        raise GuardError("provider_ownership_unconfirmed")
    # The leader is gone but members remain; they are still this group's model
    # workers only if the group id was never reused by a new leader.
    if live is None and process_start_ticks(record.pgid) is not None:
        raise GuardError("provider_ownership_unconfirmed")
    if not terminate_group(record.pgid, term_grace=stop_timeout, kill_grace=10):
        raise GuardError("provider_exit_unconfirmed")
    return time.time()


def quiesce_and_restart(
    provider_url: str,
    *,
    api_key: str,
    stop_timeout: float = 60,
    ready_timeout: float = 600,
    guard: HostInferenceGuard | None = None,
) -> Path:
    guard = guard or HostInferenceGuard(provider_url)
    owned = not guard.held
    if owned:
        guard.acquire()
    try:
        old = load_provider(guard)
        marker = json.loads(guard.marker_path.read_bytes()) if guard.marker_path.exists() else None
        stop_started = time.time()
        exit_confirmed = confirm_stopped(old, stop_timeout=stop_timeout)
        # Owner-only: the provider log can hold request metadata (SEC-F5-L4).
        log_path = guard.directory / f"{guard.identity.key}.provider.log"
        log = os.fdopen(os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), "ab")
        os.chmod(log_path, 0o600)
        try:
            process = subprocess.Popen(
                old.argv,
                cwd=old.cwd,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                close_fds=True,
                start_new_session=True,
            )
        finally:
            log.close()
        pins = _pins(old.argv)
        try:
            ready = wait_ready(
                guard.identity.canonical,
                api_key=api_key,
                model=pins["model"],
                timeout=ready_timeout,
                alive=lambda: process.poll() is None,
                owner_pgid=process.pid,
            )
            new = ProviderRecord.capture(process.pid, guard.identity)
            if _pins(new.argv) != pins:
                raise GuardError("provider_restart_pin_mismatch")
            if not new.owns_listener(guard.identity):
                raise GuardError("provider_listener_unowned")
        except BaseException:
            # A refused restart (unauthenticated, not ready, wrong pins or a
            # foreign listener) must not leave its server running (SEC-F5-L5).
            # The marker stays dirty either way; the refusal code is preserved.
            stopped = terminate_group(process.pid, term_grace=stop_timeout, kill_grace=10)
            with contextlib.suppress(subprocess.TimeoutExpired):
                process.wait(timeout=5)
            if not stopped:
                raise GuardError("provider_restart_cleanup_unconfirmed") from None
            raise
        record_provider(guard, new)
        receipt = {
            "receipt_version": 1,
            "endpoint_key": guard.identity.key,
            "old_provider": {k: v for k, v in asdict(old).items() if k != "argv"},
            "new_provider": {k: v for k, v in asdict(new).items() if k != "argv"},
            "serving_argv_sha256": hashlib.sha256(json.dumps(old.argv).encode()).hexdigest(),
            "pins": pins,
            "confirmed_exit": True,
            "marker": marker,
            "stop_started_at": stop_started,
            "exit_confirmed_at": exit_confirmed,
            "ready_at": ready,
        }
        return guard.clear_after_quiescence(receipt)
    finally:
        if owned:
            guard.release()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    record = commands.add_parser("record", help="Record the running provider (preflight)")
    record.add_argument("--pid", type=int, required=True)
    commands.add_parser("quiesce", help="Confirmed stop, pinned restart, receipt, clear")
    commands.add_parser("status", help="Print guard paths and marker state")
    args = parser.parse_args()
    endpoint = os.environ["BRAIN_INFERENCE_BASE_URL"]
    guard = HostInferenceGuard(endpoint)
    try:
        if args.command == "record":
            with guard:
                record_provider(guard, ProviderRecord.capture(args.pid, guard.identity))
            print(f"provider_recorded:{guard.provider_path}")
        elif args.command == "quiesce":
            receipt = quiesce_and_restart(endpoint, api_key=os.environ["BRAIN_INFERENCE_API_KEY"])
            print(f"provider_quiesced:{receipt}")
        else:
            print(
                json.dumps(
                    {
                        "endpoint": guard.identity.canonical,
                        "directory": str(guard.directory),
                        "marker_dirty": guard.marker_path.exists(),
                        "provider_recorded": guard.provider_path.exists(),
                    }
                )
            )
    except GuardError as exc:
        print(exc.code)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
