"""Run every declared portable case in Python/Pydantic and join actual AJV results."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import pathlib
import subprocess
import sys
import tempfile

import yaml
from brain_contracts.model_adapter import model_for, parse_model, to_wire
from brain_contracts.schema_runtime import (
    FORMATS,
    VALIDATION_KEYWORDS,
    ContractBundle,
    ContractError,
    ContractRef,
    portable_json_bytes,
    resolve_pointer,
    schema_nodes,
)

try:
    from case_data import raw_for_case
except ModuleNotFoundError:  # Imported as a module from the repository's test suite.
    from scripts.contracts.case_data import raw_for_case

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def _accepts_fragment(bundle: ContractBundle, ref: ContractRef, value: object) -> bool:
    try:
        bundle.validate(ref, value, profile="portable-json/v1")
        return True
    except ContractError as error:
        if error.code != "CONTRACT_INSTANCE_INVALID":
            raise
        return False


def cases_from(path: pathlib.Path) -> list[dict]:
    seed = json.loads(path.read_bytes())
    complete = json.loads((HERE / "cases.json").read_bytes())
    # The approved feature seed is accepted as a command input, but a partial
    # 74-case list cannot accidentally become the whole conformance proof.
    indexed = {case["id"]: case for case in complete["cases"]}
    if len(indexed) != len(complete["cases"]):
        raise ValueError("Duplicate complete case ID")
    for case in seed["cases"]:
        if case["id"] not in indexed or indexed[case["id"]] != case:
            raise ValueError(
                "Case expectation differs from the reviewed complete inventory"
            )
    return complete["cases"]


def behavior_coverage(cases: list[dict]) -> dict:
    """A new source conditional cannot quietly escape the common case list."""
    inventory = yaml.safe_load((HERE / "sources.yaml").read_text())
    mapping = json.loads((HERE / "case-behavior-map.json").read_bytes())
    expected = {case["id"]: case for case in cases}
    sources = {resource["id"]: resource for resource in inventory["resources"]}
    schemas = {
        identity: json.loads((ROOT / resource["source"]).read_bytes())
        for identity, resource in sources.items()
    }
    mapped = set()
    keywords = set()
    formats = set()
    bundle = ContractBundle.installed()
    executed_branches = 0
    for entry in mapping["entries"]:
        identity = entry["contract_id"]
        resource = sources[identity]
        if (
            entry["source"] != resource["source"]
            or entry["source_sha256"]
            != hashlib.sha256((ROOT / resource["source"]).read_bytes()).hexdigest()
        ):
            raise ValueError("Behavior source mapping drift")
        pointer = entry["schema_pointer"]
        target = resolve_pointer(schemas[identity], pointer)
        witnesses = entry["witnesses"]
        if not witnesses or not any("accept" in label for label in witnesses):
            raise ValueError("Behavior lacks accepting witnesses")
        for label, identifiers in witnesses.items():
            if not identifiers:
                raise ValueError("Empty behavior witness group")
            for identifier in identifiers:
                case = expected[identifier]
                if case["contract"] != pathlib.PurePosixPath(resource["source"]).name:
                    raise ValueError("Behavior contract mismatch")
                if case["valid"] is not ("reject" not in label):
                    raise ValueError("Behavior witness expectation mismatch")
        mapped.add((identity, pointer))
        for keyword in VALIDATION_KEYWORDS:
            if keyword in entry["behavior"] or keyword in pointer.split("/"):
                keywords.add(keyword)
        if isinstance(target, dict):
            # These applicators route the exact constraints exercised by the
            # enclosing typed cases; they have no standalone failure predicate.
            keywords.update(
                set(target).intersection(
                    {"properties", "allOf", "anyOf", "oneOf", "if", "then", "else"}
                )
            )
            if "if" in target:
                if not witnesses.get("then_accept"):
                    raise ValueError("Missing true source conditional branch")
                if (
                    "then" in target
                    and target["then"] not in ({}, True)
                    and not witnesses.get("then_reject")
                    and not entry.get("note")
                ):
                    raise ValueError(
                        "Missing rejecting true branch or explicit vacuous-branch note"
                    )
                if "else" in target:
                    if not witnesses.get("else_accept"):
                        raise ValueError("Missing false source conditional branch")
                    if (
                        target["else"] not in ({}, True)
                        and not witnesses.get("else_reject")
                        and not entry.get("note")
                    ):
                        raise ValueError("Missing rejecting false branch")
                elif not witnesses.get("false_accept"):
                    raise ValueError("Missing false source conditional witness")
                for label, identifiers in witnesses.items():
                    for identifier in identifiers:
                        case = expected[identifier]
                        base = pointer.rsplit("/allOf/", 1)[0]
                        if case.get("pointer", "") != base:
                            raise ValueError(
                                "Conditional witness is not at the exact typed enclosing source"
                            )
                        ref_name = pathlib.PurePosixPath(resource["source"]).name

                        condition = _accepts_fragment(
                            bundle,
                            ContractRef(ref_name, resource["version"], pointer + "/if"),
                            case["input"],
                        )
                        if condition is not label.startswith("then_"):
                            raise ValueError(
                                "Conditional witness took the wrong source branch: "
                                + identifier
                            )
                        selected = "then" if condition else "else"
                        if selected in target and _accepts_fragment(
                            bundle,
                            ContractRef(
                                ref_name, resource["version"], pointer + "/" + selected
                            ),
                            case["input"],
                        ) is not ("reject" not in label):
                            raise ValueError(
                                "Witness does not demonstrate branch acceptance/refusal: "
                                + identifier
                            )
                        executed_branches += 1
        if entry["behavior"].startswith("format:"):
            formats.add(entry["behavior"].split(":", 1)[1])
    conditionals = {
        (identity, pointer)
        for identity, schema in schemas.items()
        for pointer, node in schema_nodes(schema)
        if isinstance(node, dict) and "if" in node
    }
    if conditionals - mapped:
        raise ValueError("Unmapped source conditional")
    # All selected formats must have explicit positive/negative witnesses.
    if formats != set(FORMATS) or set(VALIDATION_KEYWORDS) - keywords:
        raise ValueError("Incomplete supported validation behavior coverage")
    return {
        "source_conditionals": len(conditionals),
        "behavior_entries": len(mapping["entries"]),
        "conditional_witnesses_executed": executed_branches,
        "validation_keywords": sorted(keywords),
        "formats": sorted(formats),
    }


def python_results(cases: list[dict]) -> dict:
    bundle = ContractBundle.installed()
    results = []
    for case in cases:
        if case.get("profile", "portable-json/v1") != "portable-json/v1":
            raise ValueError("Native-only cases cannot count as portable successes")
        ref = ContractRef(case["contract"], case["version"], case.get("pointer", ""))
        original = copy.deepcopy(case.get("input"))
        accepted = False
        code = None
        try:
            value = (
                bundle.decode(raw_for_case(case), profile="portable-json/v1")
                if case["kind"] == "raw-json"
                else case["input"]
            )
            bundle.validate(ref, value, profile="portable-json/v1")
            accepted = True
        except ContractError as error:
            if error.code not in {
                "CONTRACT_JSON_INVALID",
                "CONTRACT_JSON_UNSUPPORTED",
                "CONTRACT_INSTANCE_INVALID",
            }:
                raise
            code = error.code
        results.append(
            {
                "id": case["id"],
                "contract": case["contract"],
                "version": case["version"],
                "consumer": "jsonschema",
                "accepted": accepted,
                **({"code": code} if code else {}),
            }
        )
        pydantic_accepted = False
        pydantic_code = code
        if accepted:
            raw = (
                raw_for_case(case)
                if case["kind"] == "raw-json"
                else portable_json_bytes(value)
            )
            model = parse_model(ref, raw, model_for(ref), profile="portable-json/v1")
            wire = to_wire(ref, model, profile="portable-json/v1")
            if wire != value:
                raise ValueError("Lossy typed round trip")
            pydantic_accepted = True
        else:
            # Execute the actual adapter even for negatives; source rejection is
            # part of the generated/source-gated Pydantic boundary.
            try:
                raw = (
                    raw_for_case(case)
                    if case["kind"] == "raw-json"
                    else portable_json_bytes(case["input"])
                )
                parse_model(ref, raw, model_for(ref), profile="portable-json/v1")
                pydantic_accepted = True
            except ContractError as error:
                if error.code not in {
                    "CONTRACT_JSON_INVALID",
                    "CONTRACT_JSON_UNSUPPORTED",
                    "CONTRACT_INSTANCE_INVALID",
                }:
                    raise
                pydantic_code = error.code
        results.append(
            {
                "id": case["id"],
                "contract": case["contract"],
                "version": case["version"],
                "consumer": "pydantic",
                "accepted": pydantic_accepted,
                **({"code": pydantic_code} if pydantic_code else {}),
            }
        )
        if original != case.get("input"):
            raise ValueError("Consumer mutated input")
    return {
        "bundle_digest": bundle.digest,
        "versions": {
            "python": sys.version.split()[0],
            "jsonschema": importlib.metadata.version("jsonschema"),
            "pydantic": importlib.metadata.version("pydantic"),
        },
        "cases": results,
    }


def join(cases: list[dict], python: dict, ajv: dict) -> dict:
    expected = {case["id"]: case for case in cases}
    if len(expected) != len(cases) or not expected:
        raise ValueError("Missing or duplicate expected case")
    if python["bundle_digest"] != ajv.get("bundle_digest"):
        raise ValueError("Consumers used different bundle identities")
    all_results = python["cases"] + ajv["cases"]
    seen = set()
    mismatches = []
    for result in all_results:
        key = result["id"], result["consumer"]
        if (
            key in seen
            or result["id"] not in expected
            or result["consumer"] not in {"jsonschema", "pydantic", "ajv"}
        ):
            raise ValueError("Unexpected or duplicate consumer result")
        seen.add(key)
        case = expected[result["id"]]
        if (
            type(result.get("accepted")) is not bool
            or result["accepted"] is not case["valid"]
            or result.get("contract") != case["contract"]
            or result.get("version") != case["version"]
        ):
            mismatches.append({"id": result["id"], "consumer": result["consumer"]})
    required = {
        (identifier, consumer)
        for identifier in expected
        for consumer in ("jsonschema", "pydantic", "ajv")
    }
    if seen != required:
        raise ValueError("Missing consumer results")
    return {
        "status": "pass" if not mismatches else "fail",
        "bundle_digest": python["bundle_digest"],
        "total_cases": len(cases),
        "total_results": len(all_results),
        "mismatches": mismatches,
        "versions": {
            "python": python["versions"],
            "javascript": ajv.get("versions", {}),
        },
        "cases": all_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=pathlib.Path, default=HERE / "cases.json")
    parser.add_argument("--ajv-results", type=pathlib.Path)
    parser.add_argument("--python-output", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    try:
        cases = cases_from(args.cases)
        coverage = behavior_coverage(cases)
        python = python_results(cases)
        if args.python_output:
            args.python_output.write_text(json.dumps(python, indent=2) + "\n")
        if args.ajv_results:
            ajv = json.loads(args.ajv_results.read_bytes())
        else:
            with tempfile.TemporaryDirectory(prefix="nebula-ajv-") as directory:
                target = pathlib.Path(directory) / "results.json"
                subprocess.run(
                    [
                        "node",
                        str(ROOT / "experience/scripts/contracts/check.mjs"),
                        "--cases",
                        str(HERE / "cases.json"),
                        "--output",
                        str(target),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                ajv = json.loads(target.read_bytes())
        result = join(cases, python, ajv)
        result["behavior_coverage"] = coverage
    except Exception as error:  # noqa: BLE001 - CLI failures expose only fixed codes/type.
        result = {
            "status": "fail",
            "code": getattr(error, "code", "CONTRACT_CONFORMANCE_INCOMPLETE"),
            "error_type": type(error).__name__,
        }
    raw = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(raw)
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
