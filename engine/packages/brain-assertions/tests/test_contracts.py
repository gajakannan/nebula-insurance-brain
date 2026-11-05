from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from brain_contracts.assertions import (
    SCHEMA_NAMES,
    AdmissionBatch,
    AssertionContractError,
    AssertionContractUnsupported,
    canonical_json,
    decode_json,
    parse_assertion,
    validate_contract,
)
from brain_contracts.dispatch import parse_interpretation_result, parse_legacy_result, parse_result
from brain_contracts.result import InterpretationResult

ROOT = Path(__file__).resolve().parents[4]
EXAMPLES = (
    ROOT
    / "planning-mds/features/F0006-assertion-plane-origin-and-interpretation-basis"
    / "contract-examples.json"
)
if not EXAMPLES.exists():
    EXAMPLES = (
        ROOT
        / "planning-mds/features/archive/F0006-assertion-plane-origin-and-interpretation-basis"
        / "contract-examples.json"
    )
CASES = json.loads(EXAMPLES.read_text())["cases"]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_authored_contract_shape_expectations_and_packaged_schema_equality(case):
    name = Path(case["schema"]).name
    packaged = ROOT / "engine/packages/brain-contracts/src/brain_contracts/schemas" / name
    assert packaged.read_bytes() == (ROOT / "planning-mds/schemas" / name).read_bytes()
    if case["valid"]:
        validate_contract(name, case["input"])
        if name == "assertion-record-v2.schema.json":
            assert parse_assertion(canonical_json(case["input"])).model_dump(mode="json") == {
                **case["input"],
                "evidence": [{**e, "model_selector": None} for e in case["input"]["evidence"]],
            }
        if name == "assertion-admission-result-v1.schema.json":
            AdmissionBatch.model_validate_json(canonical_json(case["input"]))
    else:
        with pytest.raises(AssertionContractError):
            validate_contract(name, case["input"])


@pytest.mark.parametrize(
    "raw",
    [
        b'{"id":1,"id":2}',
        b'{"nested":{"x":1,"x":2}}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":1e999}',
        b'{"x":"\\ud800"}',
        b'{"x":"\xff"}',
        b"[",
        b"null garbage",
    ],
)
def test_strict_json_rejects_invalid_nested_values_without_echoing_input(raw):
    with pytest.raises(AssertionContractError, match="^ASSERTION_CONTRACT_INVALID$"):
        decode_json(raw)


def test_unknown_python_values_cannot_enter_json_contract():
    for value in (object(), {1: "bad key"}, {"x": float("inf")}, {"x": "\ud800"}):
        with pytest.raises(AssertionContractError):
            canonical_json(value)


@pytest.mark.parametrize("version", [None, True, False, 1, 3, 2.0, "2"])
def test_every_other_explicit_version_is_unsupported(version):
    payload = {"schema_version": version}
    with pytest.raises(AssertionContractUnsupported):
        parse_result(json.dumps(payload))


def test_explicit_v2_is_refused_by_legacy_reader_before_shape_validation():
    with pytest.raises(AssertionContractUnsupported):
        parse_legacy_result(b'{"schema_version":2}')
    with pytest.raises(AssertionContractError):
        parse_result(b"[]")
    with pytest.raises(AssertionContractUnsupported):
        parse_interpretation_result(b"{}", supported_versions=frozenset({2}))


def test_v2_result_dispatch_and_legacy_behavior(monkeypatch):
    v2 = copy.deepcopy(next(c["input"] for c in CASES if c["id"] == "v2-rejected-by-legacy"))
    import urllib.request

    monkeypatch.setattr(
        urllib.request, "urlopen", lambda *a, **kw: pytest.fail("remote schema resolution")
    )
    assert parse_result(canonical_json(v2)).schema_version == 2
    legacy = copy.deepcopy(next(c["input"] for c in CASES if c["id"] == "legacy-remains-valid"))
    legacy["provenance_ledger_ref"] = None
    legacy["assertions"][0]["model_confidence"] = None
    assert parse_legacy_result(canonical_json(legacy)) == InterpretationResult.model_validate(
        legacy
    )
    missing_optional = dict(legacy)
    missing_optional.pop("provenance_ledger_ref")
    # Keep the original Pydantic behavior even though the old JSON schema allows absence.
    with pytest.raises(AssertionContractError):
        parse_legacy_result(canonical_json(missing_optional))
    assert len(SCHEMA_NAMES) == 4
