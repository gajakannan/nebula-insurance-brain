#!/usr/bin/env python3
"""Validate F0002's synthetic contract shapes, never runtime authorization."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    planning = root / "planning-mds"
    schema = json.loads((planning / "schemas/authx-kernel.schema.json").read_text())
    examples_path = (
        planning
        / "features/F0002-tenancy-aware-domain-kernel-and-principal-contracts"
        / "contract-examples.json"
    )
    examples = json.loads(examples_path.read_text())
    Draft202012Validator.check_schema(schema)
    findings = []
    seen = set()
    for case in examples["cases"]:
        case_id = case["id"]
        if case_id in seen:
            findings.append(f"Duplicate case: {case_id}")
        seen.add(case_id)
        definition = case["schema_definition"]
        if definition not in schema["$defs"]:
            findings.append(f"{case_id}: unknown definition {definition}")
            continue
        validator = Draft202012Validator(
            {
                "$schema": schema["$schema"],
                "$defs": schema["$defs"],
                "$ref": f"#/$defs/{definition}",
            },
            format_checker=FormatChecker(),
        )
        errors = list(validator.iter_errors(case["payload"]))
        if (not errors) != case["expected_schema_valid"]:
            findings.append(
                f"{case_id}: unexpected schema outcome: "
                + ("; ".join(error.message for error in errors) or "accepted")
            )
    if not examples["cases"]:
        findings.append("No contract examples")
    print(
        json.dumps(
            {
                "check_id": "authx-contract-examples",
                "status": "fail" if findings else "pass",
                "cases": len(examples["cases"]),
                "scope": "synthetic schema shapes only; no runtime authorization proof",
                "findings": findings,
            },
            indent=2,
        )
    )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
