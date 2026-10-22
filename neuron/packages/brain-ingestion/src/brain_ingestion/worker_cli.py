"""Explicitly enabled candidate worker; credentials are read only from the environment."""

from __future__ import annotations

import argparse
import os
import signal
from pathlib import Path
from threading import BoundedSemaphore, Event
from uuid import UUID

from brain_content.checkpoints import CheckpointStore
from brain_content.config import load_content_writer_config, load_local_object_store_config
from brain_content.object_store import LocalFilesystemObjectStore
from brain_extraction.vllm_graph_client import VllmGraphClient, cached_model_token_counter
from brain_jobs.queue import DocumentJobQueue
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_worker.content_access import SourceContentAccess
from brain_worker.content_publication import AuthorizedContentPublisher
from brain_worker.document_delivery import (
    DocumentJobAuthorization,
    DocumentResultImporter,
)
from sqlalchemy import create_engine

from brain_ingestion.document_worker import DocumentWorker
from brain_ingestion.submission import enqueue_document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy-dir", type=Path, required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--import-only", action="store_true")
    parser.add_argument("--enqueue", type=Path, help="Trusted operator submission of one PDF")
    parser.add_argument("--tenant", type=UUID)
    parser.add_argument("--knowledge-base", type=UUID)
    parser.add_argument("--profile", default="gl-limits-a")
    # F0002-S0004: the trusted submitter declares the artifact's restrictions; there
    # is no default label, and missing metadata denies every later job step.
    parser.add_argument("--classification", action="append", default=[])
    parser.add_argument("--source-acl", action="append", default=[])
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
    publication = AuthorizedContentPublisher(
        queue,
        store.verified,
        CasbinAuthorizationAdapter(args.policy_dir / "model.conf", args.policy_dir / "policy.csv"),
        objects=store.objects,
    )
    access = SourceContentAccess(engine, store.verified, publication.policy)
    writer_config = load_content_writer_config()
    importer = DocumentResultImporter(
        engine, store, authorization.for_job, read_artifact=access.read
    )
    try:
        if args.enqueue:
            if not args.tenant or not args.knowledge_base or args.enqueue.suffix.lower() != ".pdf":
                parser.error("enqueue requires a PDF, --tenant, and --knowledge-base")
            if not args.classification:
                parser.error("enqueue requires at least one --classification")
            actor = UUID(os.environ["BRAIN_WORKER_PRINCIPAL_ID"])
            print(
                enqueue_document(
                    engine,
                    queue,
                    store,
                    authorization,
                    access,
                    source_path=args.enqueue,
                    tenant_id=args.tenant,
                    knowledge_base_id=args.knowledge_base,
                    actor_id=actor,
                    profile_id=args.profile,
                    classifications=args.classification,
                    source_acl_ids=args.source_acl,
                    v2_writer_enabled=writer_config.v2_writer_enabled,
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
                publish_content=publication.publish_manifest,
                load_accepted=access.resolve,
                v2_writer_enabled=writer_config.v2_writer_enabled,
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
