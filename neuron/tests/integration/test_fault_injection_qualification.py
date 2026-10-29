"""F0005-S0002 live failure injection (opt-in: BRAIN_RUN_LIVE_QUALIFICATION=1).

Faults are injected between the guarded worker and the dedicated vLLM server by
the test-only proxy, into storage by a wrapper, and into processes by abrupt exit.
Counters are taken at the converter entry point and at the proxy, never from
worker self-reports. Uncertain provider outcomes are recovered only through the
automated, confirmed stop/restart of the dedicated provider process group.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
from brain_content.verified_store import VerifiedBundleStore
from brain_extraction.vllm_graph_client import InferenceLimits
from brain_ingestion import provider_supervisor
from brain_ingestion.document_worker import WorkerStopped
from brain_ingestion.worker_guard import HostInferenceGuard
from brain_jobs.queue import events, jobs, outbox
from brain_persistence.grants import revoke_membership
from brain_persistence.models import (
    Assertion,
    AuditEventRow,
    ContentArtifact,
    ResourceAccessRow,
    ReviewItemRow,
    SemanticInterpretationRun,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent))
from f0005_live_support import (  # type: ignore[import-not-found]  # noqa: E402
    CORPUS,
    fault_proxy,
    qualification,
    require_live,
    upstream,
)

DOCUMENT = CORPUS / "documents/gl-q-007.pdf"
PROFILE = "gl-limits-b"
LEASE_SECONDS = 120.0


def _reasons(env: Any, job: Any) -> list[str]:
    with env.engine.connect() as conn:
        return list(
            conn.scalars(
                select(events.c.reason)
                .where(events.c.job_id == str(job), events.c.reason.is_not(None))
                .order_by(events.c.occurred_at)
            )
        )


def _assert_single_effect(env: Any) -> dict[str, int | None]:
    """Exactly one accepted artifact, one run, one assertion/review set, one ack."""
    with Session(env.engine) as session:
        counts = {
            "ready_artifacts": session.scalar(
                select(func.count())
                .select_from(ContentArtifact)
                .where(ContentArtifact.publication_state == "ready")
            ),
            "runs": session.scalar(select(func.count()).select_from(SemanticInterpretationRun)),
            "assertions": session.scalar(select(func.count()).select_from(Assertion)),
            "assertion_runs": session.scalar(select(func.count(func.distinct(Assertion.run_id)))),
            "review_items": session.scalar(select(func.count()).select_from(ReviewItemRow)),
            "acknowledged": session.scalar(
                select(func.count()).select_from(outbox).where(outbox.c.delivered_at.is_not(None))
            ),
            "complete_jobs": session.scalar(
                select(func.count()).select_from(jobs).where(jobs.c.state == "complete")
            ),
        }
    assert counts["ready_artifacts"] == 1
    # Exactly one run; its assertions (if the model found any) belong to it alone.
    assert counts["runs"] == 1
    assert counts["assertion_runs"] == min(1, counts["assertions"] or 0)
    assert counts["acknowledged"] == 1 and counts["complete_jobs"] == 1
    return counts


def _quiesce(settings: Any, guard: HostInferenceGuard) -> tuple[Path, float]:
    started = time.monotonic()
    receipt = provider_supervisor.quiesce_and_restart(
        settings.provider_url, api_key=settings.api_key, guard=guard, ready_timeout=600
    )
    return receipt, time.monotonic() - started


@pytest.mark.parametrize("pipeline", ["direct-baseline", "graph-dense"])
@pytest.mark.parametrize(
    ("mode", "reason"),
    [
        ("stopped", "model_unavailable"),
        ("http_5xx", "model_http_error"),
        ("malformed_json", "model_malformed_output"),
        ("schema_invalid", "model_schema_invalid"),
        ("timeout", "model_timeout"),
    ],
)
def test_provider_fault_records_distinct_reason_and_resumes_from_saved_json(
    pipeline: str, mode: str, reason: str
) -> None:
    url, settings = require_live()
    proxy = fault_proxy.FaultProxy(upstream(settings), hold_seconds=30).start()
    if mode not in ("stopped",):
        proxy.schedule = {1: mode}
    timeline: dict[str, float] = {}
    try:
        with (
            qualification.isolated(url, pipeline, v2_writer_enabled=True) as env,
            qualification.live_session(
                env,
                settings,
                transport_url=proxy.base_url,
                # Above the slowest full-reservation dense call on this GPU (~11 s),
                # below the ~60 s busy generation the `timeout` mode forwards.
                limits=InferenceLimits(request_timeout_seconds=30),
            ) as live,
        ):
            job = live.submit(DOCUMENT, PROFILE)
            if mode == "stopped":
                port = proxy.port
                proxy.stop_listening()
                assert live.worker.run_one()  # converts, publishes, then connection refused
                proxy.port = port
                proxy.start()
            elif mode == "timeout":
                timeline["fault"] = time.monotonic()
                with pytest.raises(WorkerStopped, match="provider_quiescence_required"):
                    live.worker.run_one()
                timed_out = time.monotonic()
                # M4: the client timed out while the provider was still generating.
                assert proxy.busy_at(timed_out)
                assert live.guard.marker_path.exists() and live.guard.uncertain
                # A healthy provider does not clear the uncertain marker.
                assert httpx.get(f"{upstream(settings)}/health", timeout=5).status_code == 200
                assert live.guard.marker_path.exists()
                with pytest.raises(WorkerStopped):
                    live.worker.run_one()  # no claim while dirty
                quiesce_started = time.monotonic()
                timeline["client_timed_out_after_fault"] = timed_out - timeline["fault"]
                timeline["quiescence_started_after_fault"] = quiesce_started - timeline["fault"]
                timeline["provider_busy_at_quiescence"] = proxy.busy_at(quiesce_started)
                held = next(r for r in proxy.records if r.mode == "timeout")
                timeline["busy_request_started_after_fault"] = (
                    held.upstream_started - timeline["fault"]
                )
                receipt, elapsed = _quiesce(settings, live.guard)
                timeline["quiescence_seconds"] = elapsed
                assert json.loads(receipt.read_text())["confirmed_exit"] is True
            else:
                assert live.worker.run_one()
            assert _reasons(env, job)[0] == reason
            live.drain(timeout=900)
            if "fault" in timeline:
                timeline["recovered_seconds"] = time.monotonic() - timeline["fault"]
            with env.engine.connect() as conn:
                state = conn.scalar(select(jobs.c.state).where(jobs.c.id == str(job)))
            # Zero conversion after publication: the retry reused the bundle.
            assert live.converter.launches == 1
            counts: dict[str, Any]
            if state == "complete":
                counts = dict(_assert_single_effect(env))
            else:
                # A later organic model failure may exhaust the budget; it must
                # still end explicitly, with the bundle retained and readable.
                assert state == "failed"
                counts = {"terminal_reasons": _reasons(env, job)}
            calls = [r for r in proxy.records if r.mode != "pass" or r.status is not None]
            # Evidence first, so a failed assertion still records what happened.
            print(
                json.dumps(
                    {
                        "fault_case": f"{pipeline}/{mode}",
                        "reasons": _reasons(env, job),
                        "final_state": state,
                        "conversions": live.converter.launches,
                        "proxy_requests": len(calls),
                        "max_concurrency": proxy.max_concurrency(),
                        "proxy_timeline": proxy.timeline(),
                        "counts": counts,
                        "timeline": timeline,
                    },
                    default=str,
                )
            )
            # Never more than one request inside the provider at a time.
            assert proxy.max_concurrency() <= 1
            if "recovered_seconds" in timeline:
                # One lease period plus one attempt (attempt bound: run deadline 300 s).
                assert timeline["recovered_seconds"] <= LEASE_SECONDS + 300
    finally:
        proxy.close()


class _FailingStore(VerifiedBundleStore):
    failures = 1

    def publish(self, key, manifest_bytes, files):  # type: ignore[no-untyped-def]
        if type(self).failures > 0:
            type(self).failures -= 1
            raise OSError("injected write failure before the manifest marker")
        return super().publish(key, manifest_bytes, files)


@pytest.mark.parametrize("failures", [1, 2])
def test_storage_failure_before_marker_is_never_ready_and_reconverts_at_most_once(
    failures: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    url, settings = require_live()
    monkeypatch.setattr(_FailingStore, "failures", failures)
    with qualification.isolated(url, "direct-baseline", v2_writer_enabled=True) as env:
        env.parts.publication.store.__class__ = _FailingStore
        with qualification.live_session(env, settings) as live:
            job = live.submit(DOCUMENT, PROFILE)
            live.drain(timeout=900)
            reasons = _reasons(env, job)
            with env.engine.connect() as conn:
                state = conn.scalar(select(jobs.c.state).where(jobs.c.id == str(job)))
            with Session(env.engine) as session:
                ready = session.scalar(
                    select(func.count())
                    .select_from(ContentArtifact)
                    .where(ContentArtifact.publication_state == "ready")
                )
            print(
                json.dumps(
                    {
                        "storage_case": failures,
                        "reasons": reasons,
                        "state": state,
                        "conversions": live.converter.launches,
                        "ready": ready,
                    }
                )
            )
            assert reasons[0] == "storage_write_failed"
            assert live.converter.launches == min(failures + 1, 2)
            if failures == 1:
                assert state == "complete" and ready == 1
            else:
                # Second pre-publication failure: no third conversion; explicit end.
                assert state == "failed" and ready == 0 and reasons == ["storage_write_failed"] * 2


def test_revoked_grant_between_attempts_denies_audits_and_stops() -> None:
    url, settings = require_live()
    proxy = fault_proxy.FaultProxy(upstream(settings)).start()
    proxy.schedule = {1: "http_5xx"}
    try:
        with (
            qualification.isolated(url, "direct-baseline", v2_writer_enabled=True) as env,
            qualification.live_session(env, settings, transport_url=proxy.base_url) as live,
        ):
            job = live.submit(DOCUMENT, PROFILE)
            assert live.worker.run_one()
            with Session(env.engine) as session, session.begin():
                revoke_membership(
                    session,
                    env.membership,
                    operator_id=env.actor,
                    approval_ref="f0005-qualification-revocation",
                    at=datetime.now(UTC),
                )
            time.sleep(6)
            assert live.worker.run_one()
            with Session(env.engine) as session:
                state = session.scalar(select(jobs.c.state).where(jobs.c.id == str(job)))
                denied = session.scalars(
                    select(AuditEventRow).where(
                        AuditEventRow.event_type == "authorization_decision",
                        AuditEventRow.decision.is_(False),
                    )
                ).all()
            assert _reasons(env, job) == ["model_http_error", "authorization_denied"]
            assert state == "failed" and denied
            assert len([r for r in proxy.records]) == 1  # no model call under stale authority
    finally:
        proxy.close()


def test_cancellation_stops_scheduling_and_temporary_exports_are_removed() -> None:
    url, settings = require_live()
    proxy = fault_proxy.FaultProxy(upstream(settings)).start()

    def exports() -> set[str]:
        root = Path(tempfile.gettempdir())
        return {
            p.name
            for pattern in ("nebula-source-*", "nebula-interpret-*")
            for p in root.glob(pattern)
        }

    before = exports()
    try:
        with qualification.isolated(url, "graph-dense", v2_writer_enabled=True) as env:
            with qualification.live_session(env, settings, transport_url=proxy.base_url) as live:
                job = live.submit(DOCUMENT, "gl-limits-a")

                cancelled_at: list[float] = []

                def cancel_during_first(record):  # type: ignore[no-untyped-def]
                    if record.number == 1:
                        env.parts.queue.cancel(job, env.tenant, env.knowledge_base)
                        cancelled_at.append(time.monotonic())

                proxy.on_record = cancel_during_first
                live.worker.run_one()
                time.sleep(3)
                with env.engine.connect() as conn:
                    state = conn.scalar(select(jobs.c.state).where(jobs.c.id == str(job)))
                assert state == "cancelled"
                # Scheduling stops within one in-flight call: no request starts later
                # than one heartbeat poll (1 s) after the cancellation, plus margin.
                assert cancelled_at
                late = [r for r in proxy.records if r.started > cancelled_at[0] + 1.5]
                assert late == [], [r.as_dict() for r in late]
                assert len(proxy.records) <= 2
                staging = (
                    list(live.guard.staging_root.iterdir())
                    if live.guard.staging_root.exists()
                    else []
                )
                assert staging == []
            assert exports() - before == set()
            objects = [
                p.relative_to(env.content_root).parts[:3]
                for p in env.content_root.rglob("*")
                if p.is_file()
            ]
            scope = (str(env.tenant), str(env.knowledge_base))
            # sources/ and runs/ carry tenant/KB in the key; F0004 bundles are keyed by
            # artifact and scoped by that artifact's resource-access row.
            with Session(env.engine) as session:
                bundle_scope = {
                    str(row.resource_id): (str(row.tenant_id), str(row.knowledge_base_id))
                    for row in session.scalars(select(ResourceAccessRow))
                }
            outside = [
                part
                for part in objects
                if (part[0] == "bundles" and bundle_scope.get(part[1]) != scope)
                or (part[0] != "bundles" and part[1:3] != scope)
            ]
            print(
                json.dumps(
                    {
                        "cancellation": {
                            "proxy_requests": len(proxy.records),
                            "outside_scope": outside,
                        }
                    }
                )
            )
            assert outside == []
    finally:
        proxy.close()


# ---------------------------------------------------------------------------
# Process kills (AC2) and competing workers (AC4) run real worker subprocesses.
# ---------------------------------------------------------------------------


def _child(url: str, handle: dict[str, str], mode: str, transport: str) -> int:
    """Subprocess worker: crash at a kill point, or drain/hold for the guard proofs."""
    from brain_content.checkpoints import CheckpointStore
    from brain_worker.document_delivery import DocumentResultImporter
    from sqlalchemy import event as sa_event

    env = qualification.attach(url, handle)
    settings = qualification.LiveSettings.from_environment()

    def crash() -> None:
        os._exit(17)

    if mode == "bundle":
        original_publish = VerifiedBundleStore.publish

        def publish(self, *a, **k):  # type: ignore[no-untyped-def]
            result = original_publish(self, *a, **k)
            crash()
            return result

        VerifiedBundleStore.publish = publish  # type: ignore[method-assign]
    elif mode == "run":
        original_run = CheckpointStore.publish_run

        def publish_run(self, **k):  # type: ignore[no-untyped-def]
            result = original_run(self, **k)
            crash()
            return result

        CheckpointStore.publish_run = publish_run  # type: ignore[method-assign]
    elif mode == "import":

        def mid_import(_c, _cur, statement, *_a):  # type: ignore[no-untyped-def]
            if statement.startswith("INSERT INTO review_item"):
                crash()

        sa_event.listen(env.engine, "before_cursor_execute", mid_import)
    elif mode == "imported":
        original_import = DocumentResultImporter.run_one

        def run_one(self):  # type: ignore[no-untyped-def]
            if original_import(self):
                crash()
            return False

        DocumentResultImporter.run_one = run_one  # type: ignore[method-assign]
    try:
        with qualification.live_session(env, settings, transport_url=transport) as live:
            print("acquired", flush=True)
            live.drain(timeout=900)
    except Exception as exc:  # noqa: BLE001 - child reports a stable code only
        print(getattr(exc, "code", type(exc).__name__), flush=True)
        return 2
    return 0


def _first_line(process: subprocess.Popen[str]) -> str:
    assert process.stdout is not None
    return process.stdout.readline().strip()


def _spawn(url: str, env: Any, mode: str, proxy: Any) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, __file__, "child", url, json.dumps(env.handle()), mode, proxy.base_url],
        stdout=subprocess.PIPE,
        text=True,
        env=os.environ.copy(),
    )


@pytest.mark.parametrize("kill_point", ["bundle", "run", "import", "imported"])
def test_worker_killed_at_each_point_recovers_with_single_effects(kill_point: str) -> None:
    url, settings = require_live()
    proxy = fault_proxy.FaultProxy(upstream(settings)).start()
    try:
        with qualification.isolated(url, "graph-dense", v2_writer_enabled=True) as env:
            job = None
            with qualification.live_session(env, settings) as setup:
                job = setup.submit(DOCUMENT, PROFILE)
            child = _spawn(url, env, kill_point, proxy)
            assert child.wait(900) == 17
            killed = time.monotonic()
            requests_by_child = len(proxy.records)
            with qualification.live_session(env, settings, transport_url=proxy.base_url) as live:
                live.drain(timeout=900)
                recovered = time.monotonic() - killed
                counts = _assert_single_effect(env)
                # Replacement never reconverted a published bundle.
                assert live.converter.launches == 0
                later_requests = len(proxy.records) - requests_by_child
                if kill_point in ("run", "import", "imported"):
                    assert later_requests == 0  # published result recovered without model calls
            print(
                json.dumps(
                    {
                        "kill_point": kill_point,
                        "recovered_seconds": recovered,
                        "child_requests": requests_by_child,
                        "replacement_requests": later_requests,
                        "counts": counts,
                        "reasons": _reasons(env, job),
                    }
                )
            )
            assert recovered <= LEASE_SECONDS + 300
    finally:
        proxy.close()


def test_second_worker_is_refused_and_killed_holder_requires_confirmed_quiescence() -> None:
    url, settings = require_live()
    proxy = fault_proxy.FaultProxy(upstream(settings), hold_seconds=45).start()
    try:
        with qualification.isolated(url, "graph-dense", v2_writer_enabled=True) as env:
            with qualification.live_session(env, settings) as setup:
                jobs_submitted = [
                    setup.submit(CORPUS / f"documents/gl-q-00{n}.pdf", "gl-limits-b")
                    for n in (2, 3, 5, 6, 7)
                ]
            worker_a = _spawn(url, env, "drain", proxy)
            assert _first_line(worker_a) == "acquired"
            worker_b = _spawn(url, env, "drain", proxy)
            assert _first_line(worker_b) == "inference_guard_busy"
            assert worker_b.wait(60) == 2
            # Hold the next provider request past A's life, then kill A mid-request.
            proxy.schedule = {len(proxy.records) + 1: "timeout"}
            deadline = time.monotonic() + 600
            while time.monotonic() < deadline and not any(
                r.mode == "timeout" for r in proxy.records
            ):
                time.sleep(0.2)
            time.sleep(1)
            killed = time.monotonic()
            with env.engine.connect() as conn:
                held_claim = conn.execute(
                    select(events.c.job_id, events.c.occurred_at)
                    .where(events.c.event == "claimed")
                    .order_by(events.c.occurred_at.desc())
                    .limit(1)
                ).one()
                # The kill time on the same database clock the job events use.
                killed_db = env.parts.queue._now(conn)
            worker_a.send_signal(signal.SIGKILL)
            worker_a.wait()
            # M4: A died while the provider was still working on its request.
            assert proxy.busy_at(killed)
            held_requests = len(proxy.records)
            with env.engine.connect() as conn:
                claims_before = conn.scalar(
                    select(func.count()).select_from(events).where(events.c.event == "claimed")
                )
            worker_b = _spawn(url, env, "drain", proxy)
            assert _first_line(worker_b) == "provider_quiescence_required"
            assert worker_b.wait(60) == 2
            with env.engine.connect() as conn:
                claims_after = conn.scalar(
                    select(func.count()).select_from(events).where(events.c.event == "claimed")
                )
            assert claims_after == claims_before  # B made no claim
            assert len(proxy.records) == held_requests  # zero requests from B
            assert proxy.max_concurrency() <= 1
            guard = HostInferenceGuard(settings.provider_url)
            guard.acquire()
            busy_at_quiescence = proxy.busy_at(time.monotonic())
            receipt, elapsed = _quiesce(settings, guard)
            guard.release()
            proxy.schedule = {}
            with qualification.live_session(env, settings, transport_url=proxy.base_url) as live:
                live.drain(timeout=1800)
            with env.engine.connect() as conn:
                states = conn.execute(select(jobs.c.state)).scalars().all()
                held_end = conn.scalar(
                    select(func.max(events.c.occurred_at)).where(
                        events.c.job_id == held_claim.job_id,
                        events.c.event.in_(("complete", "failed")),
                    )
                )
            # Recovery bound for the job A held (database clock): confirmed
            # quiescence, then at most one lease period plus one attempt.
            assert held_end is not None
            # Measured from the kill (delta review D-5), on the database clock.
            held_recovery = held_end - killed_db
            print(
                json.dumps(
                    {
                        "competing_workers": {
                            "quiescence_seconds": elapsed,
                            "held_job_recovery_seconds": held_recovery,
                            "provider_busy_at_quiescence": busy_at_quiescence,
                            "receipt": str(receipt),
                            "states": states,
                            "max_concurrency": proxy.max_concurrency(),
                            "requests": len(proxy.records),
                        }
                    }
                )
            )
            assert proxy.max_concurrency() <= 1
            assert set(states) <= {"complete", "failed"} and len(states) == len(jobs_submitted)
            assert held_recovery <= elapsed + LEASE_SECONDS + 300
    finally:
        proxy.close()


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "child":
    raise SystemExit(_child(sys.argv[2], json.loads(sys.argv[3]), sys.argv[4], sys.argv[5]))
