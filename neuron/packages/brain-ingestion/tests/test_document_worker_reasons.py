"""F0005 worker failure-reason, retry-rule and guard-stop behavior (offline)."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Event
from typing import Any
from uuid import uuid4

import pytest
from brain_content.identities import ParserMigrationRequired
from brain_ingestion.content_workflow import PublicationFailed
from brain_ingestion.conversion_process import ConversionError, ConverterCleanupFailed
from brain_ingestion.document_worker import (
    LEGACY_PIPELINE,
    AttemptFailed,
    DocumentTask,
    DocumentWorker,
    WorkerStopped,
    classify,
    guard_fault,
    model_failure_reason,
)
from brain_jobs.queue import JobLease, LeaseLost
from brain_security.execution import AuthorizationDenied


@pytest.mark.parametrize(
    ("exc", "reason"),
    [
        (AttemptFailed("model_timeout"), "model_timeout"),
        (ConversionError("conversion_timeout"), "conversion_timeout"),
        (ConversionError("stage_guard_mismatch"), "stage_guard_mismatch"),
        (ConversionError("cancelled"), "cancelled"),
        (ConversionError("child_exit_7"), "conversion_failed"),
        (PublicationFailed("storage_write_failed"), "storage_write_failed"),
        (AuthorizationDenied(None), "authorization_denied"),  # type: ignore[arg-type]
        (PermissionError("revoked"), "authorization_denied"),
        (NotImplementedError("targeting"), "unsupported_targeting"),
        (ParserMigrationRequired("recipe"), "conversion_failed"),
        (RuntimeError("unexpected"), "conversion_failed"),
    ],
)
def test_classify_maps_every_exception_to_a_stable_reason(exc: BaseException, reason: str) -> None:
    assert classify(exc) == reason


class _Client:
    def __init__(
        self, calls: list[dict[str, Any]], rejections: list[dict[str, Any]] | None = None
    ) -> None:
        self._calls = calls
        self._rejections = rejections or []

    def diagnostics(self) -> dict[str, Any]:
        return {"calls": self._calls, "rejections": self._rejections}


@pytest.mark.parametrize(
    ("calls", "reason"),
    [
        ([], None),
        ([{"outcome": "complete", "failure_class": None}], None),
        ([{"outcome": "failed", "failure_class": "unavailable"}], "model_unavailable"),
        ([{"outcome": "failed", "failure_class": "timeout"}], "model_timeout"),
        ([{"outcome": "failed", "failure_class": "http_error"}], "model_http_error"),
        ([{"outcome": "failed", "failure_class": "malformed"}], "model_malformed_output"),
        ([{"outcome": "failed", "failure_class": "schema_invalid"}], "model_schema_invalid"),
        ([{"outcome": "cancelled", "failure_class": None}], "cancelled"),
        (
            [{"outcome": "run_deadline_exceeded", "failure_class": "deadline"}],
            "model_deadline_exceeded",
        ),
        # A provider fault (L-N4): the worker stops; no model reason for the job.
        ([{"outcome": "usage_exceeds_reservation", "failure_class": "budget"}], None),
        (
            [
                {"outcome": "complete", "failure_class": None},
                {"outcome": "failed", "failure_class": "timeout"},
                {"outcome": "failed", "failure_class": "malformed"},
            ],
            "model_timeout",
        ),
    ],
)
def test_model_failure_reason_reports_the_first_failed_call(
    calls: list[dict[str, Any]], reason: str | None
) -> None:
    assert model_failure_reason(_Client(calls)) == reason  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("code", "failure_class", "reason"),
    [
        ("context_limit_exceeded", "budget", "model_budget_exceeded"),
        ("call_budget_exceeded", "budget", "model_budget_exceeded"),
        ("token_budget_exceeded", "budget", "model_budget_exceeded"),
        ("run_deadline_exceeded", "deadline", "model_deadline_exceeded"),
        ("cancelled", "cancelled", "cancelled"),
        ("invalid_schema", "invalid_request", "interpretation_failed"),
    ],
)
def test_pre_dispatch_rejections_report_their_own_reason(
    code: str, failure_class: str, reason: str
) -> None:
    # Never sent, so no call record: the rejection alone must fail the attempt (H1).
    rejected = [{"phase": "dense_fill", "outcome": code, "failure_class": failure_class}]
    complete = [{"outcome": "complete", "failure_class": None}]
    assert model_failure_reason(_Client(complete, rejected)) == reason  # type: ignore[arg-type]


def test_a_marker_fault_is_reported_as_a_guard_fault_not_a_model_reason() -> None:
    client = _Client(
        [], [{"outcome": "inflight_marker_not_durable", "failure_class": "unavailable"}]
    )
    assert guard_fault(client) == "inflight_marker_not_durable"  # type: ignore[arg-type]
    assert guard_fault(_Client([{"outcome": "complete"}])) is None  # type: ignore[arg-type]


def test_historical_tasks_without_a_pipeline_keep_their_graph_direct_meaning() -> None:
    sha = "a" * 64
    task = DocumentTask(
        document_id=uuid4(),
        version_id=uuid4(),
        source_sha256=sha,
        recipe_sha256=sha,
        profile_id="gl-limits",
        profile_version="1",
        schema_sha256=sha,
        actor_id=uuid4(),
        correlation_id=uuid4(),
    )

    assert task.pipeline is None
    assert task.effective_pipeline == LEGACY_PIPELINE == "graph-direct"
    assert task.model_copy(update={"pipeline": "direct-baseline"}).effective_pipeline == (
        "direct-baseline"
    )


@dataclass
class _Queue:
    prior: list[str] = field(default_factory=list)
    launches: int = 1
    lease_seconds: float = 0.3
    claims: int = 0
    outcomes: list[tuple[str, str]] = field(default_factory=list)
    heartbeat_error: BaseException | None = None

    def claim(self) -> JobLease | None:
        self.claims += 1
        return JobLease(
            job_id=uuid4(),
            tenant_id=uuid4(),
            knowledge_base_id=uuid4(),
            artifact_id=uuid4(),
            generation=0,
            attempt=1,
            payload={},
        )

    def heartbeat(self, lease: JobLease) -> None:
        if self.heartbeat_error is not None:
            raise self.heartbeat_error

    def failure_reasons(self, job_id: object) -> list[str]:
        return list(self.prior)

    def conversion_started(self, lease: JobLease) -> None:
        self.launches += 1

    def conversion_launches(self, job_id: object) -> int:
        return self.launches

    def fail(self, lease: JobLease, *, reason: str) -> None:
        self.outcomes.append(("fail", reason))

    def retry(self, lease: JobLease, *, reason: str) -> None:
        self.outcomes.append(("retry", reason))


class _EmptyQueue(_Queue):
    def claim(self) -> JobLease | None:
        return None


@dataclass
class _Guard:
    held: bool = True
    uncertain: bool = False


def _worker(queue: _Queue, guard: _Guard | None = None, raises: BaseException | None = None):
    worker = DocumentWorker(
        queue=queue,  # type: ignore[arg-type]
        store=None,  # type: ignore[arg-type]
        authorize_for_job=lambda *_: None,  # type: ignore[arg-type,return-value]
        client_factory=lambda _cancelled: None,  # type: ignore[arg-type,return-value]
        publish_content=lambda *_: None,  # type: ignore[arg-type]
        converter=object(),  # type: ignore[arg-type]
        load_accepted=lambda *_: None,  # type: ignore[arg-type,return-value]
        guard=guard,  # type: ignore[arg-type]
    )

    def execute(lease: JobLease, cancelled: Event) -> None:
        if raises is not None:
            raise raises

    worker._execute = execute  # type: ignore[method-assign]
    return worker


def test_physical_conversion_requires_a_converter_or_the_supervisor() -> None:
    with pytest.raises(ValueError, match="supervised converter"):
        DocumentWorker(
            queue=_Queue(),  # type: ignore[arg-type]
            store=None,  # type: ignore[arg-type]
            authorize_for_job=lambda *_: None,  # type: ignore[arg-type,return-value]
            client_factory=lambda _c: None,  # type: ignore[arg-type,return-value]
            publish_content=lambda *_: None,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("launches", "reason", "outcome"),
    [
        (1, "conversion_failed", "retry"),
        (2, "conversion_failed", "fail"),
        (2, "storage_write_failed", "fail"),
        # A crash mid-publication records no reason but its launch still counts (M2).
        (2, "conversion_timeout", "fail"),
        (1, "conversion_timeout", "retry"),
        (1, "model_unavailable", "retry"),
        (3, "model_timeout", "retry"),
        (1, "interpretation_failed", "retry"),
        (1, "model_deadline_exceeded", "retry"),
        (1, "model_contract_fallback", "retry"),
        (1, "model_budget_exceeded", "fail"),
        (1, "stage_guard_mismatch", "fail"),
        (1, "unsupported_output", "fail"),
        (1, "authorization_denied", "fail"),
    ],
)
def test_failures_reconvert_at_most_once_and_terminal_reasons_never_retry(
    launches: int, reason: str, outcome: str
) -> None:
    queue = _Queue(launches=launches)
    worker = _worker(queue, raises=AttemptFailed(reason))  # type: ignore[arg-type]

    assert worker.run_one() is True
    assert queue.outcomes == [(outcome, reason)]
    assert worker.last_reason == reason


def test_an_empty_queue_reports_no_work() -> None:
    assert _worker(_EmptyQueue()).run_one() is False


@pytest.mark.parametrize(
    ("guard", "code"),
    [
        (_Guard(held=False), "inference_guard_not_held"),
        (_Guard(uncertain=True), "provider_quiescence_required"),
    ],
)
def test_worker_refuses_to_claim_without_a_held_quiescent_guard(guard: _Guard, code: str) -> None:
    queue = _Queue()

    with pytest.raises(WorkerStopped) as stopped:
        _worker(queue, guard=guard).run_one()

    assert stopped.value.code == code
    assert queue.claims == 0


def test_uncertain_provider_work_stops_the_worker_after_recording_the_failure() -> None:
    queue, guard = _Queue(), _Guard()
    worker = _worker(queue, guard=guard, raises=AttemptFailed("model_timeout"))

    def execute(lease: JobLease, cancelled: Event) -> None:
        guard.uncertain = True  # an ambiguous dispatch during this attempt
        raise AttemptFailed("model_timeout")

    worker._execute = execute  # type: ignore[method-assign]

    with pytest.raises(WorkerStopped, match="provider_quiescence_required"):
        worker.run_one()
    assert queue.outcomes == [("retry", "model_timeout")]


def test_unconfirmed_converter_cleanup_stops_without_recording_a_reason() -> None:
    queue = _Queue()
    worker = _worker(queue, raises=ConverterCleanupFailed("converter_cleanup_unconfirmed"))

    with pytest.raises(WorkerStopped, match="converter_cleanup_unconfirmed"):
        worker.run_one()
    assert queue.outcomes == []


def test_a_lost_lease_records_nothing() -> None:
    queue = _Queue()

    assert _worker(queue, raises=LeaseLost()).run_one() is True
    assert queue.outcomes == []


def test_a_failed_heartbeat_cancels_the_attempt() -> None:
    queue = _Queue(heartbeat_error=LeaseLost())
    seen: list[bool] = []
    worker = _worker(queue)

    def execute(lease: JobLease, cancelled: Event) -> None:
        seen.append(cancelled.wait(2.0))

    worker._execute = execute  # type: ignore[method-assign]

    assert worker.run_one() is True
    assert seen == [True]


@pytest.mark.parametrize("error", [RuntimeError("transient database error"), ValueError("mapping")])
def test_errors_after_a_ready_bundle_are_not_conversion_failures(error: Exception) -> None:
    # M1: attempt 2 publishes, then fails unexpectedly; the conversion budget is untouched.
    queue = _Queue(launches=2)
    worker = _worker(queue)

    def execute(lease: JobLease, cancelled: Event) -> None:
        worker._published = True
        raise error

    worker._execute = execute  # type: ignore[method-assign]

    assert worker.run_one() is True
    assert queue.outcomes == [("retry", "interpretation_failed")]


def test_the_same_error_before_publication_stays_a_conversion_failure() -> None:
    queue = _Queue(launches=1)

    assert _worker(queue, raises=RuntimeError("before publication")).run_one() is True
    assert queue.outcomes == [("retry", "conversion_failed")]


def test_a_guard_infrastructure_fault_stops_the_worker_without_failing_the_job() -> None:
    # M3: the job is left for reclaim after its lease instead of being drained.
    queue = _Queue()
    worker = _worker(queue, raises=WorkerStopped("inflight_marker_not_durable"))

    with pytest.raises(WorkerStopped, match="inflight_marker_not_durable"):
        worker.run_one()
    assert queue.outcomes == []


@pytest.mark.parametrize(("launches", "allowed"), [(0, True), (1, True), (2, False), (3, False)])
def test_no_third_conversion_starts_after_silent_crashes(launches: int, allowed: bool) -> None:
    # N1: two crashes recorded no reason, but both launches count before a third.
    queue = _Queue(launches=launches)
    worker = _worker(queue)
    lease = queue.claim()
    assert lease is not None
    if allowed:
        worker._start_conversion(lease)
        assert queue.launches == launches + 1
    else:
        with pytest.raises(ConversionError, match="conversion_budget_exhausted"):
            worker._start_conversion(lease)
        assert queue.launches == launches  # nothing launched


def test_an_exhausted_budget_ends_the_job_terminally() -> None:
    queue = _Queue(launches=2)
    worker = _worker(queue, raises=ConversionError("conversion_budget_exhausted"))

    assert worker.run_one() is True
    assert queue.outcomes == [("fail", "conversion_failed")]


def test_serving_usage_beyond_the_reservation_stops_the_worker() -> None:
    # L-N4: a provider misconfiguration must not fail every queued job.
    exceeded = {"outcome": "usage_exceeds_reservation", "failure_class": "budget"}
    assert guard_fault(_Client([exceeded])) == "usage_exceeds_reservation"  # type: ignore[arg-type]
    assert guard_fault(_Client([], [exceeded])) == "usage_exceeds_reservation"  # type: ignore[arg-type]


def test_a_stale_marker_during_a_run_stops_the_worker_without_failing_the_job() -> None:
    # Delta review D-1: provider_quiescence_required is a host fault, not this job's.
    stale = {"outcome": "provider_quiescence_required", "failure_class": "unavailable"}
    assert guard_fault(_Client([], [stale])) == "provider_quiescence_required"  # type: ignore[arg-type]


def test_usage_beyond_the_reservation_stops_run_one_without_recording_a_reason() -> None:
    # Delta review D-5: the L-N4 rule through run_one, not only the helper.
    queue = _Queue()
    worker = _worker(queue, raises=WorkerStopped("usage_exceeds_reservation"))
    with pytest.raises(WorkerStopped, match="usage_exceeds_reservation"):
        worker.run_one()
    assert queue.outcomes == []


def test_a_timeout_followed_by_a_quiescence_refusal_still_reports_the_timeout() -> None:
    # Live G2 round 3: dense timed out, the next call was refused as uncertain.
    calls = [{"outcome": "provider_timeout", "failure_class": "timeout"}]
    rejected = [{"outcome": "provider_quiescence_required", "failure_class": "unavailable"}]
    client = _Client(calls, rejected)
    assert model_failure_reason(client) == "model_timeout"  # type: ignore[arg-type]
    assert guard_fault(client) == "provider_quiescence_required"  # type: ignore[arg-type]


def test_a_host_fault_alone_has_no_model_reason() -> None:
    rejected = [{"outcome": "provider_quiescence_required", "failure_class": "unavailable"}]
    assert model_failure_reason(_Client([], rejected)) is None  # type: ignore[arg-type]
