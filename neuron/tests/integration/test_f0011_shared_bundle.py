"""Unchanged Neuron native DTO consumers use the common installed contracts."""

from __future__ import annotations

import copy
import hashlib
import json
import socket
from importlib.resources import files
from pathlib import Path
from typing import Any, NoReturn

import pytest
from brain_contracts.assertions import AssertionContractError
from brain_contracts.dispatch import parse_result
from brain_contracts.result import InterpretationResult
from brain_contracts.schema_runtime import ContractBundle, ContractRef
from brain_extraction import openai_compatible_adapter
from brain_ingestion import bundle_writer, content_projection
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[3]


def accepted(contract: str) -> dict[str, Any]:
    cases = json.loads((ROOT / "scripts/contracts/cases.json").read_bytes())["cases"]
    return copy.deepcopy(
        next(
            case["input"]
            for case in cases
            if case["contract"] == contract
            and case["valid"]
            and case.get("kind", "instance") == "instance"
            and not case.get("pointer")
        )
    )


def native_legacy_result() -> dict[str, Any]:
    source = accepted("interpretation-result.schema.json")
    # Match the existing native producer's explicit nullable fields. Their
    # omission is a retained-reader refusal, not a portable source-schema failure.
    source["provenance_ledger_ref"] = None
    for assertion in source["assertions"]:
        assertion.setdefault("model_confidence", None)
    return source


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("No model or network call belongs in this contract smoke")

    monkeypatch.setattr(socket.socket, "connect", blocked)


def test_neuron_resource_digest_matches_the_common_release() -> None:
    packaged = files("brain_contracts").joinpath("resources/v1/manifest.json").read_bytes()
    expected = (ROOT / "schemas/contracts/v1/manifest.json").read_bytes()
    assert packaged == expected
    assert ContractBundle.installed().digest == hashlib.sha256(expected).hexdigest()


@pytest.mark.parametrize(
    ("contract", "model"),
    [
        ("content-artifact-manifest.schema.json", bundle_writer.ArtifactManifest),
        ("content-artifact-manifest-v2.schema.json", content_projection.ArtifactManifestV2),
    ],
)
def test_unchanged_neuron_content_dtos_validate_through_shared_resources(
    contract: str, model: type[BaseModel]
) -> None:
    source = accepted(contract)
    before = copy.deepcopy(source)
    parsed = model.model_validate_json(json.dumps(source))
    output = parsed.model_dump(mode="json")
    ContractBundle.installed().validate(
        ContractRef(contract, str(source["artifact_contract_version"])),
        output,
        profile="native-compat/v1",
    )
    assert source == before
    assert output["artifact_contract_version"] == source["artifact_contract_version"]


def test_existing_direct_baseline_producer_uses_the_shared_legacy_dto() -> None:
    assert openai_compatible_adapter.InterpretationResult is InterpretationResult
    source = native_legacy_result()
    produced = openai_compatible_adapter.InterpretationResult.model_validate_json(
        json.dumps(source)
    )
    output = produced.model_dump(mode="json")
    assert "schema_version" not in output
    ContractBundle.installed().validate(
        ContractRef("interpretation-result", "1"), output, profile="native-compat/v1"
    )


@pytest.mark.parametrize(
    "contract", ["interpretation-result.schema.json", "interpretation-result-v2.schema.json"]
)
def test_both_existing_result_readers_work_in_the_neuron_runtime(contract: str) -> None:
    source = (
        native_legacy_result()
        if contract == "interpretation-result.schema.json"
        else accepted(contract)
    )
    result = parse_result(json.dumps(source))
    assert result.run_id is not None
    assert result.artifact_id is not None


def test_failed_v2_never_becomes_a_legacy_result() -> None:
    source = accepted("interpretation-result-v2.schema.json")
    source["assertions"] = "invalid"
    with pytest.raises(AssertionContractError):
        parse_result(json.dumps(source))


def test_retained_legacy_reader_still_requires_its_explicit_nullable_fields() -> None:
    source = accepted("interpretation-result.schema.json")
    with pytest.raises(AssertionContractError):
        parse_result(json.dumps(source))
