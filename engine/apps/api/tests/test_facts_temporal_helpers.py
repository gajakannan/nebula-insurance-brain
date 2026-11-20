"""Pure helpers of the `/facts` commit route (F0008). They decide which documents a
fact-temporal/v1 commit READ-checks up front, so they are covered without a
database: the PostgreSQL suites prove the end-to-end behaviour."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from brain_api.routes.facts import _conservative_window, _ending_refs, _instant_of

START = {"instant": "2026-06-01T05:00:00Z", "granularity": "DAY", "zone": "America/Chicago"}
END = {"instant": "2026-09-01T05:00:00Z", "granularity": "DAY", "zone": "America/Chicago"}


def test_bounded_window_uses_both_instants() -> None:
    window = _conservative_window(
        {"valid_from": START, "valid_to_state": "BOUNDED", "valid_to": END}
    )
    assert window == (datetime(2026, 6, 1, 5, tzinfo=UTC), datetime(2026, 9, 1, 5, tzinfo=UTC))


@pytest.mark.parametrize(
    "temporal",
    [
        {"valid_from": START, "valid_to_state": "OPEN"},
        {"valid_from": START, "valid_to_state": "UNKNOWN", "valid_to": END},
    ],
)
def test_open_and_unknown_ends_are_unbounded(temporal: dict) -> None:
    assert _conservative_window(temporal) == (datetime(2026, 6, 1, 5, tzinfo=UTC), None)


@pytest.mark.parametrize(
    "temporal",
    [
        None,
        "not a block",
        {"valid_from": None, "valid_to_state": "OPEN"},  # unknown start: floored later
        {"valid_from": {"instant": "June", "granularity": "DAY"}, "valid_to_state": "OPEN"},
        {"valid_from": {"instant": "2026-06-01T05:00:00"}, "valid_to_state": "OPEN"},  # naive
        {"valid_from": "2026-06-01T05:00:00Z", "valid_to_state": "OPEN"},
    ],
)
def test_unknown_or_malformed_start_widens_to_unbounded(temporal: object) -> None:
    """Widening can only over-check documents, never skip one."""
    assert _conservative_window(temporal)[0] is None


def test_instant_of_rejects_non_strings() -> None:
    assert _instant_of({"instant": 20260601}) is None
    assert _instant_of(["2026-06-01T05:00:00Z"]) is None


def test_ending_refs_parses_only_well_formed_lists() -> None:
    ref = uuid4()
    assert _ending_refs({"ending_evidence_refs": [str(ref)]}) == (ref,)
    assert _ending_refs({"ending_evidence_refs": ["not-a-uuid"]}) == ()
    assert _ending_refs({"ending_evidence_refs": "x"}) == ()
    assert _ending_refs(None) == ()
