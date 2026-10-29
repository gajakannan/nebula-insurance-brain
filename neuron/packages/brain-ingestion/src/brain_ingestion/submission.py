"""Trusted enqueue: reuse accepted or pending physical identity before conversion."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from brain_content.checkpoints import CheckpointStore
from brain_content.identities import ParserMigrationRequired, fallback_key, new_source_identity
from brain_content.object_store import ObjectAlreadyExistsError
from brain_domain.authx import ResourceKey, ResourceType
from brain_extraction.graph_interpretation import PIPELINES
from brain_extraction.profiles import load_profile
from brain_jobs.queue import DocumentJobQueue, JobLease, QueueFull, jobs
from brain_persistence.content_repository import ContentArtifactRepository
from brain_persistence.models import ResourceAccessRow
from brain_persistence.tenancy import provision_resource_access
from brain_worker.content_access import SourceContentAccess
from brain_worker.content_submissions import source_submission
from brain_worker.document_delivery import DocumentJobAuthorization
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from brain_ingestion.conversion_recipe import physical_recipe
from brain_ingestion.document_worker import DocumentTask


def enqueue_document(
    engine: Engine,
    queue: DocumentJobQueue,
    store: CheckpointStore,
    authorization: DocumentJobAuthorization,
    access: SourceContentAccess,
    *,
    source_path: Path,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    actor_id: UUID,
    profile_id: str,
    classifications: list[str],
    source_acl_ids: list[str],
    v2_writer_enabled: bool,
    pipeline: str,
) -> UUID:
    if pipeline not in PIPELINES:
        raise ValueError("unknown extraction pipeline")
    source_bytes = source_path.read_bytes()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    profile = load_profile(profile_id)
    with source_submission(engine, tenant_id, knowledge_base_id, source_sha):
        with Session(engine) as session:
            repository = ContentArtifactRepository(session)
            source = repository.find_source(tenant_id, knowledge_base_id, source_sha)
            pending = (
                session.execute(
                    select(jobs)
                    .where(
                        jobs.c.tenant_id == str(tenant_id),
                        jobs.c.knowledge_base_id == str(knowledge_base_id),
                        jobs.c.payload["source_sha256"].as_string() == source_sha,
                    )
                    .order_by(jobs.c.available_at, jobs.c.id)
                )
                .mappings()
                .all()
            )
        existing = False
        if source is not None and source[1]:
            if len(source[1]) != 1:
                raise ParserMigrationRequired("source has ambiguous accepted artifacts")
            key = source[1][0]
            probe = JobLease(
                uuid4(),
                tenant_id,
                knowledge_base_id,
                key.artifact_id,
                0,
                0,
                {
                    "actor_id": str(actor_id),
                    "correlation_id": str(uuid4()),
                    "source_sha256": source_sha,
                },
            )
            retained = access.read(probe, key.artifact_id)
            document_id, version_id = retained.manifest.document_id, retained.manifest.version_id
            recipe = getattr(
                retained.manifest, "recipe_sha256", retained.manifest.execution.configuration_hash
            )
            contract = key.contract_version
            existing = True
        elif pending:
            tasks = [DocumentTask.model_validate(row["payload"]) for row in pending]
            identities = {
                (
                    task.document_id,
                    task.version_id,
                    task.recipe_sha256,
                    task.content_contract_version,
                    UUID(row["artifact_id"]),
                )
                for task, row in zip(tasks, pending, strict=True)
            }
            if len(identities) != 1:
                raise ParserMigrationRequired("pending source has conflicting physical identities")
            document_id, version_id, recipe, contract, artifact_id = identities.pop()
            from brain_content.validation import ArtifactKey

            key = ArtifactKey(artifact_id, tenant_id, knowledge_base_id, contract)
            existing = True
        else:
            document_id = (
                source[0]
                if source
                else uuid5(NAMESPACE_URL, f"nebula:{tenant_id}:{knowledge_base_id}:{source_sha}")
            )
            contract = 2 if v2_writer_enabled else 1
            recipe = physical_recipe(contract)
            identity = new_source_identity(
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                document_id=document_id,
                source_sha256=source_sha,
                recipe_sha256=recipe,
                contract_version=contract,
            )
            version_id, key = identity.version_id, identity.key
        task = DocumentTask(
            document_id=document_id,
            version_id=version_id,
            source_sha256=source_sha,
            recipe_sha256=recipe,
            content_contract_version=contract,
            profile_id=profile.profile_id,
            profile_version=profile.profile_version,
            schema_sha256=profile.schema_sha256,
            actor_id=actor_id,
            correlation_id=uuid4(),
            pipeline=pipeline,
        )
        # The selected pipeline is part of identity: a different engine over the same
        # immutable artifact is a different job/run, not a conflicting payload.
        request_key = hashlib.sha256(
            f"{key.artifact_id}:{actor_id}:{profile.profile_id}:{profile.profile_version}:{profile.schema_sha256}:{pipeline}".encode()
        ).hexdigest()
        task.correlation_id = uuid5(key.artifact_id, request_key)
        # Refuse new work beyond the queue bound before provisioning security
        # metadata or storing source bytes. The queue's locked check stays
        # authoritative for concurrent submitters; duplicates remain idempotent.
        if queue.max_depth is not None and queue.depth() >= queue.max_depth:
            with Session(engine) as session:
                duplicate = session.execute(
                    select(jobs.c.id).where(
                        jobs.c.tenant_id == str(tenant_id),
                        jobs.c.knowledge_base_id == str(knowledge_base_id),
                        jobs.c.request_key == request_key,
                    )
                ).first()
            if duplicate is None:
                raise QueueFull()
        payload = task.model_dump(mode="json", exclude_defaults=True)
        lease = JobLease(uuid4(), tenant_id, knowledge_base_id, key.artifact_id, 0, 0, payload)
        resources = [key]
        # Accepted v2 content needs no fallback provisioning or conversion. An
        # unaccepted v2 submission reserves both deterministic resource scopes.
        if contract == 2 and not (source and source[1]):
            resources.append(fallback_key(version_id, tenant_id, knowledge_base_id))
        with Session(engine) as session, session.begin():
            for resource in resources:
                prior = session.get(ResourceAccessRow, ("content_artifact", resource.artifact_id))
                if existing:
                    if prior is None or (prior.tenant_id, prior.knowledge_base_id) != (
                        tenant_id,
                        knowledge_base_id,
                    ):
                        raise PermissionError("retained source security metadata is unavailable")
                    if set(prior.classifications) != set(classifications) or set(
                        prior.source_acl_ids
                    ) != set(source_acl_ids):
                        raise PermissionError(
                            "retained source restrictions require governed change"
                        )
                else:
                    provision_resource_access(
                        session,
                        ResourceKey(ResourceType.CONTENT_ARTIFACT, resource.artifact_id),
                        tenant_id=tenant_id,
                        knowledge_base_id=knowledge_base_id,
                        classifications=classifications,
                        source_acl_ids=source_acl_ids,
                        actor_id=actor_id,
                        at=datetime.now(UTC),
                        allow_before_record=True,
                    )
        for resource in resources:
            authorize = authorization.for_job(lease)
            authorize(tenant_id, knowledge_base_id, resource.artifact_id, "ingest")
            authorize(tenant_id, knowledge_base_id, resource.artifact_id, "interpret")
        source_key = f"sources/{tenant_id}/{knowledge_base_id}/{source_sha}.pdf"
        try:
            store.objects.create_exclusive(source_key, source_bytes)
        except ObjectAlreadyExistsError:
            if store.objects.read(source_key) != source_bytes:
                raise ValueError("retained source conflict") from None
        # Preserve the byte shape of an existing legacy task when its normalized
        # command is identical; the generic queue keeps strict payload comparison.
        with Session(engine) as session:
            prior = session.execute(
                select(jobs.c.payload).where(
                    jobs.c.tenant_id == str(tenant_id),
                    jobs.c.knowledge_base_id == str(knowledge_base_id),
                    jobs.c.request_key == request_key,
                )
            ).scalar_one_or_none()
        if prior is not None and DocumentTask.model_validate(prior) == task:
            payload = prior
        return queue.enqueue(
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
            artifact_id=key.artifact_id,
            request_key=request_key,
            payload=payload,
        )
