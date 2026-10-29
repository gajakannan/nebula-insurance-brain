"""Document worker CLI; credentials are read only from the environment.

New submissions pin `extraction.pipeline` from the committed configuration
(`direct-baseline` until F0005's recorded acceptance). Processing acquires the
host inference guard before any queue claim, conversion or model request.
"""

from __future__ import annotations

import argparse
import os
import signal
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from threading import BoundedSemaphore, Event
from uuid import UUID

import yaml  # type: ignore[import-untyped]
from brain_content.checkpoints import CheckpointStore
from brain_content.config import (
    ConfigError,
    _find_config_file,
    load_content_writer_config,
    load_extraction_config,
    load_job_queue_config,
    load_local_object_store_config,
)
from brain_content.object_store import LocalFilesystemObjectStore
from brain_extraction.vllm_graph_client import (
    DEFAULT_LIMITS,
    InferenceLimits,
    VllmGraphClient,
    cached_model_token_counter,
)
from brain_jobs.queue import DocumentJobQueue, QueueFull
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_worker.content_access import SourceContentAccess
from brain_worker.content_publication import AuthorizedContentPublisher
from brain_worker.document_delivery import (
    DocumentJobAuthorization,
    DocumentResultImporter,
)
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from brain_ingestion.conversion_process import SupervisedConverter
from brain_ingestion.document_worker import DocumentWorker, WorkerStopped
from brain_ingestion.submission import enqueue_document
from brain_ingestion.worker_guard import GuardError, HostInferenceGuard, load_provider

# The host guard directory is fixed by the account UID; configuration cannot move it.
_FORBIDDEN_CONFIG_KEYS = ("inference_guard", "guard_directory", "inference_guard_directory")


@dataclass
class Composition:
    queue: DocumentJobQueue
    store: CheckpointStore
    authorization: DocumentJobAuthorization
    access: SourceContentAccess
    publication: AuthorizedContentPublisher
    importer: DocumentResultImporter


def compose(engine: Engine, policy_dir: Path) -> Composition:
    config = load_local_object_store_config()
    if not config.immutable:
        raise ConfigError("document ingestion requires immutable object storage")
    store = CheckpointStore(LocalFilesystemObjectStore(config))
    authorization = DocumentJobAuthorization(
        engine, policy_dir / "model.conf", policy_dir / "policy.csv"
    )
    queue = DocumentJobQueue(engine, max_depth=load_job_queue_config().max_queue_depth)
    publication = AuthorizedContentPublisher(
        queue,
        store.verified,
        CasbinAuthorizationAdapter(policy_dir / "model.conf", policy_dir / "policy.csv"),
        objects=store.objects,
    )
    access = SourceContentAccess(engine, store.verified, publication.policy)
    importer = DocumentResultImporter(
        engine, store, authorization.for_job, read_artifact=access.read
    )
    return Composition(queue, store, authorization, access, publication, importer)


def reject_guard_override() -> None:
    override = os.environ.get("BRAIN_LOCAL_CONFIG_PATH")
    path = Path(override) if override else _find_config_file(Path.cwd())
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if any(key in data for key in _FORBIDDEN_CONFIG_KEYS):
        raise ConfigError("the inference guard directory cannot be configured")


def processing_worker(
    parts: Composition,
    *,
    provider_url: str,
    api_key: str,
    model: str,
    revision: str,
    guard: HostInferenceGuard,
    transport_url: str | None = None,
    limits: InferenceLimits | None = None,
    supervisor: SupervisedConverter | None = None,
    observe: Callable[[dict[str, object]], None] | None = None,
) -> DocumentWorker:
    """Compose one guarded processing worker; the caller has acquired `guard`.

    `transport_url` exists only for the test-only fault proxy that forwards this
    owner's requests; the guard key is always the recorded provider identity.
    """
    if not guard.held:
        raise GuardError("inference_guard_not_held")
    guard.require_quiescent()
    load_provider(guard)  # allowlist: only the preflight-recorded dedicated provider
    supervisor = supervisor or SupervisedConverter(guard.staging_root)
    supervisor.reap_orphans()
    counter = cached_model_token_counter(model, revision)
    slots = BoundedSemaphore(1)

    def client_factory(cancelled: Event) -> VllmGraphClient:
        return VllmGraphClient(
            base_url=transport_url or provider_url,
            api_key=api_key,
            model_id=model,
            model_revision=revision,
            token_counter=counter,
            slots=slots,
            cancelled=cancelled,
            dispatch_guard=guard.inflight,
            limits=limits or DEFAULT_LIMITS,
        )

    return DocumentWorker(
        queue=parts.queue,
        store=parts.store,
        authorize_for_job=parts.authorization.for_job,
        client_factory=client_factory,
        publish_content=parts.publication.publish_manifest,
        load_accepted=parts.access.resolve,
        v2_writer_enabled=load_content_writer_config().v2_writer_enabled,
        supervisor=supervisor,
        guard=guard,
        observe=observe,
    )


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
    # Unknown pipeline values fail startup; there is no environment override.
    extraction = load_extraction_config()
    reject_guard_override()
    database = os.environ["BRAIN_WORKER_DATABASE_URL"]
    if not database.startswith("postgresql+psycopg://"):
        parser.error("worker requires a postgresql+psycopg database URL")
    engine = create_engine(database, pool_pre_ping=True)
    guard: HostInferenceGuard | None = None
    try:
        parts = compose(engine, args.policy_dir)
        if args.enqueue:
            if not args.tenant or not args.knowledge_base or args.enqueue.suffix.lower() != ".pdf":
                parser.error("enqueue requires a PDF, --tenant, and --knowledge-base")
            if not args.classification:
                parser.error("enqueue requires at least one --classification")
            actor = UUID(os.environ["BRAIN_WORKER_PRINCIPAL_ID"])
            try:
                job = enqueue_document(
                    engine,
                    parts.queue,
                    parts.store,
                    parts.authorization,
                    parts.access,
                    source_path=args.enqueue,
                    tenant_id=args.tenant,
                    knowledge_base_id=args.knowledge_base,
                    actor_id=actor,
                    profile_id=args.profile,
                    classifications=args.classification,
                    source_acl_ids=args.source_acl,
                    v2_writer_enabled=load_content_writer_config().v2_writer_enabled,
                    pipeline=extraction.pipeline,
                )
            except QueueFull as exc:
                print(exc.code)
                return 4
            print(job)
            return 0
        stop = Event()
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda *_: stop.set())
        worker = None
        if not args.import_only:
            endpoint = os.environ["BRAIN_INFERENCE_BASE_URL"]
            guard = HostInferenceGuard(endpoint)
            try:
                # Before the first claim, conversion, coupled import or inference call.
                guard.acquire()
                worker = processing_worker(
                    parts,
                    provider_url=endpoint,
                    api_key=os.environ["BRAIN_INFERENCE_API_KEY"],
                    model=os.environ["BRAIN_INFERENCE_MODEL"],
                    revision=os.environ["BRAIN_INFERENCE_MODEL_REVISION"],
                    guard=guard,
                )
            except GuardError as exc:
                print(exc.code)
                return 2
        # One host worker / one document / one model request at a time.
        while not stop.is_set():
            try:
                worked = worker.run_one() if worker is not None else False
            except WorkerStopped as exc:
                print(exc.code)
                return 3
            imported = parts.importer.run_one()
            if args.once:
                break
            if not worked and not imported:
                stop.wait(1)
        return 0
    finally:
        if guard is not None:
            guard.release()
        engine.dispose()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        # SDK/DB exceptions may contain credentials or source text.
        raise SystemExit(f"document_worker_failed:{type(exc).__name__}") from None
