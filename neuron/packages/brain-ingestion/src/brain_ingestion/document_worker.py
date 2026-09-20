"""Composition of engine-owned jobs, Graph activities, and artifact checkpoints."""

from __future__ import annotations

import hashlib
import tempfile
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from threading import Event, Thread
from uuid import UUID, uuid5

from brain_content.checkpoints import CheckpointStore
from brain_content.manifest import ArtifactManifest
from brain_content.object_store import ObjectNotFoundError
from brain_extraction.docling_graph_pipeline import DoclingGraphPipelineAdapter
from brain_extraction.graph_interpretation import GraphInterpretationService
from brain_extraction.profiles import load_profile
from brain_extraction.vllm_graph_client import VllmGraphClient
from brain_interpretation.parsed_content import ParseResult
from brain_interpretation.result import InterpretationResult
from brain_jobs.queue import DocumentJobQueue, JobLease, LeaseLost
from docling_core.types.doc import DoclingDocument
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.engine import Connection

from brain_ingestion.bundle_writer import build_bundle
from brain_ingestion.docling_adapter import DoclingAdapter


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


class DocumentWorker:
    def __init__(
        self,
        *,
        queue: DocumentJobQueue,
        store: CheckpointStore,
        authorize_for_job: Callable[[JobLease], Callable[[UUID, UUID, UUID, str], None]],
        client_factory: Callable[[Event], VllmGraphClient],
        record_artifact: Callable[[Connection, ArtifactManifest], None],
        converter: Callable[[Path], ParseResult[DoclingDocument]] | None = None,
    ) -> None:
        self.queue, self.store = queue, store
        self.authorize_for_job = authorize_for_job
        self.client_factory = client_factory
        self.record_artifact = record_artifact
        self.converter = converter

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
        try:
            manifest, _ = self.store.load(
                lease.artifact_id, lease.tenant_id, lease.knowledge_base_id
            )
        except ObjectNotFoundError:
            source_key = (
                f"sources/{lease.tenant_id}/{lease.knowledge_base_id}/{task.source_sha256}.pdf"
            )
            source_bytes = self.store.objects.read(source_key)
            if hashlib.sha256(source_bytes).hexdigest() != task.source_sha256:
                raise ValueError("source hash mismatch") from None
            converter = self.converter if self.converter is not None else DoclingAdapter().parse

            def publish(parsed: ParseResult[DoclingDocument]) -> None:
                manifest, files = build_bundle(
                    parsed,
                    tenant_id=lease.tenant_id,
                    knowledge_base_id=lease.knowledge_base_id,
                    document_id=task.document_id,
                    version_id=task.version_id,
                    artifact_id=lease.artifact_id,
                    source_sha256=task.source_sha256,
                    configuration_hash=task.recipe_sha256,
                    source_bytes=source_bytes,
                    source_filename="source.pdf",
                )
                authorize(lease.tenant_id, lease.knowledge_base_id, lease.artifact_id, "ingest")
                self.queue.publish(lease, lambda: self.store.publish(manifest, files))

            client = self.client_factory(cancelled)
            try:
                with tempfile.TemporaryDirectory(prefix="nebula-source-") as directory:
                    source = Path(directory) / "source.pdf"
                    source.write_bytes(source_bytes)
                    DoclingGraphPipelineAdapter(llm_client=client, model_id=client.model).run(
                        source=source,
                        template=profile.template,
                        converter=converter,
                        publish=publish,
                        conversion_only=True,
                    )
            finally:
                client.close()
            manifest, _ = self.store.load(
                lease.artifact_id, lease.tenant_id, lease.knowledge_base_id
            )
        if (
            manifest.source_sha256,
            manifest.version_id,
            manifest.document_id,
            manifest.execution.configuration_hash,
        ) != (task.source_sha256, task.version_id, task.document_id, task.recipe_sha256):
            raise ValueError("checkpoint belongs to a different source or conversion recipe")
        self.queue.publish_transaction(lease, lambda conn: self.record_artifact(conn, manifest))
        # Recover a successfully published prior attempt whose DB completion was
        # interrupted. Never pay for another model call to rediscover that result.
        for attempt in range(lease.attempt - 1, 0, -1):
            run_id = uuid5(lease.job_id, f"attempt:{attempt}")
            try:
                outputs = self.store.load_run(
                    tenant_id=lease.tenant_id,
                    knowledge_base_id=lease.knowledge_base_id,
                    artifact_id=lease.artifact_id,
                    run_id=run_id,
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
                lease.artifact_id,
                task.profile_id,
                task.profile_version,
                task.schema_sha256,
            ):
                raise ValueError("published run does not match the queued profile")
            if result.status != "failed":
                authorize(lease.tenant_id, lease.knowledge_base_id, lease.artifact_id, "interpret")
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
                artifact_id=lease.artifact_id,
                run_id=run_id,
                profile=profile,
                client=client,
                publish=lambda operation: self.queue.publish(lease, operation),
            )
        finally:
            client.close()
        if result.status == "failed":
            self.queue.retry(lease)
        else:
            self.queue.finish(
                lease, f"runs/{lease.tenant_id}/{lease.knowledge_base_id}/{run_id}/manifest.json"
            )
