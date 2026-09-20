"""Engine-owned authorization and transactional import of candidate Graph results.

The outbox is a delivery boundary, never an instruction to commit canonical facts.
Only fixed-template assertions are supported; unhandled entity/relationship output
fails closed instead of silently losing it.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from uuid import UUID, uuid4, uuid5

from brain_content.checkpoints import ArtifactIntegrityError, CheckpointStore
from brain_content.manifest import ArtifactManifest
from brain_contracts.result import InterpretationResult
from brain_jobs.queue import JobLease, jobs, leases, outbox
from brain_persistence.models import (
    Assertion,
    AssertionEvidence,
    AuditEventRow,
    ContentArtifact,
    DocumentVersion,
    MembershipRow,
    PrincipalRow,
    ReviewItemRow,
    SemanticInterpretationRun,
    SourceDocument,
)
from brain_review.evidence import evidence_binding_to_locator
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from sqlalchemy import func, select, update
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session

Authorizer = Callable[[UUID, UUID, UUID, str], None]


class DocumentJobAuthorization:
    """Re-read actor status, current grants, and policy at every sensitive boundary.

    Jobs are submitted by a trusted service, not with an unverified caller-supplied
    identity. Neither the service identity nor old membership snapshots are grants.
    Every decision commits its audit record, including denials.
    """

    def __init__(self, engine: Engine, model_path: Path, policy_path: Path) -> None:
        self.engine, self.model_path, self.policy_path = engine, model_path, policy_path

    def for_job(self, lease: JobLease) -> Authorizer:
        actor_id = UUID(lease.payload["actor_id"])
        trace_id = str(UUID(lease.payload["correlation_id"]))

        def authorize(tenant: UUID, kb: UUID, artifact: UUID, action: str) -> None:
            if (tenant, kb, artifact) != (
                lease.tenant_id,
                lease.knowledge_base_id,
                lease.artifact_id,
            ) or action not in {"ingest", "interpret"}:
                raise PermissionError("job authorization scope mismatch")
            enforcer = CasbinAuthorizationAdapter(self.model_path, self.policy_path)
            allowed, revision, reason = False, 0, "inactive_principal"
            with Session(self.engine) as session, session.begin():
                actor = session.get(PrincipalRow, actor_id)
                if actor is not None and actor.status == "active":
                    grants = session.scalars(
                        select(MembershipRow).where(
                            MembershipRow.principal_id == actor_id,
                            MembershipRow.tenant_id == tenant,
                            MembershipRow.knowledge_base_id == kb,
                            MembershipRow.revoked_at.is_(None),
                        )
                    ).all()
                    reason = "no_membership" if not grants else "policy_denied"
                    for grant in grants:
                        revision = max(revision, grant.grant_revision)
                        if enforcer.enforce(
                            grant.role, str(kb), "content_artifact", str(kb), action
                        ):
                            allowed, revision, reason = True, grant.grant_revision, "allowed"
                            break
                session.add(
                    AuditEventRow(
                        id=uuid4(),
                        actor_principal_id=actor_id,
                        delegate_principal_id=None,
                        resource_type="content_artifact",
                        resource_id=artifact,
                        action=action,
                        decision=allowed,
                        reason_code=reason,
                        policy_hash=enforcer.policy_hash,
                        grant_revision=revision,
                        trace_id=trace_id,
                    )
                )
            if not allowed:
                raise PermissionError("document job authorization denied")

        return authorize


def _register_artifact(session: Session, manifest: ArtifactManifest) -> None:
    source = session.get(SourceDocument, manifest.document_id)
    if source is None:
        source = SourceDocument(
            id=manifest.document_id,
            tenant_id=manifest.tenant_id,
            knowledge_base_id=manifest.knowledge_base_id,
            source_sha256=manifest.source_sha256,
        )
        session.add(source)
        session.flush()
    if (source.tenant_id, source.knowledge_base_id, source.source_sha256) != (
        manifest.tenant_id,
        manifest.knowledge_base_id,
        manifest.source_sha256,
    ):
        raise ArtifactIntegrityError("source identity conflict")
    version = session.get(DocumentVersion, manifest.version_id)
    if version is None:
        session.add(DocumentVersion(id=manifest.version_id, source_document_id=source.id))
        session.flush()
    elif version.source_document_id != source.id:
        raise ArtifactIntegrityError("version identity conflict")
    artifact = session.get(ContentArtifact, manifest.artifact_id)
    if artifact is None:
        session.add(
            ContentArtifact(
                id=manifest.artifact_id,
                document_version_id=manifest.version_id,
                artifact_sha256=manifest.artifact_sha256,
                page_count=manifest.page_count,
                extraction_status=manifest.extraction_quality.status,
            )
        )
        session.flush()
    elif (artifact.document_version_id, artifact.artifact_sha256) != (
        manifest.version_id,
        manifest.artifact_sha256,
    ):
        raise ArtifactIntegrityError("content identity conflict")


def register_document_artifact(connection: Connection, manifest: ArtifactManifest) -> None:
    """Register readable source metadata before model extraction, in the caller's fence.

    A later extraction failure leaves the artifact available to authorized review.
    A database failure after filesystem publication is repaired on the next attempt.
    """
    with Session(bind=connection) as session:
        _register_artifact(session, manifest)


class DocumentResultImporter:
    def __init__(
        self,
        engine: Engine,
        store: CheckpointStore,
        authorize_for_job: Callable[[JobLease], Authorizer],
    ) -> None:
        self.engine, self.store, self.authorize_for_job = engine, store, authorize_for_job

    def run_one(self) -> bool:
        with self.engine.begin() as conn:
            row = (
                conn.execute(
                    select(outbox)
                    .where(outbox.c.delivered_at.is_(None))
                    .order_by(outbox.c.created_at)
                    .with_for_update(skip_locked=True)
                    .limit(1)
                )
                .mappings()
                .first()
            )
            if row is None:
                return False
            job = (
                conn.execute(select(jobs).where(jobs.c.id == row["job_id"]).with_for_update())
                .mappings()
                .one()
            )
            if job["state"] != "complete" or job["result_ref"] != row["result_ref"]:
                raise ArtifactIntegrityError("outbox completion mismatch")
            lease = JobLease(
                UUID(job["id"]),
                UUID(job["tenant_id"]),
                UUID(job["knowledge_base_id"]),
                UUID(job["artifact_id"]),
                job["generation"],
                job["attempt"],
                job["payload"],
            )
            if (row["tenant_id"], row["knowledge_base_id"]) != (
                job["tenant_id"],
                job["knowledge_base_id"],
            ):
                raise ArtifactIntegrityError("outbox scope mismatch")
            self.authorize_for_job(lease)(
                lease.tenant_id, lease.knowledge_base_id, lease.artifact_id, "interpret"
            )
            # Serialize imports for two profiles sharing a not-yet-imported artifact.
            conn.execute(
                select(leases)
                .where(leases.c.artifact_id == str(lease.artifact_id))
                .with_for_update()
            ).one()
            prefix = f"runs/{lease.tenant_id}/{lease.knowledge_base_id}/"
            result_ref = row["result_ref"]
            if not result_ref.startswith(prefix) or not result_ref.endswith("/manifest.json"):
                raise ArtifactIntegrityError("outbox result namespace mismatch")
            run_id = UUID(result_ref[len(prefix) : -len("/manifest.json")])
            manifest, _ = self.store.load(
                lease.artifact_id, lease.tenant_id, lease.knowledge_base_id
            )
            files = self.store.load_run(
                tenant_id=lease.tenant_id,
                knowledge_base_id=lease.knowledge_base_id,
                artifact_id=lease.artifact_id,
                run_id=run_id,
            )
            result = InterpretationResult.model_validate_json(files["result.json"])
            if (result.run_id, result.artifact_id) != (run_id, lease.artifact_id):
                raise ArtifactIntegrityError("interpretation identity mismatch")
            if (
                result.run_configuration.profile_id,
                result.run_configuration.profile_version,
                result.run_configuration.schema_hash,
            ) != (
                lease.payload["profile_id"],
                lease.payload["profile_version"],
                lease.payload["schema_sha256"],
            ):
                raise ArtifactIntegrityError("interpretation profile mismatch")
            if result.entities or result.relationships or result.status == "failed":
                raise ValueError("unsupported or failed interpretation output")
            if (
                str(manifest.document_id),
                str(manifest.version_id),
                manifest.source_sha256,
                manifest.execution.configuration_hash,
            ) != (
                lease.payload["document_id"],
                lease.payload["version_id"],
                lease.payload["source_sha256"],
                lease.payload["recipe_sha256"],
            ):
                raise ArtifactIntegrityError("job source identity mismatch")
            with Session(bind=conn) as session:
                _register_artifact(session, manifest)
                # The outbox delivered marker and all rows commit together. A pre-existing
                # run with a pending outbox is not a retry of this transaction.
                if session.get(SemanticInterpretationRun, run_id) is not None:
                    raise ArtifactIntegrityError("run already imported outside this outbox")
                config = result.run_configuration.model_dump(mode="json")
                config["graph_run"] = json.loads(files["metadata.json"])
                session.add(
                    SemanticInterpretationRun(
                        id=run_id,
                        artifact_id=manifest.artifact_id,
                        profile_id=result.run_configuration.profile_id,
                        profile_version=result.run_configuration.profile_version,
                        status=result.status,
                        counters=result.counters.model_dump(),
                        run_configuration=config,
                        created_at=result.created_at,
                    )
                )
                session.flush()
                for candidate in result.assertions:
                    if not candidate.evidence or any(
                        e.artifact_id != manifest.artifact_id for e in candidate.evidence
                    ):
                        raise ArtifactIntegrityError("assertion evidence scope mismatch")
                    session.add(
                        Assertion(
                            id=candidate.id,
                            run_id=run_id,
                            origin="MACHINE_EXTRACTION",
                            version=1,
                            subject_type=candidate.subject_type,
                            slot_type=candidate.slot_type,
                            value=candidate.value,
                            model_confidence=candidate.model_confidence,
                            interpretation_basis=candidate.interpretation_basis,
                        )
                    )
                    session.flush()
                    for index, evidence in enumerate(candidate.evidence):
                        session.add(
                            AssertionEvidence(
                                id=uuid5(candidate.id, f"evidence:{index}"),
                                assertion_id=candidate.id,
                                **evidence.model_dump(exclude={"bbox"}),
                                bbox=evidence.bbox.model_dump() if evidence.bbox else None,
                            )
                        )
                    unresolved = any(e.precision == "unresolved" for e in candidate.evidence)
                    # Unknown model confidence is not a confidence of 1. Candidate
                    # adoption has no automatic acceptance policy.
                    if (
                        unresolved
                        or candidate.model_confidence is None
                        or candidate.model_confidence < 0.5
                    ):
                        evidence = next(
                            (e for e in candidate.evidence if e.precision == "unresolved"),
                            candidate.evidence[0],
                        )
                        locator = evidence_binding_to_locator(
                            **evidence.model_dump(),
                            unresolved_reason="property_not_uniquely_located"
                            if unresolved
                            else None,
                        )
                        session.add(
                            ReviewItemRow(
                                id=uuid5(candidate.id, "review"),
                                type="PROVENANCE_CORRECTION"
                                if unresolved
                                else "EXTRACTION_CORRECTION",
                                status="open",
                                assertion_id=candidate.id,
                                assertion_version=1,
                                tenant_id=manifest.tenant_id,
                                knowledge_base_id=manifest.knowledge_base_id,
                                evidence=asdict(locator),
                            )
                        )
                session.flush()
            conn.execute(
                update(outbox)
                .where(outbox.c.job_id == row["job_id"])
                .values(
                    delivered_at=func.extract("epoch", func.clock_timestamp())
                    if conn.dialect.name == "postgresql"
                    else func.strftime("%s", "now")
                )
            )
        return True
