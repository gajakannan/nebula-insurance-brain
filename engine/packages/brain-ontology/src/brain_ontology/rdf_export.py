"""Deterministic RDF/OWL interchange (ADR-0012, F0012-S0007 AC2).

Turtle and JSON-LD are both rendered from one sorted triple list, so they are
isomorphic by construction; the `semantic_rdf` gate re-checks it with rdflib.

Only the supported inference subset is written as RDFS/OWL axioms
(`rdfs:subClassOf`, `rdfs:subPropertyOf`, `owl:inverseOf`). Domain and range
are validation constraints (ADR-0081 D2), so they are exported as the annotation
properties `nebula:validationDomain` / `nebula:validationRange`, which no
RDFS/OWL reasoner uses to infer a type.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from brain_domain.ontology import IRI_PREFIX

OWL = "http://www.w3.org/2002/07/owl#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
SKOS = "http://www.w3.org/2004/02/skos/core#"
XSD = "http://www.w3.org/2001/XMLSchema#"
NEBULA = "urn:nebula:vocab:"
PREFIXES = (
    ("nebula", NEBULA),
    ("owl", OWL),
    ("rdf", RDF),
    ("rdfs", RDFS),
    ("skos", SKOS),
    ("xsd", XSD),
)


@dataclass(frozen=True, slots=True, order=True)
class Literal:
    value: str
    language: str | None = None


Term = str | Literal  # a str is an IRI


def _iri(term_id: str) -> str:
    return IRI_PREFIX + term_id


def _range_iri(value: str) -> str:
    return XSD + value[4:] if value.startswith("xsd:") else _iri(value)


def triples(
    release_ref: str, label: str, terms: Iterable[Mapping[str, Any]]
) -> list[tuple[str, str, Term]]:
    out: set[tuple[str, str, Term]] = {
        (release_ref, RDF + "type", OWL + "Ontology"),
        (release_ref, OWL + "versionInfo", Literal(label)),
    }
    for term in terms:
        s = term["iri"]
        kind = term["kind"]
        if kind == "class":
            out.add((s, RDF + "type", OWL + "Class"))
            for parent in term.get("parents", []):
                out.add((s, RDFS + "subClassOf", _iri(parent)))
        elif kind in {"object_property", "datatype_property"}:
            rdf_kind = "ObjectProperty" if kind == "object_property" else "DatatypeProperty"
            out.add((s, RDF + "type", OWL + rdf_kind))
            out.add((s, NEBULA + "validationDomain", _iri(term["domain"])))
            out.add((s, NEBULA + "validationRange", _range_iri(term["range"])))
            out.add((s, NEBULA + "temporalKind", Literal(term["temporal_kind"])))
            for sup in term.get("sub_property_of", []):
                out.add((s, RDFS + "subPropertyOf", _iri(sup)))
            if term.get("inverse_of"):
                out.add((s, OWL + "inverseOf", _iri(term["inverse_of"])))
            if term.get("predicate_key"):
                out.add((s, NEBULA + "predicateKey", Literal(term["predicate_key"])))
        elif kind == "code_value":
            out.add((s, RDF + "type", OWL + "NamedIndividual"))
            out.add((s, RDF + "type", _iri(term["code_of"])))
            for scheme, code in sorted(term.get("external_codes", {}).items()):
                if code is not None:
                    out.add((s, NEBULA + "externalCode", Literal(f"{scheme}={code}")))
        for tag, text in sorted(term.get("labels", {}).items()):
            out.add((s, SKOS + "prefLabel", Literal(text, tag)))
        for alias in term.get("aliases", []):
            out.add((s, SKOS + "altLabel", Literal(alias["value"], alias["tag"])))
        out.add((s, SKOS + "definition", Literal(term["definition"], "en-US")))
    return sorted(out, key=lambda t: (t[0], t[1], _sort(t[2])))


def _sort(o: Term) -> tuple[int, str, str]:
    if isinstance(o, Literal):
        return (1, o.value, o.language or "")
    return (0, o, "")


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def _ttl_iri(iri: str) -> str:
    for prefix, ns in PREFIXES:
        if iri.startswith(ns) and iri[len(ns) :].isidentifier():
            return f"{prefix}:{iri[len(ns) :]}"
    return f"<{iri}>"


def _ttl_obj(o: Term) -> str:
    if isinstance(o, Literal):
        return f'"{_escape(o.value)}"' + (f"@{o.language}" if o.language else "")
    return _ttl_iri(o)


def to_turtle(rows: list[tuple[str, str, Term]]) -> str:
    lines = [f"@prefix {p}: <{ns}> ." for p, ns in PREFIXES]
    subject: str | None = None
    for s, p, o in rows:
        if s != subject:
            if subject is not None:
                lines[-1] += " ."
            lines.append("")
            lines.append(f"{_ttl_iri(s)} {_ttl_iri(p)} {_ttl_obj(o)}")
            subject = s
        else:
            lines[-1] += " ;"
            lines.append(f"    {_ttl_iri(p)} {_ttl_obj(o)}")
    if subject is not None:
        lines[-1] += " ."
    return "\n".join(lines) + "\n"


def to_jsonld(rows: list[tuple[str, str, Term]]) -> str:
    """Expanded JSON-LD (no context needed to read it back)."""
    nodes: dict[str, dict[str, list[dict[str, str]]]] = {}
    for s, p, o in rows:
        values = nodes.setdefault(s, {}).setdefault(p, [])
        if isinstance(o, Literal):
            item = {"@value": o.value}
            if o.language:
                item["@language"] = o.language
            values.append(item)
        else:
            values.append({"@id": o})
    graph = [{"@id": s, **props} for s, props in sorted(nodes.items())]
    return json.dumps(graph, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
