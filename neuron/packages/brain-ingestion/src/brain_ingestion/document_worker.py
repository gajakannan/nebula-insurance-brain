"""Composition of engine-owned jobs, Graph activities, and artifact checkpoints."""

from __future__ import annotations

import time
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from threading import Event, Thread
from typing import Literal
from uuid import UUID, uuid5

from brain_content.checkpoints import CheckpointStore
from brain_content.identities import ParserMigrationRequired
from brain_content.object_store import ObjectNotFoundError
from brain_content.validation import VerifiedBundle
from brain_extraction.graph_interpretation import GraphInterpretationService, Pipeline
from brain_extraction.profiles import load_profile
from brain_extraction.vllm_graph_client import VllmGraphClient
from brain_interpretation.parsed_content import ParseResult
from brain_interpretation.result import InterpretationResult
from brain_jobs.queue import DocumentJobQueue, FailureReason, JobLease, LeaseLost
from brain_security.execution import AuthorizationDenied
from docling_core.types.doc import DoclingDocument
from pydantic import BaseModel, ConfigDict, Field

from brain_ingestion.content_workflow import (
    ContentPublisher,
    PublicationFailed,
    load_or_convert_content,
)
from brain_ingestion.conversion_process import (
    ConversionError,
    ConverterCleanupFailed,
    SupervisedConverter,
)
from brain_ingestion.worker_guard import GuardError, HostInferenceGuard

# WHY: failures before a ready bundle may reconvert once (S0002-AC3); never after.
_PRE_PUBLICATION: frozenset[str] = frozenset(
    {"conversion_timeout", "conversion_failed", "storage_write_failed"}
)
# One original conversion plus at most one reconversion per job.
_MAX_CONVERSIONS = 2
# WHY: another attempt cannot change these outcomes, so they are terminal.
_TERMINAL: frozenset[str] = frozenset(
    {
        "stage_guard_mismatch",
        "unsupported_targeting",
        "unsupported_output",
        "authorization_denied",
        # The same saved JSON under the same budget is rejected the same way.
        "model_budget_exceeded",
    }
)
_MODEL_REASONS: dict[str, FailureReason] = {
    "unavailable": "model_unavailable",
    "timeout": "model_timeout",
    "http_error": "model_http_error",
    "malformed": "model_malformed_output",
    "schema_invalid": "model_schema_invalid",
    "budget": "model_budget_exceeded",
    "deadline": "model_deadline_exceeded",
    "cancelled": "cancelled",
    "invalid_request": "interpretation_failed",
}
# Host or provider faults are infrastructure, not this job's failure: stop the
# worker and leave the job for reclaim. A guard marker that cannot be written
# (F0005 M3), or serving usage beyond its reservation, meaning a changed tokenizer
# or an ignored output cap (Code Review L-N4).
_GUARD_FAULTS = frozenset(
    {"inflight_marker_not_durable", "provider_quiescence_required", "usage_exceeds_reservation"}
)
# WHY: jobs submitted before pipeline selection were processed by Graph's direct
# contract; they keep that meaning rather than adopting the current default.
LEGACY_PIPELINE: Pipeline = "graph-direct"


class DocumentTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_id: UUID
    version_id: UUID
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    recipe_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    profile_id: str
    profile_version: str
    schema_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    actor_id: UUID
    correlation_id: UUID
    content_contract_version: Literal[1, 2] = 1
    # Pinned at submission; absent only on historical jobs (see LEGACY_PIPELINE).
    pipeline: Pipeline | None = None

    @property
    def effective_pipeline(self) -> Pipeline:
        return self.pipeline or LEGACY_PIPELINE


class AttemptFailed(RuntimeError):
    def __init__(self, reason: FailureReason) -> None:
        self.reason = reason
        super().__init__(reason)


class WorkerStopped(RuntimeError):
    """The worker must stop claiming: uncertain provider work or unconfirmed cleanup."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def model_failure_reason(client: VllmGraphClient) -> FailureReason | None:
    """Reason of the first failed call or pre-dispatch rejection, if any."""
    diagnostics = client.diagnostics()
    for record in (*diagnostics["calls"], *diagnostics.get("rejections", ())):
        if record["outcome"] == "complete" or record["outcome"] in _GUARD_FAULTS:
            # Host faults are not this job's model failure (see guard_fault).
            continue
        failure = record.get("failure_class")
        if failure in _MODEL_REASONS:
            return _MODEL_REASONS[failure]
        if record["outcome"] == "cancelled":
            return "cancelled"
    return None


def guard_fault(client: VllmGraphClient) -> str | None:
    diagnostics = client.diagnostics()
    for record in (*diagnostics["calls"], *diagnostics.get("rejections", ())):
        if record["outcome"] in _GUARD_FAULTS:
            return str(record["outcome"])
    return None


def classify(exc: BaseException) -> FailureReason:
    if isinstance(exc, AttemptFailed):
        return exc.reason
    if isinstance(exc, ConversionError):
        if exc.code == "conversion_timeout":
            return "conversion_timeout"
        if exc.code == "stage_guard_mismatch":
            return "stage_guard_mismatch"
        if exc.code == "cancelled":
            return "cancelled"
        return "conversion_failed"
    if isinstance(exc, PublicationFailed):
        return "storage_write_failed"
    if isinstance(exc, AuthorizationDenied | PermissionError):
        return "authorization_denied"
    if isinstance(exc, NotImplementedError):
        return "unsupported_targeting"
    if isinstance(exc, ParserMigrationRequired):
        return "conversion_failed"
    return "conversion_failed"


class DocumentWorker:
    def __init__(
        self,
        *,
        queue: DocumentJobQueue,
        store: CheckpointStore,
        authorize_for_job: Callable[[JobLease], Callable[[UUID, UUID, UUID, str], None]],
        client_factory: Callable[[Event], VllmGraphClient],
        publish_content: ContentPublisher,
        converter: Callable[[Path], ParseResult[DoclingDocument]] | None = None,
        load_accepted: Callable[[JobLease], VerifiedBundle | None] | None = None,
        v2_writer_enabled: bool = False,
        supervisor: SupervisedConverter | None = None,
        guard: HostInferenceGuard | None = None,
        observe: Callable[[dict[str, object]], None] | None = None,
    ) -> None:
        if converter is None and supervisor is None:
            raise ValueError("physical conversion requires the supervised converter")
        self.queue, self.store = queue, store
        self.authorize_for_job = authorize_for_job
        self.client_factory = client_factory
        self.publish_content = publish_content
        self.converter = converter
        self.load_accepted, self.v2_writer_enabled = load_accepted, v2_writer_enabled
        self.supervisor, self.guard = supervisor, guard
        # Qualification timing only: identities and monotonic times, never content.
        self.observe = observe
        self.last_reason: FailureReason | None = None
        # Set once this attempt holds a verified, ready bundle (F0005 M1).
        self._published = False

    def run_one(self) -> bool:
        if self.guard is not None:
            if not self.guard.held:
                raise WorkerStopped("inference_guard_not_held")
            if self.guard.uncertain:
                raise WorkerStopped("provider_quiescence_required")
        lease = self.queue.claim()
        if lease is None:
            return False
        cancelled, stop = Event(), Event()

        # Poll at least every second: a cancelled or fenced job must stop model
        # scheduling within one in-flight call (S0002-AC4), not one lease third.
        interval = min(self.queue.lease_seconds / 3, 1.0)

        def heartbeat() -> None:
            while not stop.wait(interval):
                try:
                    self.queue.heartbeat(lease)
                except Exception:
                    cancelled.set()
                    return

        thread = Thread(target=heartbeat, daemon=True)
        thread.start()
        self.last_reason = None
        self._published = False
        stopped: WorkerStopped | None = None
        try:
            self._execute(lease, cancelled)
        except LeaseLost:
            cancelled.set()
        except WorkerStopped as exc:
            # Host infrastructure fault: stop claiming and leave the job to be
            # reclaimed after its lease, instead of failing every queued job.
            stopped = exc
        except ConverterCleanupFailed as exc:
            # Keep the receipt/staging for DevOps; the next startup reaper fails
            # closed while the group survives. Never start another conversion.
            stopped = WorkerStopped(exc.code)
        except Exception as exc:
            # Job history contains stable reason codes, not source or SDK errors.
            reason = classify(exc)
            if self._published and reason in _PRE_PUBLICATION:
                # After a ready bundle nothing is a conversion failure, and an
                # unexpected error never spends the reconversion budget.
                reason = "interpretation_failed"
            self.last_reason = reason
            with suppress(LeaseLost):
                self._record_failure(lease, reason)
        finally:
            stop.set()
            thread.join(timeout=self.queue.lease_seconds)
        if stopped is not None:
            raise stopped
        if self.guard is not None and self.guard.uncertain:
            raise WorkerStopped("provider_quiescence_required")
        return True

    def _start_conversion(self, lease: JobLease) -> None:
        # Enforce the budget before launching, not only after a failure: silent
        # crashes record no reason but each one spent a launch (Code Review N1).
        if self.queue.conversion_launches(lease.job_id) >= _MAX_CONVERSIONS:
            raise ConversionError("conversion_budget_exhausted")
        self.queue.conversion_started(lease)

    def _record_failure(self, lease: JobLease, reason: FailureReason) -> None:
        terminal = reason in _TERMINAL
        if reason in _PRE_PUBLICATION:
            # Count durable launches, not recorded reasons: a crash mid-conversion
            # records no reason but still spent a conversion (F0005 M2).
            terminal = terminal or self.queue.conversion_launches(lease.job_id) >= _MAX_CONVERSIONS
        if terminal:
            self.queue.fail(lease, reason=reason)
        else:
            self.queue.retry(lease, reason=reason)

    def _execute(self, lease: JobLease, cancelled: Event) -> None:
        task = DocumentTask.model_validate(lease.payload)
        profile = load_profile(task.profile_id)
        if (profile.profile_version, profile.schema_sha256) != (
            task.profile_version,
            task.schema_sha256,
        ):
            raise ValueError("queued extraction profile changed")
        authorize = self.authorize_for_job(lease)
        authorize(lease.tenant_id, lease.knowledge_base_id, lease.artifact_id, "ingest")
        authorize(lease.tenant_id, lease.knowledge_base_id, lease.artifact_id, "interpret")
        bundle = load_or_convert_content(
            lease=lease,
            task=task,
            store=self.store,
            authorize=authorize,
            publisher=self.publish_content,
            load_accepted=self.load_accepted,
            converter=self.converter,
            client_factory=self.client_factory,
            cancelled=cancelled,
            profile=profile,
            v2_writer_enabled=self.v2_writer_enabled,
            supervisor=self.supervisor,
            attempt_id=f"{lease.job_id}-{lease.generation}",
            before_conversion=lambda: self._start_conversion(lease),
        )
        self._published = True
        key = bundle.key
        if bundle.manifest.source_sha256 != task.source_sha256:
            raise ValueError("accepted checkpoint belongs to a different source")
        # Recover a successfully published prior attempt whose DB completion was
        # interrupted. Never pay for another model call to rediscover that result.
        for attempt in range(lease.attempt - 1, 0, -1):
            run_id = uuid5(lease.job_id, f"attempt:{attempt}")
            try:
                outputs = self.store.load_run(
                    tenant_id=lease.tenant_id,
                    knowledge_base_id=lease.knowledge_base_id,
                    artifact_id=key.artifact_id,
                    run_id=run_id,
                    artifact_key=key,
                )
            except ObjectNotFoundError:
                continue
            result = InterpretationResult.model_validate_json(outputs["result.json"])
            if (
                result.run_id,
                result.artifact_id,
                result.run_configuration.profile_id,
                result.run_configuration.profile_version,
                result.run_configuration.schema_hash,
            ) != (
                run_id,
                key.artifact_id,
                task.profile_id,
                task.profile_version,
                task.schema_sha256,
            ):
                raise ValueError("published run does not match the queued profile")
            if result.status != "failed":
                authorize(lease.tenant_id, lease.knowledge_base_id, key.artifact_id, "interpret")
                self.queue.finish(
                    lease,
                    f"runs/{lease.tenant_id}/{lease.knowledge_base_id}/{run_id}/manifest.json",
                )
                return
        client = self.client_factory(cancelled)
        run_id = uuid5(lease.job_id, f"attempt:{lease.attempt}")
        timing: dict[str, object] = {
            "job_id": str(lease.job_id),
            "attempt": lease.attempt,
            "pipeline": task.effective_pipeline,
            "interpretation_started": time.monotonic(),
        }

        def publish(operation: Callable[[], str]) -> str:
            reference = self.queue.publish(lease, operation)
            timing["result_published"] = time.monotonic()
            return reference

        try:
            result = GraphInterpretationService(self.store, authorize).interpret(
                tenant_id=lease.tenant_id,
                knowledge_base_id=lease.knowledge_base_id,
                artifact_id=key.artifact_id,
                run_id=run_id,
                profile=profile,
                client=client,
                publish=publish,
                artifact_key=key,
                output_contract_version=2,
                pipeline=task.pipeline,
            )
            model_reason = model_failure_reason(client)
            fault = guard_fault(client)
        finally:
            client.close()
            if self.observe is not None:
                timing["interpretation_finished"] = time.monotonic()
                self.observe({**timing, "calls": len(client.diagnostics()["calls"])})
        if fault is not None and model_reason is None:
            # Only a host fault: stop without failing the job. A genuine model
            # failure in the same run (for example the timeout that made the
            # guard uncertain) is recorded first; run_one then stops on the
            # uncertain guard.
            raise WorkerStopped(fault)
        if result.status == "failed":
            if "unsupported_output" in result.warnings:
                raise AttemptFailed("unsupported_output")
            if cancelled.is_set():
                raise AttemptFailed("cancelled")
            if model_reason is not None:
                raise AttemptFailed(model_reason)
            if "dense_contract_fallback" in result.warnings:
                raise AttemptFailed("model_contract_fallback")
            if any(w.startswith("pipeline_failure:") for w in result.warnings):
                raise AttemptFailed("interpretation_failed")
            raise AttemptFailed("model_malformed_output")
        self.queue.finish(
            lease, f"runs/{lease.tenant_id}/{lease.knowledge_base_id}/{run_id}/manifest.json"
        )


__all__ = ["DocumentTask", "DocumentWorker", "GuardError", "WorkerStopped"]
