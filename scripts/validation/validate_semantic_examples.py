#!/usr/bin/env python3
"""Validate teaching artifact shape and references, not runtime reasoning behavior."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_commercial_pc_snapshot  # noqa: E402  sibling script, also loaded when tests import this file by path

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = Path("planning-mds/examples/neurosymbolic-gl/records.json")
SCHEMA = Path("planning-mds/schemas/semantic-example.schema.json")
FORMATS = FormatChecker()


@FORMATS.checks("date-time", raises=ValueError)
def check_timestamp(value: object) -> bool:
    # jsonschema's optional RFC3339 dependency is not part of planning tooling.
    # Validate the timestamp subset used here without silently skipping formats.
    if not isinstance(value, str):
        return True  # The schema's type check owns non-string values.
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value):
        return False
    return datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is not None


REFERENCES = {
    "entities": {"concept_ref": "concepts"},
    "slots": {"subject_ref": "entities"},
    "assertions": {"subject_ref": "entities", "run_ref": "runs", "evidence_ref": "evidence"},
    "reviews": {"assertion_ref": "assertions"},
    "commits": {"assertion_ref": "assertions", "review_ref": "reviews"},
    "facts": {"slot_ref": "slots", "assertion_ref": "assertions", "commit_ref": "commits"},
    "rules": {"evidence_ref": "evidence", "subject_ref": "entities"},
    "assessments": {"subject_ref": "entities", "fact_ref": "facts", "rule_ref": "rules"},
}


def check_local_link(root: Path, source: Path, link: str) -> list[str]:
    """Check repository-local paths and the simple heading anchors used in examples."""
    if "://" in link or link.startswith("mailto:"):
        return []
    path, _, anchor = link.partition("#")
    target = (source.parent / path).resolve() if path else source.resolve()
    if not target.is_relative_to(root.resolve()):
        return [f"{source.name}: reference escapes product: {link}"]
    if not target.exists():
        return [f"{source.name}: missing reference: {link}"]
    if anchor and target.suffix == ".md":
        headings = re.findall(r"^#+\s+(.+?)\s*$", target.read_text(encoding="utf-8"), re.M)
        anchors = {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings}
        if anchor not in anchors:
            return [f"{source.name}: missing heading reference: {link}"]
    return []


def validate_records(root: Path, data: dict, schema: dict) -> list[str]:
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FORMATS).iter_errors(data),
        key=lambda error: str(list(error.absolute_path)),
    )
    if errors:
        return [f"{BUNDLE}: {list(e.absolute_path)}: {e.message}" for e in errors]

    findings: list[str] = []
    groups = {name: rows for name, rows in data.items() if isinstance(rows, list)}
    indexes = {name: {row["id"] for row in rows} for name, rows in groups.items()}
    seen: set[str] = set()
    for name, rows in groups.items():
        for row in rows:
            if row["id"] in seen:
                findings.append(f"Duplicate record ID: {row['id']}")
            seen.add(row["id"])
            for field, target_group in REFERENCES.get(name, {}).items():
                if row[field] not in indexes[target_group]:
                    findings.append(f"{row['id']}: dangling {field}: {row[field]}")

    source = root / BUNDLE
    for field in ("schema_ref", "feature_ref"):
        findings.extend(check_local_link(root, source, data[field]))
    for evidence in data["evidence"]:
        link_findings = check_local_link(root, source, evidence["source_ref"])
        findings.extend(link_findings)
        if not link_findings:
            target = source.parent / evidence["source_ref"].split("#", 1)[0]
            if evidence["quote"] not in target.read_text(encoding="utf-8"):
                findings.append(f"{evidence['id']}: illustrative quote missing from source")
    artifacts = {item["artifact_id"] for item in data["evidence"]}
    for run in data["runs"]:
        if run["artifact_id"] not in artifacts:
            findings.append(f"{run['id']}: unknown illustrative artifact")
    return findings


def validate_examples(root: Path) -> list[str]:
    data = json.loads((root / BUNDLE).read_text(encoding="utf-8"))
    schema = json.loads((root / SCHEMA).read_text(encoding="utf-8"))
    findings = validate_records(root, data, schema)
    findings.extend(validate_commercial_example(root))
    examples = root / "planning-mds/examples"
    documents = [examples / "README.md", examples / "future-semantics.md"]
    documents.extend(sorted((examples / "neurosymbolic-gl").glob("*.md")))
    documents.extend(sorted((examples / "commercial-pc-account").glob("*.md")))
    for document in documents:
        for link in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            findings.extend(check_local_link(root, document, link))
    return findings


def validate_commercial_example(root: Path) -> list[str]:
    """Check the authored P&C bundle and projection lineage; do not run a reasoner."""
    folder = root / "planning-mds/examples/commercial-pc-account"
    data = json.loads((folder / "records.json").read_text(encoding="utf-8"))
    schema = json.loads((root / "planning-mds/schemas/commercial-pc-example.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema, format_checker=FORMATS).iter_errors(data))
    if errors:
        return [f"EX-PC-001: {list(e.absolute_path)}: {e.message}" for e in errors]
    findings: list[str] = []
    groups = {key: {row["id"]: row for row in rows} for key, rows in data.items() if isinstance(rows, list)}
    all_ids = [row["id"] for rows in data.values() if isinstance(rows, list) for row in rows]
    if len(all_ids) != len(set(all_ids)):
        findings.append("EX-PC-001: duplicate record identity")
    references = {
        "entities": {"evidence_ref": "evidence"},
        "slots": {"subject_ref": "entities"},
        "assertions": {"subject_ref": "entities", "evidence_ref": "evidence", "run_ref": "runs"},
        "commits": {"review_ref": "reviews"},
        "facts": {"slot_id": "slots", "assertion_ref": "assertions", "commit_ref": "commits"},
    }
    for group, fields in references.items():
        for row in data[group]:
            for field, target in fields.items():
                if row[field] not in groups[target]:
                    findings.append(f"{row['id']}: unresolved {field}")
    for assertion in data["assertions"]:
        target = assertion["object"].get("ref")
        if target and target not in groups["entities"]:
            findings.append(f"{assertion['id']}: unresolved object")
    for review in data["reviews"]:
        if not set(review["assertion_refs"]) <= groups["assertions"].keys():
            findings.append(f"{review['id']}: unresolved reviewed assertion")
    if findings:
        return findings  # Reference failures must not cascade into dictionary lookups.
    artifacts = {e["artifact_id"] for e in data["evidence"]}
    for run in data["runs"]:
        if run["artifact_id"] not in artifacts or run["ontology_release"] != data["ontology_release"]:
            findings.append(f"{run['id']}: artifact/release mismatch")
    for evidence in data["evidence"]:
        link_errors = check_local_link(root, folder / "records.json", evidence["source_ref"])
        findings.extend(link_errors)
        if not link_errors:
            path, _, anchor = evidence["source_ref"].partition("#")
            text = (folder / path).read_text(encoding="utf-8")
            if evidence["quote"] not in text:
                findings.append(f"{evidence['id']}: quote missing from synthetic source")
            section = re.split(r"^## ", text, flags=re.M)
            section = next((part for part in section if part.startswith(anchor + "\n")), "")
            date = evidence["document_date"]
            if date and f"Document date: {date[:10]}." not in section:
                findings.append(f"{evidence['id']}: document date not stated in its source section")
    for assertion in data["assertions"]:
        run = groups["runs"][assertion["run_ref"]]
        evidence = groups["evidence"][assertion["evidence_ref"]]
        if run["artifact_id"] != evidence["artifact_id"]:
            findings.append(f"{assertion['id']}: run and evidence use different artifacts")

    stamp = build_commercial_pc_snapshot.stamp
    ontology = yaml.safe_load((folder / "ontology.yaml").read_text(encoding="utf-8"))
    temporal_kinds = {prop["id"]: prop["temporal_kind"] for prop in ontology["properties"]}
    for fact in data["facts"]:
        assertion = groups["assertions"][fact["assertion_ref"]]
        evidence = groups["evidence"][assertion["evidence_ref"]]
        slot = groups["slots"][fact["slot_id"]]
        commit = groups["commits"][fact["commit_ref"]]
        review = groups["reviews"][commit["review_ref"]]
        valid_time = fact["valid_time"]
        if (slot["subject_ref"], slot["predicate"]) != (assertion["subject_ref"], assertion["predicate"]):
            findings.append(f"{fact['id']}: slot and assertion disagree")
        if slot["qualifiers"].get("target_ref") != assertion["object"].get("ref"):
            findings.append(f"{fact['id']}: relationship target differs from slot qualifier")
        if assertion["id"] not in review["assertion_refs"] or assertion["mood"] != "ASSERTION":
            findings.append(f"{fact['id']}: missing source-reading review or a request promoted in this fixture")
        if valid_time["kind"] != temporal_kinds.get(assertion["predicate"]):
            findings.append(f"{fact['id']}: valid-time kind differs from the property's temporal_kind")
        if valid_time["kind"] == "STATE":
            ended_undated = valid_time["to_state"] == "UNKNOWN"
            if ended_undated != (assertion.get("time_shape") == "ENDED_UNDATED"):
                findings.append(f"{fact['id']}: UNKNOWN end must come from an ENDED_UNDATED source reading")
            attested = valid_time["attested_to"] if ended_undated else valid_time["attested_from"]
            if evidence["document_date"] is None or stamp(attested) != stamp(evidence["document_date"]):
                findings.append(f"{fact['id']}: attestation differs from its evidence document date")
            if ended_undated and stamp(valid_time["attested_from"]) >= stamp(valid_time["attested_to"]):
                findings.append(f"{fact['id']}: undated end reported before the state was attested")
            start, end = build_commercial_pc_snapshot.integrity_interval(valid_time)
            if start >= end:
                findings.append(f"{fact['id']}: empty/reversed valid interval")
        if fact["recorded_to"] and stamp(fact["recorded_from"]) >= stamp(fact["recorded_to"]):
            findings.append(f"{fact['id']}: empty/reversed recorded interval")
        if stamp(commit["accepted_at"]) != stamp(fact["recorded_from"]):
            findings.append(f"{fact['id']}: commit and recorded time disagree")
        if evidence["document_date"] and stamp(fact["recorded_from"]) < stamp(evidence["document_date"]):
            findings.append(f"{fact['id']}: recorded before its source document existed")
    for index, left in enumerate(data["facts"]):
        for right in data["facts"][index + 1:]:
            if left["slot_id"] != right["slot_id"]:
                continue
            left_valid = build_commercial_pc_snapshot.integrity_interval(left["valid_time"])
            right_valid = build_commercial_pc_snapshot.integrity_interval(right["valid_time"])
            valid_overlap = max(left_valid[0], right_valid[0]) < min(left_valid[1], right_valid[1])
            recorded_overlap = ((right["recorded_to"] is None or stamp(left["recorded_from"]) < stamp(right["recorded_to"]))
                                and (left["recorded_to"] is None or stamp(right["recorded_from"]) < stamp(left["recorded_to"])))
            if valid_overlap and recorded_overlap:
                findings.append(f"{left['id']}/{right['id']}: overlapping versions in both time dimensions")

    expected = []
    for fact in build_commercial_pc_snapshot.select_facts(data):
        assertion = groups["assertions"][fact["assertion_ref"]]
        expected.append({"subject_ref": assertion["subject_ref"], "predicate": assertion["predicate"],
                         "object": assertion["object"], "fact_ref": fact["id"], "assertion_ref": assertion["id"],
                         "evidence_ref": assertion["evidence_ref"], "commit_ref": fact["commit_ref"]})
    projection = json.loads((folder / "snapshot-index.json").read_text(encoding="utf-8"))
    for field in ("tenant_id", "knowledge_base_id", "ontology_release", "snapshot"):
        if projection.get(field) != data[field]:
            findings.append(f"EX-PC-001: projection {field} differs from source context")
    if projection.get("statements") != expected:
        findings.append("EX-PC-001: snapshot lineage does not match selected fact versions")
    for name, text in build_commercial_pc_snapshot.build(data).items():
        if (folder / name).read_text(encoding="utf-8") != text:
            findings.append(f"EX-PC-001: {name} differs from records.json; run scripts/validation/build_commercial_pc_snapshot.py")
    outcomes = yaml.safe_load((folder / "expected-results.yaml").read_text(encoding="utf-8"))
    manifest = yaml.safe_load((folder / "release.yaml").read_text(encoding="utf-8"))
    if manifest["release_iri"] != data["ontology_release"]:
        findings.append("EX-PC-001: release manifest identity mismatch")
    versions = {m["version_iri"] for m in manifest["modules"]}
    if len(versions) != len(manifest["modules"]):
        findings.append("EX-PC-001: duplicate module version in composed release")
    for module in manifest["modules"]:
        if module["version_iri"] == manifest["release_iri"] or not set(module["dependencies"]) <= versions:
            findings.append(f"{module['id']}: invalid module identity or dependency lock")
    for artifact in manifest["modules"] + manifest["artifacts"]:
        link_errors = check_local_link(root, folder / "release.yaml", artifact["file"])
        findings.extend(link_errors)
        if not link_errors and hashlib.sha256((folder / artifact["file"]).read_bytes()).hexdigest() != artifact["sha256"]:
            findings.append(f"EX-PC-001: stale fixture digest: {artifact['file']}")
    for row in outcomes["timeline"]:
        valid, known = stamp(row["valid_as_of"]), stamp(row["known_as_of"])
        readings = [(f, build_commercial_pc_snapshot.read(f, valid, known)) for f in data["facts"] if f["slot_id"] == row["slot"]]
        readings = [(f, result) for f, result in readings if result]
        result = readings[0][1] if len(readings) == 1 else ("ABSENT" if not readings else "AMBIGUOUS")
        if result != row["result"] or (readings and readings[0][0]["id"] != row.get("fact")):
            findings.append(f"{row['case']}: expected {row['result']} {row.get('fact', '')}, read {result}")
        elif "value" in row and groups["assertions"][readings[0][0]["assertion_ref"]]["object"].get("value") != row["value"]:
            findings.append(f"{row['case']}: unexpected authored value")
    for row in outcomes["shacl"]:
        for key in ("shape", "data"):
            findings.extend(check_local_link(root, folder / "expected-results.yaml", row[key]))
    for row in outcomes["queries"]:
        findings.extend(check_local_link(root, folder / "expected-results.yaml", row["file"]))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        findings = validate_examples(args.product_root.resolve())
    except (OSError, ValueError, SchemaError, yaml.YAMLError) as error:
        findings = [str(error)]
    print(json.dumps({
        "check_id": "semantic-examples",
        "status": "fail" if findings else "pass",
        "scope": "educational schema and references only; runtime behavior not executed",
        "findings": findings,
    }, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
