"""Candidate response guards shared by API delivery and the history preflight.

The caller completes the existing authorization/domain checks first. These
guards inspect normalized output; a failure is an internal invariant error.
"""

from __future__ import annotations

from typing import Any

from brain_contracts.schema_runtime import ContractRef, validate_contract


def guard_fact_response(payload: dict[str, Any], *, validity_unknown: bool = False) -> None:
    ref = (
        ContractRef("fact-temporal-v1", "1", "/$defs/validity_unknown_read")
        if validity_unknown
        else ContractRef("fact-version-read-v1", "1")
    )
    validate_contract(ref, payload, profile="native-compat/v1")


def guard_commit_response(payload: dict[str, Any]) -> None:
    validate_contract(
        ContractRef("canonical-commit-response", "1"), payload, profile="native-compat/v1"
    )
