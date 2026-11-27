"""`OntologyReleaseStore` (F0012-S0004/S0005/S0006, ADR-0081 D4/D6/D8).

Runs inside the caller's unit of work, which `AuthorizationExecution` already
authorized and will commit or roll back with the authorization audit. Nothing
here commits. Every table is append-only in the database (migration 0017).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from brain_contracts.schema_runtime import ContractError, ContractRef, validate_contract
from brain_domain.audit import AuditEvent
from brain_domain.authx import AuthorizationDecision, ResourceType
from brain_domain.ontology import (
    RESERVED_PREDICATE_NAMESPACES,
    OntologyReason,
    OntologyRefused,
    definition_digest,
    manifest_digest,
    only_added_axioms,
    release_ref_for,
    sha256_jcs,
)
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from brain_persistence.assertion_models import AssertionSemantics
from brain_persistence.authx import audit_timestamp
from brain_persistence.models import AuditEventRow, FactSlotRow
from brain_persistence.ontology_models import (
    OntologyChangeRecordRow,
    OntologyImpactReportRow,
    OntologyModuleVersionRow,
    OntologyReleaseModuleRow,
    OntologyReleaseReviewRow,
    OntologyReleaseRow,
    OntologyReleaseSelectionRow,
    OntologyTermRow,
)

MANIFEST_REF = ContractRef("ontology-release-manifest-v1", "1")

Scope = tuple[UUID, UUID]


@dataclass(frozen=True, slots=True)
class InstallResult:
    status: str  # installed | already_installed
    release_id: UUID
    release_ref: str
    manifest_digest: str
    terms: int


@dataclass(frozen=True, slots=True)
class InstalledRelease:
    id: UUID
    release_ref: str
    name: str
    sequence: int
    manifest_digest: str
    manifest: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class PredicateRow:
    release_ref: str
    term_iri: str
    predicate_key: str
    cardinality: str
    value_type: str
    temporal_kind: str
    normalized: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class Selection:
    sequence: int
    action: str
    release_ref: str
    release_id: UUID
    review_id: UUID | None
    actor_principal_id: UUID
    selected_at: datetime


@dataclass(frozen=True, slots=True)
class StoredReport:
    id: UUID
    status: str
    report_digest: str
    report: Mapping[str, Any]
    candidate_release_id: UUID
    predecessor_release_id: UUID | None


@dataclass(frozen=True, slots=True)
class StoredReview:
    id: UUID
    report_id: UUID
    decision: str


def verify_release_content(manifest: Mapping[str, Any], normalized: Mapping[str, Any]) -> None:
    """Recompute every digest from content before any row is written (S0004 edge case)."""
    try:
        validate_contract(MANIFEST_REF, manifest, profile="portable-json/v1")
    except ContractError as exc:
        raise OntologyRefused(OntologyReason.MANIFEST_INVALID, exc.issue.schema_pointer) from exc
    digest = manifest_digest(manifest)
    if manifest["manifest_digest"] != digest or manifest["release_ref"] != release_ref_for(digest):
        raise OntologyRefused(OntologyReason.MANIFEST_DIGEST_MISMATCH, "manifest")
    modules = {m["id"]: m for m in normalized.get("modules", [])}
    declared = {m["id"]: m for m in manifest["modules"]}
    if set(modules) != set(declared):
        raise OntologyRefused(OntologyReason.MANIFEST_DIGEST_MISMATCH, "module set")
    for module_id, module in modules.items():
        if (
            sha256_jcs(module["normalized"]) != declared[module_id]["digest"]
            or module["digest"] != declared[module_id]["digest"]
        ):
            raise OntologyRefused(OntologyReason.MANIFEST_DIGEST_MISMATCH, f"module {module_id}")
    rows = normalized.get("terms", [])
    for row in rows:
        if (
            definition_digest(row["term"]) != row["definition_digest"]
            or row["term"]["iri"] != row["iri"]
        ):
            raise OntologyRefused(OntologyReason.MANIFEST_DIGEST_MISMATCH, f"term {row['iri']}")
    module_iris = sorted(t["iri"] for m in modules.values() for t in m["normalized"]["terms"])
    if module_iris != [r["iri"] for r in rows]:
        raise OntologyRefused(OntologyReason.MANIFEST_DIGEST_MISMATCH, "term set")
    if sha256_jcs([[r["iri"], r["definition_digest"]] for r in rows]) != manifest["terms_digest"]:
        raise OntologyRefused(OntologyReason.MANIFEST_DIGEST_MISMATCH, "terms")
    if normalized.get("change_records", []) != manifest["change_records"]:
        raise OntologyRefused(OntologyReason.MANIFEST_DIGEST_MISMATCH, "change records")
    # The installed `ontology_term` predicate rows come from the normalized terms; they
    # must equal the manifest's predicate list, and no release may claim a namespace
    # owned by the static registry (`sys`, `test`).
    from_terms = sorted(
        (r["iri"], t["predicate_key"], t["cardinality"], t["value_type"], t["temporal_kind"])
        for r in rows
        if (t := r["term"]).get("predicate_key")
    )
    declared_predicates = sorted(
        (p["term_iri"], p["predicate_key"], p["cardinality"], p["value_type"], p["temporal_kind"])
        for p in manifest["predicates"]
    )
    if from_terms != declared_predicates:
        raise OntologyRefused(OntologyReason.MANIFEST_DIGEST_MISMATCH, "predicates")
    for _, key, *_ in declared_predicates:
        if key.split(":", 1)[0] in RESERVED_PREDICATE_NAMESPACES:
            raise OntologyRefused(OntologyReason.MANIFEST_INVALID, f"reserved namespace in {key}")


class OntologyReleaseStore:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- locks ---------------------------------------------------------------

    async def _lock_scope(self, scope: Scope) -> None:
        """Serialize install and selection per tenant/KB (released at transaction end)."""
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:k, 12))"),
            {"k": f"ontology:{scope[0]}:{scope[1]}"},
        )

    # --- install (S0004 AC2/AC6/AC7, S0002 AC2) -------------------------------

    async def install(
        self,
        scope: Scope,
        manifest: Mapping[str, Any],
        normalized: Mapping[str, Any],
        *,
        actor_id: UUID,
        at: datetime,
    ) -> InstallResult:
        verify_release_content(manifest, normalized)
        tenant_id, kb_id = scope
        await self._lock_scope(scope)
        existing = await self.release_by_ref(scope, manifest["release_ref"])
        if existing is not None:
            return InstallResult(
                "already_installed", existing.id, existing.release_ref, existing.manifest_digest, 0
            )

        covered = {iri for r in manifest["change_records"] for iri in r["source_iris"]}
        history = await self._session.execute(
            select(
                OntologyTermRow.term_iri,
                OntologyTermRow.definition_digest,
                OntologyTermRow.normalized,
            ).where(
                OntologyTermRow.tenant_id == tenant_id, OntologyTermRow.knowledge_base_id == kb_id
            )
        )
        known: dict[str, dict[str, Mapping[str, Any]]] = {}
        for iri, digest, term in history:
            known.setdefault(iri, {})[digest.strip()] = term
        for row in normalized["terms"]:
            published = known.get(row["iri"])
            if (
                published
                and row["definition_digest"] not in published
                and row["iri"] not in covered
                and not any(only_added_axioms(prev, row["term"]) for prev in published.values())
            ):
                raise OntologyRefused(OntologyReason.IDENTITY_REUSE_REJECTED, row["iri"])

        release_id = uuid4()
        module_ids: dict[str, UUID] = {}
        for module in normalized["modules"]:
            found = (
                await self._session.execute(
                    select(OntologyModuleVersionRow).where(
                        OntologyModuleVersionRow.tenant_id == tenant_id,
                        OntologyModuleVersionRow.knowledge_base_id == kb_id,
                        OntologyModuleVersionRow.module_id == module["id"],
                        OntologyModuleVersionRow.version == module["version"],
                    )
                )
            ).scalar_one_or_none()
            if found is not None:
                if found.content_digest.strip() != module["digest"]:
                    raise OntologyRefused(
                        OntologyReason.MODULE_VERSION_IMMUTABLE,
                        f"{module['id']}@{module['version']}",
                    )
                module_ids[module["id"]] = found.id
                continue
            module_ids[module["id"]] = uuid4()
            self._session.add(
                OntologyModuleVersionRow(
                    id=module_ids[module["id"]],
                    tenant_id=tenant_id,
                    knowledge_base_id=kb_id,
                    module_id=module["id"],
                    version=module["version"],
                    content_digest=module["digest"],
                    authoring_schema=module["normalized"]["authoring_schema"],
                    normalized=module["normalized"],
                    created_by=actor_id,
                    created_at=at,
                )
            )
        self._session.add(
            OntologyReleaseRow(
                id=release_id,
                tenant_id=tenant_id,
                knowledge_base_id=kb_id,
                release_ref=manifest["release_ref"],
                name=manifest["name"],
                sequence=manifest["sequence"],
                manifest_digest=manifest["manifest_digest"],
                manifest=dict(manifest),
                installed_by=actor_id,
                installed_at=at,
            )
        )
        await self._session.flush()
        for module_id, version_id in sorted(module_ids.items()):
            self._session.add(
                OntologyReleaseModuleRow(
                    release_id=release_id,
                    module_version_id=version_id,
                    module_id=module_id,
                    tenant_id=tenant_id,
                    knowledge_base_id=kb_id,
                )
            )
        for row in normalized["terms"]:
            term = row["term"]
            has_predicate = "predicate_key" in term
            self._session.add(
                OntologyTermRow(
                    release_id=release_id,
                    tenant_id=tenant_id,
                    knowledge_base_id=kb_id,
                    term_iri=row["iri"],
                    term_kind=row["kind"],
                    definition_digest=row["definition_digest"],
                    normalized=term,
                    predicate_key=term.get("predicate_key"),
                    cardinality=term.get("cardinality") if has_predicate else None,
                    value_type=term.get("value_type") if has_predicate else None,
                    temporal_kind=term.get("temporal_kind") if has_predicate else None,
                )
            )
        for record in manifest["change_records"]:
            self._session.add(
                OntologyChangeRecordRow(
                    id=uuid4(),
                    release_id=release_id,
                    tenant_id=tenant_id,
                    knowledge_base_id=kb_id,
                    change_class=record["class"],
                    source_iris=list(record["source_iris"]),
                    replacement_iris=list(record["replacement_iris"]),
                    rationale=record["rationale"],
                )
            )
        await self._session.flush()
        return InstallResult(
            "installed",
            release_id,
            manifest["release_ref"],
            manifest["manifest_digest"],
            len(normalized["terms"]),
        )

    # --- reads ----------------------------------------------------------------

    @staticmethod
    def _release(row: OntologyReleaseRow) -> InstalledRelease:
        return InstalledRelease(
            row.id,
            row.release_ref,
            row.name,
            row.sequence,
            row.manifest_digest.strip(),
            row.manifest,
        )

    async def release_by_ref(self, scope: Scope, release_ref: str) -> InstalledRelease | None:
        row = (
            await self._session.execute(
                select(OntologyReleaseRow).where(
                    OntologyReleaseRow.tenant_id == scope[0],
                    OntologyReleaseRow.knowledge_base_id == scope[1],
                    OntologyReleaseRow.release_ref == release_ref,
                )
            )
        ).scalar_one_or_none()
        return self._release(row) if row is not None else None

    async def release_by_id(self, scope: Scope, release_id: UUID) -> InstalledRelease | None:
        row = (
            await self._session.execute(
                select(OntologyReleaseRow).where(
                    OntologyReleaseRow.tenant_id == scope[0],
                    OntologyReleaseRow.knowledge_base_id == scope[1],
                    OntologyReleaseRow.id == release_id,
                )
            )
        ).scalar_one_or_none()
        return self._release(row) if row is not None else None

    async def terms(self, release_id: UUID) -> list[Mapping[str, Any]]:
        rows = await self._session.execute(
            select(OntologyTermRow.normalized, OntologyTermRow.definition_digest)
            .where(OntologyTermRow.release_id == release_id)
            .order_by(OntologyTermRow.term_iri)
        )
        return [{**normalized, "_definition_digest": digest.strip()} for normalized, digest in rows]

    async def constraints(self, release_id: UUID) -> list[Mapping[str, Any]]:
        rows = await self._session.execute(
            select(OntologyModuleVersionRow.normalized)
            .join(
                OntologyReleaseModuleRow,
                OntologyReleaseModuleRow.module_version_id == OntologyModuleVersionRow.id,
            )
            .where(OntologyReleaseModuleRow.release_id == release_id)
            .order_by(OntologyModuleVersionRow.module_id)
        )
        out: list[Mapping[str, Any]] = []
        for (normalized,) in rows:
            out.extend(normalized.get("constraints", []))
        return sorted(out, key=lambda c: c["id"])

    async def predicates(self, scope: Scope, release_refs: Sequence[str]) -> list[PredicateRow]:
        """Predicate contracts of the named releases installed in this tenant/KB only
        (S0005 AC2). One query, same session."""
        if not release_refs:
            return []
        rows = await self._session.execute(
            select(
                OntologyReleaseRow.release_ref,
                OntologyTermRow.term_iri,
                OntologyTermRow.predicate_key,
                OntologyTermRow.cardinality,
                OntologyTermRow.value_type,
                OntologyTermRow.temporal_kind,
                OntologyTermRow.normalized,
            )
            .join(OntologyTermRow, OntologyTermRow.release_id == OntologyReleaseRow.id)
            .where(
                OntologyReleaseRow.tenant_id == scope[0],
                OntologyReleaseRow.knowledge_base_id == scope[1],
                OntologyReleaseRow.release_ref.in_(sorted(set(release_refs))),
                OntologyTermRow.predicate_key.is_not(None),
            )
        )
        return [PredicateRow(*row) for row in rows]

    async def head(self, scope: Scope, *, for_update: bool = False) -> Selection | None:
        if for_update:
            await self._lock_scope(scope)
        history = await self.history(scope, limit=1)
        return history[0] if history else None

    async def history(self, scope: Scope, *, limit: int | None = None) -> list[Selection]:
        query = (
            select(OntologyReleaseSelectionRow, OntologyReleaseRow.release_ref)
            .join(
                OntologyReleaseRow, OntologyReleaseRow.id == OntologyReleaseSelectionRow.release_id
            )
            .where(
                OntologyReleaseSelectionRow.tenant_id == scope[0],
                OntologyReleaseSelectionRow.knowledge_base_id == scope[1],
            )
        )
        if limit is not None:
            query = query.order_by(OntologyReleaseSelectionRow.sequence.desc()).limit(limit)
        else:
            query = query.order_by(OntologyReleaseSelectionRow.sequence)
        rows = await self._session.execute(query)
        return [
            Selection(
                s.sequence,
                s.action,
                ref,
                s.release_id,
                s.review_id,
                s.actor_principal_id,
                s.selected_at,
            )
            for s, ref in rows
        ]

    async def was_activated(self, scope: Scope, release_id: UUID) -> bool:
        found = await self._session.execute(
            select(func.count())
            .select_from(OntologyReleaseSelectionRow)
            .where(
                OntologyReleaseSelectionRow.tenant_id == scope[0],
                OntologyReleaseSelectionRow.knowledge_base_id == scope[1],
                OntologyReleaseSelectionRow.release_id == release_id,
                OntologyReleaseSelectionRow.action == "activate",
            )
        )
        return bool(found.scalar_one())

    # --- reach (S0006 AC4) ----------------------------------------------------------

    async def reach(self, scope: Scope, predicate_keys: Sequence[str]) -> list[dict[str, Any]]:
        """Affected identity-v1 FactSlots per predicate key and typed assertions that
        reference the key, each with its tenant/KB denominator."""
        tenant_id, kb_id = scope
        slot_total = (
            await self._session.execute(
                select(func.count())
                .select_from(FactSlotRow)
                .where(
                    FactSlotRow.tenant_id == tenant_id,
                    FactSlotRow.knowledge_base_id == kb_id,
                    FactSlotRow.identity_version.is_not(None),
                )
            )
        ).scalar_one()
        assertion_total = (
            await self._session.execute(
                select(func.count())
                .select_from(AssertionSemantics)
                .where(
                    AssertionSemantics.tenant_id == tenant_id,
                    AssertionSemantics.knowledge_base_id == kb_id,
                    AssertionSemantics.predicate_id.is_not(None),
                )
            )
        ).scalar_one()
        out: list[dict[str, Any]] = []
        for key in sorted(set(predicate_keys)):
            slots = (
                await self._session.execute(
                    select(func.count())
                    .select_from(FactSlotRow)
                    .where(
                        FactSlotRow.tenant_id == tenant_id,
                        FactSlotRow.knowledge_base_id == kb_id,
                        FactSlotRow.identity_version.is_not(None),
                        FactSlotRow.predicate_key == key,
                    )
                )
            ).scalar_one()
            assertions = (
                await self._session.execute(
                    select(func.count())
                    .select_from(AssertionSemantics)
                    .where(
                        AssertionSemantics.tenant_id == tenant_id,
                        AssertionSemantics.knowledge_base_id == kb_id,
                        AssertionSemantics.predicate_id == key,
                    )
                )
            ).scalar_one()
            out.append(
                {
                    "population": "fact_slot",
                    "predicate_key": key,
                    "affected": slots,
                    "denominator": slot_total,
                }
            )
            out.append(
                {
                    "population": "assertion",
                    "predicate_key": key,
                    "affected": assertions,
                    "denominator": assertion_total,
                }
            )
        return out

    # --- reports, reviews, selections (S0006) ---------------------------------------------

    async def save_report(
        self,
        scope: Scope,
        report: Mapping[str, Any],
        *,
        candidate_id: UUID,
        predecessor_id: UUID | None,
        actor_id: UUID,
        at: datetime,
    ) -> StoredReport:
        existing = (
            await self._session.execute(
                select(OntologyImpactReportRow).where(
                    OntologyImpactReportRow.tenant_id == scope[0],
                    OntologyImpactReportRow.knowledge_base_id == scope[1],
                    OntologyImpactReportRow.report_digest == report["report_digest"],
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return self._report(existing)
        row = OntologyImpactReportRow(
            id=uuid4(),
            tenant_id=scope[0],
            knowledge_base_id=scope[1],
            predecessor_release_id=predecessor_id,
            candidate_release_id=candidate_id,
            status=report["status"],
            report_digest=report["report_digest"],
            report=dict(report),
            generated_by=actor_id,
            generated_at=at,
        )
        self._session.add(row)
        await self._session.flush()
        return self._report(row)

    @staticmethod
    def _report(row: OntologyImpactReportRow) -> StoredReport:
        return StoredReport(
            row.id,
            row.status,
            row.report_digest.strip(),
            row.report,
            row.candidate_release_id,
            row.predecessor_release_id,
        )

    async def report(self, scope: Scope, report_id: UUID) -> StoredReport | None:
        row = (
            await self._session.execute(
                select(OntologyImpactReportRow).where(
                    OntologyImpactReportRow.tenant_id == scope[0],
                    OntologyImpactReportRow.knowledge_base_id == scope[1],
                    OntologyImpactReportRow.id == report_id,
                )
            )
        ).scalar_one_or_none()
        return self._report(row) if row is not None else None

    async def save_review(
        self,
        scope: Scope,
        *,
        report_id: UUID,
        decision: str,
        rationale: str,
        reviewer_id: UUID,
        decision_id: UUID,
        at: datetime,
    ) -> UUID:
        review_id = uuid4()
        self._session.add(
            OntologyReleaseReviewRow(
                id=review_id,
                tenant_id=scope[0],
                knowledge_base_id=scope[1],
                report_id=report_id,
                decision=decision,
                reviewer_principal_id=reviewer_id,
                decision_id=decision_id,
                rationale=rationale,
                decided_at=at,
            )
        )
        await self._session.flush()
        return review_id

    async def review(self, scope: Scope, review_id: UUID) -> StoredReview | None:
        row = (
            await self._session.execute(
                select(OntologyReleaseReviewRow).where(
                    OntologyReleaseReviewRow.tenant_id == scope[0],
                    OntologyReleaseReviewRow.knowledge_base_id == scope[1],
                    OntologyReleaseReviewRow.id == review_id,
                )
            )
        ).scalar_one_or_none()
        return StoredReview(row.id, row.report_id, row.decision) if row is not None else None

    async def append_selection(
        self,
        scope: Scope,
        *,
        sequence: int,
        action: str,
        release_id: UUID,
        review_id: UUID | None,
        actor_id: UUID,
        decision_id: UUID,
        at: datetime,
    ) -> None:
        self._session.add(
            OntologyReleaseSelectionRow(
                id=uuid4(),
                tenant_id=scope[0],
                knowledge_base_id=scope[1],
                sequence=sequence,
                action=action,
                release_id=release_id,
                review_id=review_id,
                actor_principal_id=actor_id,
                decision_id=decision_id,
                selected_at=at,
            )
        )
        await self._session.flush()

    # --- audit (G0-9) ---------------------------------------------------------------------

    async def audit(
        self,
        decision: AuthorizationDecision,
        *,
        command: str,
        outcome: str,
        payload: Mapping[str, Any],
        at: datetime,
    ) -> None:
        """One `ontology_release_<command>` event linked to the decision."""
        self._session.add(
            AuditEventRow(
                id=uuid4(),
                occurred_at=audit_timestamp(at),
                actor_principal_id=decision.actor_principal_id,
                delegate_principal_id=decision.executor_principal_id,
                resource_type=ResourceType.ONTOLOGY_RELEASE.value,
                resource_id=decision.resource.id,
                action=str(decision.action),
                decision=decision.allowed,
                reason_code=outcome,
                policy_hash=decision.policy_hash,
                grant_revision=decision.grant_revision,
                trace_id=decision.trace_id,
                decision_id=decision.decision_id,
                event_type=f"ontology_release_{command.replace('-', '_')}",
                operation_outcome="succeeded"
                if outcome in {"installed", "already_installed", "recorded", "selected", "listed"}
                else "failed",
                payload=dict(payload),
            )
        )
        await self._session.flush()


__all__ = [
    "AuditEvent",
    "InstallResult",
    "InstalledRelease",
    "OntologyReleaseStore",
    "PredicateRow",
    "Selection",
    "StoredReport",
    "StoredReview",
    "verify_release_content",
]
