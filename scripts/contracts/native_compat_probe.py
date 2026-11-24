"""Run fixed native-only cases through the real retained readers/validators.

Use the same probe against a frozen baseline package and the candidate package.
Results contain case IDs, acceptance and fixed safe error codes only.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from brain_content.contracts import validate_contract as content_validate
from brain_content.manifest import parse_manifest
from brain_contracts.assertions import validate_contract as assertion_validate
from brain_contracts.dispatch import parse_result


def run_cases(path: Path) -> list[dict[str, Any]]:
    inventory = json.loads(path.read_bytes())
    assert inventory["profile"] == "native-compat/v1"
    results = []
    for case in inventory["cases"]:
        payload = copy.deepcopy(case["input"])
        before = copy.deepcopy(payload)
        validator = (
            content_validate if case["consumer"] == "content" else assertion_validate
        )
        try:
            validator(case["contract"], payload)
        except ValueError:
            source_valid = False
        else:
            source_valid = True
        raw = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        code = None
        exact = True
        try:
            model = (
                parse_manifest(raw)
                if case["consumer"] == "content"
                else parse_result(raw, allow_v2=case.get("allow_v2", True))
            )
            if case.get("exact_counter"):
                exact = (
                    model.model_dump(mode="json")["counters"]["prompt_tokens"]
                    == (payload["counters"]["prompt_tokens"])
                )
        except ValueError as exc:
            reader_valid = False
            code = getattr(exc, "code", None) or (
                "CONTENT_CONTRACT_INVALID"
                if case["consumer"] == "content"
                else "ASSERTION_CONTRACT_INVALID"
            )
        else:
            reader_valid = True
        matched = (
            source_valid == case["source_valid"]
            and reader_valid == case["reader_valid"]
            and code == case["reader_code"]
            and exact
            and payload == before
        )
        results.append(
            {
                "id": case["id"],
                "profile": "native-compat/v1",
                "consumer": case["consumer"],
                "contract": case["contract"],
                "version": "2" if case["contract"].endswith("-v2.schema.json") else "1",
                "source_valid": source_valid,
                "reader_valid": reader_valid,
                "reader_code": code,
                "exact_roundtrip": exact,
                "input_unchanged": payload == before,
                "matched": matched,
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases", type=Path, default=Path(__file__).with_name("native-cases.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = run_cases(args.cases)
    passing = bool(results) and all(result["matched"] for result in results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {"status": "pass" if passing else "fail", "results": results}, indent=2
        )
        + "\n"
    )
    print(json.dumps({"cases": len(results), "status": "pass" if passing else "fail"}))
    return 0 if passing else 1


if __name__ == "__main__":
    raise SystemExit(main())
