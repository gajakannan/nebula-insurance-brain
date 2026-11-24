"""Every common case exercises the actual generated/source-gated adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from brain_contracts.model_adapter import model_for, parse_model, to_wire
from brain_contracts.schema_runtime import (
    ContractBundle,
    ContractError,
    ContractRef,
    portable_json_bytes,
)
from pydantic import BaseModel, ConfigDict
from scripts.contracts.case_data import raw_for_case

ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "scripts/contracts/cases.json").is_file()
)
CASES = json.loads((ROOT / "scripts/contracts/cases.json").read_bytes())["cases"]


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_generated_source_gated_case(case):
    ref = ContractRef(case["contract"], case["version"], case.get("pointer", ""))
    if not case["valid"]:
        with pytest.raises(ContractError) as error:
            raw = (
                raw_for_case(case)
                if case["kind"] == "raw-json"
                else portable_json_bytes(case["input"])
            )
            parse_model(ref, raw, model_for(ref), profile="portable-json/v1")
        assert error.value.code in {
            "CONTRACT_INSTANCE_INVALID",
            "CONTRACT_JSON_INVALID",
            "CONTRACT_JSON_UNSUPPORTED",
        }
        return
    raw = raw_for_case(case) if case["kind"] == "raw-json" else portable_json_bytes(case["input"])
    model = parse_model(ref, raw, model_for(ref), profile="portable-json/v1")
    wire = to_wire(ref, model, profile="portable-json/v1")
    expected = json.loads(raw)
    assert wire == expected
    assert model.model_config.get("json_schema_extra", {}) == ContractBundle.installed().metadata(
        ref
    )


def test_a_lossy_or_hand_edited_model_cannot_be_accepted():
    class LossyModel(BaseModel):
        model_config = ConfigDict(extra="ignore")
        type: str
        amount: str
        currency: str

    ref = ContractRef("qualified-money-v1", "1")
    raw = (
        '{"type":"money","amount":"12345678901234567890.00001",'
        '"currency":"USD","basis":"each_occurrence"}'
    )
    with pytest.raises(ContractError, match="CONTRACT_MODEL_MISMATCH"):
        parse_model(ref, raw, LossyModel, profile="portable-json/v1")


def test_explicit_null_absence_and_open_payload_keys_survive():
    cases = [case for case in CASES if case["valid"] and case["kind"] == "instance"]
    assert any("null" in json.dumps(case["input"]) for case in cases)
    for case in cases:
        ref = ContractRef(case["contract"], case["version"], case.get("pointer", ""))
        raw = json.dumps(case["input"])
        model = parse_model(ref, raw, model_for(ref), profile="portable-json/v1")
        assert to_wire(ref, model, profile="portable-json/v1") == case["input"]


def test_unknown_generated_model_selector_fails_explicitly():
    with pytest.raises(ContractError, match="CONTRACT_MODEL_MISMATCH"):
        model_for(ContractRef("future-contract", "99"))
