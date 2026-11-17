"""Offline check of F0008 contract examples against the planning schemas (local refs only)."""
import json, sys
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
schemas = root / "planning-mds" / "schemas"
names = ["fact-temporal-v1.schema.json", "canonical-commit-request.schema.json"]
docs = {n: json.loads((schemas / n).read_text()) for n in names}
registry = Registry().with_resources(
    (d["$id"], Resource.from_contents(d)) for d in docs.values()
)
temporal_id = docs["fact-temporal-v1.schema.json"]["$id"]
targets = {
    "commit_request": docs["canonical-commit-request.schema.json"],
    "version_temporal": {"$ref": f"{temporal_id}#/$defs/version_temporal"},
    "validity_unknown_read": {"$ref": f"{temporal_id}#/$defs/validity_unknown_read"},
}
for d in docs.values():
    Draft202012Validator.check_schema(d)
examples = json.loads(next((root / "planning-mds" / "features").glob("F0008-*/contract-examples.json")).read_text())
failures = 0
for case in examples["cases"]:
    v = Draft202012Validator(targets[case["target"]], registry=registry, format_checker=FormatChecker())
    ok = v.is_valid(case["instance"])
    status = "PASS" if ok == case["valid"] else "FAIL"
    failures += status == "FAIL"
    print(f"{status} {case['id']} expected_valid={case['valid']} got_valid={ok} :: {case['covers']}")
print(f"{len(examples['cases'])} cases, {failures} failures")
sys.exit(1 if failures else 0)
