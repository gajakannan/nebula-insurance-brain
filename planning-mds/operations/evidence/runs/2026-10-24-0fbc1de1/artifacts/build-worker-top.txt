"""Composition of engine-owned jobs, Graph activities, and artifact checkpoints."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from threading import Event, Thread
from typing import Literal
from uuid import UUID, uuid5

from brain_content.checkpoints import CheckpointStore
from brain_content.object_store import ObjectNotFoundError
from brain_content.validation import VerifiedBundle
from brain_extraction.graph_interpretation import GraphInterpretationService
from brain_extraction.profiles import load_profile
from brain_extraction.vllm_graph_client import VllmGraphClient
from brain_interpretation.parsed_content import ParseResult
from brain_interpretation.result import InterpretationResult
from brain_jobs.queue import DocumentJobQueue, JobLease, LeaseLost
from docling_core.types.doc import DoclingDocument
from pydantic import BaseModel, ConfigDict, Field

from brain_ingestion.content_workflow import ContentPublisher, load_or_convert_content


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
    ) -> None:
        self.queue, self.store = queue, store
        self.authorize_for_job = authorize_for_job
        self.client_factory = client_factory
        self.publish_content = publish_content
        self.converter = converter
        self.load_accepted, self.v2_writer_enabled = load_accepted, v2_writer_enabled

    def run_one(self) -> bool:
        lease = self.queue.claim()
        if lease is None:
            return False
        cancelled, stop = Event(), Event()

        def heartbeat() -> None:
            while not stop.wait(self.queue.lease_seconds / 3):
                try:
                    self.queue.heartbeat(lease)
                except Exception:
                    cancelled.set()
                    return

        thread = Thread(target=heartbeat, daemon=True)
        thread.start()
        try:
            self._execute(lease, cancelled)
        except LeaseLost:
            cancelled.set()
        except Exception:
            # Job history contains stable state transitions, not source or SDK errors.
            with suppress(LeaseLost):
                self.queue.retry(lease)
        finally:
            stop.set()
            thread.join(timeout=self.queue.lease_seconds)
        return True

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
        )
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
        try:
            result = GraphInterpretationService(self.store, authorize).interpret(
                tenant_id=lease.tenant_id,
                knowledge_base_id=lease.knowledge_base_id,
                artifact_id=key.artifact_id,
                run_id=run_id,
                profile=profile,
                client=client,
                publish=lambda operation: self.queue.publish(lease, operation),
                artifact_key=key,
                output_contract_version=2,
            )
        finally:
            client.close()
        if result.status == "failed":
            self.queue.retry(lease)
        else:
            self.queue.finish(
                lease, f"runs/{lease.tenant_id}/{lease.knowledge_base_id}/{run_id}/manifest.json"
            )
