"""Independent server-side source restrictions; confidence never grants truth."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from brain_contracts.assertions import wire_value

ALL_OPERATIONS = ("RESOLVE", "CREATE", "AUTO_ACCEPT", "CLOSE", "SUPERSEDE")


class AssertionIneligible(ValueError):
    code = "ASSERTION_INELIGIBLE"

    def __init__(self) -> None:
        super().__init__(self.code)


@dataclass(frozen=True)
class Eligibility:
    review_required: bool
    reasons: tuple[str, ...]
    blocked_operations: tuple[str, ...]


def evaluate_eligibility(record: Any, evidence: Sequence[Any]) -> Eligibility:
    record = wire_value(record)
    support = [wire_value(item) for item in evidence]
    reasons: list[str] = []
    blocked: set[str] = set()
    if record["assertion_kind"] == "OPEN_STATEMENT":
        reasons.append("OPEN_STATEMENT")
        blocked.update(ALL_OPERATIONS)
    if "mood" in record["qualifiers"]:
        reasons.append("MOOD")
        blocked.update(ALL_OPERATIONS)
    qualified_non_described = any(
        e.get("origin_qualification") == "qualified"
        and e.get("text_origin") in ("STATED", "OCR", "TRANSCRIBED")
        and e.get("precision") != "unresolved"
        for e in support
    )
    described = any(
        e.get("origin_qualification") == "qualified" and e.get("text_origin") == "DESCRIBED"
        for e in support
    )
    if described and not qualified_non_described:
        reasons.append("DESCRIBED_EVIDENCE")
        blocked.update(("AUTO_ACCEPT", "CLOSE", "SUPERSEDE"))
    if not support or any(e.get("precision") == "unresolved" for e in support):
        reasons.append("UNRESOLVED_EVIDENCE")
        blocked.add("AUTO_ACCEPT")
    if any(
        e.get("origin_qualification") != "qualified" or e.get("text_origin") is None
        for e in support
    ):
        reasons.append("LEGACY_UNQUALIFIED")
        blocked.add("AUTO_ACCEPT")
    return Eligibility(
        bool(reasons), tuple(reasons), tuple(op for op in ALL_OPERATIONS if op in blocked)
    )


def require_eligible(
    record: Any,
    evidence: Sequence[Any],
    *,
    closes_existing: bool,
    reviewed: bool = False,
) -> None:
    eligibility = evaluate_eligibility(record, evidence)
    if "CREATE" in eligibility.blocked_operations:
        raise AssertionIneligible()
    if closes_existing and any(
        op in eligibility.blocked_operations for op in ("CLOSE", "SUPERSEDE")
    ):
        raise AssertionIneligible()
    if eligibility.review_required and not reviewed:
        raise AssertionIneligible()
