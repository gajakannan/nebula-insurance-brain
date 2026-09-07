from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/validation/validate_semantic_examples.py"
spec = importlib.util.spec_from_file_location("semantic_examples", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


@pytest.fixture
def records():
    return json.loads((ROOT / validator.BUNDLE).read_text())


def validate(records):
    schema = json.loads((ROOT / validator.SCHEMA).read_text())
    return validator.validate_records(ROOT, records, schema)


def test_repository_example_and_markdown_links_resolve():
    assert validator.validate(ROOT) == []


@pytest.mark.parametrize("field,value", [
    ("fact_ref", "EX-F-MISSING"),
    ("rule_ref", "EX-RULE-MISSING"),
    ("subject_ref", "EX-COV-MISSING"),
])
def test_dangling_assessment_lineage_is_rejected(records, field, value):
    records["assessments"][0][field] = value
    assert any("dangling" in item for item in validate(records))


def test_duplicate_identity_is_rejected(records):
    records["facts"].append(dict(records["facts"][0]))
    assert any("Duplicate record ID" in item for item in validate(records))


@pytest.mark.parametrize("mutation", ["numeric_money", "confidence", "timestamp", "invalid_date", "unlabeled_output", "operator"])
def test_malformed_or_misleading_records_fail_schema(records, mutation):
    if mutation == "numeric_money":
        records["facts"][0]["amount"] = 500000.0
    elif mutation == "confidence":
        records["assertions"][0]["model_confidence"] = 1.1
    elif mutation == "timestamp":
        records["assessments"][0]["known_as_of"] = "July 8"
    elif mutation == "invalid_date":
        records["assessments"][0]["known_as_of"] = "2026-02-30T00:00:00Z"
    elif mutation == "unlabeled_output":
        records["status"] = "executed"
    elif mutation == "operator":
        records["rules"][0]["operation"] = "execute_logic_string"
    assert validate(records)


def test_source_and_provenance_links_are_not_silently_accepted(records):
    records["evidence"][0]["source_ref"] = "source-package.md#missing-region"
    assert any("missing heading" in item for item in validate(records))
    records["evidence"][0]["source_ref"] = "../../../../../../outside.md"
    assert any("escapes product" in item for item in validate(records))


def test_quoted_teaching_evidence_must_exist(records):
    records["evidence"][0]["quote"] = "A nonexistent source statement."
    assert any("quote missing" in item for item in validate(records))


def test_structure_check_does_not_claim_to_execute_reasoning(records):
    # Runtime conformance is a separate future gate; this check is deliberately
    # limited to structure and references, not a second implementation of rules.
    records["assessments"][0]["outcome"] = "MEETS_GUIDELINE"
    assert validate(records) == []
