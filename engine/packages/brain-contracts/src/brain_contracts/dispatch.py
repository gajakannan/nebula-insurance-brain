"""Explicit version dispatch; a failed reader never falls back to another version."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import JsonValue

from brain_contracts.assertions import (
    AssertionContractError,
    AssertionContractUnsupported,
    AssertionRecordV2,
    ContractModel,
    EntityReferenceV2,
    canonical_json,
    decode_json,
    validate_contract,
)
from brain_contracts.result import Counters, InterpretationResult, RunConfiguration


class InterpretationResultV2(ContractModel):
    schema_name = "interpretation-result-v2.schema.json"
    schema_version: Literal[2]
    run_id: UUID
    artifact_id: UUID
    status: Literal["complete", "partial", "failed"]
    entities: tuple[EntityReferenceV2, ...]
    assertions: tuple[AssertionRecordV2, ...]
    relationships: tuple[JsonValue, ...]
    quality_signals: dict[str, float]
    warnings: tuple[str, ...]
    failed_chunks: tuple[str, ...]
    run_configuration: RunConfiguration
    counters: Counters
    provenance_ledger_ref: str | None = None
    created_at: datetime


def parse_result(
    raw: bytes | str, *, allow_v2: bool = True
) -> InterpretationResult | InterpretationResultV2:
    value = decode_json(raw)
    if not isinstance(value, dict):
        raise AssertionContractError()
    if "schema_version" not in value:
        try:
            validate_contract("interpretation-result.schema.json", value)
            return InterpretationResult.model_validate_json(canonical_json(value))
        except (ValueError, TypeError):
            raise AssertionContractError() from None
    if type(value["schema_version"]) is not int or value["schema_version"] != 2 or not allow_v2:
        raise AssertionContractUnsupported()
    try:
        return InterpretationResultV2.model_validate_json(canonical_json(value))
    except (ValueError, TypeError):
        raise AssertionContractError() from None


def parse_legacy_result(raw: bytes | str) -> InterpretationResult:
    result = parse_result(raw, allow_v2=False)
    assert isinstance(result, InterpretationResult)
    return result


require_legacy_result = parse_legacy_result


def parse_interpretation_result(
    raw: bytes | str,
    *,
    supported_versions: frozenset[int] = frozenset({1, 2}),
) -> InterpretationResult | InterpretationResultV2:
    value = decode_json(raw)
    if not isinstance(value, dict):
        raise AssertionContractError()
    selected = 2 if type(value.get("schema_version")) is int and value["schema_version"] == 2 else 1
    if selected not in supported_versions:
        raise AssertionContractUnsupported()
    return parse_result(raw, allow_v2=2 in supported_versions)
