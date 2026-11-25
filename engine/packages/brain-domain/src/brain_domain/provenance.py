"""F0009 provenance and correction-lineage carriers (ADR-0080, Proposed).

Frozen, I/O-free carriers for the internal provenance reader, the reserved
future-learning identity and the non-applied review submission. The graph
invariants here go beyond schema shape (assembly plan "Edge Semantics"):
closed per-kind endpoint pairs, unique records/edges, endpoint presence,
connectivity to the root, acyclic directional ancestry and an honest
COMPLETE/INCOMPLETE label. Nothing here authorizes anything.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, get_args
from uuid import UUID

from brain_domain.authx import ResourceKey, ResourceType

JsonObject = Mapping[str, Any]

QUERY_CONTRACT = "provenance-query/v1"
RESULT_CONTRACT = "provenance-result/v1"
RESERVATION_CONTRACT = "learning-candidate-reservation/v1"
ATTEMPT_CONTRACT = "review-submission-attempt/v1"

# Fixed traversal limits (assembly plan Step 4). Refusal happens at limit + 1.
MAX_CORRECTION_LINKS = 256
MAX_RECORDS = 2048
MAX_EDGES = 8192

RootKind = Literal["assertion", "fact_version"]
RecordKind = Literal[
    "assertion",
    "evidence",
    "content_artifact",
    "document_version",
    "source_document",
    "interpretation_run",
    "review_decision",
    "review_attempt",
    "learning_reservation",
    "fact_version",
    "fact_change",
    "derivation_reference",
]
EdgeKind = Literal[
    "corrected_from",
    "supported_by",
    "ending_evidence",
    "located_in",
    "interpreted_in",
    "interprets",
    "artifact_of",
    "version_of",
    "reviews",
    "created_assertion",
    "reserved_learning",
    "recorded_decision",
    "split_of",
    "changed_from",
    "changed_to",
    "attested_by",
    "derived_from",
]
GapReason = Literal["LEGACY_UNQUALIFIED", "METADATA_UNAVAILABLE", "DERIVATION_UNAVAILABLE"]
Completeness = Literal["COMPLETE", "INCOMPLETE"]
AttemptOutcome = Literal["ALREADY_DECIDED", "BATCH_REFUSED"]

ROOT_KINDS: frozenset[str] = frozenset(get_args(RootKind))
RECORD_KINDS: frozenset[str] = frozenset(get_args(RecordKind))
EDGE_KINDS: frozenset[str] = frozenset(get_args(EdgeKind))
ANCHOR_TYPES: frozenset[ResourceType] = frozenset(
    {ResourceType.FACT_SLOT, ResourceType.REVIEW_TASK, ResourceType.CONTENT_ARTIFACT}
)

# The closed edge table: kind -> allowed (source kind, target kind) pairs.
EDGE_PAIRS: Mapping[str, frozenset[tuple[str, str]]] = {
    "corrected_from": frozenset({("assertion", "assertion")}),
    "supported_by": frozenset({("assertion", "evidence"), ("fact_version", "evidence")}),
    "ending_evidence": frozenset({("fact_version", "evidence")}),
    "located_in": frozenset({("evidence", "content_artifact")}),
    "interpreted_in": frozenset({("assertion", "interpretation_run")}),
    "interprets": frozenset({("interpretation_run", "content_artifact")}),
    "artifact_of": frozenset({("content_artifact", "document_version")}),
    "version_of": frozenset({("document_version", "source_document")}),
    "reviews": frozenset({("review_decision", "assertion"), ("review_attempt", "assertion")}),
    "created_assertion": frozenset({("review_decision", "assertion")}),
    "reserved_learning": frozenset({("review_decision", "learning_reservation")}),
    "recorded_decision": frozenset({("fact_version", "review_decision")}),
    "split_of": frozenset({("fact_version", "fact_version")}),
    "changed_from": frozenset({("fact_change", "fact_version")}),
    "changed_to": frozenset({("fact_change", "fact_version")}),
    "attested_by": frozenset({("fact_version", "content_artifact")}),
    "derived_from": frozenset(
        {("assertion", "derivation_reference"), ("fact_version", "derivation_reference")}
    ),
}
# Directional ancestry that must stay acyclic.
ACYCLIC_EDGE_KINDS = frozenset({"corrected_from", "split_of"})


class ProvenanceContractError(ValueError):
    """A carrier or result violates the provenance contract or graph invariants."""


class LineageNotFound(Exception):
    """Non-disclosing refusal: the root/anchor association is invalid, a protected
    target is dangling or ownership disagrees. Callers map it to the same 404 used
    for an unknown or inaccessible root (S0001 AC7, S0004 AC2)."""

    def __init__(self) -> None:
        super().__init__("lineage not found")


class LineageUnavailable(Exception):
    """A cycle, an exceeded limit, a topology change between discovery and load, or
    an output invariant failure. No partial graph is returned (S0001 AC5)."""

    def __init__(self) -> None:
        super().__init__("lineage unavailable")


@dataclass(frozen=True, slots=True, order=True)
class RecordRef:
    kind: str
    id: UUID

    def __post_init__(self) -> None:
        if self.kind not in RECORD_KINDS:
            raise ProvenanceContractError("unknown record kind")
        if not isinstance(self.id, UUID):
            raise ProvenanceContractError("record id must be a UUID")

    def to_json(self) -> dict[str, str]:
        return {"kind": self.kind, "id": str(self.id)}


@dataclass(frozen=True, slots=True)
class ProvenanceQuery:
    root: RecordRef
    anchor: ResourceKey
    contract: str = QUERY_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != QUERY_CONTRACT:
            raise ProvenanceContractError("unsupported query contract")
        if self.root.kind not in ROOT_KINDS:
            raise ProvenanceContractError("root must be an assertion or fact version")
        if self.anchor.type not in ANCHOR_TYPES or not isinstance(self.anchor.id, UUID):
            raise ProvenanceContractError("unsupported anchor")

    @classmethod
    def from_json(cls, value: Mapping[str, Any]) -> ProvenanceQuery:
        """Shape-only parse of the closed wire query. It authorizes nothing."""
        if not isinstance(value, Mapping) or set(value) != {"contract", "root", "anchor"}:
            raise ProvenanceContractError("query must have exactly contract, root and anchor")
        root, anchor = value["root"], value["anchor"]
        if not isinstance(root, Mapping) or set(root) != {"kind", "id"}:
            raise ProvenanceContractError("invalid root")
        if not isinstance(anchor, Mapping) or set(anchor) != {"type", "id"}:
            raise ProvenanceContractError("invalid anchor")
        try:
            root_ref = RecordRef(str(root["kind"]), UUID(str(root["id"])))
            anchor_key = ResourceKey(ResourceType(str(anchor["type"])), UUID(str(anchor["id"])))
        except (ValueError, TypeError) as exc:
            raise ProvenanceContractError("invalid query identity") from exc
        return cls(root=root_ref, anchor=anchor_key, contract=str(value["contract"]))

    def to_json(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "root": self.root.to_json(),
            "anchor": {"type": self.anchor.type.value, "id": str(self.anchor.id)},
        }


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    kind: str
    id: UUID
    data: JsonObject

    @property
    def ref(self) -> RecordRef:
        return RecordRef(self.kind, self.id)

    def to_json(self) -> dict[str, Any]:
        return {"kind": self.kind, "id": str(self.id), "data": dict(self.data)}


@dataclass(frozen=True, slots=True, order=True)
class ProvenanceEdge:
    kind: str
    source: RecordRef
    target: RecordRef

    def __post_init__(self) -> None:
        pairs = EDGE_PAIRS.get(self.kind)
        if pairs is None:
            raise ProvenanceContractError("unknown edge kind")
        if (self.source.kind, self.target.kind) not in pairs:
            raise ProvenanceContractError("edge endpoints do not match its kind")

    def to_json(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "source": self.source.to_json(),
            "target": self.target.to_json(),
        }


@dataclass(frozen=True, slots=True, order=True)
class MetadataGap:
    record: RecordRef
    field: str
    reason: str

    def __post_init__(self) -> None:
        if self.reason not in get_args(GapReason):
            raise ProvenanceContractError("unknown gap reason")
        if not self.field:
            raise ProvenanceContractError("gap field is required")

    def to_json(self) -> dict[str, Any]:
        return {"record": self.record.to_json(), "field": self.field, "reason": self.reason}


def _sort_key_record(record: ProvenanceRecord) -> tuple[str, str]:
    return (record.kind, str(record.id))


def _sort_key_edge(edge: ProvenanceEdge) -> tuple[str, str, str, str, str]:
    return (
        edge.kind,
        edge.source.kind,
        str(edge.source.id),
        edge.target.kind,
        str(edge.target.id),
    )


def _sort_key_gap(gap: MetadataGap) -> tuple[str, str, str, str]:
    return (gap.record.kind, str(gap.record.id), gap.field, gap.reason)


@dataclass(frozen=True, slots=True)
class ProvenanceResult:
    root: RecordRef
    tenant_id: UUID
    knowledge_base_id: UUID
    completeness: str
    records: tuple[ProvenanceRecord, ...]
    edges: tuple[ProvenanceEdge, ...]
    gaps: tuple[MetadataGap, ...]
    contract: str = RESULT_CONTRACT

    def __post_init__(self) -> None:
        validate_graph(self)

    @classmethod
    def assemble(
        cls,
        *,
        root: RecordRef,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        records: Iterable[ProvenanceRecord],
        edges: Iterable[ProvenanceEdge],
        gaps: Iterable[MetadataGap],
    ) -> ProvenanceResult:
        """Deterministic order and an honest completeness label (COMPLETE iff no gap)."""
        ordered_gaps = tuple(sorted(set(gaps), key=_sort_key_gap))
        return cls(
            root=root,
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
            completeness="INCOMPLETE" if ordered_gaps else "COMPLETE",
            records=tuple(sorted(records, key=_sort_key_record)),
            edges=tuple(sorted(set(edges), key=_sort_key_edge)),
            gaps=ordered_gaps,
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "root": self.root.to_json(),
            "tenant_id": str(self.tenant_id),
            "knowledge_base_id": str(self.knowledge_base_id),
            "completeness": self.completeness,
            "records": [r.to_json() for r in self.records],
            "edges": [e.to_json() for e in self.edges],
            "gaps": [g.to_json() for g in self.gaps],
        }


def _has_cycle(edges: Iterable[ProvenanceEdge]) -> bool:
    """Tri-color DFS over the directional ancestry edges only. A shared
    predecessor (a DAG) is not a cycle."""
    graph: dict[RecordRef, list[RecordRef]] = {}
    for edge in edges:
        if edge.kind in ACYCLIC_EDGE_KINDS:
            graph.setdefault(edge.source, []).append(edge.target)
    white, grey, black = 0, 1, 2
    color: dict[RecordRef, int] = {}
    for start in sorted(graph):
        if color.get(start, white) != white:
            continue
        stack: list[tuple[RecordRef, int]] = [(start, 0)]
        color[start] = grey
        while stack:
            node, index = stack[-1]
            successors = graph.get(node, [])
            if index < len(successors):
                stack[-1] = (node, index + 1)
                nxt = successors[index]
                state = color.get(nxt, white)
                if state == grey:
                    return True
                if state == white:
                    color[nxt] = grey
                    stack.append((nxt, 0))
            else:
                color[node] = black
                stack.pop()
    return False


def validate_graph(result: ProvenanceResult) -> None:
    """Graph invariants beyond the schema (assembly plan Edge Semantics)."""
    if result.contract != RESULT_CONTRACT:
        raise ProvenanceContractError("unsupported result contract")
    if result.root.kind not in ROOT_KINDS:
        raise ProvenanceContractError("root must be an assertion or fact version")
    if result.completeness not in ("COMPLETE", "INCOMPLETE"):
        raise ProvenanceContractError("invalid completeness")
    if not result.records:
        raise ProvenanceContractError("a result names at least its root")
    if len(result.records) > MAX_RECORDS or len(result.edges) > MAX_EDGES:
        raise ProvenanceContractError("traversal limit exceeded")
    refs = [r.ref for r in result.records]
    present = set(refs)
    if len(present) != len(refs):
        raise ProvenanceContractError("duplicate record")
    if result.root not in present:
        raise ProvenanceContractError("root record is missing")
    if len(set(result.edges)) != len(result.edges):
        raise ProvenanceContractError("duplicate edge")
    adjacency: dict[RecordRef, set[RecordRef]] = {ref: set() for ref in present}
    for edge in result.edges:
        if edge.source not in present or edge.target not in present:
            raise ProvenanceContractError("edge endpoint is missing")
        adjacency[edge.source].add(edge.target)
        adjacency[edge.target].add(edge.source)
    for gap in result.gaps:
        if gap.record not in present:
            raise ProvenanceContractError("gap names a missing record")
    if (result.completeness == "COMPLETE") != (not result.gaps):
        raise ProvenanceContractError("completeness disagrees with gaps")
    reached = {result.root}
    frontier = [result.root]
    while frontier:
        node = frontier.pop()
        for nxt in adjacency[node]:
            if nxt not in reached:
                reached.add(nxt)
                frontier.append(nxt)
    if reached != present:
        raise ProvenanceContractError("record is not connected to the root")
    if _has_cycle(result.edges):
        raise ProvenanceContractError("directional ancestry contains a cycle")


@dataclass(frozen=True, slots=True)
class LearningCandidateReservation:
    """One server-owned future-learning identity per new effective correction
    (S0005). It conveys no approval, authority, evidence count or benchmark
    membership."""

    id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID
    review_decision_id: UUID
    original_assertion_id: UUID
    corrected_assertion_id: UUID
    reviewer_principal_id: UUID
    reserved_at: datetime
    contract: str = RESERVATION_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != RESERVATION_CONTRACT:
            raise ProvenanceContractError("unsupported reservation contract")
        if self.reserved_at.tzinfo is None:
            raise ProvenanceContractError("reserved_at must be timezone-aware")
        if self.original_assertion_id == self.corrected_assertion_id:
            raise ProvenanceContractError("a correction cannot reserve its own original")

    def to_json(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "knowledge_base_id": str(self.knowledge_base_id),
            "review_decision_id": str(self.review_decision_id),
            "original_assertion_id": str(self.original_assertion_id),
            "corrected_assertion_id": str(self.corrected_assertion_id),
            "reviewer_principal_id": str(self.reviewer_principal_id),
            "reserved_at": self.reserved_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class ReviewSubmissionAttempt:
    """A protected, append-only record of a submission that was not applied
    (S0002 AC6). It is never an accepted decision and carries no child or
    candidate identity."""

    id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID
    review_item_id: UUID
    review_batch_id: UUID
    original_assertion_id: UUID
    reviewer_principal_id: UUID
    submitted_at: datetime
    event_sha256: str
    assertion_version: int
    action: str
    reason_code: str | None
    corrected_value: JsonObject | None
    evidence: JsonObject | None
    reviewer_comment: str | None
    outcome: str
    authorization_decision_id: UUID
    contract: str = ATTEMPT_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != ATTEMPT_CONTRACT:
            raise ProvenanceContractError("unsupported attempt contract")
        if self.outcome not in get_args(AttemptOutcome):
            raise ProvenanceContractError("an attempt is never applied")
        if self.action not in ("ACCEPT", "CORRECT", "REJECT", "BLOCKED"):
            raise ProvenanceContractError("unknown action")
        if self.assertion_version < 1:
            raise ProvenanceContractError("assertion_version must be positive")
        if len(self.event_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in self.event_sha256
        ):
            raise ProvenanceContractError("event_sha256 must be lowercase hex")
        if self.submitted_at.tzinfo is None:
            raise ProvenanceContractError("submitted_at must be timezone-aware")

    def to_json(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "knowledge_base_id": str(self.knowledge_base_id),
            "review_item_id": str(self.review_item_id),
            "review_batch_id": str(self.review_batch_id),
            "original_assertion_id": str(self.original_assertion_id),
            "reviewer_principal_id": str(self.reviewer_principal_id),
            "submitted_at": self.submitted_at.isoformat(),
            "event_sha256": self.event_sha256,
            "assertion_version": self.assertion_version,
            "action": self.action,
            "reason_code": self.reason_code,
            "corrected_value": dict(self.corrected_value)
            if self.corrected_value is not None
            else None,
            "evidence": dict(self.evidence) if self.evidence is not None else None,
            "reviewer_comment": self.reviewer_comment,
            "outcome": self.outcome,
            "authorization_decision_id": str(self.authorization_decision_id),
        }
