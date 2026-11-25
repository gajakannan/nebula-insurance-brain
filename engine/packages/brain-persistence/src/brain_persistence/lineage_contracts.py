"""F0011 installed-bundle guards for the F0009 lineage carriers (ADR-0079/0080).

Each carrier is validated against its closed, offline schema before it is staged
or returned. A failure raises the bundle's fixed-code `ContractError`, which
carries no payload value.
"""

from __future__ import annotations

from typing import Any

from brain_contracts.schema_runtime import ContractBundle, ContractRef, WireProfile

RESERVATION = ContractRef("learning-candidate-reservation-v1", "1")
ATTEMPT = ContractRef("review-submission-attempt-v1", "1")
QUERY = ContractRef("provenance-query-v1", "1")
RESULT = ContractRef("provenance-result-v1", "1")

PROFILES: dict[ContractRef, WireProfile] = {
    RESERVATION: "portable-json/v1",
    ATTEMPT: "native-compat/v1",
    QUERY: "portable-json/v1",
    RESULT: "native-compat/v1",
}


def validate_lineage(ref: ContractRef, value: Any) -> None:
    ContractBundle.installed().validate(ref, value, profile=PROFILES[ref])
