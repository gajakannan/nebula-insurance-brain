#!/usr/bin/env python3
"""Seed one realistic row of S0003/S0004/S0005 data so the backup/restore drill
(F0001-S0006) has something real to back up and verify — a content bundle with
citations, a review decision, and a committed bitemporal fact. Run against the
live compose Postgres and the local content root (`config/local.yaml`).

This does not replace S0003's actual parse-once proof (real Docling/vLLM) or
S0004's actual Review Panel round trip — it constructs the same *shapes* those
stories produce, directly, so the restore drill's citation check
(`scripts/ops/verify_citations.py`) has real bundle files and DB rows to
compare, without re-running live inference for what is fundamentally an
infrastructure proof (does backup/restore preserve what's there).

Usage (from the repo root, so `config/local.yaml` resolves):
    uv run --directory engine python3 ../scripts/dev/seed_restore_drill_fixture.py
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from brain_content.config import load_local_object_store_config
from brain_content.manifest import (
    ArtifactFile,
    ArtifactManifest,
    DoclingDocumentRef,
    ExecutionRecord,
    ExtractionQuality,
)
from brain_content.object_store import LocalFilesystemObjectStore
from brain_content.store import LocalContentArtifactStore
from brain_domain.facts import ChangeReason, CommitProposal
from brain_domain.principal import Membership, Principal, PrincipalKind, PrincipalStatus
from brain_persistence.models import (
    Assertion,
    AssertionEvidence,
    ContentArtifact,
    DocumentVersion,
    FactSlotRow,
    MembershipRow,
    PrincipalRow,
    ReviewBatchRow,
    ReviewDecisionRow,
    ReviewItemRow,
    SourceDocument,
)
from brain_persistence.repositories import SqlAlchemyFactCommitRepository
from brain_persistence.session import make_engine, make_session_factory
from brain_security.audit import InMemoryAuditEventRepository, RepositoryAuditSink
from brain_security.authorization import AuthorizationService
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_temporal.commit import CanonicalCommitService

ISSUER = "https://authentik.local/application/o/brain/"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    database_url = os.environ.get(
        "BRAIN_DATABASE_URL", "postgresql+asyncpg://brain:brain@localhost:5432/brain"
    )
    engine = make_engine(database_url)
    session_factory = make_session_factory(engine)

    tenant_id, kb_id = uuid4(), uuid4()
    document_id, version_id, artifact_id = uuid4(), uuid4(), uuid4()

    blocks = [
        {
            "block_id": "text-0",
            "page": 1,
            "text": "General Aggregate Limit: $2,000,000",
            "bbox": {"l": 72.0, "t": 100.0, "r": 400.0, "b": 120.0, "page": 1},
            "char_start": 0,
            "char_end": 35,
        }
    ]
    layout = [{"page": 1, "width": 612.0, "height": 792.0}]
    docling_document_bytes = json.dumps(
        {"schema_name": "DoclingDocument", "version": "1.0.0"}
    ).encode()
    files = {
        "docling-document.json": docling_document_bytes,
        "normalized.md": b"# GL Policy Declarations\n\nGeneral Aggregate Limit: $2,000,000\n",
        "blocks.jsonl": ("\n".join(json.dumps(b) for b in blocks) + "\n").encode(),
        "tables.jsonl": b"",
        "layout.jsonl": ("\n".join(json.dumps(entry) for entry in layout) + "\n").encode(),
    }
    artifact_files = [
        ArtifactFile(path=path, sha256=_sha256(data), size_bytes=len(data))
        for path, data in sorted(files.items())
    ]
    artifact_sha256 = _sha256(
        "".join(f.sha256 for f in sorted(artifact_files, key=lambda f: f.path)).encode()
    )
    manifest = ArtifactManifest(
        artifact_contract_version=1,
        tenant_id=tenant_id,
        knowledge_base_id=kb_id,
        document_id=document_id,
        version_id=version_id,
        artifact_id=artifact_id,
        source_sha256=_sha256(b"synthetic restore-drill fixture source"),
        artifact_sha256=artifact_sha256,
        docling_document=DoclingDocumentRef(
            path="docling-document.json",
            schema_version="1.0.0",
            sha256=_sha256(docling_document_bytes),
        ),
        files=artifact_files,
        execution=ExecutionRecord(
            parser_package_version="restore-drill-fixture",
            model_artifact_digests=[],
            configuration_hash="n/a",
            environment_digest="n/a",
        ),
        extraction_quality=ExtractionQuality(status="complete", failed_pages=[], warnings=[]),
        page_count=1,
        created_at=datetime.now(UTC),
    )

    os.chdir(repo_root)  # so load_local_object_store_config() finds config/local.yaml
    content_store = LocalContentArtifactStore(
        LocalFilesystemObjectStore(load_local_object_store_config())
    )
    await content_store.put_bundle(manifest, files)

    async with session_factory() as session:
        source = SourceDocument(
            id=document_id,
            tenant_id=tenant_id,
            knowledge_base_id=kb_id,
            source_sha256=manifest.source_sha256,
        )
        session.add(source)
        await session.flush()
        version = DocumentVersion(id=version_id, source_document_id=source.id)
        session.add(version)
        await session.flush()
        artifact = ContentArtifact(
            id=artifact_id,
            document_version_id=version.id,
            artifact_sha256=artifact_sha256,
            page_count=1,
            extraction_status="complete",
        )
        session.add(artifact)
        await session.flush()

        assertion = Assertion(
            id=uuid4(),
            run_id=None,
            origin="MACHINE_EXTRACTION",
            subject_type="Policy",
            slot_type="general_aggregate_limit",
            value={"value": "$2,000,000"},
            model_confidence=0.92,
            interpretation_basis="EXPLICIT",
        )
        session.add(assertion)
        await session.flush()
        session.add(
            AssertionEvidence(
                assertion_id=assertion.id,
                artifact_id=artifact.id,
                block_id="text-0",
                page=1,
                bbox=blocks[0]["bbox"],
                char_start=0,
                char_end=35,
                precision="exact-span",
            )
        )
        session.add(
            AssertionEvidence(
                assertion_id=assertion.id,
                artifact_id=artifact.id,
                block_id=None,
                page=1,
                bbox=None,
                char_start=None,
                char_end=None,
                precision="page",
            )
        )
        await session.flush()

        reviewer = PrincipalRow(
            id=uuid4(),
            kind="user",
            issuer=ISSUER,
            subject="restore-drill-reviewer",
            status="active",
        )
        session.add(reviewer)
        await session.flush()
        session.add(
            MembershipRow(
                id=uuid4(),
                principal_id=reviewer.id,
                tenant_id=tenant_id,
                knowledge_base_id=kb_id,
                role="Reviewer",
                grant_revision=1,
                revoked_at=None,
            )
        )
        batch = ReviewBatchRow(id=uuid4(), assembling_principal_id=reviewer.id)
        session.add(batch)
        await session.flush()
        review_item = ReviewItemRow(
            id=uuid4(),
            type="LOW_CONFIDENCE_ASSERTION",
            status="decided",
            assertion_id=assertion.id,
            assertion_version=1,
            tenant_id=tenant_id,
            knowledge_base_id=kb_id,
            review_batch_id=batch.id,
        )
        session.add(review_item)
        await session.flush()
        session.add(
            ReviewDecisionRow(
                id=uuid4(),
                review_item_id=review_item.id,
                review_batch_id=batch.id,
                action="ACCEPT",
                reviewer_principal_id=reviewer.id,
                assertion_version=1,
                stale=False,
                event_sha256=_sha256(f"restore-drill-{review_item.id}".encode()),
            )
        )
        await session.commit()

    service_principal_subject = "restore-drill-service"
    async with session_factory() as session:
        service_principal = PrincipalRow(
            id=uuid4(),
            kind="service",
            issuer=ISSUER,
            subject=service_principal_subject,
            status="active",
        )
        session.add(service_principal)
        await session.flush()
        session.add(
            MembershipRow(
                id=uuid4(),
                principal_id=service_principal.id,
                tenant_id=tenant_id,
                knowledge_base_id=kb_id,
                role="ServicePrincipal",
                grant_revision=1,
                revoked_at=None,
            )
        )
        slot_id = uuid4()
        session.add(
            FactSlotRow(
                id=slot_id,
                entity_id=uuid4(),
                slot_type="general_aggregate_limit",
                tenant_id=tenant_id,
                knowledge_base_id=kb_id,
            )
        )
        await session.flush()
        service_principal_id = service_principal.id
        await session.commit()

    casbin_model = repo_root / "planning-mds" / "security" / "policies" / "model.conf"
    casbin_policy = repo_root / "planning-mds" / "security" / "policies" / "policy.csv"
    actor = Principal(
        id=service_principal_id,
        kind=PrincipalKind.SERVICE,
        issuer=ISSUER,
        subject=service_principal_subject,
        status=PrincipalStatus.ACTIVE,
    )
    membership = Membership(
        principal_id=service_principal_id,
        tenant_id=tenant_id,
        knowledge_base_id=kb_id,
        role="ServicePrincipal",
        grant_revision=1,
        revoked_at=None,
    )
    authz = AuthorizationService(
        CasbinAuthorizationAdapter(casbin_model, casbin_policy),
        RepositoryAuditSink(InMemoryAuditEventRepository()),
    )
    async with session_factory() as session:
        repository = SqlAlchemyFactCommitRepository(session)
        commit_service = CanonicalCommitService(repository, authz)
        result = await commit_service.commit(
            actor,
            [membership],
            CommitProposal(
                slot_id=slot_id,
                value={"amount": "2000000.00"},
                valid_from=datetime(2026, 1, 1, tzinfo=UTC),
                valid_to=None,
                change_reason=ChangeReason.SUPERSEDED,
                evidence_refs=(uuid4(),),
                review_decision_id=None,
                source_received_at=datetime(2026, 1, 10, tzinfo=UTC),
                artifact_created_at=datetime(2026, 1, 10, tzinfo=UTC),
                assertion_created_at=datetime(2026, 1, 10, tzinfo=UTC),
                expected_current_version_id=None,
                idempotency_key=f"restore-drill-{uuid4()}",
            ),
            trace_id="restore-drill-seed",
        )
        await session.commit()

    await engine.dispose()

    print("Restore-drill fixture seeded:")
    print(f"  tenant_id={tenant_id}")
    print(f"  knowledge_base_id={kb_id}")
    print(
        f"  content artifact_id={artifact_id} (bundle with 1 block-level + 1 page-level citation)"
    )
    print(f"  fact slot_id={slot_id}, commit_id={result.commit_id}")


if __name__ == "__main__":
    asyncio.run(main())
