"""F0006 scoped assertion persistence and existing-consumer enforcement.

Every method uses the caller's unit of work. This adapter never commits or
constructs authority; source reads require current, staged authorization audit.
"""

from __future__ import annotations

import copy
import hashlib
import json
import unicodedata
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from functools import partial
from typing import Any
from uuid import UUID, uuid4, uuid5

from brain_assertions.eligibility import AssertionIneligible, evaluate_eligibility, require_eligible
from brain_assertions.normalization import locate_quote
from brain_assertions.ports import NameClaimConflict
from brain_content.contracts import decode_json
from brain_content.service import ArtifactMetadata
from brain_content.store import ContentArtifactStore
from brain_content.validation import ArtifactIntegrityError, VerifiedBundle
from brain_contracts.assertions import AdmittedAssertion, AssertionRecordV2
from brain_domain.assertions import ProducerContext, SourceAccessProof, TimeReference, VerifiedBlock
from brain_domain.authx import Action, AuthorizationDecision, ResourceKey, ResourceType
from brain_domain.review import EvidenceLocator
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from brain_persistence.assertion_models import (
    AssertionDocumentReference,
    AssertionNameClaim,
    AssertionSemantics,
)
from brain_persistence.content_repository import ContentArtifactRepository
from brain_persistence.models import (
    Assertion,
    AssertionEvidence,
    AuditEventRow,
    ContentArtifact,
    DocumentVersion,
    ReviewDecisionRow,
    ReviewItemRow,
    SemanticInterpretationRun,
)
from brain_persistence.tenancy import inherit_resource_access

NORMALIZATION_VERSION = "f0006-grounding-v1"
OPEN_SLOT = "__OPEN_STATEMENT_V2__"


class AssertionIdConflict(ValueError):
    code = "ASSERTION_ID_CONFLICT"


class UnsupportedAssertionCorrection(ValueError):
    """The existing review payload cannot express a semantic change safely."""


def canonical_json(value: Any) -> bytes:
    def serialize(item: Any) -> Any:
        if isinstance(item, (UUID, datetime)):
            return str(item) if isinstance(item, UUID) else item.isoformat()
        if hasattr(item, "model_dump"):
            return item.model_dump(mode="json")
        raise TypeError("non-JSON value")

    return json.dumps(
        value,
        default=serialize,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def hash_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def normalized_name(value: str) -> str:
    # WHY: name identity deliberately omits quote-specific currency/hyphen rules.
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def carrier_value(record: Mapping[str, Any]) -> dict:
    obj = record["object"]
    if obj["kind"] == "ENTITY":
        return {"object_ref": str(obj["ref"])}
    value = obj["value"]
    return copy.deepcopy(value) if isinstance(value, dict) else {"literal": value}


def wire_evidence(value: Mapping[str, Any]) -> dict:
    """Private retained hashes are not part of the protected wire schema."""
    return {key: copy.deepcopy(item) for key, item in value.items() if not key.startswith("_")}


async def _current_audits(
    session: AsyncSession,
    *,
    keys: Sequence[ResourceKey],
    action: str,
    actor_id: UUID,
    owner: tuple[UUID, UUID],
    decision_ids: Sequence[UUID] | None = None,
) -> list[AuditEventRow]:
    """Only decisions inserted by this unit of work can authorize its effects.

    The facade stages success audit before invoking the mutation. Checking xmin
    prevents a direct caller from replaying a successful historical decision.
    """
    if not keys:
        return []
    if session.get_bind().dialect.name != "postgresql":
        raise PermissionError("current source authorization required")
    query = select(AuditEventRow).where(
        AuditEventRow.event_type == "authorization_decision",
        AuditEventRow.action == str(action),
        AuditEventRow.actor_principal_id == actor_id,
        AuditEventRow.decision.is_(True),
        AuditEventRow.operation_outcome == "succeeded",
        text("audit_event.xmin::text = pg_current_xact_id()::text"),
    )
    if decision_ids is not None:
        query = query.where(AuditEventRow.decision_id.in_(decision_ids))
    rows = list((await session.execute(query)).scalars())
    valid = {}
    for row in rows:
        scope = (row.payload or {}).get("scope", {})
        if (scope.get("tenant_id"), scope.get("knowledge_base_id")) == tuple(map(str, owner)):
            valid[(row.resource_type, row.resource_id)] = row
    if any((str(key.type), key.id) not in valid for key in keys):
        raise PermissionError("current source authorization required")
    return [valid[(str(key.type), key.id)] for key in keys]


class SqlAlchemyAdmissionSources:
    """F0004 verified bytes projected through the authorized source port."""

    def __init__(
        self,
        session: AsyncSession,
        content_store: ContentArtifactStore,
        *,
        time_resolver: Callable[[ProducerContext, UUID], Awaitable[TimeReference]] | None = None,
        action: str = Action.INTERPRET,
    ) -> None:
        self.session = session
        self.content_store = content_store
        self.time_resolver = time_resolver
        self.action = action

    async def _bundle(self, context: ProducerContext) -> tuple[ArtifactMetadata, VerifiedBundle]:
        await _current_audits(
            self.session,
            keys=[ResourceKey(ResourceType.CONTENT_ARTIFACT, context.artifact_id)],
            action=self.action,
            actor_id=context.actor_id,
            owner=(context.tenant_id, context.knowledge_base_id),
        )
        metadata = await self.session.run_sync(
            lambda s: ContentArtifactRepository(s).get_metadata(context.artifact_id)
        )
        if (metadata.key.tenant_id, metadata.key.knowledge_base_id, metadata.version_id) != (
            context.tenant_id,
            context.knowledge_base_id,
            context.document_version_id,
        ):
            raise PermissionError("source scope mismatch")
        bundle = await self.content_store.load_verified(metadata.key)
        metadata.verify_identity(bundle)
        await self.session.run_sync(lambda s: ContentArtifactRepository(s).verify_indexes(bundle))
        return metadata, bundle

    async def block(self, context: ProducerContext, block_id: str) -> VerifiedBlock:
        _, bundle = await self._bundle(context)
        native = decode_json(bundle.files["docling-document.json"])
        if bundle.key.contract_version == 2:
            block = next((b for b in bundle.blocks if b.block_id == block_id), None)
            if block is None:
                raise LookupError("source block missing")
            anchor = block.origin_anchor.model_dump(mode="json")
            selector = {
                **anchor,
                "block_id": block_id,
                "native_ref": block.native_ref,
                "precision": "block",
            }
            regions = anchor.get("regions", [])
            if len(regions) == 1:
                selector.update({k: v for k, v in regions[0].items() if v is not None})
            node: Any = native
            try:
                for part in block.native_ref.removeprefix("#/").split("/"):
                    part = part.replace("~1", "/").replace("~0", "~")
                    node = node[int(part)] if isinstance(node, list) else node[part]
            except (KeyError, IndexError, TypeError, ValueError):
                raise ArtifactIntegrityError("native selector is unresolved") from None
            if isinstance(node, dict) and isinstance(node.get("source_locator"), dict):
                selector.update(copy.deepcopy(node["source_locator"]))
            cells = [
                (t, cell) for t in bundle.tables for cell in t.cells if block_id in cell.block_ids
            ]
            if len(cells) == 1:
                table, cell = cells[0]
                selector.update(
                    table_id=table.table_id,
                    cell_id=cell.cell_id,
                    row=cell.row_start,
                    column=cell.col_start,
                    precision="table_cell",
                )
            return VerifiedBlock(
                context.artifact_id,
                block_id,
                block.text,
                selector,
                block.text_origin,
                "qualified",
                block.producer.model_dump(mode="json"),
                block.confidence,
            )
        records = [
            decode_json(line) for line in bundle.files["blocks.jsonl"].splitlines() if line.strip()
        ]
        block = next((b for b in records if str(b.get("block_id", b.get("id"))) == block_id), None)
        if block is None or not isinstance(block.get("text"), str):
            raise LookupError("source block missing")
        selector = {
            key: copy.deepcopy(value)
            for key, value in block.items()
            if key not in ("text", "text_origin", "producer", "confidence")
        }
        selector.update(block_id=block_id, precision="block")
        return VerifiedBlock(
            context.artifact_id,
            block_id,
            block["text"],
            selector,
            None,
            "legacy_unqualified",
            None,
            None,
        )

    async def time_reference(self, context: ProducerContext, ref: UUID) -> TimeReference:
        if self.time_resolver is None:
            raise LookupError("time reference not registered")
        resolved = await self.time_resolver(context, ref)
        if (resolved.id, resolved.tenant_id, resolved.knowledge_base_id, resolved.artifact_id) != (
            ref,
            context.tenant_id,
            context.knowledge_base_id,
            context.artifact_id,
        ):
            raise PermissionError("time reference scope mismatch")
        return resolved


class SqlAlchemyAssertionRepository:
    def __init__(
        self, session: AsyncSession, *, content_store: ContentArtifactStore | None = None
    ) -> None:
        self.session = session
        self.content_store = content_store

    async def lock_context(self, context: ProducerContext) -> None:
        await _current_audits(
            self.session,
            keys=[ResourceKey(ResourceType.CONTENT_ARTIFACT, context.artifact_id)],
            action=Action.INTERPRET,
            actor_id=context.actor_id,
            owner=(context.tenant_id, context.knowledge_base_id),
        )
        run = await self.session.get(SemanticInterpretationRun, context.run_id)
        artifact = await self.session.get(ContentArtifact, context.artifact_id)
        if (
            run is None
            or artifact is None
            or (run.artifact_id, run.tenant_id, run.knowledge_base_id)
            != (context.artifact_id, context.tenant_id, context.knowledge_base_id)
            or (artifact.document_version_id, artifact.tenant_id, artifact.knowledge_base_id)
            != (context.document_version_id, context.tenant_id, context.knowledge_base_id)
        ):
            raise PermissionError("assertion source scope mismatch")
        version = (
            await self.session.execute(
                select(DocumentVersion)
                .where(DocumentVersion.id == context.document_version_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if version is None or (version.tenant_id, version.knowledge_base_id) != (
            context.tenant_id,
            context.knowledge_base_id,
        ):
            raise PermissionError("assertion document scope mismatch")

    async def _retain_references(self, context: ProducerContext, item: AdmittedAssertion) -> None:
        for entity in sorted(item.metadata.entity_snapshots, key=lambda x: x["id"]):
            ref = UUID(entity["id"])
            existing = await self.session.get(AssertionDocumentReference, ref)
            if existing is not None:
                if (
                    existing.document_version_id,
                    existing.tenant_id,
                    existing.knowledge_base_id,
                    existing.entity_type,
                    existing.label,
                ) != (
                    context.document_version_id,
                    context.tenant_id,
                    context.knowledge_base_id,
                    entity["entity_type"],
                    entity["label"],
                ):
                    raise AssertionIdConflict("ASSERTION_ID_CONFLICT")
            else:
                self.session.add(
                    AssertionDocumentReference(
                        id=ref,
                        document_version_id=context.document_version_id,
                        tenant_id=context.tenant_id,
                        knowledge_base_id=context.knowledge_base_id,
                        entity_type=entity["entity_type"],
                        label=entity["label"],
                        created_by=context.actor_id,
                        created_at=item.created_at,
                    )
                )
                await self.session.flush()
            name = normalized_name(entity["label"])
            key = (context.document_version_id, context.tenant_id, context.knowledge_base_id, name)
            claim = await self.session.get(AssertionNameClaim, key)
            if claim is not None:
                if claim.entity_ref != ref:
                    raise NameClaimConflict("NAME_CLAIMED_BY_ANOTHER")
            else:
                self.session.add(
                    AssertionNameClaim(
                        document_version_id=context.document_version_id,
                        tenant_id=context.tenant_id,
                        knowledge_base_id=context.knowledge_base_id,
                        normalized_name=name,
                        entity_ref=ref,
                        created_by=context.actor_id,
                        created_at=item.created_at,
                    )
                )
                await self.session.flush()

    async def persist(
        self, context: ProducerContext, item: AdmittedAssertion, *, delivery_key: str
    ) -> AdmittedAssertion:
        record = item.record.model_dump(mode="json")
        metadata = item.metadata
        verified = [e.model_dump(mode="json") for e in item.server_evidence]
        artifact = await self.session.get(ContentArtifact, context.artifact_id)
        if artifact is None:
            raise PermissionError("assertion source scope mismatch")
        for value in verified:
            value["_source_hashes"] = {
                "block": metadata.source_hashes.get(value["block_id"]),
                "artifact": artifact.artifact_sha256,
                "manifest": artifact.manifest_sha256,
            }
        digest = hash_json(
            {
                "record": record,
                "entities": metadata.entity_snapshots,
                "time_references": metadata.time_reference_snapshot,
                "verified_evidence": verified,
                "context": vars(context),
                "delivery_key": delivery_key,
                "normalization_version": NORMALIZATION_VERSION,
            }
        )
        existing = await self.session.get(Assertion, item.record.id)
        if existing is not None:
            sem = await self.session.get(AssertionSemantics, existing.id)
            if (
                existing.semantic_contract_version != 2
                or sem is None
                or (existing.tenant_id, existing.knowledge_base_id, existing.run_id)
                != (context.tenant_id, context.knowledge_base_id, context.run_id)
                or sem.admission_sha256 != digest
            ):
                raise AssertionIdConflict("ASSERTION_ID_CONFLICT")
            return item.model_copy(
                update={"created_by": sem.created_by, "created_at": sem.created_at}
            )
        # WHY: failed name ownership must roll back its references without losing
        # independently admitted siblings; infrastructure failures still propagate.
        async with self.session.begin_nested():
            await self._retain_references(context, item)
            subject = next(e for e in metadata.entity_snapshots if e["id"] == record["subject_ref"])
            self.session.add(
                Assertion(
                    id=item.record.id,
                    run_id=context.run_id,
                    semantic_contract_version=2,
                    origin=record["origin"],
                    original_assertion_id=None,
                    subject_type=subject["entity_type"],
                    slot_type=record["predicate_id"] or OPEN_SLOT,
                    value=carrier_value(record),
                    model_confidence=record["model_confidence"],
                    interpretation_basis=record["interpretation_basis"],
                    tenant_id=context.tenant_id,
                    knowledge_base_id=context.knowledge_base_id,
                    created_at=item.created_at.replace(tzinfo=None),
                )
            )
            await self.session.flush()
            self.session.add(
                AssertionSemantics(
                    assertion_id=item.record.id,
                    document_version_id=context.document_version_id,
                    tenant_id=context.tenant_id,
                    knowledge_base_id=context.knowledge_base_id,
                    subject_ref=UUID(record["subject_ref"]),
                    object_ref=UUID(record["object"]["ref"])
                    if record["object"]["kind"] == "ENTITY"
                    else None,
                    assertion_kind=record["assertion_kind"],
                    fact_mode=record["mode"],
                    assertion_origin=record["origin"],
                    predicate_id=record["predicate_id"],
                    ontology_release=record["ontology_release"],
                    record=record,
                    entity_snapshots=list(metadata.entity_snapshots),
                    verified_evidence=verified,
                    time_reference_snapshot=list(metadata.time_reference_snapshot),
                    raw_item_sha256=metadata.raw_item_sha256,
                    admission_sha256=digest,
                    created_by=context.actor_id,
                    created_at=item.created_at,
                )
            )
            await self.session.flush()
            for value in verified:
                self.session.add(
                    _evidence_row(
                        item.record.id, context.tenant_id, context.knowledge_base_id, value
                    )
                )
            await self.session.flush()
            if (
                item.review_required
                or record["model_confidence"] is None
                or record["model_confidence"] < 0.5
            ):
                reasons = item.reasons or ("LOW_CONFIDENCE",)
                for reason in reasons:
                    review_id = uuid5(item.record.id, reason)
                    first = verified[0]
                    provenance = reason in (
                        "DESCRIBED_EVIDENCE",
                        "UNRESOLVED_EVIDENCE",
                        "LEGACY_UNQUALIFIED",
                    )
                    self.session.add(
                        ReviewItemRow(
                            id=review_id,
                            type="PROVENANCE_CORRECTION" if provenance else "EXTRACTION_CORRECTION",
                            status="open",
                            assertion_id=item.record.id,
                            assertion_version=1,
                            tenant_id=context.tenant_id,
                            knowledge_base_id=context.knowledge_base_id,
                            evidence=_review_locator(first),
                        )
                    )
                    await self.session.flush()
                    await self.session.run_sync(
                        partial(
                            inherit_resource_access,
                            source=ResourceKey(ResourceType.CONTENT_ARTIFACT, context.artifact_id),
                            target=ResourceKey(ResourceType.REVIEW_TASK, review_id),
                            actor_id=context.actor_id,
                            at=item.created_at,
                            add_dependency_on_source=True,
                        )
                    )
        return item

    async def source_keys(self, assertion_id: UUID) -> tuple[ResourceKey, ...]:
        try:
            discovery = await discover_sources(
                self.session, (), None, assertion_ids=(assertion_id,)
            )
        except AssertionIneligible:
            raise LookupError("assertion source unavailable") from None
        return discovery.keys

    async def project(self, assertion_id: UUID) -> dict:
        row = await self.session.get(Assertion, assertion_id)
        if row is None:
            raise LookupError("assertion not found")
        sem = await self.session.get(AssertionSemantics, assertion_id)
        result = {
            "id": str(row.id),
            "semantic_contract_version": row.semantic_contract_version,
            "run_id": str(row.run_id) if row.run_id else None,
            "origin": row.origin,
            "original_assertion_id": str(row.original_assertion_id)
            if row.original_assertion_id
            else None,
            "subject_type": row.subject_type,
            "slot_type": row.slot_type,
            "value": copy.deepcopy(row.value),
            "interpretation_basis": row.interpretation_basis,
            "model_confidence": row.model_confidence,
            "tenant_id": str(row.tenant_id),
            "knowledge_base_id": str(row.knowledge_base_id),
            "created_at": row.created_at.isoformat(),
        }
        if row.semantic_contract_version == 1:
            if row.origin == "MACHINE_EXTRACTION":
                result["compatibility_origin"] = "DOCUMENT_INTERPRETATION"
            return result
        if sem is None:
            raise AssertionIneligible()
        support = [wire_evidence(e) for e in sem.verified_evidence]
        eligibility = evaluate_eligibility(sem.record, support)
        result.update(
            record=copy.deepcopy(sem.record),
            server_evidence=support,
            review_required=eligibility.review_required,
            reasons=list(eligibility.reasons),
            blocked_operations=list(eligibility.blocked_operations),
            created_by=str(sem.created_by),
            created_at=sem.created_at.isoformat(),
        )
        # The reserved carrier has no meaning in an old reader.
        result.pop("slot_type")
        return result


def _review_locator(evidence: Mapping[str, Any]) -> dict:
    precision = {"span": "exact-span", "table_cell": "table-cell"}.get(
        evidence["precision"], evidence["precision"]
    )
    return {
        "source": str(evidence["artifact_id"]),
        "precision": precision,
        "part": evidence["block_id"],
        "unresolved_reason": "unresolved" if precision == "unresolved" else None,
        "selector": [copy.deepcopy(evidence["selector"])],
    }


def _evidence_row(
    assertion_id: UUID, tenant_id: UUID, kb_id: UUID, value: Mapping[str, Any]
) -> AssertionEvidence:
    selector = value["selector"]
    return AssertionEvidence(
        id=UUID(str(value["evidence_id"])),
        assertion_id=assertion_id,
        artifact_id=UUID(str(value["artifact_id"])),
        block_id=value["block_id"],
        page=selector.get("page"),
        bbox=selector.get("bbox"),
        char_start=selector.get("char_start"),
        char_end=selector.get("char_end"),
        precision=value["precision"],
        tenant_id=tenant_id,
        knowledge_base_id=kb_id,
    )


@dataclass(frozen=True)
class SourceDiscovery:
    keys: tuple[ResourceKey, ...]
    has_v2: bool


async def discover_sources(
    session: AsyncSession,
    evidence_refs: Sequence[UUID],
    review_decision_id: UUID | None,
    *,
    assertion_ids: Sequence[UUID] = (),
) -> SourceDiscovery:
    """Resolve authority keys without materializing a claim or source excerpt.

    Column projections deliberately avoid ORM entities: identity-map population
    must not make protected payloads available before the READ decision.
    """
    seeds = set(assertion_ids)
    if evidence_refs:
        seeds.update(
            (
                await session.execute(
                    select(AssertionEvidence.assertion_id).where(
                        AssertionEvidence.id.in_(evidence_refs)
                    )
                )
            ).scalars()
        )
    if review_decision_id is not None:
        decision = (
            await session.execute(
                select(
                    ReviewDecisionRow.review_item_id, ReviewDecisionRow.corrected_assertion_id
                ).where(ReviewDecisionRow.id == review_decision_id)
            )
        ).one_or_none()
        if decision is not None:
            assertion_id = await session.scalar(
                select(ReviewItemRow.assertion_id).where(
                    ReviewItemRow.id == decision.review_item_id
                )
            )
            if assertion_id is None:
                raise AssertionIneligible()
            seeds.add(assertion_id)
            if decision.corrected_assertion_id is not None:
                seeds.add(decision.corrected_assertion_id)
    parents: dict[UUID, UUID | None] = {}
    has_v2 = False
    for seed in sorted(seeds, key=str):
        seen: set[UUID] = set()
        current: UUID | None = seed
        while current is not None:
            if current in seen or len(seen) >= 256:
                raise AssertionIneligible()
            seen.add(current)
            if current not in parents:
                row = (
                    await session.execute(
                        select(
                            Assertion.original_assertion_id, Assertion.semantic_contract_version
                        ).where(Assertion.id == current)
                    )
                ).one_or_none()
                if row is None or row.semantic_contract_version not in (1, 2):
                    raise AssertionIneligible()
                parents[current] = row.original_assertion_id
                has_v2 |= row.semantic_contract_version == 2
            current = parents[current]
    artifacts = (
        (
            await session.execute(
                select(AssertionEvidence.artifact_id)
                .distinct()
                .where(AssertionEvidence.assertion_id.in_(parents))
            )
        ).scalars()
        if parents
        else ()
    )
    return SourceDiscovery(
        tuple(
            sorted(ResourceKey(ResourceType.CONTENT_ARTIFACT, identity) for identity in artifacts)
        ),
        has_v2,
    )


@dataclass
class SourceLineage:
    assertions: list[Assertion]
    semantics: list[AssertionSemantics]
    evidence: list[AssertionEvidence]
    keys: tuple[ResourceKey, ...]
    has_v2: bool
    incomplete: bool
    invalid: bool
    reviewed: bool


async def resolve_lineage(
    session: AsyncSession,
    evidence_refs: Sequence[UUID],
    review_decision_id: UUID | None,
    *,
    assertion_ids: Sequence[UUID] = (),
) -> SourceLineage:
    seeds = set(assertion_ids)
    supplied = (
        list(
            (
                await session.execute(
                    select(AssertionEvidence).where(AssertionEvidence.id.in_(evidence_refs))
                )
            ).scalars()
        )
        if evidence_refs
        else []
    )
    seeds.update(e.assertion_id for e in supplied)
    incomplete = len({e.id for e in supplied}) != len(set(evidence_refs))
    reviewed = False
    review_seeds: set[UUID] = set()
    invalid = False
    if review_decision_id is not None:
        decision = await session.get(ReviewDecisionRow, review_decision_id)
        if decision is None:
            incomplete = True
        else:
            item = await session.get(ReviewItemRow, decision.review_item_id)
            if item is None:
                invalid = True
            else:
                review_seeds.add(item.assertion_id)
                if (decision.tenant_id, decision.knowledge_base_id) != (
                    item.tenant_id,
                    item.knowledge_base_id,
                ):
                    invalid = True
            if decision.corrected_assertion_id is not None:
                review_seeds.add(decision.corrected_assertion_id)
            seeds.update(review_seeds)
            reviewed = not decision.stale and decision.action in ("ACCEPT", "CORRECT")
    rows: dict[UUID, Assertion] = {}
    review_chain: set[UUID] = set()
    for seed in sorted(seeds, key=str):
        seen: set[UUID] = set()
        current: UUID | None = seed
        while current is not None:
            if current in seen or len(seen) >= 256:
                invalid = True
                break
            seen.add(current)
            row = await session.get(Assertion, current)
            if row is None:
                invalid = True
                break
            if seed in review_seeds:
                review_chain.add(current)
            rows[current] = row
            current = row.original_assertion_id
    if review_seeds and any(e.assertion_id not in review_chain for e in supplied):
        invalid = True
    semantics: list[AssertionSemantics] = []
    all_evidence = (
        list(
            (
                await session.execute(
                    select(AssertionEvidence).where(AssertionEvidence.assertion_id.in_(rows))
                )
            ).scalars()
        )
        if rows
        else []
    )
    has_v2 = any(a.semantic_contract_version == 2 for a in rows.values())
    for row in rows.values():
        sem = await session.get(AssertionSemantics, row.id)
        if row.semantic_contract_version == 2:
            if sem is None:
                invalid = True
            else:
                semantics.append(sem)
                if (sem.tenant_id, sem.knowledge_base_id) != (row.tenant_id, row.knowledge_base_id):
                    invalid = True
        elif sem is not None:
            invalid = True
    keys = tuple(
        sorted({ResourceKey(ResourceType.CONTENT_ARTIFACT, e.artifact_id) for e in all_evidence})
    )
    for evidence in all_evidence:
        owner = rows[evidence.assertion_id]
        artifact = await session.get(ContentArtifact, evidence.artifact_id)
        if (
            artifact is None
            or (evidence.tenant_id, evidence.knowledge_base_id)
            != (owner.tenant_id, owner.knowledge_base_id)
            or (artifact.tenant_id, artifact.knowledge_base_id)
            != (owner.tenant_id, owner.knowledge_base_id)
        ):
            invalid = True
    return SourceLineage(
        list(rows.values()), semantics, all_evidence, keys, has_v2, incomplete, invalid, reviewed
    )


def issue_source_access(
    session: AsyncSession, decisions: Sequence[AuthorizationDecision]
) -> SourceAccessProof | None:
    reads = [
        d
        for d in decisions
        if str(d.action) == str(Action.READ)
        and d.resource.type == ResourceType.CONTENT_ARTIFACT
        and d.allowed
        and d.scope is not None
    ]
    owners = {(d.scope.tenant_id, d.scope.knowledge_base_id) for d in reads if d.scope is not None}
    if not owners:
        return None
    if len(owners) > 1:
        raise AssertionIneligible()
    (owner,) = owners
    proof = SourceAccessProof(
        owner[0],
        owner[1],
        uuid4(),
        tuple(sorted({d.resource.id for d in reads}, key=str)),
        tuple(d.decision_id for d in reads),
    )
    session.info["f0006_source_proof"] = (
        proof,
        session.get_transaction(),
        reads[0].actor_principal_id,
    )
    return proof


async def require_commit_sources(
    session: AsyncSession,
    *,
    evidence_refs: Sequence[UUID],
    review_decision_id: UUID | None,
    authorized_scope: tuple[UUID, UUID],
    closes_existing: bool,
    source_access: SourceAccessProof | None,
) -> None:
    discovery = await discover_sources(session, evidence_refs, review_decision_id)
    if not discovery.has_v2:
        return  # Explicit pilot compatibility: unregistered legacy UUIDs remain accepted.
    issued = session.info.get("f0006_source_proof")
    if (
        source_access is None
        or issued is None
        or issued[0] is not source_access
        or issued[1] is not session.get_transaction()
        or (source_access.tenant_id, source_access.knowledge_base_id) != authorized_scope
        or set(source_access.source_artifact_ids) != {k.id for k in discovery.keys}
    ):
        raise AssertionIneligible()
    try:
        await _current_audits(
            session,
            keys=discovery.keys,
            action=Action.READ,
            actor_id=issued[2],
            owner=authorized_scope,
            decision_ids=source_access.authorization_decision_ids,
        )
    except PermissionError as exc:
        raise AssertionIneligible() from exc
    lineage = await resolve_lineage(session, evidence_refs, review_decision_id)
    if (
        lineage.invalid
        or lineage.incomplete
        or not lineage.keys
        or set(lineage.keys) != set(discovery.keys)
        or any((a.tenant_id, a.knowledge_base_id) != authorized_scope for a in lineage.assertions)
    ):
        raise AssertionIneligible()
    for sem in lineage.semantics:
        require_eligible(
            sem.record,
            [wire_evidence(e) for e in sem.verified_evidence],
            closes_existing=closes_existing,
            reviewed=lineage.reviewed,
        )


async def correct_assertion_v2(
    session: AsyncSession,
    original: Assertion,
    *,
    value: dict,
    evidence: EvidenceLocator | None,
    actor_id: UUID | None,
    item: ReviewItemRow | None,
    content_store: ContentArtifactStore | None,
) -> UUID:
    sem = await session.get(AssertionSemantics, original.id)
    if sem is None or actor_id is None or item is None:
        raise UnsupportedAssertionCorrection("v2 correction context required")
    owner = (original.tenant_id, original.knowledge_base_id)
    lineage = await resolve_lineage(session, (), None, assertion_ids=(original.id,))
    if lineage.invalid or not lineage.keys:
        raise UnsupportedAssertionCorrection("v2 source unavailable")
    await _current_audits(
        session, keys=lineage.keys, action=Action.READ, actor_id=actor_id, owner=owner
    )
    await _current_audits(
        session,
        keys=[ResourceKey(ResourceType.REVIEW_TASK, item.id)],
        action=Action.ANNOTATE,
        actor_id=actor_id,
        owner=owner,
    )
    record = copy.deepcopy(sem.record)
    if record["assertion_kind"] == "OPEN_STATEMENT" or record["object"]["kind"] == "ENTITY":
        if value != carrier_value(record):
            raise UnsupportedAssertionCorrection("semantic editing requires a new contract")
    else:
        record["object"] = {
            "kind": "LITERAL",
            "value": value["literal"] if set(value) == {"literal"} else value,
        }
    verified = copy.deepcopy(sem.verified_evidence)
    if evidence is not None and asdict(evidence) != item.evidence:
        if content_store is None or len(verified) == 0 or evidence.part is None:
            raise UnsupportedAssertionCorrection("new evidence requires source admission")
        try:
            artifact_id = UUID(evidence.source)
        except ValueError:
            raise UnsupportedAssertionCorrection("source identity required") from None
        if artifact_id not in {key.id for key in lineage.keys}:
            raise UnsupportedAssertionCorrection("correction source changed")
        context = ProducerContext(
            original.tenant_id,
            original.knowledge_base_id,
            actor_id,
            artifact_id,
            sem.document_version_id,
            original.run_id or original.id,
            "HUMAN_REVIEW",
            "human-review",
            "human-review",
            str(item.id),
        )
        source = await SqlAlchemyAdmissionSources(session, content_store, action=Action.READ).block(
            context, evidence.part
        )
        quote = verified[0]["quote"]
        location = locate_quote(source.text, quote, source.native_selector)
        if location is None:
            raise UnsupportedAssertionCorrection("quote is absent from new locator")
        artifact = await session.get(ContentArtifact, artifact_id)
        if artifact is None:
            raise UnsupportedAssertionCorrection("source artifact not found")
        verified = [
            {
                "artifact_id": str(artifact_id),
                "block_id": source.block_id,
                "quote": quote,
                "normalization_version": NORMALIZATION_VERSION,
                "precision": location.precision,
                "selector": location.selector,
                "text_origin": source.text_origin,
                "origin_qualification": source.origin_qualification,
                "producer": dict(source.producer) if source.producer else None,
                "producer_confidence": source.producer_confidence,
                "_source_hashes": {
                    "block": hashlib.sha256(source.text.encode()).hexdigest(),
                    "artifact": artifact.artifact_sha256,
                    "manifest": artifact.manifest_sha256,
                },
            }
        ]
        record["evidence"] = [
            {
                "artifact_id": str(artifact_id),
                "block_id": source.block_id,
                "quote": quote,
                "model_selector": None,
            }
        ]
    child_id = uuid4()
    record.update(id=str(child_id), origin="HUMAN_REVIEW", model_confidence=None)
    # JSON validation is strict, offline, and refuses unsupported semantic edits.
    try:
        AssertionRecordV2.model_validate_json(canonical_json(record))
    except (ValueError, TypeError) as exc:
        raise UnsupportedAssertionCorrection("invalid corrected claim") from exc
    for ordinal, entry in enumerate(verified):
        entry["evidence_id"] = str(uuid5(child_id, str(ordinal)))
    now = datetime.now(UTC)
    raw_hash = hash_json(
        {
            "review_item_id": str(item.id),
            "assertion_version": item.assertion_version,
            "corrected_value": value,
            "evidence_seen": asdict(evidence) if evidence else None,
        }
    )
    digest = hash_json(
        {
            "record": record,
            "original_assertion_id": str(original.id),
            "verified_evidence": verified,
            "normalization_version": NORMALIZATION_VERSION,
            "reviewer_principal_id": str(actor_id),
            "review_item_id": str(item.id),
        }
    )
    session.add(
        Assertion(
            id=child_id,
            run_id=None,
            semantic_contract_version=2,
            origin="HUMAN_REVIEW",
            original_assertion_id=original.id,
            subject_type=original.subject_type,
            slot_type=original.slot_type,
            value=carrier_value(record),
            model_confidence=None,
            interpretation_basis=original.interpretation_basis,
            tenant_id=original.tenant_id,
            knowledge_base_id=original.knowledge_base_id,
            created_at=now.replace(tzinfo=None),
        )
    )
    await session.flush()
    session.add(
        AssertionSemantics(
            assertion_id=child_id,
            document_version_id=sem.document_version_id,
            tenant_id=sem.tenant_id,
            knowledge_base_id=sem.knowledge_base_id,
            subject_ref=sem.subject_ref,
            object_ref=sem.object_ref,
            assertion_kind=sem.assertion_kind,
            fact_mode=sem.fact_mode,
            assertion_origin="HUMAN_REVIEW",
            predicate_id=sem.predicate_id,
            ontology_release=sem.ontology_release,
            record=record,
            entity_snapshots=copy.deepcopy(sem.entity_snapshots),
            verified_evidence=verified,
            time_reference_snapshot=copy.deepcopy(sem.time_reference_snapshot),
            raw_item_sha256=raw_hash,
            admission_sha256=digest,
            created_by=actor_id,
            created_at=now,
        )
    )
    for entry in verified:
        session.add(_evidence_row(child_id, sem.tenant_id, sem.knowledge_base_id, entry))
    await session.flush()
    return child_id
