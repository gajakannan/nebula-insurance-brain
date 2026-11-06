from __future__ import annotations

import pytest
from brain_assertions.eligibility import AssertionIneligible, evaluate_eligibility, require_eligible


def source(origin="STATED", *, qualification="qualified", precision="block"):
    return {"text_origin": origin, "origin_qualification": qualification, "precision": precision}


def record(kind="TYPED_ASSERTION", *, mood=None):
    return {
        "assertion_kind": kind,
        "qualifiers": {} if mood is None else {"mood": mood},
        "model_confidence": 1.0,
        "mode": "DERIVED",
        "interpretation_basis": "AMBIGUOUS",
    }


@pytest.mark.parametrize("mood", ["subject to", "offered", "warrants", "if sprinkler installed"])
def test_supplied_mood_cannot_be_cleared_by_confidence_mode_or_review(mood):
    claim = record(mood=mood)
    eligibility = evaluate_eligibility(claim, [source()])
    assert "MOOD" in eligibility.reasons
    assert set(eligibility.blocked_operations) == {
        "RESOLVE",
        "CREATE",
        "AUTO_ACCEPT",
        "CLOSE",
        "SUPERSEDE",
    }
    with pytest.raises(AssertionIneligible, match="^ASSERTION_INELIGIBLE$"):
        require_eligible(claim, [source()], closes_existing=False, reviewed=True)


def test_open_and_mood_are_independent():
    e = evaluate_eligibility(record("OPEN_STATEMENT", mood="offered"), [source("DESCRIBED")])
    assert e.reasons == ("OPEN_STATEMENT", "MOOD", "DESCRIBED_EVIDENCE")
    with pytest.raises(AssertionIneligible):
        require_eligible(record("OPEN_STATEMENT"), [source()], closes_existing=True, reviewed=True)


def test_described_initial_use_needs_review_and_cannot_close_after_review():
    assert evaluate_eligibility(record(), [source("DESCRIBED")]).blocked_operations == (
        "AUTO_ACCEPT",
        "CLOSE",
        "SUPERSEDE",
    )
    with pytest.raises(AssertionIneligible):
        require_eligible(record(), [source("DESCRIBED")], closes_existing=False)
    require_eligible(record(), [source("DESCRIBED")], closes_existing=False, reviewed=True)
    with pytest.raises(AssertionIneligible):
        require_eligible(record(), [source("DESCRIBED")], closes_existing=True, reviewed=True)


@pytest.mark.parametrize(
    "extra",
    [source(None, qualification="legacy_unqualified"), source("STATED", precision="unresolved")],
)
def test_unqualified_or_unresolved_addition_does_not_clear_described(extra):
    assert (
        "DESCRIBED_EVIDENCE" in evaluate_eligibility(record(), [source("DESCRIBED"), extra]).reasons
    )


@pytest.mark.parametrize("origin", ["STATED", "OCR", "TRANSCRIBED"])
def test_verified_support_clears_described_only_and_operative_policy_is_admissible(origin):
    support = [source("DESCRIBED"), source(origin)]
    assert evaluate_eligibility(record(), support).reasons == ()
    require_eligible(record(), support, closes_existing=True)


def test_unknown_origin_and_unresolved_support_keep_review_restrictions():
    e = evaluate_eligibility(
        record(), [source(None, qualification="legacy_unqualified", precision="unresolved")]
    )
    assert e.reasons == ("UNRESOLVED_EVIDENCE", "LEGACY_UNQUALIFIED")
    assert e.review_required
    assert e.blocked_operations == ("AUTO_ACCEPT",)
    assert evaluate_eligibility(record(), []).reasons == ("UNRESOLVED_EVIDENCE",)
