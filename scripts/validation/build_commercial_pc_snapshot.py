#!/usr/bin/env python3
"""Generate the Cedar Bridge snapshot projections from records.json.

snapshot.ttl, snapshot.jsonld and snapshot-index.json are derived views of the
fact versions selected at the bundle's valid/known coordinates. Edit
records.json, then run this script; validate_semantic_examples.py fails when a
committed projection differs from this output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path("planning-mds/examples/commercial-pc-account")
OUTPUTS = ("snapshot.ttl", "snapshot.jsonld", "snapshot-index.json")
PREFIXES = {
    "pc": "https://example.invalid/nebula/ont/commercial-example/",
    "d": "https://example.invalid/nebula/data/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}
JSONLD_PREFIXES = ("pc", "d", "rdfs", "xsd")
# RDF 1.1 treats xsd:string and simple literals as one value, but rdflib and
# pySHACL compare terms, so sh:hasValue "X" never matches "X"^^xsd:string.
# Emit strings as simple literals so shapes and boundary fixtures can use them.
SIMPLE_LITERAL = "xsd:string"
IDENTITY_NOTE = (
    "Types and labels come from records.entities with evidence references; they are authored "
    "identity/classification metadata, not additional committed business facts."
)


VALUE, UNKNOWN = "VALUE", "UNKNOWN"


def stamp(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def recorded_at(fact: dict, known: datetime) -> bool:
    return stamp(fact["recorded_from"]) <= known and (fact["recorded_to"] is None or known < stamp(fact["recorded_to"]))


def read_valid(valid_time: dict, valid: datetime) -> str | None:
    """Teaching reading of ADR-0064 valid time: VALUE, UNKNOWN, or None (does not hold).

    STATE: an unknown start reads UNKNOWN before attested_from, never "since always".
    An UNKNOWN end reads VALUE through the last attestation, UNKNOWN until the document
    that reported the ending (attested_to), and None afterwards.
    EVENT: a snapshot shows events that occurred at or before valid_as_of.
    """
    kind = valid_time["kind"]
    if kind == "ETERNAL":
        return VALUE
    if kind == "EVENT":
        return VALUE if stamp(valid_time["at"]) <= valid else None
    attested = stamp(valid_time["attested_from"])
    if valid < (stamp(valid_time["from"]) if valid_time["from"] else attested):
        return UNKNOWN if valid_time["from"] is None else None
    state = valid_time["to_state"]
    if state == "BOUNDED":
        return VALUE if valid < stamp(valid_time["to"]) else None
    if state == "OPEN" or valid <= attested:
        return VALUE
    return UNKNOWN if valid < stamp(valid_time["attested_to"]) else None


def integrity_interval(valid_time: dict) -> tuple[datetime, datetime]:
    """Range used for the no-overlap check; an UNKNOWN end closes at attested_to (ADR-0064 option)."""
    kind = valid_time["kind"]
    if kind == "ETERNAL":
        return datetime.min.replace(tzinfo=timezone.utc), datetime.max.replace(tzinfo=timezone.utc)
    if kind == "EVENT":
        at = stamp(valid_time["at"])
        return at, at + timedelta(microseconds=1)
    start = stamp(valid_time["from"] or valid_time["attested_from"])
    end = {"BOUNDED": valid_time.get("to"), "UNKNOWN": valid_time.get("attested_to")}.get(valid_time["to_state"])
    return start, stamp(end) if end else datetime.max.replace(tzinfo=timezone.utc)


def read(fact: dict, valid: datetime, known: datetime) -> str | None:
    return read_valid(fact["valid_time"], valid) if recorded_at(fact, known) else None


def select_facts(data: dict) -> list[dict]:
    """Fact versions that read as VALUE at the snapshot's valid/known coordinates."""
    valid = stamp(data["snapshot"]["valid_as_of"])
    known = stamp(data["snapshot"]["known_as_of"])
    return [fact for fact in data["facts"] if read(fact, valid, known) == VALUE]


def _statements(data: dict) -> list[dict]:
    assertions = {row["id"]: row for row in data["assertions"]}
    statements = []
    for fact in select_facts(data):
        assertion = assertions[fact["assertion_ref"]]
        statements.append({
            "subject_ref": assertion["subject_ref"],
            "predicate": assertion["predicate"],
            "object": assertion["object"],
            "fact_ref": fact["id"],
            "assertion_ref": assertion["id"],
            "evidence_ref": assertion["evidence_ref"],
            "commit_ref": fact["commit_ref"],
        })
    return statements


def _turtle_object(value: dict) -> str:
    if "ref" in value:
        return f"d:{value['ref']}"
    literal = json.dumps(value["value"])
    datatype = value.get("datatype")
    return literal if datatype in (None, SIMPLE_LITERAL) else f"{literal}^^{datatype}"


def _jsonld_object(value: dict) -> dict:
    if "ref" in value:
        return {"@id": f"d:{value['ref']}"}
    datatype = value.get("datatype")
    if datatype in (None, SIMPLE_LITERAL):
        return {"@value": value["value"]}
    return {"@value": value["value"], "@type": datatype}


def build(data: dict) -> dict[str, str]:
    statements = _statements(data)
    turtle = [f"@prefix {name}: <{iri}> ." for name, iri in PREFIXES.items()]
    turtle += ["", "# Accepted illustrative projection at the coordinates in records.json. Not an authorization boundary."]
    turtle += [f"d:{e['id']} a {e['type']} ; rdfs:label {json.dumps(e['label'])} ." for e in data["entities"]]
    turtle += [f"d:{s['subject_ref']} {s['predicate']} {_turtle_object(s['object'])} ." for s in statements]

    nodes = {e["id"]: {"@id": f"d:{e['id']}", "@type": e["type"], "rdfs:label": e["label"]} for e in data["entities"]}
    for statement in statements:
        nodes[statement["subject_ref"]].setdefault(statement["predicate"], []).append(_jsonld_object(statement["object"]))
    jsonld = {"@context": {name: PREFIXES[name] for name in JSONLD_PREFIXES}, "@graph": list(nodes.values())}

    index = {
        "status": "illustrative-projection-lineage",
        "ontology_release": data["ontology_release"],
        "tenant_id": data["tenant_id"],
        "knowledge_base_id": data["knowledge_base_id"],
        "snapshot": data["snapshot"],
        "identity_metadata": IDENTITY_NOTE,
        "statements": statements,
    }
    return {
        "snapshot.ttl": "\n".join(turtle) + "\n",
        "snapshot.jsonld": json.dumps(jsonld, indent=2, ensure_ascii=False) + "\n",
        "snapshot-index.json": json.dumps(index, indent=2, ensure_ascii=False) + "\n",
    }


def refresh_digests(folder: Path) -> list[str]:
    """Rewrite release.yaml sha256 values in place, keeping its layout. Returns the changed files."""
    manifest = folder / "release.yaml"
    lines = manifest.read_text(encoding="utf-8").splitlines(keepends=True)
    changed, current = [], None
    for number, line in enumerate(lines):
        if match := re.match(r"\s*(?:- )?file: (\S+)", line):
            current = match.group(1)
        elif (match := re.match(r"(\s*sha256: )([0-9a-f]{64})(\s*)$", line)) and current:
            digest = hashlib.sha256((folder / current).read_bytes()).hexdigest()
            if digest != match.group(2):
                lines[number] = f"{match.group(1)}{digest}{match.group(3)}"
                changed.append(current)
            current = None
    manifest.write_text("".join(lines), encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", help="exit 1 if a committed projection is stale; write nothing")
    parser.add_argument("--refresh-digests", action="store_true",
                        help="after writing, update release.yaml fixture digests (byte identity only, not compatibility)")
    args = parser.parse_args()
    folder = args.product_root.resolve() / FOLDER
    outputs = build(json.loads((folder / "records.json").read_text(encoding="utf-8")))
    stale = [name for name, text in outputs.items() if (folder / name).read_text(encoding="utf-8") != text]
    if args.check:
        for name in stale:
            print(f"stale generated projection: {FOLDER / name}")
        return 1 if stale else 0
    for name in stale:
        (folder / name).write_text(outputs[name], encoding="utf-8")
        print(f"wrote {FOLDER / name}")
    if args.refresh_digests:
        for name in refresh_digests(folder):
            print(f"refreshed digest: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
