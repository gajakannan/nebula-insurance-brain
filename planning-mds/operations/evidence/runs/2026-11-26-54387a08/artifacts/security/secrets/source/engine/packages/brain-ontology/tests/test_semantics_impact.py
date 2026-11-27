"""ADR-0081 D2 inference subset, RDF export (S0007 AC2 unit level) and the impact
report (S0006 AC1-AC4 unit level, EX-ONT-003/004)."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import pytest
from brain_domain.ontology import report_digest, term_iri
from brain_ontology.impact import ReleaseSnapshot, analyze, assemble
from brain_ontology.rdf_export import NEBULA, RDFS, Literal, to_jsonld, to_turtle, triples
from brain_ontology.semantics import ClosureBoundExceeded, Entailment, closure

SCOPE = (UUID("00000000-0000-4000-8000-000000000001"), UUID("00000000-0000-4000-8000-000000000002"))


def term(tid: str, kind: str = "class", **extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": tid,
        "iri": term_iri(tid),
        "kind": kind,
        "labels": {"en-US": tid},
        "definition": f"Definition of {tid} for tests.",
    }
    if kind == "class":
        base["parents"] = []
    base.update(extra)
    return base


def prop(tid: str, domain: str, range_: str, **extra: Any) -> dict[str, Any]:
    return term(tid, "object_property", domain=domain, range=range_, temporal_kind="STATE", **extra)


def snap(
    ref: str,
    terms: list[dict[str, Any]],
    constraints: list[dict[str, Any]] | None = None,
    records: list[dict[str, Any]] | None = None,
) -> ReleaseSnapshot:
    digest = ref * 64
    return ReleaseSnapshot(
        f"ontrel:sha256-{digest}", digest, terms, constraints or [], records or []
    )


def ent(s: str, r: str, o: str) -> Entailment:
    return Entailment(term_iri(s), r, term_iri(o))


# --- semantics ----------------------------------------------------------------


def test_closure_reflexive_transitive_and_inverse() -> None:
    terms = [
        term("x.a"),
        term("x.b", parents=["x.a"]),
        term("x.c", parents=["x.b"]),
        prop("x.p", "x.a", "x.a"),
        prop("x.q", "x.a", "x.a", sub_property_of=["x.p"]),
        prop("x.r", "x.a", "x.a", inverse_of="x.p"),
    ]
    result = closure(terms)
    assert ent("x.c", "subClassOf", "x.a") in result
    assert ent("x.a", "subClassOf", "x.a") in result
    assert ent("x.q", "subPropertyOf", "x.p") in result
    assert ent("x.p", "inverseOf", "x.r") in result and ent("x.r", "inverseOf", "x.p") in result


def test_domain_and_range_never_infer() -> None:
    """S0001 AC6: no entailment mentions a domain/range class through the property."""
    terms = [term("x.a"), term("x.b"), prop("x.p", "x.a", "x.b")]
    result = closure(terms)
    assert all(e.relation != "rdf:type" for e in result)
    assert ent("x.a", "subClassOf", "x.b") not in result
    assert {e.relation for e in result} <= {"subClassOf", "subPropertyOf", "inverseOf"}


def test_closure_bound() -> None:
    terms = [term(f"x.c{i}", parents=[f"x.c{i - 1}"] if i else []) for i in range(30)]
    with pytest.raises(ClosureBoundExceeded):
        closure(terms, bound=50)


def test_rdf_export_deterministic_and_equivalent() -> None:
    terms = [
        term("x.a", aliases=[{"tag": "fr-FR", "value": 'Chose "a"'}]),
        term("x.b", parents=["x.a"]),
        prop("x.p", "x.a", "x.b", predicate_key="xx:p@v1"),
        term(
            "x.r", "datatype_property", domain="x.a", range="xsd:decimal", temporal_kind="ETERNAL"
        ),
        term("x.k", "code_value", code_of="x.a", external_codes={"Scheme": "K", "Other": None}),
    ]
    rows = triples("ontrel:sha256-" + "a" * 64, "x@1", terms)
    assert rows == triples("ontrel:sha256-" + "a" * 64, "x@1", list(reversed(terms)))
    assert (term_iri("x.b"), RDFS + "subClassOf", term_iri("x.a")) in rows
    assert (term_iri("x.p"), NEBULA + "validationDomain", term_iri("x.a")) in rows
    assert not any(p in (RDFS + "domain", RDFS + "range") for _, p, _ in rows)
    assert (term_iri("x.k"), NEBULA + "externalCode", Literal("Scheme=K")) in rows
    ttl = to_turtle(rows)
    assert '\\"a\\"' in ttl and "@fr-FR" in ttl
    graph = json.loads(to_jsonld(rows))
    count = sum(len(v) for node in graph for k, v in node.items() if k != "@id")
    assert count == len(rows)


# --- impact report ---------------------------------------------------------------


def test_first_release_report() -> None:
    cand = snap("a", [term("x.a"), term("x.b", parents=["x.a"])])
    analysis = analyze(None, cand)
    report = assemble(SCOPE, None, cand, analysis, [])
    assert report["predecessor"] is None and report["status"] == "complete"
    assert {c["class"] for c in report["changes"]} == {"additive"}
    assert report["inference"]["result"] == "no_change_within_scope"
    assert "first release" in report["inference"]["scope"]
    assert report["report_digest"] == report_digest(report)
    assert [u["owner"] for u in report["unexamined"]] == ["F0015", "F0065", "F0034"]


def test_ex_ont_003_entailment_change_in_an_additive_edit() -> None:
    pred = snap("a", [term("x.a"), term("x.b")])
    cand = snap("b", [term("x.a", parents=["x.b"]), term("x.b")])
    analysis = analyze(pred, cand)
    assert analysis.changes == [
        {
            "term_iri": term_iri("x.a"),
            "class": "additive",
            "detail": "axioms added to an existing term",
        }
    ]
    assert analysis.inference["result"] == "changes_detected"
    assert analysis.inference["added"] == [ent("x.a", "subClassOf", "x.b").to_json()]
    assert not analysis.unresolved


def test_ex_ont_004_constraint_tightening_with_unchanged_closure() -> None:
    c = {
        "id": "x.c.currency",
        "construct": "minCardinality",
        "subject": "x.a",
        "property": "x.p",
        "value": 0,
        "stage": "canonical-admission",
        "consumer": "F0065 assessment",
        "applicability": "money values",
        "severity": "violation",
        "on_nonconformance": "refuse",
        "data_basis": "asserted",
    }
    terms = [term("x.a"), prop("x.p", "x.a", "x.a")]
    pred = snap("a", terms, [c])
    cand = snap("b", terms, [{**c, "value": 1}])
    analysis = analyze(pred, cand)
    assert analysis.inference["result"] == "no_change_within_scope"
    assert analysis.constraints == [
        {
            "constraint_id": "x.c.currency",
            "consumer": "F0065 assessment",
            "change": "tightened",
            "detail": "minCardinality 0 -> 1",
        }
    ]
    assert {
        "term_iri": term_iri("x.a"),
        "class": "constraint_tightening",
        "detail": "a constraint on this term is stricter",
    } in analysis.changes


def test_constraint_diffs_by_kind() -> None:
    base = {
        "id": "x.c",
        "construct": "maxCardinality",
        "subject": "x.a",
        "property": "x.p",
        "value": 2,
        "stage": "example-validation",
        "consumer": "gate",
        "applicability": "all",
        "severity": "warning",
        "on_nonconformance": "warn",
        "data_basis": "asserted",
    }
    terms = [term("x.a"), prop("x.p", "x.a", "x.a")]
    variants = {
        "loosened": {"value": 3},
        "stage_changed": {"stage": "authoring"},
        "data_basis_changed": {"data_basis": {"inferred": "nebula-tbox-subset/v1"}},
        "applicability_changed": {"applicability": "some"},
    }
    for change, delta in variants.items():
        analysis = analyze(snap("a", terms, [base]), snap("b", terms, [{**base, **delta}]))
        assert change in {c["change"] for c in analysis.constraints}, change
    severity = analyze(
        snap("a", terms, [base]), snap("b", terms, [{**base, "severity": "violation"}])
    )
    assert {c["change"] for c in severity.constraints} == {"tightened"}
    added = analyze(
        snap("a", terms, []),
        snap("b", terms, [{**base, "severity": "violation", "stage": "authoring"}]),
    )
    assert added.constraints[0]["change"] == "added"
    assert any(c["class"] == "constraint_tightening" for c in added.changes)
    removed = analyze(snap("a", terms, [base]), snap("b", terms, []))
    assert removed.constraints[0]["change"] == "removed"
    operands = analyze(
        snap("a", terms, [{**base, "construct": "disjoint", "with": ["x.a"]}]),
        snap("b", terms, [{**base, "construct": "disjoint", "with": ["x.p"]}]),
    )
    assert operands.constraints[0]["change"] == "applicability_changed"


def test_rename_split_retirement_and_unclassified() -> None:
    pred = snap(
        "a",
        [term("x.a"), term("x.b"), term("x.c"), prop("x.p", "x.a", "x.a", predicate_key="xx:p@v1")],
    )
    records = [
        {
            "class": "split",
            "source_iris": [term_iri("x.b")],
            "replacement_iris": [term_iri("x.b1"), term_iri("x.b2")],
            "rationale": "split",
        },
    ]
    cand = snap(
        "b",
        [
            term("x.a", labels={"en-US": "Renamed"}),
            term("x.b1"),
            term("x.b2"),
            term("x.c", definition="Silently redefined without a record."),
            prop("x.p", "x.a", "x.a", predicate_key="xx:p@v1"),
        ],
        records=records,
    )
    analysis = analyze(pred, cand)
    classes = {c["term_iri"]: c["class"] for c in analysis.changes}
    assert classes[term_iri("x.a")] == "rename_alias"
    assert classes[term_iri("x.b")] == "split" and classes[term_iri("x.b1")] == "split"
    assert classes[term_iri("x.c")] == "unclassified"
    report = assemble(SCOPE, pred, cand, analysis, [])
    assert report["status"] == "incomplete" and report["unresolved"]

    gone = analyze(pred, snap("c", [t for t in pred.terms if t["id"] != "x.c"]))
    assert {c["class"] for c in gone.changes if c["term_iri"] == term_iri("x.c")} == {
        "unclassified"
    }
    assert "xx:p@v1" not in gone.predicate_keys
    retired = analyze(
        pred,
        snap(
            "d",
            [t for t in pred.terms if t["id"] != "x.p"],
            records=[
                {
                    "class": "retirement",
                    "source_iris": [term_iri("x.p")],
                    "replacement_iris": [],
                    "rationale": "r",
                }
            ],
        ),
    )
    assert {c["class"] for c in retired.changes} == {"retirement"}
    assert retired.predicate_keys == {"xx:p@v1"}


def test_bound_exceeded_is_unresolved_never_no_change() -> None:
    chain = [term(f"x.c{i}", parents=[f"x.c{i - 1}"] if i else []) for i in range(30)]
    analysis = analyze(snap("a", chain), snap("b", chain), bound=50)
    assert analysis.inference["result"] == "unresolved"
    report = assemble(SCOPE, snap("a", chain), snap("b", chain), analysis, [])
    assert report["status"] == "incomplete"


def test_report_reach_and_determinism() -> None:
    pred = snap("a", [term("x.a")])
    cand = snap("b", [term("x.a"), prop("x.p", "x.a", "x.a", predicate_key="xx:p@v1")])
    reach = [
        {"population": "fact_slot", "predicate_key": "xx:p@v1", "affected": 0, "denominator": 7}
    ]
    first = assemble(SCOPE, pred, cand, analyze(pred, cand), reach)
    second = assemble(SCOPE, pred, cand, analyze(pred, cand), reach)
    assert first == second and first["reach"] == reach
