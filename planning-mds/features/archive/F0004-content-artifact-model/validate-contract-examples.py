#!/usr/bin/env python3
"""Validate F0004 synthetic planning examples; no runtime or byte-integrity claim."""
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


def main() -> int:
    feature = Path(__file__).resolve().parent
    schemas = next(parent for parent in feature.parents if parent.name == "planning-mds") / "schemas"
    names = [
        "content-artifact-manifest.schema.json",
        "content-artifact-manifest-v2.schema.json",
        "content-artifact-manifest-read.schema.json",
        "content-records-v2.schema.json",
        "document-date-record.schema.json",
        "interpretation-output-manifest.schema.json",
    ]
    documents = {name: json.loads((schemas / name).read_text()) for name in names}
    for document in documents.values():
        Draft202012Validator.check_schema(document)
    # Registry has no retrieval callback: all references must resolve locally.
    registry = Registry().with_resources(
        (document["$id"], Resource.from_contents(document))
        for document in documents.values()
    )
    cases = json.loads((feature / "contract-examples.json").read_text())["cases"]
    assert len({case["id"] for case in cases}) == len(cases), "Duplicate case IDs"
    assert {case["expected_valid"] for case in cases} == {True, False}
    failures = []
    for case in cases:
        validator = Draft202012Validator(
            documents[case["schema"]], registry=registry, format_checker=FormatChecker()
        )
        errors = list(validator.iter_errors(case["payload"]))
        if (not errors) != case["expected_valid"]:
            failures.append({"case": case["id"], "errors": [e.message for e in errors]})
    print(json.dumps({
        "schemas_checked": len(documents), "cases": len(cases),
        "valid_cases": sum(case["expected_valid"] for case in cases),
        "invalid_cases": sum(not case["expected_valid"] for case in cases),
        "failures": failures,
        "scope": "Schema conformance only; integrity, authorization and persistence need runtime proof.",
    }, indent=2))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
