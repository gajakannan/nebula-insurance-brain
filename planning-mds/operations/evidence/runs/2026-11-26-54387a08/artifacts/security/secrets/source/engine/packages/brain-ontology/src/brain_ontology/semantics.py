"""The supported inference subset `nebula-tbox-subset/v1` (ADR-0081 D2).

Only `subClassOf` and `subPropertyOf` (reflexive-transitive) and `inverseOf`
(symmetric) entail anything. `domain`, `range`, `disjoint` and cardinalities are
validation constraints: they never contribute an entailment, so a domain or range
declaration never infers the type of anything.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from brain_domain.ontology import IRI_PREFIX

DEFAULT_BOUND = 100_000


@dataclass(frozen=True, slots=True, order=True)
class Entailment:
    subject: str
    relation: str
    object: str

    def to_json(self) -> dict[str, str]:
        return {"subject": self.subject, "relation": self.relation, "object": self.object}


class ClosureBoundExceeded(Exception):
    """The closure grew past its bound: the analysis is unresolved, never 'no change'."""


def asserted(terms: Iterable[Mapping[str, Any]]) -> set[Entailment]:
    """Asserted axioms of the supported rules over normalized terms (IRIs)."""
    axioms: set[Entailment] = set()
    for term in terms:
        iri = term["iri"]
        for parent in term.get("parents", []):
            axioms.add(Entailment(iri, "subClassOf", IRI_PREFIX + parent))
        for sup in term.get("sub_property_of", []):
            axioms.add(Entailment(iri, "subPropertyOf", IRI_PREFIX + sup))
        if term.get("inverse_of"):
            axioms.add(Entailment(iri, "inverseOf", IRI_PREFIX + term["inverse_of"]))
    return axioms


def closure(
    terms: Iterable[Mapping[str, Any]], *, bound: int = DEFAULT_BOUND
) -> frozenset[Entailment]:
    """Deterministic fixpoint: reflexive-transitive subClassOf/subPropertyOf over
    the declared classes/properties, and symmetric inverseOf."""
    terms = list(terms)
    edges: dict[str, dict[str, set[str]]] = {"subClassOf": {}, "subPropertyOf": {}}
    result: set[Entailment] = set()
    for term in terms:
        kind = term.get("kind")
        if kind == "class":
            edges["subClassOf"].setdefault(term["iri"], set())
        elif kind in {"object_property", "datatype_property"}:
            edges["subPropertyOf"].setdefault(term["iri"], set())
    for axiom in asserted(terms):
        if axiom.relation == "inverseOf":
            result.add(axiom)
            result.add(Entailment(axiom.object, "inverseOf", axiom.subject))
        else:
            edges[axiom.relation].setdefault(axiom.subject, set()).add(axiom.object)
            edges[axiom.relation].setdefault(axiom.object, set())
    for relation, graph in edges.items():
        for node in sorted(graph):
            seen = {node}
            stack = [node]
            while stack:
                current = stack.pop()
                for nxt in graph.get(current, ()):
                    if nxt not in seen:
                        seen.add(nxt)
                        stack.append(nxt)
            for target in seen:
                result.add(Entailment(node, relation, target))
                if len(result) > bound:
                    raise ClosureBoundExceeded(f"more than {bound} entailments")
    return frozenset(result)


def restricted(entailments: Iterable[Entailment], scope: frozenset[str]) -> set[Entailment]:
    """Entailments whose subject and object both exist in `scope` (predecessor terms)."""
    return {e for e in entailments if e.subject in scope and e.object in scope}
