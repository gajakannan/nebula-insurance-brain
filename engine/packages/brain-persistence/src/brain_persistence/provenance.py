"""F0009 provenance repository: metadata-first discovery, exact materialization.

`discover` selects identity, ownership and link columns only (never assertion
values, review payloads, excerpts, model payloads or source bytes) and derives the
READ requirement of every linked resource. `materialize` re-runs the same
discovery under share locks, refuses a changed topology, then loads exactly the
planned rows and serializes them with the stored values. Neither method commits.

Closure (assembly plan Step 4-5, Edge Semantics):

- an assertion: its correction ancestry, evidence, artifacts, run and the review
  history of that ancestry (decisions, the children they created, reservations
  and refused attempts);
- a fact version: its supporting and ending evidence (each to its assertion
  closure), its recorded decision, its split ancestry, the direct incoming and
  outgoing canonical changes with their endpoints (predecessor ancestry only), and
  the artifacts behind any exposed attestation dates.

One stored link yields exactly one edge; nothing is inferred.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from brain_domain.authx import ResourceKey, ResourceType
from brain_domain.provenance import (
    MAX_CORRECTION_LINKS,
    MAX_EDGES,
    MAX_RECORDS,
    LearningCandidateReservation,
    LineageNotFound,
    LineageUnavailable,
    MetadataGap,
    ProvenanceEdge,
    ProvenanceQuery,
    ProvenanceRecord,
    ProvenanceResult,
    RecordRef,
    ReviewSubmissionAttempt,
)
from brain_provenance.ports import ProvenancePlan
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from brain_persistence.assertion_models import AssertionSemantics
from brain_persistence.models import (
    Assertion,
    AssertionEvidence,
    AuditEventRow,
    CanonicalCommitRow,
    CanonicalFactChangeRow,
    CanonicalFactVersionRow,
    ContentArtifact,
    DocumentVersion,
    ReviewDecisionRow,
    ReviewItemRow,
    SemanticInterpretationRun,
    SourceDocument,
)
from brain_persistence.provenance_models import (
    LearningCandidateReservationRow,
    ReviewSubmissionAttemptRow,
)

Owner = tuple[UUID, UUID]


def _utc(value: datetime | None) -> str | None:
    """F0001 timestamp columns are naive UTC (`audit_timestamp`); emit RFC 3339."""
    if value is None:
        return None
    aware = value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    return aware.isoformat()


def _ref(kind: str, identity: UUID) -> RecordRef:
    return RecordRef(kind, identity)


@dataclass
class _Topology:
    """The metadata-only closure. Fingerprinted to detect a concurrent change."""

    root: RecordRef
    anchor: ResourceKey
    owner: Owner | None = None
    refs: set[RecordRef] = field(default_factory=set)
    edges: set[tuple[str, RecordRef, RecordRef]] = field(default_factory=set)
    keys: set[ResourceKey] = field(default_factory=set)
    # Legacy (pre-F0008) versions whose stored evidence ids name no registered row.
    unregistered: set[UUID] = field(default_factory=set)

    def own(self, tenant_id: UUID, knowledge_base_id: UUID) -> None:
        owner = (tenant_id, knowledge_base_id)
        if self.owner is None:
            self.owner = owner
        elif owner != self.owner:
            # Cross-tenant/KB link: refuse without disclosing the target (S0003 AC6).
            raise LineageNotFound()

    def add(self, ref: RecordRef) -> bool:
        if ref in self.refs:
            return False
        self.refs.add(ref)
        if len(self.refs) > MAX_RECORDS:
            raise LineageUnavailable()
        return True

    def link(self, kind: str, source: RecordRef, target: RecordRef) -> None:
        self.edges.add((kind, source, target))
        if len(self.edges) > MAX_EDGES:
            raise LineageUnavailable()

    def fingerprint(self) -> str:
        digest = hashlib.sha256()
        digest.update(
            f"{self.root.kind}:{self.root.id}|{self.anchor.type}:{self.anchor.id}".encode()
        )
        digest.update(f"|owner:{self.owner}".encode())
        for ref in sorted(self.refs):
            digest.update(f"|r:{ref.kind}:{ref.id}".encode())
        for kind, source, target in sorted(
            self.edges, key=lambda e: (e[0], e[1].kind, str(e[1].id), e[2].kind, str(e[2].id))
        ):
            digest.update(f"|e:{kind}:{source.kind}:{source.id}:{target.kind}:{target.id}".encode())
        for key in sorted(self.keys):
            digest.update(f"|k:{key.type}:{key.id}".encode())
        for identity in sorted(self.unregistered, key=str):
            digest.update(f"|u:{identity}".encode())
        return digest.hexdigest()


class SqlAlchemyProvenanceRepository:
    """`brain_provenance.ports.ProvenanceRepository` over SQLAlchemy/PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------ discovery

    async def discover(self, query: ProvenanceQuery) -> ProvenancePlan:
        topology = await self._walk(query, lock=False)
        return self._plan(topology)

    def _plan(self, topology: _Topology) -> ProvenancePlan:
        assert topology.owner is not None
        return ProvenancePlan(
            root=topology.root,
            anchor=topology.anchor,
            tenant_id=topology.owner[0],
            knowledge_base_id=topology.owner[1],
            record_refs=tuple(sorted(topology.refs)),
            source_keys=tuple(sorted(topology.keys)),
            metadata_fingerprint=topology.fingerprint(),
        )

    async def _walk(self, query: ProvenanceQuery, *, lock: bool) -> _Topology:
        walker = _Walker(self._session, _Topology(query.root, query.anchor), lock=lock)
        if query.root.kind == "assertion":
            await walker.assertion_root(query.root.id, query.anchor)
        else:
            await walker.version_root(query.root.id, query.anchor)
        return walker.topology

    # ------------------------------------------------------------ materialization

    async def materialize(self, plan: ProvenancePlan) -> ProvenanceResult:
        query = ProvenanceQuery(root=plan.root, anchor=plan.anchor)
        topology = await self._walk(query, lock=True)
        if topology.fingerprint() != plan.metadata_fingerprint:
            # A concurrent append/version/ownership change: never reselect endpoints.
            raise LineageUnavailable()
        loader = _Loader(self._session, topology)
        records, gaps = await loader.load()
        edges = [ProvenanceEdge(kind, source, target) for kind, source, target in topology.edges]
        assert topology.owner is not None
        return ProvenanceResult.assemble(
            root=plan.root,
            tenant_id=topology.owner[0],
            knowledge_base_id=topology.owner[1],
            records=records,
            edges=edges,
            gaps=gaps,
        )


class _Walker:
    """Column-only traversal. Every select names explicit columns, so the ORM
    identity map never holds a protected payload before READ is decided."""

    def __init__(self, session: AsyncSession, topology: _Topology, *, lock: bool) -> None:
        self._session = session
        self.topology = topology
        self._lock = lock
        self._assertions_done: set[UUID] = set()
        self._reviewed: set[UUID] = set()
        self._artifacts_done: set[UUID] = set()
        self._versions_done: dict[UUID, bool] = {}

    async def _one(self, statement: Any) -> Any:
        if self._lock:
            statement = statement.with_for_update(read=True)
        return (await self._session.execute(statement)).one_or_none()

    async def _all(self, statement: Any) -> Sequence[Any]:
        if self._lock:
            statement = statement.with_for_update(read=True)
        return (await self._session.execute(statement)).all()

    # ---------------------------------------------------------------- assertions

    async def _ancestry(self, assertion_id: UUID) -> list[Any]:
        """The correction chain from `assertion_id` to its machine original."""
        chain: list[Any] = []
        seen: set[UUID] = set()
        current: UUID | None = assertion_id
        while current is not None:
            if current in seen:
                raise LineageUnavailable()  # cyclic correction history
            if len(seen) > MAX_CORRECTION_LINKS:
                raise LineageUnavailable()
            seen.add(current)
            row = await self._one(
                select(
                    Assertion.id,
                    Assertion.run_id,
                    Assertion.original_assertion_id,
                    Assertion.tenant_id,
                    Assertion.knowledge_base_id,
                ).where(Assertion.id == current)
            )
            if row is None:
                raise LineageNotFound()  # dangling protected target
            self.topology.own(row.tenant_id, row.knowledge_base_id)
            chain.append(row)
            current = row.original_assertion_id
        return chain

    async def _visit_assertion(self, assertion_id: UUID) -> list[Any]:
        """Add an assertion, its ancestry, evidence, run and artifacts. Returns the chain."""
        chain = await self._ancestry(assertion_id)
        for row in chain:
            if row.id in self._assertions_done:
                continue
            self._assertions_done.add(row.id)
            ref = _ref("assertion", row.id)
            self.topology.add(ref)
            if row.original_assertion_id is not None:
                self.topology.link(
                    "corrected_from", ref, _ref("assertion", row.original_assertion_id)
                )
            if row.run_id is not None:
                run = await self._one(
                    select(
                        SemanticInterpretationRun.id,
                        SemanticInterpretationRun.artifact_id,
                        SemanticInterpretationRun.tenant_id,
                        SemanticInterpretationRun.knowledge_base_id,
                    ).where(SemanticInterpretationRun.id == row.run_id)
                )
                if run is None:
                    raise LineageNotFound()
                self.topology.own(run.tenant_id, run.knowledge_base_id)
                run_ref = _ref("interpretation_run", run.id)
                self.topology.add(run_ref)
                self.topology.link("interpreted_in", ref, run_ref)
                await self._visit_artifact(run.artifact_id)
                self.topology.link("interprets", run_ref, _ref("content_artifact", run.artifact_id))
            for evidence in await self._all(
                select(
                    AssertionEvidence.id,
                    AssertionEvidence.artifact_id,
                    AssertionEvidence.tenant_id,
                    AssertionEvidence.knowledge_base_id,
                )
                .where(AssertionEvidence.assertion_id == row.id)
                .order_by(AssertionEvidence.id)
            ):
                await self._add_evidence(evidence)
                self.topology.link("supported_by", ref, _ref("evidence", evidence.id))
        return chain

    async def _add_evidence(self, evidence: Any) -> None:
        self.topology.own(evidence.tenant_id, evidence.knowledge_base_id)
        ev_ref = _ref("evidence", evidence.id)
        self.topology.add(ev_ref)
        await self._visit_artifact(evidence.artifact_id)
        self.topology.link("located_in", ev_ref, _ref("content_artifact", evidence.artifact_id))

    async def _visit_artifact(self, artifact_id: UUID) -> None:
        if artifact_id in self._artifacts_done:
            return
        self._artifacts_done.add(artifact_id)
        artifact = await self._one(
            select(
                ContentArtifact.id,
                ContentArtifact.document_version_id,
                ContentArtifact.tenant_id,
                ContentArtifact.knowledge_base_id,
            ).where(ContentArtifact.id == artifact_id)
        )
        if artifact is None:
            raise LineageNotFound()
        self.topology.own(artifact.tenant_id, artifact.knowledge_base_id)
        art_ref = _ref("content_artifact", artifact.id)
        self.topology.add(art_ref)
        # Source model/run/document nodes inherit this artifact's READ (Step 4.4).
        self.topology.keys.add(ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact.id))
        version = await self._one(
            select(
                DocumentVersion.id,
                DocumentVersion.source_document_id,
                DocumentVersion.tenant_id,
                DocumentVersion.knowledge_base_id,
            ).where(DocumentVersion.id == artifact.document_version_id)
        )
        if version is None:
            raise LineageNotFound()
        self.topology.own(version.tenant_id, version.knowledge_base_id)
        dv_ref = _ref("document_version", version.id)
        self.topology.add(dv_ref)
        self.topology.link("artifact_of", art_ref, dv_ref)
        document = await self._one(
            select(
                SourceDocument.id, SourceDocument.tenant_id, SourceDocument.knowledge_base_id
            ).where(SourceDocument.id == version.source_document_id)
        )
        if document is None:
            raise LineageNotFound()
        self.topology.own(document.tenant_id, document.knowledge_base_id)
        sd_ref = _ref("source_document", document.id)
        self.topology.add(sd_ref)
        self.topology.link("version_of", dv_ref, sd_ref)

    async def _review_history(self, assertion_ids: Iterable[UUID]) -> None:
        """Decisions and refused attempts that review a member of the ancestry, the
        children those decisions created, and their reservations."""
        pending = sorted(set(assertion_ids) - self._reviewed, key=str)
        if not pending:
            return
        self._reviewed.update(pending)
        decisions = await self._all(
            select(
                ReviewDecisionRow.id,
                ReviewDecisionRow.review_item_id,
                ReviewDecisionRow.corrected_assertion_id,
                ReviewDecisionRow.tenant_id,
                ReviewDecisionRow.knowledge_base_id,
                ReviewItemRow.assertion_id,
            )
            .join(ReviewItemRow, ReviewItemRow.id == ReviewDecisionRow.review_item_id)
            .where(ReviewItemRow.assertion_id.in_(pending))
            .order_by(ReviewDecisionRow.id)
        )
        for decision in decisions:
            await self._add_decision(decision)
        attempts = await self._all(
            select(
                ReviewSubmissionAttemptRow.id,
                ReviewSubmissionAttemptRow.review_item_id,
                ReviewSubmissionAttemptRow.original_assertion_id,
                ReviewSubmissionAttemptRow.tenant_id,
                ReviewSubmissionAttemptRow.knowledge_base_id,
            )
            .where(ReviewSubmissionAttemptRow.original_assertion_id.in_(pending))
            .order_by(ReviewSubmissionAttemptRow.id)
        )
        for attempt in attempts:
            self.topology.own(attempt.tenant_id, attempt.knowledge_base_id)
            at_ref = _ref("review_attempt", attempt.id)
            self.topology.add(at_ref)
            self.topology.keys.add(ResourceKey(ResourceType.REVIEW_TASK, attempt.review_item_id))
            self.topology.link("reviews", at_ref, _ref("assertion", attempt.original_assertion_id))

    async def _add_decision(self, decision: Any) -> RecordRef:
        self.topology.own(decision.tenant_id, decision.knowledge_base_id)
        dec_ref = _ref("review_decision", decision.id)
        if not self.topology.add(dec_ref):
            return dec_ref
        # Exposing a decision requires current READ on its review task (Step 4.4).
        self.topology.keys.add(ResourceKey(ResourceType.REVIEW_TASK, decision.review_item_id))
        await self._visit_assertion(decision.assertion_id)
        self.topology.link("reviews", dec_ref, _ref("assertion", decision.assertion_id))
        if decision.corrected_assertion_id is not None:
            await self._visit_assertion(decision.corrected_assertion_id)
            self.topology.link(
                "created_assertion", dec_ref, _ref("assertion", decision.corrected_assertion_id)
            )
        reservation = await self._one(
            select(
                LearningCandidateReservationRow.id,
                LearningCandidateReservationRow.tenant_id,
                LearningCandidateReservationRow.knowledge_base_id,
            ).where(LearningCandidateReservationRow.review_decision_id == decision.id)
        )
        if reservation is not None:
            # A reservation inherits its decision/task authority (Step 4.4).
            self.topology.own(reservation.tenant_id, reservation.knowledge_base_id)
            res_ref = _ref("learning_reservation", reservation.id)
            self.topology.add(res_ref)
            self.topology.link("reserved_learning", dec_ref, res_ref)
        return dec_ref

    async def assertion_root(self, root_id: UUID, anchor: ResourceKey) -> None:
        # Step 4.3: prove the anchor lies on the root's own chain before expanding
        # evidence, artifacts or review history (code review CR-L1).
        ancestry = [row.id for row in await self._ancestry(root_id)]
        await self._prove_assertion_anchor(root_id, ancestry, anchor)
        chain = await self._visit_assertion(root_id)
        await self._review_history([row.id for row in chain])

    async def _prove_assertion_anchor(
        self, root_id: UUID, ancestry: list[UUID], anchor: ResourceKey
    ) -> None:
        """Step 4.3: the anchor must lie on the root's own stored chain; an
        arbitrary anchor never authorizes a lineage."""
        if anchor.type == ResourceType.REVIEW_TASK:
            item = await self._one(
                select(
                    ReviewItemRow.assertion_id,
                    ReviewItemRow.tenant_id,
                    ReviewItemRow.knowledge_base_id,
                ).where(ReviewItemRow.id == anchor.id)
            )
            if item is None:
                raise LineageNotFound()
            self.topology.own(item.tenant_id, item.knowledge_base_id)
            if item.assertion_id in ancestry:
                return
            created = await self._one(
                select(ReviewDecisionRow.id).where(
                    ReviewDecisionRow.review_item_id == anchor.id,
                    ReviewDecisionRow.corrected_assertion_id == root_id,
                )
            )
            if created is None:
                raise LineageNotFound()
            return
        if anchor.type == ResourceType.CONTENT_ARTIFACT:
            evidence_artifacts = (
                await self._session.execute(
                    select(AssertionEvidence.artifact_id).where(
                        AssertionEvidence.assertion_id.in_(ancestry)
                    )
                )
            ).scalars()
            run_artifacts = (
                await self._session.execute(
                    select(SemanticInterpretationRun.artifact_id)
                    .join(Assertion, Assertion.run_id == SemanticInterpretationRun.id)
                    .where(Assertion.id.in_(ancestry))
                )
            ).scalars()
            if anchor.id not in {*evidence_artifacts, *run_artifacts}:
                raise LineageNotFound()
            return
        # Assertion roots are never anchored on a fact slot (Step 4.3).
        raise LineageNotFound()

    # ----------------------------------------------------------- fact versions

    async def _version_meta(self, version_id: UUID) -> Any:
        row = await self._one(
            select(
                CanonicalFactVersionRow.id,
                CanonicalFactVersionRow.slot_id,
                CanonicalFactVersionRow.tenant_id,
                CanonicalFactVersionRow.knowledge_base_id,
                CanonicalFactVersionRow.evidence,
                CanonicalFactVersionRow.review_decision_id,
                CanonicalFactVersionRow.split_of_version_id,
                CanonicalFactVersionRow.temporal_contract,
                CanonicalFactVersionRow.attested_from_value,
                CanonicalFactVersionRow.attested_through_value,
                CanonicalFactVersionRow.attested_to_value,
            ).where(CanonicalFactVersionRow.id == version_id)
        )
        if row is None:
            raise LineageNotFound()
        self.topology.own(row.tenant_id, row.knowledge_base_id)
        return row

    async def _evidence_by_ids(self, ids: list[UUID]) -> dict[UUID, Any]:
        if not ids:
            return {}
        rows = await self._all(
            select(
                AssertionEvidence.id,
                AssertionEvidence.assertion_id,
                AssertionEvidence.artifact_id,
                AssertionEvidence.tenant_id,
                AssertionEvidence.knowledge_base_id,
            ).where(AssertionEvidence.id.in_(ids))
        )
        return {row.id: row for row in rows}

    async def _visit_version(
        self, version_id: UUID, slot_id: UUID, *, full: bool, path: frozenset[UUID]
    ) -> RecordRef:
        """Add a version. `full` follows its evidence and decision; split ancestry is
        always followed. Cross-slot or cyclic split history refuses (S0003 AC6)."""
        if version_id in path:
            raise LineageUnavailable()
        ver_ref = _ref("fact_version", version_id)
        done = self._versions_done.get(version_id)
        if done is not None and (done or not full):
            return ver_ref
        self._versions_done[version_id] = full
        row = await self._version_meta(version_id)
        if row.slot_id != slot_id:
            raise LineageNotFound()
        self.topology.add(ver_ref)
        self.topology.keys.add(ResourceKey(ResourceType.FACT_SLOT, row.slot_id))
        evidence = row.evidence if isinstance(row.evidence, dict) else {}
        support = [UUID(str(e)) for e in evidence.get("refs", [])]
        ending = [UUID(str(e)) for e in evidence.get("ending_refs", [])]
        exposes_attestation = row.temporal_contract is not None and any(
            (row.attested_from_value, row.attested_through_value, row.attested_to_value)
        )
        if full or exposes_attestation:
            found = await self._evidence_by_ids([*support, *ending])
            missing = [e for e in (*support, *ending) if e not in found]
            if missing:
                if row.temporal_contract is not None:
                    raise LineageNotFound()  # a modern version's evidence is dangling
                # Explicit legacy pilot boundary: unregistered UUIDs stay unqualified.
                self.topology.unregistered.update(missing)
            for kind, ids in (("supported_by", support), ("ending_evidence", ending)):
                for evidence_id in ids:
                    ev = found.get(evidence_id)
                    if ev is None:
                        continue
                    await self._add_evidence(ev)
                    self.topology.link(kind, ver_ref, _ref("evidence", ev.id))
                    if exposes_attestation:
                        # SEC-F8-NEW-01 join: the artifacts behind exposed dates.
                        self.topology.link(
                            "attested_by", ver_ref, _ref("content_artifact", ev.artifact_id)
                        )
                    if full:
                        chain = await self._visit_assertion(ev.assertion_id)
                        await self._review_history([r.id for r in chain])
        if full and row.review_decision_id is not None:
            decision = await self._one(
                select(
                    ReviewDecisionRow.id,
                    ReviewDecisionRow.review_item_id,
                    ReviewDecisionRow.corrected_assertion_id,
                    ReviewDecisionRow.tenant_id,
                    ReviewDecisionRow.knowledge_base_id,
                    ReviewItemRow.assertion_id,
                )
                .join(ReviewItemRow, ReviewItemRow.id == ReviewDecisionRow.review_item_id)
                .where(ReviewDecisionRow.id == row.review_decision_id)
            )
            if decision is None:
                if row.temporal_contract is not None:
                    raise LineageNotFound()
                self.topology.unregistered.add(row.review_decision_id)
            else:
                dec_ref = await self._add_decision(decision)
                # A stored link only; it implies no acceptance by review (S0003 AC5).
                self.topology.link("recorded_decision", ver_ref, dec_ref)
                # Same closure as an evidence assertion: its ancestry's review history.
                chain = await self._visit_assertion(decision.assertion_id)
                await self._review_history([r.id for r in chain])
        if row.split_of_version_id is not None:
            predecessor = await self._visit_version(
                row.split_of_version_id, slot_id, full=full, path=path | {version_id}
            )
            self.topology.link("split_of", ver_ref, predecessor)
        return ver_ref

    async def version_root(self, version_id: UUID, anchor: ResourceKey) -> None:
        meta = await self._version_meta(version_id)
        # Canonical roots use their own fact-slot anchor only (Step 4.3).
        if anchor.type != ResourceType.FACT_SLOT or anchor.id != meta.slot_id:
            raise LineageNotFound()
        root_ref = await self._visit_version(version_id, meta.slot_id, full=True, path=frozenset())
        changes = await self._all(
            select(
                CanonicalFactChangeRow.id,
                CanonicalFactChangeRow.from_version_id,
                CanonicalFactChangeRow.to_version_id,
                CanonicalFactChangeRow.tenant_id,
                CanonicalFactChangeRow.knowledge_base_id,
            )
            .where(
                or_(
                    CanonicalFactChangeRow.to_version_id == version_id,
                    CanonicalFactChangeRow.from_version_id == version_id,
                )
            )
            .order_by(CanonicalFactChangeRow.id)
        )
        for change in changes:
            self.topology.own(change.tenant_id, change.knowledge_base_id)
            ch_ref = _ref("fact_change", change.id)
            self.topology.add(ch_ref)
            for kind, endpoint in (
                ("changed_from", change.from_version_id),
                ("changed_to", change.to_version_id),
            ):
                if endpoint is None:
                    continue  # a creation change has no predecessor
                target = (
                    root_ref
                    if endpoint == version_id
                    else await self._visit_version(
                        endpoint, meta.slot_id, full=False, path=frozenset()
                    )
                )
                self.topology.link(kind, ch_ref, target)


class _Loader:
    """Loads exactly the planned rows after every READ requirement was decided."""

    def __init__(self, session: AsyncSession, topology: _Topology) -> None:
        self._session = session
        self._topology = topology
        self._by_kind: dict[str, list[UUID]] = {}
        for ref in topology.refs:
            self._by_kind.setdefault(ref.kind, []).append(ref.id)

    def _ids(self, kind: str) -> list[UUID]:
        return sorted(self._by_kind.get(kind, []), key=str)

    async def _rows(self, model: Any, kind: str) -> list[Any]:
        ids = self._ids(kind)
        if not ids:
            return []
        rows = list(
            (
                await self._session.execute(
                    select(model).where(model.id.in_(ids)).with_for_update(read=True)
                )
            ).scalars()
        )
        if len(rows) != len(ids):
            raise LineageUnavailable()
        return rows

    async def load(self) -> tuple[list[ProvenanceRecord], list[MetadataGap]]:
        records: list[ProvenanceRecord] = []
        gaps: list[MetadataGap] = []
        assertion_versions: dict[UUID, int] = {}
        verified: dict[UUID, dict] = {}

        for row in await self._rows(Assertion, "assertion"):
            ref = _ref("assertion", row.id)
            assertion_versions[row.id] = row.semantic_contract_version
            semantics: dict | None = None
            if row.semantic_contract_version == 2:
                sem = await self._session.get(AssertionSemantics, row.id)
                if sem is None:
                    # Missing mandatory v2 carrier is an integrity failure, never legacy.
                    raise LineageUnavailable()
                semantics = sem.record
                for entry in sem.verified_evidence:
                    verified[UUID(str(entry["evidence_id"]))] = entry
                if sem.fact_mode == "DERIVED":
                    # No derivation producer is delivered yet (F0018); never fabricated.
                    gaps.append(MetadataGap(ref, "derivation", "DERIVATION_UNAVAILABLE"))
            else:
                gaps.append(MetadataGap(ref, "semantics", "LEGACY_UNQUALIFIED"))
            if row.origin != "HUMAN_REVIEW" and row.run_id is None:
                gaps.append(MetadataGap(ref, "run_id", "METADATA_UNAVAILABLE"))
            records.append(
                ProvenanceRecord(
                    "assertion",
                    row.id,
                    {
                        "semantic_contract_version": row.semantic_contract_version,
                        "version": row.version,
                        "run_id": str(row.run_id) if row.run_id else None,
                        "origin": row.origin,
                        "original_assertion_id": str(row.original_assertion_id)
                        if row.original_assertion_id
                        else None,
                        "subject_type": row.subject_type,
                        "slot_type": row.slot_type,
                        "value": row.value,
                        "model_confidence": row.model_confidence,
                        "interpretation_basis": row.interpretation_basis,
                        "created_at": _utc(row.created_at),
                        "semantics": semantics,
                    },
                )
            )

        for row in await self._rows(AssertionEvidence, "evidence"):
            ref = _ref("evidence", row.id)
            stored = verified.get(row.id)
            if stored is None:
                legacy = assertion_versions.get(row.assertion_id) != 2
                gaps.append(
                    MetadataGap(
                        ref,
                        "stored_content_record",
                        "LEGACY_UNQUALIFIED" if legacy else "METADATA_UNAVAILABLE",
                    )
                )
            records.append(
                ProvenanceRecord(
                    "evidence",
                    row.id,
                    {
                        "assertion_id": str(row.assertion_id),
                        "artifact_id": str(row.artifact_id),
                        "block_id": row.block_id,
                        "page": row.page,
                        "bbox": row.bbox,
                        "char_start": row.char_start,
                        "char_end": row.char_end,
                        "precision": row.precision,
                        "created_at": _utc(row.created_at),
                        "stored_content_record": stored,
                    },
                )
            )

        for row in await self._rows(ContentArtifact, "content_artifact"):
            ref = _ref("content_artifact", row.id)
            if row.artifact_contract_version is None:
                gaps.append(MetadataGap(ref, "artifact_contract_version", "LEGACY_UNQUALIFIED"))
            records.append(
                ProvenanceRecord(
                    "content_artifact",
                    row.id,
                    {
                        "document_version_id": str(row.document_version_id),
                        "artifact_sha256": row.artifact_sha256,
                        "artifact_contract_version": row.artifact_contract_version,
                        "manifest_sha256": row.manifest_sha256,
                        "recipe_sha256": row.recipe_sha256,
                        "publication_state": row.publication_state,
                        "created_at": _utc(row.created_at),
                    },
                )
            )

        for row in await self._rows(DocumentVersion, "document_version"):
            records.append(
                ProvenanceRecord(
                    "document_version",
                    row.id,
                    {
                        "source_document_id": str(row.source_document_id),
                        "created_at": _utc(row.created_at),
                    },
                )
            )

        for row in await self._rows(SourceDocument, "source_document"):
            records.append(
                ProvenanceRecord(
                    "source_document",
                    row.id,
                    {"source_sha256": row.source_sha256, "created_at": _utc(row.created_at)},
                )
            )

        for row in await self._rows(SemanticInterpretationRun, "interpretation_run"):
            records.append(
                ProvenanceRecord(
                    "interpretation_run",
                    row.id,
                    {
                        "artifact_id": str(row.artifact_id),
                        "profile_id": row.profile_id,
                        "profile_version": row.profile_version,
                        "status": row.status,
                        "run_configuration": row.run_configuration,
                        "counters": row.counters,
                        "created_at": _utc(row.created_at),
                    },
                )
            )

        for row in await self._rows(ReviewDecisionRow, "review_decision"):
            records.append(ProvenanceRecord("review_decision", row.id, _decision_json(row)))

        for row in await self._rows(ReviewSubmissionAttemptRow, "review_attempt"):
            attempt = ReviewSubmissionAttempt(
                id=row.id,
                tenant_id=row.tenant_id,
                knowledge_base_id=row.knowledge_base_id,
                review_item_id=row.review_item_id,
                review_batch_id=row.review_batch_id,
                original_assertion_id=row.original_assertion_id,
                reviewer_principal_id=row.reviewer_principal_id,
                submitted_at=row.submitted_at,
                event_sha256=row.event_sha256,
                assertion_version=row.assertion_version,
                action=row.action,
                reason_code=row.reason_code,
                corrected_value=row.corrected_value,
                evidence=row.evidence,
                reviewer_comment=row.reviewer_comment,
                outcome=row.outcome,
                authorization_decision_id=row.authorization_decision_id,
            )
            records.append(ProvenanceRecord("review_attempt", row.id, attempt.to_json()))

        for row in await self._rows(LearningCandidateReservationRow, "learning_reservation"):
            reservation = LearningCandidateReservation(
                id=row.id,
                tenant_id=row.tenant_id,
                knowledge_base_id=row.knowledge_base_id,
                review_decision_id=row.review_decision_id,
                original_assertion_id=row.original_assertion_id,
                corrected_assertion_id=row.corrected_assertion_id,
                reviewer_principal_id=row.reviewer_principal_id,
                reserved_at=row.reserved_at,
            )
            records.append(ProvenanceRecord("learning_reservation", row.id, reservation.to_json()))

        versions = {
            row.id: row for row in await self._rows(CanonicalFactVersionRow, "fact_version")
        }
        for row in versions.values():
            ref = _ref("fact_version", row.id)
            if row.temporal_contract is None:
                gaps.append(MetadataGap(ref, "temporal", "LEGACY_UNQUALIFIED"))
            refs = row.evidence.get("refs", []) if isinstance(row.evidence, dict) else []
            ending = row.evidence.get("ending_refs", []) if isinstance(row.evidence, dict) else []
            if any(UUID(str(e)) in self._topology.unregistered for e in (*refs, *ending)) or (
                row.review_decision_id is not None
                and row.review_decision_id in self._topology.unregistered
            ):
                gaps.append(MetadataGap(ref, "evidence_refs", "LEGACY_UNQUALIFIED"))
            records.append(ProvenanceRecord("fact_version", row.id, _version_json(row)))

        for row in await self._rows(CanonicalFactChangeRow, "fact_change"):
            ref = _ref("fact_change", row.id)
            to_version = versions.get(row.to_version_id)
            commit_id = to_version.commit_id if to_version is not None else None
            actor = await self._commit_actor(commit_id) if commit_id is not None else None
            if commit_id is None:
                gaps.append(MetadataGap(ref, "commit_id", "METADATA_UNAVAILABLE"))
            if actor is None:
                gaps.append(MetadataGap(ref, "actor_principal_id", "METADATA_UNAVAILABLE"))
            records.append(
                ProvenanceRecord(
                    "fact_change",
                    row.id,
                    {
                        "from_version_id": str(row.from_version_id)
                        if row.from_version_id
                        else None,
                        "to_version_id": str(row.to_version_id),
                        "reason": row.reason,
                        "created_at": _utc(row.created_at),
                        "actor_principal_id": str(actor) if actor else None,
                        "commit_id": str(commit_id) if commit_id else None,
                    },
                )
            )
        return records, gaps

    async def _commit_actor(self, commit_id: UUID) -> UUID | None:
        """The actor only from an unambiguous stored relation: the commit's
        authorization decision audit row. Never guessed from the request."""
        decision_id = await self._session.scalar(
            select(CanonicalCommitRow.authorization_decision_id).where(
                CanonicalCommitRow.id == commit_id
            )
        )
        if decision_id is None:
            return None
        actors = (
            (
                await self._session.execute(
                    select(AuditEventRow.actor_principal_id)
                    .where(
                        AuditEventRow.decision_id == decision_id,
                        AuditEventRow.event_type == "authorization_decision",
                    )
                    .distinct()
                )
            )
            .scalars()
            .all()
        )
        return actors[0] if len(actors) == 1 else None


def _decision_json(row: ReviewDecisionRow) -> dict[str, Any]:
    """The stored decision in the review-decision schema shape (native values)."""
    return {
        "id": str(row.id),
        "review_item_id": str(row.review_item_id),
        "review_batch_id": str(row.review_batch_id),
        "action": row.action,
        "reason_code": row.reason_code,
        "corrected_value": row.corrected_value,
        "corrected_assertion_id": str(row.corrected_assertion_id)
        if row.corrected_assertion_id
        else None,
        "evidence": _decision_evidence(row.evidence),
        "reviewer_principal_id": str(row.reviewer_principal_id),
        "reviewer_comment": row.reviewer_comment,
        "decided_at": _utc(row.decided_at),
        "assertion_version": row.assertion_version,
        "stale": row.stale,
        "event_sha256": row.event_sha256,
    }


def _decision_evidence(evidence: dict | None) -> dict | None:
    """Stored locators keep their values; absent optional members are omitted, not
    invented (the schema has no null for `part` or `unresolved_reason`)."""
    if evidence is None:
        return None
    return {key: value for key, value in evidence.items() if value is not None}


def _version_json(row: CanonicalFactVersionRow) -> dict[str, Any]:
    """The shipped fact-version-read-v1 normalization (FactVersionOut), applied to
    the exact stored row. `temporal` is absent for a legacy pilot version."""
    from brain_persistence.repositories import _fact_version_from_row

    version = _fact_version_from_row(row)
    result: dict[str, Any] = {
        "id": str(version.id),
        "fact_slot_id": str(version.fact_slot_id),
        "value": dict(version.value),
        "valid_start": _utc(version.valid_start),
        "valid_end": _utc(version.valid_end),
        "recorded_start": _utc(version.recorded_start),
        "recorded_end": _utc(version.recorded_end),
        "change_reason": version.change_reason.value if version.change_reason else None,
        "evidence_refs": [str(e) for e in version.evidence_refs],
        "commit_id": str(version.commit_id),
        "canonical_accepted_at": _utc(version.canonical_accepted_at),
        "review_decision_id": str(version.review_decision_id)
        if version.review_decision_id
        else None,
        "source_received_at": _utc(version.source_received_at),
        "artifact_created_at": _utc(version.artifact_created_at),
        "assertion_created_at": _utc(version.assertion_created_at),
    }
    if version.temporal is not None:
        result["temporal"] = version.temporal.to_json()
    return result
