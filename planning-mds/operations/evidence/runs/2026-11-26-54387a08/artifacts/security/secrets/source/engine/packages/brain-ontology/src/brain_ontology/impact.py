"""Predecessor-to-candidate impact report (F0012-S0006, ADR-0081 D8, ADR-0045).

`analyze` is pure and deterministic. It classifies every changed term, diffs
the supported inference closure restricted to predecessor terms, and diffs the
constraints per consumer. `assemble` adds scope, reach counts with denominators
and the populations no producer exists for yet, and computes the report digest.
A change it cannot classify, or a closure that exceeds its bound, makes the
report `incomplete`; neither is ever reported as "no change".
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from brain_contracts.schema_runtime import ContractRef, validate_contract
from brain_domain.ontology import (
    IMPACT_CONTRACT,
    RULESET,
    definition_digest,
    only_added_axioms,
    report_digest,
)

from brain_ontology.semantics import DEFAULT_BOUND, ClosureBoundExceeded, closure, restricted

IMPACT_REF = ContractRef("ontology-impact-report-v1", "1")
UNEXAMINED = (
    {
        "population": "extraction profiles and templates",
        "owner": "F0015",
        "reason": "no producer in this release",
    },
    {"population": "stored assessments", "owner": "F0065", "reason": "no producer in this release"},
    {"population": "graph projections", "owner": "F0034", "reason": "no producer in this release"},
)
_STAGE_REFUSES = {
    "authoring",
    "canonical-admission",
    "example-validation",
    "assessment-preconditions",
}


@dataclass(frozen=True, slots=True)
class ReleaseSnapshot:
    release_ref: str
    manifest_digest: str
    terms: Sequence[Mapping[str, Any]]
    constraints: Sequence[Mapping[str, Any]] = ()
    change_records: Sequence[Mapping[str, Any]] = ()

    def ident(self) -> dict[str, str]:
        return {"release_ref": self.release_ref, "manifest_digest": self.manifest_digest}

    def by_iri(self) -> dict[str, Mapping[str, Any]]:
        return {t["iri"]: t for t in self.terms}


@dataclass(slots=True)
class Analysis:
    changes: list[dict[str, str]] = field(default_factory=list)
    inference: dict[str, Any] = field(default_factory=dict)
    constraints: list[dict[str, str]] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    predicate_keys: set[str] = field(default_factory=set)


def _clean(term: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in term.items() if not k.startswith("_")}


def _record_class(iri: str, records: Iterable[Mapping[str, Any]]) -> str | None:
    for record in records:
        if iri in record["source_iris"] or iri in record["replacement_iris"]:
            return str(record["class"])
    return None


def _classify(pred: ReleaseSnapshot | None, cand: ReleaseSnapshot, out: Analysis) -> None:
    before = pred.by_iri() if pred else {}
    after = cand.by_iri()
    records = cand.change_records
    for iri in sorted(set(before) | set(after)):
        old, new = before.get(iri), after.get(iri)
        cls: str | None
        detail = ""
        if old is None:
            cls = _record_class(iri, records) or "additive"
            detail = "new term"
        elif new is None:
            cls = _record_class(iri, records)
            detail = "removed from the candidate"
            if cls is None:
                cls, detail = "unclassified", "removed without a change record"
        else:
            if definition_digest(_clean(old)) == definition_digest(_clean(new)):
                if _clean(old).get("labels") == _clean(new).get("labels") and _clean(old).get(
                    "aliases"
                ) == _clean(new).get("aliases"):
                    continue
                cls, detail = "rename_alias", "labels or aliases changed; definition unchanged"
            else:
                cls = _record_class(iri, records)
                if cls is None and only_added_axioms(old, new):
                    cls, detail = "additive", "axioms added to an existing term"
                elif cls is None:
                    cls, detail = "unclassified", "definition changed without a change record"
        if cls == "unclassified":
            out.unresolved.append(f"{iri}: {detail}")
        out.changes.append({"term_iri": iri, "class": cls, "detail": detail})
        for term in (old, new):
            if term is not None and term.get("predicate_key"):
                out.predicate_keys.add(str(term["predicate_key"]))


def _infer(pred: ReleaseSnapshot | None, cand: ReleaseSnapshot, out: Analysis, bound: int) -> None:
    scope_terms = frozenset(pred.by_iri()) if pred else frozenset()
    scope = (
        "entailments whose subject and object are both predecessor terms"
        if pred
        else "no predecessor: first release, nothing to compare"
    )
    try:
        old = restricted(closure(pred.terms, bound=bound), scope_terms) if pred else set()
        new = restricted(closure(cand.terms, bound=bound), scope_terms) if pred else set()
    except ClosureBoundExceeded as exc:
        out.unresolved.append(f"inference: {exc}")
        out.inference = {
            "ruleset": RULESET,
            "scope": scope,
            "result": "unresolved",
            "added": [],
            "removed": [],
        }
        return
    added = sorted(new - old)
    removed = sorted(old - new)
    out.inference = {
        "ruleset": RULESET,
        "scope": scope,
        "result": "changes_detected" if added or removed else "no_change_within_scope",
        "added": [e.to_json() for e in added],
        "removed": [e.to_json() for e in removed],
    }


def _constraint_entries(old: Mapping[str, Any], new: Mapping[str, Any]) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    if old.get("stage") != new.get("stage"):
        entries.append(("stage_changed", f"{old.get('stage')} -> {new.get('stage')}"))
    if old.get("data_basis") != new.get("data_basis"):
        entries.append(("data_basis_changed", "data basis changed"))
    if old.get("applicability") != new.get("applicability") or old.get("subject") != new.get(
        "subject"
    ):
        entries.append(("applicability_changed", "applicability or subject changed"))
    construct = new.get("construct")
    if old.get("construct") != construct or old.get("property") != new.get("property"):
        entries.append(("applicability_changed", "construct or property changed"))
    elif construct in {"minCardinality", "maxCardinality"} and old.get("value") != new.get("value"):
        stricter = (
            (new["value"] < old["value"])
            if construct == "maxCardinality"
            else (new["value"] > old["value"])
        )
        entries.append(
            (
                "tightened" if stricter else "loosened",
                f"{construct} {old['value']} -> {new['value']}",
            )
        )
    elif sorted(old.get("with", [])) != sorted(new.get("with", [])) or old.get(
        "expression"
    ) != new.get("expression"):
        entries.append(("applicability_changed", "constraint operands changed"))
    if old.get("severity") != new.get("severity"):
        stricter = new.get("severity") == "violation"
        entries.append(
            (
                "tightened" if stricter else "loosened",
                f"severity {old.get('severity')} -> {new.get('severity')}",
            )
        )
    return entries


def _constraints(pred: ReleaseSnapshot | None, cand: ReleaseSnapshot, out: Analysis) -> None:
    before = {c["id"]: c for c in (pred.constraints if pred else ())}
    after = {c["id"]: c for c in cand.constraints}
    tightened_subjects: set[str] = set()
    for cid in sorted(set(before) | set(after)):
        old, new = before.get(cid), after.get(cid)
        if old is None:
            assert new is not None
            if pred is None:
                continue  # a first release has nothing to compare
            out.constraints.append(
                {
                    "constraint_id": cid,
                    "consumer": new["consumer"],
                    "change": "added",
                    "detail": f"new {new['construct']} at {new['stage']}",
                }
            )
            if new.get("severity") == "violation" and new.get("stage") in _STAGE_REFUSES:
                tightened_subjects.add(new["subject"])
        elif new is None:
            out.constraints.append(
                {
                    "constraint_id": cid,
                    "consumer": old["consumer"],
                    "change": "removed",
                    "detail": f"{old['construct']} removed",
                }
            )
        else:
            for change, detail in _constraint_entries(old, new):
                out.constraints.append(
                    {
                        "constraint_id": cid,
                        "consumer": new["consumer"],
                        "change": change,
                        "detail": detail,
                    }
                )
                if change == "tightened":
                    tightened_subjects.add(new["subject"])
    listed = {c["term_iri"] for c in out.changes}
    for subject in sorted(tightened_subjects):
        iri = "urn:nebula:ont:" + subject
        if iri not in listed:
            out.changes.append(
                {
                    "term_iri": iri,
                    "class": "constraint_tightening",
                    "detail": "a constraint on this term is stricter",
                }
            )
    out.changes.sort(key=lambda c: (c["term_iri"], c["class"]))


def analyze(
    pred: ReleaseSnapshot | None, cand: ReleaseSnapshot, *, bound: int = DEFAULT_BOUND
) -> Analysis:
    out = Analysis()
    _classify(pred, cand, out)
    _infer(pred, cand, out, bound)
    _constraints(pred, cand, out)
    return out


def assemble(
    scope: tuple[UUID, UUID],
    pred: ReleaseSnapshot | None,
    cand: ReleaseSnapshot,
    analysis: Analysis,
    reach: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "contract": IMPACT_CONTRACT,
        "status": "incomplete" if analysis.unresolved else "complete",
        "scope": {"tenant_id": str(scope[0]), "knowledge_base_id": str(scope[1])},
        "predecessor": pred.ident() if pred else None,
        "candidate": cand.ident(),
        "changes": analysis.changes,
        "inference": analysis.inference,
        "constraints": analysis.constraints,
        "reach": [dict(r) for r in reach],
        "unexamined": [dict(u) for u in UNEXAMINED],
        "unresolved": sorted(analysis.unresolved),
    }
    report["report_digest"] = report_digest(report)
    # Output guard before persistence (contract inventory, ontology-impact-report-v1).
    validate_contract(IMPACT_REF, report, profile="portable-json/v1")
    return report
