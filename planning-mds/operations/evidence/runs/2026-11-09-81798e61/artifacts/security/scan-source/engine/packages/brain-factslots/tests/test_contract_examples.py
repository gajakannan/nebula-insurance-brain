"""The 26 F0007 design cases (`contract-examples.json`) against the design schemas
and against the runtime parsers, so the schemas and the code cannot drift apart.

Schema validity alone does not prove resolution, authorization or persistence;
those are the PostgreSQL suites."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
from brain_domain.fact_answers import FactAnswerRejected, parse_answer
from brain_domain.fact_values import ValueType
from referencing import Registry, Resource

FEATURE = next(
    p / "planning-mds/features"
    for p in Path(__file__).resolve().parents
    if (p / "planning-mds/features").is_dir()
)
EXAMPLES = next(FEATURE.glob("**/F0007-*/contract-examples.json"))
SCHEMAS = FEATURE.parent / "schemas"
CASES = json.loads(EXAMPLES.read_text())["cases"]


def _registry() -> Registry:
    resources = []
    for name in ("fact-slot-key-v1", "fact-answer-v1", "fact-slot-resolution-result-v1"):
        schema = json.loads((SCHEMAS / f"{name}.schema.json").read_text())
        resource = Resource.from_contents(schema)
        resources += [(schema["$id"], resource), (f"{name}.schema.json", resource)]
    return Registry().with_resources(resources)


REGISTRY = _registry()


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_design_case_matches_its_schema(case):
    schema = json.loads((EXAMPLES.parent / case["schema"]).resolve().read_text())
    validator = jsonschema.Draft202012Validator(schema, registry=REGISTRY)
    assert validator.is_valid(case["input"]) == case["valid"]


ANSWERS = [c for c in CASES if "fact-answer" in c["schema"]]


@pytest.mark.parametrize("case", ANSWERS, ids=[c["id"] for c in ANSWERS])
def test_runtime_answer_parser_agrees_with_the_schema(case):
    """A schema-invalid envelope is refused by the runtime parser too. Name cases
    need a store for evidence, so only their shape is compared here."""
    value = case["input"].get("value", {})
    value_type = (
        ValueType(value["type"])
        if isinstance(value, dict) and "type" in value
        else (ValueType.MONEY)
    )
    try:
        parse_answer(case["input"], value_type=value_type, basis_required=False)
        accepted = True
    except FactAnswerRejected:
        accepted = False
    assert accepted == case["valid"], case["id"]
