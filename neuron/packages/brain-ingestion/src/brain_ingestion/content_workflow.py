"""Resolve/recover/publish content inside the existing document job lifecycle."""

from __future__ import annotations

import hashlib
import tempfile
from collections.abc import Callable, Mapping
from importlib.metadata import version
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Literal, Protocol
from uuid import UUID

from brain_content.checkpoints import CheckpointStore
from brain_content.identities import ParserMigrationRequired, fallback_key
from brain_content.manifest import Manifest, ParserExecutionV2
from brain_content.object_store import ObjectNotFoundError
from brain_content.validation import ArtifactKey, VerifiedBundle
from brain_extraction.docling_graph_pipeline import DoclingGraphPipelineAdapter
from brain_extraction.profiles import ExtractionProfile
from brain_extraction.vllm_graph_client import VllmGraphClient
from brain_interpretation.parsed_content import ParseResult
from brain_jobs.queue import JobLease
from docling_core.types.doc import DoclingDocument

from brain_ingestion.bundle_writer import _environment_digest, build_bundle
from brain_ingestion.content_projection import (
    PROJECTION_VERSION,
    OriginUnavailable,
    build_bundle_v2,
)
from brain_ingestion.conversion_recipe import physical_recipe
from brain_ingestion.docling_adapter import DoclingAdapter

if TYPE_CHECKING:
    from brain_ingestion.document_worker import DocumentTask


class ContentPublisher(Protocol):
    def __call__(
        self,
        lease: JobLease,
        manifest: Manifest,
        files: Mapping[str, bytes],
        *,
        writer_fallback_reason: Literal["ORIGIN_UNAVAILABLE"] | None = None,
        unattributed_item_count: int = 0,
    ) -> Manifest: ...


def load_or_convert_content(
    *,
    lease: JobLease,
    task: DocumentTask,
    store: CheckpointStore,
    authorize: Callable[[UUID, UUID, UUID, str], None],
    publisher: ContentPublisher,
    load_accepted: Callable[[JobLease], VerifiedBundle | None] | None,
    converter: Callable[[Path], ParseResult[DoclingDocument]] | None,
    client_factory: Callable[[Event], VllmGraphClient],
    cancelled: Event,
    profile: ExtractionProfile,
    v2_writer_enabled: bool,
) -> VerifiedBundle:
    accepted = load_accepted(lease) if load_accepted else None
    if accepted is not None:
        authorize(lease.tenant_id, lease.knowledge_base_id, accepted.key.artifact_id, "ingest")
        authorize(lease.tenant_id, lease.knowledge_base_id, accepted.key.artifact_id, "interpret")
        return accepted
    preferred = ArtifactKey(
        lease.artifact_id, lease.tenant_id, lease.knowledge_base_id, task.content_contract_version
    )
    candidates = [preferred]
    if task.content_contract_version == 2:
        candidates.append(fallback_key(task.version_id, lease.tenant_id, lease.knowledge_base_id))
    for key in candidates:
        authorize(lease.tenant_id, lease.knowledge_base_id, key.artifact_id, "ingest")
        authorize(lease.tenant_id, lease.knowledge_base_id, key.artifact_id, "interpret")
        try:
            retained = store.load_verified(key)
        except ObjectNotFoundError:
            # Only an absent completion marker is a recoverable miss. Corrupt
            # accepted bytes never cause another key lookup or conversion.
            continue
        publisher(lease, retained.manifest, retained.files)
        return store.load_verified(key)
    if task.content_contract_version == 2 and not v2_writer_enabled:
        raise ParserMigrationRequired("v2 publication is disabled for new sources")
    if converter is None and physical_recipe(task.content_contract_version) != task.recipe_sha256:
        raise ParserMigrationRequired("queued physical recipe differs from the installed parser")
    source_key = f"sources/{lease.tenant_id}/{lease.knowledge_base_id}/{task.source_sha256}.pdf"
    source_bytes = store.objects.read(source_key)
    if hashlib.sha256(source_bytes).hexdigest() != task.source_sha256:
        raise ValueError("source hash mismatch")
    convert = (
        converter or DoclingAdapter(capture_provenance=task.content_contract_version == 2).parse
    )
    published: VerifiedBundle | None = None

    def publish(parsed: ParseResult[DoclingDocument]) -> None:
        nonlocal published
        if (
            parsed.status == "failed"
            or parsed.page_count < 1
            or not (parsed.document.texts or parsed.document.tables)
        ):
            raise ValueError("CONTENT_CONTRACT_INVALID")
        reason: Literal["ORIGIN_UNAVAILABLE"] | None = None
        count = 0
        target = preferred
        manifest: Manifest
        if task.content_contract_version == 2:
            try:
                manifest, files = build_bundle_v2(
                    parsed,
                    tenant_id=lease.tenant_id,
                    knowledge_base_id=lease.knowledge_base_id,
                    document_id=task.document_id,
                    version_id=task.version_id,
                    artifact_id=preferred.artifact_id,
                    source_bytes=source_bytes,
                    recipe_sha256=task.recipe_sha256,
                    execution=ParserExecutionV2(
                        parser_name="docling",
                        parser_package_version=f"docling=={version('docling')}",
                        projection_version=PROJECTION_VERSION,
                        configuration_hash=task.recipe_sha256,
                        model_artifact_digests=[],
                        environment_digest=_environment_digest(),
                    ),
                    provenance=parsed.provenance,
                    retained_assets={},
                )
            except OriginUnavailable as exc:
                reason, count = "ORIGIN_UNAVAILABLE", len(exc.references)
                target = fallback_key(task.version_id, lease.tenant_id, lease.knowledge_base_id)
                manifest, files = build_bundle(
                    parsed,
                    tenant_id=lease.tenant_id,
                    knowledge_base_id=lease.knowledge_base_id,
                    document_id=task.document_id,
                    version_id=task.version_id,
                    artifact_id=target.artifact_id,
                    source_sha256=task.source_sha256,
                    configuration_hash=task.recipe_sha256,
                    source_bytes=source_bytes,
                    source_filename="source.pdf",
                )
        else:
            manifest, files = build_bundle(
                parsed,
                tenant_id=lease.tenant_id,
                knowledge_base_id=lease.knowledge_base_id,
                document_id=task.document_id,
                version_id=task.version_id,
                artifact_id=target.artifact_id,
                source_sha256=task.source_sha256,
                configuration_hash=task.recipe_sha256,
                source_bytes=source_bytes,
                source_filename="source.pdf",
            )
        authorize(lease.tenant_id, lease.knowledge_base_id, target.artifact_id, "ingest")
        publisher(
            lease, manifest, files, writer_fallback_reason=reason, unattributed_item_count=count
        )
        published = store.load_verified(target)

    client = client_factory(cancelled)
    try:
        with tempfile.TemporaryDirectory(prefix="nebula-source-") as directory:
            path = Path(directory) / "source.pdf"
            path.write_bytes(source_bytes)
            DoclingGraphPipelineAdapter(llm_client=client, model_id=client.model).run(
                source=path,
                template=profile.template,
                converter=convert,
                publish=publish,
                conversion_only=True,
            )
    finally:
        client.close()
    if published is None:
        raise RuntimeError("conversion did not publish a verified checkpoint")
    return published
