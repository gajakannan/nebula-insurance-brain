#!/usr/bin/env python3
"""Validate teaching artifact shape and references, not runtime reasoning behavior."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

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


def validate(root: Path) -> list[str]:
    data = json.loads((root / BUNDLE).read_text(encoding="utf-8"))
    schema = json.loads((root / SCHEMA).read_text(encoding="utf-8"))
    findings = validate_records(root, data, schema)
    examples = root / "planning-mds/examples"
    documents = [examples / "README.md", examples / "future-semantics.md"]
    documents.extend(sorted((examples / "neurosymbolic-gl").glob("*.md")))
    for document in documents:
        for link in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            findings.extend(check_local_link(root, document, link))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        findings = validate(args.product_root.resolve())
    except (OSError, ValueError, SchemaError) as error:
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
