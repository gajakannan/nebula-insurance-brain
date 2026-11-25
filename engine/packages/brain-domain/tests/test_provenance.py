"""F0009 provenance carriers and graph invariants (assembly plan Edge Semantics)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from brain_domain.authx import ResourceKey, ResourceType
from brain_domain.provenance import (
    EDGE_PAIRS,
    MAX_RECORDS,
    LearningCandidateReservation,
    MetadataGap,
    ProvenanceContractError,
    ProvenanceEdge,
    ProvenanceQuery,
    ProvenanceRecord,
    ProvenanceResult,
    RecordRef,
    ReviewSubmissionAttempt,
)

T, K = uuid4(), uuid4()


def _rec(kind: str, identity: UUID | None = None) -> ProvenanceRecord:
    return ProvenanceRecord(kind, identity or uuid4(), {})


def _result(records, edges, gaps=()) -> ProvenanceResult:
    return ProvenanceResult.assemble(
        root=records[0].ref,
        tenant_id=T,
        knowledge_base_id=K,
        records=records,
        edges=edges,
        gaps=gaps,
    )


def test_query_round_trip_and_shape_only_refusals() -> None:
    query = ProvenanceQuery(
        root=RecordRef("fact_version", uuid4()),
        anchor=ResourceKey(ResourceType.FACT_SLOT, uuid4()),
    )
    assert ProvenanceQuery.from_json(query.to_json()) == query
    wire = query.to_json()
    for bad in (
        {**wire, "principal_id": str(uuid4())},  # no authority on the wire
        {**wire, "contract": "provenance-query/v2"},
        {**wire, "root": {"kind": "evidence", "id": str(uuid4())}},
        {**wire, "root": {"kind": "assertion", "id": "not-a-uuid"}},
        {**wire, "anchor": {"type": "tenant", "id": str(uuid4())}},
        {k: v for k, v in wire.items() if k != "anchor"},
    ):
        with pytest.raises(ProvenanceContractError):
            ProvenanceQuery.from_json(bad)


def test_edge_table_is_closed_and_directional() -> None:
    a, e = RecordRef("assertion", uuid4()), RecordRef("evidence", uuid4())
    ProvenanceEdge("supported_by", a, e)
    with pytest.raises(ProvenanceContractError):
        ProvenanceEdge("supported_by", e, a)  # reversed direction
    with pytest.raises(ProvenanceContractError):
        ProvenanceEdge("reviewed_by", a, a)  # retired kind
    with pytest.raises(ProvenanceContractError):
        ProvenanceEdge("located_in", a, e)  # wrong endpoint kind
    assert len(EDGE_PAIRS) == 17


def test_assemble_is_deterministic_and_labels_completeness_honestly() -> None:
    root, ev, art = _rec("assertion"), _rec("evidence"), _rec("content_artifact")
    edges = [
        ProvenanceEdge("located_in", ev.ref, art.ref),
        ProvenanceEdge("supported_by", root.ref, ev.ref),
    ]
    complete = _result([root, art, ev], edges)
    assert complete.completeness == "COMPLETE"
    assert [r.kind for r in complete.records] == ["assertion", "content_artifact", "evidence"]
    assert [e.kind for e in complete.edges] == ["located_in", "supported_by"]
    gap = MetadataGap(root.ref, "semantics", "LEGACY_UNQUALIFIED")
    incomplete = _result([root, art, ev], list(reversed(edges)), [gap, gap])
    assert incomplete.completeness == "INCOMPLETE" and incomplete.gaps == (gap,)
    assert incomplete.to_json()["edges"] == complete.to_json()["edges"]


def test_root_missing_duplicate_and_dangling_endpoints_refuse() -> None:
    root, other = _rec("assertion"), _rec("evidence")
    with pytest.raises(ProvenanceContractError):
        ProvenanceResult(
            root=RecordRef("assertion", uuid4()),
            tenant_id=T,
            knowledge_base_id=K,
            completeness="COMPLETE",
            records=(root.__class__("assertion", root.id, {}),),
            edges=(),
            gaps=(),
        )
    with pytest.raises(ProvenanceContractError):
        _result([root, ProvenanceRecord("assertion", root.id, {})], [])
    with pytest.raises(ProvenanceContractError):
        _result([root], [ProvenanceEdge("supported_by", root.ref, other.ref)])


def test_unreachable_record_is_an_assembly_defect() -> None:
    root, island = _rec("assertion"), _rec("evidence")
    with pytest.raises(ProvenanceContractError, match="connected"):
        _result([root, island], [])


def test_completeness_must_agree_with_gaps() -> None:
    root = _rec("assertion")
    with pytest.raises(ProvenanceContractError):
        ProvenanceResult(
            root=root.ref,
            tenant_id=T,
            knowledge_base_id=K,
            completeness="COMPLETE",
            records=(root,),
            edges=(),
            gaps=(MetadataGap(root.ref, "semantics", "LEGACY_UNQUALIFIED"),),
        )


def test_correction_and_split_cycles_refuse_but_shared_predecessors_do_not() -> None:
    a, b = _rec("assertion"), _rec("assertion")
    with pytest.raises(ProvenanceContractError, match="cycle"):
        _result(
            [a, b],
            [
                ProvenanceEdge("corrected_from", a.ref, b.ref),
                ProvenanceEdge("corrected_from", b.ref, a.ref),
            ],
        )
    v1, v2, v3 = _rec("fact_version"), _rec("fact_version"), _rec("fact_version")
    dag = _result(
        [v1, v2, v3],
        [ProvenanceEdge("split_of", v1.ref, v3.ref), ProvenanceEdge("split_of", v2.ref, v3.ref)],
    )
    assert dag.completeness == "COMPLETE"


def test_record_limit_refuses_at_limit_plus_one() -> None:
    root = _rec("fact_version")
    evidence = [_rec("evidence") for _ in range(MAX_RECORDS)]
    edges = [ProvenanceEdge("supported_by", root.ref, e.ref) for e in evidence]
    with pytest.raises(ProvenanceContractError, match="limit"):
        _result([root, *evidence], edges)


def test_reservation_and_attempt_carriers() -> None:
    now = datetime.now(UTC)
    reservation = LearningCandidateReservation(
        id=uuid4(),
        tenant_id=T,
        knowledge_base_id=K,
        review_decision_id=uuid4(),
        original_assertion_id=uuid4(),
        corrected_assertion_id=uuid4(),
        reviewer_principal_id=uuid4(),
        reserved_at=now,
    )
    assert reservation.to_json()["contract"] == "learning-candidate-reservation/v1"
    same = uuid4()
    with pytest.raises(ProvenanceContractError):
        LearningCandidateReservation(
            id=uuid4(),
            tenant_id=T,
            knowledge_base_id=K,
            review_decision_id=uuid4(),
            original_assertion_id=same,
            corrected_assertion_id=same,
            reviewer_principal_id=uuid4(),
            reserved_at=now,
        )
    with pytest.raises(ProvenanceContractError):
        LearningCandidateReservation(
            id=uuid4(),
            tenant_id=T,
            knowledge_base_id=K,
            review_decision_id=uuid4(),
            original_assertion_id=uuid4(),
            corrected_assertion_id=uuid4(),
            reviewer_principal_id=uuid4(),
            reserved_at=now.replace(tzinfo=None),
        )
    base = dict(
        id=uuid4(),
        tenant_id=T,
        knowledge_base_id=K,
        review_item_id=uuid4(),
        review_batch_id=uuid4(),
        original_assertion_id=uuid4(),
        reviewer_principal_id=uuid4(),
        submitted_at=now,
        event_sha256="a" * 64,
        assertion_version=1,
        action="CORRECT",
        reason_code="MISREAD_VALUE",
        corrected_value={"amount": "1"},
        evidence=None,
        reviewer_comment=None,
        outcome="BATCH_REFUSED",
        authorization_decision_id=uuid4(),
    )
    assert ReviewSubmissionAttempt(**base).to_json()["outcome"] == "BATCH_REFUSED"
    for bad in (
        {"outcome": "APPLIED"},
        {"event_sha256": "A" * 64},
        {"assertion_version": 0},
        {"action": "COMMIT"},
    ):
        with pytest.raises(ProvenanceContractError):
            ReviewSubmissionAttempt(**{**base, **bad})
