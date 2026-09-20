"""Explicitly enabled candidate worker; credentials are read only from the environment."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
from importlib.metadata import version
from pathlib import Path
from threading import BoundedSemaphore, Event
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from brain_content.checkpoints import CheckpointStore
from brain_content.config import load_local_object_store_config
from brain_content.object_store import LocalFilesystemObjectStore, ObjectAlreadyExistsError
from brain_extraction.profiles import load_profile
from brain_extraction.vllm_graph_client import VllmGraphClient, cached_model_token_counter
from brain_jobs.queue import DocumentJobQueue, JobLease
from brain_worker.document_delivery import (
    DocumentJobAuthorization,
    DocumentResultImporter,
    register_document_artifact,
)
from sqlalchemy import create_engine

from brain_ingestion.document_worker import DocumentTask, DocumentWorker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy-dir", type=Path, required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--import-only", action="store_true")
    parser.add_argument("--enqueue", type=Path, help="Trusted operator submission of one PDF")
    parser.add_argument("--tenant", type=UUID)
    parser.add_argument("--knowledge-base", type=UUID)
    parser.add_argument("--profile", default="gl-limits-a")
    args = parser.parse_args()
    if os.environ.get("BRAIN_ENABLE_GRAPH_CANDIDATE") != "1":
        parser.error(
            "candidate activation requires BRAIN_ENABLE_GRAPH_CANDIDATE=1; ADR-0060 is Proposed"
        )
    database = os.environ["BRAIN_WORKER_DATABASE_URL"]
    if not database.startswith("postgresql+psycopg://"):
        parser.error("worker requires a postgresql+psycopg database URL")
    engine = create_engine(database, pool_pre_ping=True)
    config = load_local_object_store_config()
    if not config.immutable:
        parser.error("candidate ingestion requires immutable object storage")
    store = CheckpointStore(LocalFilesystemObjectStore(config))
    authorization = DocumentJobAuthorization(
        engine, args.policy_dir / "model.conf", args.policy_dir / "policy.csv"
    )
    queue = DocumentJobQueue(engine)
    importer = DocumentResultImporter(engine, store, authorization.for_job)
    try:
        if args.enqueue:
            if not args.tenant or not args.knowledge_base or args.enqueue.suffix.lower() != ".pdf":
                parser.error("enqueue requires a PDF, --tenant, and --knowledge-base")
            actor = UUID(os.environ["BRAIN_WORKER_PRINCIPAL_ID"])
            profile = load_profile(args.profile)
            # Version the effective physical recipe independently of the extraction profile.
            recipe = hashlib.sha256(
                json.dumps(
                    {"adapter": "docling-default-pdf-v1", "docling": version("docling")},
                    sort_keys=True,
                ).encode()
            ).hexdigest()
            source = args.enqueue.read_bytes()
            source_sha = hashlib.sha256(source).hexdigest()
            document_id = uuid5(
                NAMESPACE_URL, f"nebula:{args.tenant}:{args.knowledge_base}:{source_sha}"
            )
            version_id = uuid5(document_id, recipe)
            artifact_id = uuid5(version_id, "content")
            task = DocumentTask(
                document_id=document_id,
                version_id=version_id,
                source_sha256=source_sha,
                recipe_sha256=recipe,
                profile_id=profile.profile_id,
                profile_version=profile.profile_version,
                schema_sha256=profile.schema_sha256,
                actor_id=actor,
                correlation_id=uuid4(),
            )
            lease = JobLease(
                uuid4(),
                args.tenant,
                args.knowledge_base,
                artifact_id,
                0,
                0,
                task.model_dump(mode="json"),
            )
            authorization.for_job(lease)(args.tenant, args.knowledge_base, artifact_id, "ingest")
            authorization.for_job(lease)(args.tenant, args.knowledge_base, artifact_id, "interpret")
            source_key = f"sources/{args.tenant}/{args.knowledge_base}/{source_sha}.pdf"
            try:
                store.objects.create_exclusive(source_key, source)
            except ObjectAlreadyExistsError:
                if store.objects.read(source_key) != source:
                    raise ValueError("retained source conflict") from None
            # Stable actor/correlation identity permits identical operator retries.
            request_key = hashlib.sha256(
                f"{artifact_id}:{actor}:{profile.profile_id}:{profile.profile_version}:{profile.schema_sha256}".encode()
            ).hexdigest()
            task.correlation_id = uuid5(artifact_id, request_key)
            print(
                queue.enqueue(
                    tenant_id=args.tenant,
                    knowledge_base_id=args.knowledge_base,
                    artifact_id=artifact_id,
                    request_key=request_key,
                    payload=task.model_dump(mode="json"),
                )
            )
            return 0
        stop = Event()
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda *_: stop.set())
        worker = None
        if not args.import_only:
            model = os.environ["BRAIN_INFERENCE_MODEL"]
            revision = os.environ["BRAIN_INFERENCE_MODEL_REVISION"]
            key = os.environ["BRAIN_INFERENCE_API_KEY"]
            endpoint = os.environ["BRAIN_INFERENCE_BASE_URL"]
            counter = cached_model_token_counter(model, revision)
            slots = BoundedSemaphore(1)

            def client_factory(cancelled: Event) -> VllmGraphClient:
                return VllmGraphClient(
                    base_url=endpoint,
                    api_key=key,
                    model_id=model,
                    model_revision=revision,
                    token_counter=counter,
                    slots=slots,
                    cancelled=cancelled,
                )

            worker = DocumentWorker(
                queue=queue,
                store=store,
                authorize_for_job=authorization.for_job,
                client_factory=client_factory,
                record_artifact=register_document_artifact,
            )
        # One process / one document / one model request at a time. Deployment must
        # cap replicas; this semaphore is intentionally not a distributed GPU quota.
        while not stop.is_set():
            worked = worker.run_one() if worker is not None else False
            imported = importer.run_one()
            if args.once:
                break
            if not worked and not imported:
                stop.wait(1)
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        # SDK/DB exceptions may contain credentials or source text.
        raise SystemExit(f"document_worker_failed:{type(exc).__name__}") from None
