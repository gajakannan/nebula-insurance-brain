#!/usr/bin/env python3
"""Offline check of F0007 contract-examples.json against the authored design schemas.

Resolves only local schema files (no network $ref). Exit 0 when every case's
schema verdict matches its declared `valid` flag and every schema is a valid
Draft 2020-12 schema."""
import argparse
import json
import sys
from pathlib import Path

import jsonschema
from referencing import Registry, Resource

parser = argparse.ArgumentParser()
parser.add_argument("--product-root", required=True, type=Path)
args = parser.parse_args()
root = args.product_root.resolve()
feature = root / "planning-mds/features/F0007-factslot-model"
schemas_dir = root / "planning-mds/schemas"
names = ["fact-slot-key-v1", "fact-answer-v1", "fact-slot-resolution-result-v1"]
docs = {n: json.loads((schemas_dir / f"{n}.schema.json").read_text()) for n in names}
registry = Registry()
for n, d in docs.items():
    jsonschema.Draft202012Validator.check_schema(d)
    resource = Resource.from_contents(d)
    registry = registry.with_resource(d["$id"], resource).with_resource(f"{n}.schema.json", resource)


def refuse(uri):
    raise LookupError(f"non-local $ref refused: {uri}")


registry = registry.crawl()
examples = json.loads((feature / "contract-examples.json").read_text())
failures = 0
for case in examples["cases"]:
    schema_path = (feature / case["schema"]).resolve()
    schema = docs[schema_path.name.removesuffix(".schema.json")]
    validator = jsonschema.Draft202012Validator(
        schema, registry=registry, format_checker=jsonschema.FormatChecker()
    )
    ok = validator.is_valid(case["input"])
    status = "PASS" if ok == case["valid"] else "FAIL"
    failures += status == "FAIL"
    print(f"{status} {case['id']}: valid={ok} expected={case['valid']} ({case['story']})")
print(f"{len(examples['cases'])} cases, {failures} failures, {len(names)} schemas checked")
sys.exit(1 if failures else 0)
