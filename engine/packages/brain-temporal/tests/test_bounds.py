"""F0008-S0001/S0002 unit proof: per-bound granularity and zone, truncation in
zone (every granularity, DST in America/Chicago, Etc/GMT+6), parse refusal
codes, attestation derivation and placement (ADR-0078 D2-D4).

Expectations come from the story ACs and EX-SEM-003/004, not from the code.
The PostgreSQL trigger agreement is proven in test_temporal_v1_commit.py."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from brain_domain.temporal import (
    Bound,
    DatePrecision,
    DocumentDate,
    EndState,
    Granularity,
    StartBasis,
    TemporalReason,
    TemporalRejected,
)
from brain_temporal.attestation import check_expected, derive_attestation, place
from brain_temporal.bounds import (
    parse_bound,
    parse_commit_temporal,
    period_end,
    truncate,
    validate_bound,
    zone_info,
)

CHI = "America/Chicago"


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def code(exc: pytest.ExceptionInfo[TemporalRejected]) -> TemporalReason:
    return exc.value.code


# --- S0001 AC1/AC2: granularity, zone and truncation ----------------------

# (granularity, truncated instant in America/Chicago, an untruncated instant)
TRUNCATED = [
    (Granularity.YEAR, "2026-01-01T06:00:00Z", "2026-02-01T06:00:00Z"),
    (Granularity.QUARTER, "2026-04-01T05:00:00Z", "2026-05-01T05:00:00Z"),
    (Granularity.MONTH, "2026-06-01T05:00:00Z", "2026-06-02T05:00:00Z"),
    (Granularity.DAY, "2026-06-01T05:00:00Z", "2026-06-01T06:00:00Z"),
    (Granularity.HOUR, "2026-06-01T07:00:00Z", "2026-06-01T07:30:00Z"),
    (Granularity.MINUTE, "2026-06-01T07:01:00Z", "2026-06-01T07:01:30Z"),
    (Granularity.SECOND, "2026-06-01T07:01:30Z", "2026-06-01T07:01:30.500000Z"),
]


@pytest.mark.parametrize(("granularity", "good", "bad"), TRUNCATED, ids=lambda v: str(v))
def test_s0001_ac1_ac2_every_granularity_accepts_truncated_and_refuses_untruncated(
    granularity: Granularity, good: str, bad: str
) -> None:
    assert validate_bound(Bound(utc(good), granularity, CHI)).instant == utc(good)
    with pytest.raises(TemporalRejected) as refused:
        validate_bound(Bound(utc(bad), granularity, CHI))
    assert code(refused) is TemporalReason.BOUND_NOT_TRUNCATED


def test_s0001_ac2_chicago_midnight_is_accepted_and_the_same_instant_in_utc_is_not() -> None:
    instant = utc("2026-06-01T05:00:00Z")
    assert validate_bound(Bound(instant, Granularity.DAY, CHI)).instant == instant
    with pytest.raises(TemporalRejected) as refused:
        validate_bound(Bound(instant, Granularity.DAY, "UTC"))
    assert code(refused) is TemporalReason.BOUND_NOT_TRUNCATED


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ({"instant": "2026-06-01T05:00:00Z", "zone": CHI}, TemporalReason.GRANULARITY_INVALID),
        (
            {"instant": "2026-06-01T05:00:00Z", "granularity": "WEEK", "zone": CHI},
            TemporalReason.GRANULARITY_INVALID,
        ),
        (
            {"instant": "2026-06-01T05:00:00Z", "granularity": "DAY"},
            TemporalReason.TIME_ZONE_INVALID,
        ),
        (
            {"instant": "2026-06-01T05:00:00Z", "granularity": "DAY", "zone": "Mars/Olympus"},
            TemporalReason.TIME_ZONE_INVALID,
        ),
        (
            {"instant": "2026-06-01T05:00:00Z", "granularity": "DAY", "zone": "CDT"},
            TemporalReason.TIME_ZONE_INVALID,
        ),
        (
            {"instant": "2026-06-01T05:00:00Z", "granularity": "DAY", "zone": "../../etc/passwd"},
            TemporalReason.TIME_ZONE_INVALID,
        ),
        (
            {"instant": "2026-06-01T05:00:00", "granularity": "DAY", "zone": CHI},
            TemporalReason.TIME_ZONE_INVALID,
        ),
    ],
)
def test_s0001_ac1_missing_or_unknown_granularity_or_zone_is_refused(
    raw: dict[str, str], reason: TemporalReason
) -> None:
    with pytest.raises(TemporalRejected) as refused:
        parse_bound(raw)
    assert code(refused) is reason


def test_s0001_ac3_ex_sem_003_minute_start_in_standard_time_round_trips() -> None:
    bound = parse_bound(
        {"instant": "2026-07-01T06:01:00Z", "granularity": "MINUTE", "zone": "Etc/GMT+6"}
    )
    assert bound == Bound(utc("2026-07-01T06:01:00Z"), Granularity.MINUTE, "Etc/GMT+6")
    # America/Chicago would mean CDT in July: 12:01 a.m. CDT is 05:01Z, not 06:01Z.
    assert truncate(utc("2026-07-01T05:01:00Z"), Granularity.DAY, CHI) == utc(
        "2026-07-01T05:00:00Z"
    )
    assert truncate(utc("2026-07-01T06:01:00Z"), Granularity.DAY, "Etc/GMT+6") == utc(
        "2026-07-01T06:00:00Z"
    )


def test_s0001_ac4_day_start_reads_back_as_the_same_local_day() -> None:
    bound = parse_bound({"instant": "2026-06-01T05:00:00Z", "granularity": "DAY", "zone": CHI})
    assert bound.instant.astimezone(zone_info(CHI)).date().isoformat() == "2026-06-01"
    assert bound.instant.date().isoformat() == "2026-06-01"  # never 2026-05-31


@pytest.mark.parametrize(
    ("instant", "granularity", "expected_end"),
    [
        # DST spring forward (2026-03-08 has 23 hours in Chicago).
        ("2026-03-08T06:00:00Z", Granularity.DAY, "2026-03-09T05:00:00Z"),
        # DST fall back (2026-11-01 has 25 hours in Chicago).
        ("2026-11-01T05:00:00Z", Granularity.DAY, "2026-11-02T06:00:00Z"),
        ("2026-03-01T06:00:00Z", Granularity.MONTH, "2026-04-01T05:00:00Z"),
        ("2026-10-01T05:00:00Z", Granularity.QUARTER, "2027-01-01T06:00:00Z"),
        ("2026-01-01T06:00:00Z", Granularity.YEAR, "2027-01-01T06:00:00Z"),
        ("2026-11-01T06:00:00Z", Granularity.HOUR, "2026-11-01T07:00:00Z"),
    ],
)
def test_s0001_dst_boundaries_in_chicago(
    instant: str, granularity: Granularity, expected_end: str
) -> None:
    start = utc(instant)
    assert validate_bound(Bound(start, granularity, CHI)).instant == start
    assert period_end(start, granularity, CHI) == utc(expected_end)


def test_s0001_dst_fall_back_second_hour_keeps_its_own_offset() -> None:
    # 01:00 CST on 2026-11-01 (the repeated hour) is 07:00Z and truncated to HOUR.
    second = utc("2026-11-01T07:00:00Z")
    assert truncate(second, Granularity.HOUR, CHI) == second
    assert truncate(utc("2026-11-01T07:30:00Z"), Granularity.HOUR, CHI) == second


def test_s0001_ac5_start_and_end_have_independent_granularities() -> None:
    proposal = parse_commit_temporal(
        {
            "contract": "fact-temporal/v1",
            "valid_from": {"instant": "2026-06-01T05:00:00Z", "granularity": "DAY", "zone": CHI},
            "valid_from_basis": "TEMPLATE_FIELD",
            "valid_to_state": "BOUNDED",
            "valid_to": {"instant": "2027-01-01T06:00:00Z", "granularity": "MONTH", "zone": CHI},
        }
    )
    assert proposal.valid_from is not None and proposal.valid_to is not None
    assert proposal.valid_from.granularity is Granularity.DAY
    assert proposal.valid_to.granularity is Granularity.MONTH
    with pytest.raises(TemporalRejected) as refused:
        parse_commit_temporal(
            {
                "contract": "fact-temporal/v1",
                "valid_from": {
                    "instant": "2026-06-01T05:00:00Z",
                    "granularity": "DAY",
                    "zone": CHI,
                },
                "valid_from_basis": "TEMPLATE_FIELD",
                "valid_to_state": "BOUNDED",
                # Day-truncated, but not month-truncated: the end has its own check.
                "valid_to": {
                    "instant": "2026-12-15T06:00:00Z",
                    "granularity": "MONTH",
                    "zone": CHI,
                },
            }
        )
    assert code(refused) is TemporalReason.BOUND_NOT_TRUNCATED


# --- S0002 AC1 and S0005 AC1: block structure codes -----------------------

START = {"instant": "2026-06-01T05:00:00Z", "granularity": "DAY", "zone": CHI}
END = {"instant": "2026-09-01T05:00:00Z", "granularity": "DAY", "zone": CHI}


def _block(**changes: object) -> dict[str, object]:
    block: dict[str, object] = {
        "contract": "fact-temporal/v1",
        "valid_from": START,
        "valid_from_basis": "TEMPLATE_FIELD",
        "valid_to_state": "OPEN",
    }
    block.update(changes)
    return {k: v for k, v in block.items() if v is not None}


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"valid_to_state": "CLOSED"}, TemporalReason.END_STATE_INVALID),
        ({"valid_to": END}, TemporalReason.END_STATE_INVALID),  # OPEN with an end
        ({"valid_to_state": "BOUNDED"}, TemporalReason.END_STATE_INVALID),  # no end
        (
            {"valid_to_state": "BOUNDED", "valid_to": START},  # end not after start
            TemporalReason.END_STATE_INVALID,
        ),
        (
            {"valid_to_state": "UNKNOWN", "attestation_zone": CHI},  # no ending evidence
            TemporalReason.END_STATE_INVALID,
        ),
        (
            {"valid_to_state": "UNKNOWN", "ending_evidence_refs": [str(uuid4())]},  # no zone
            TemporalReason.END_STATE_INVALID,
        ),
        (
            {
                "valid_to_state": "UNKNOWN",
                "valid_to": END,
                "attestation_zone": CHI,
                "ending_evidence_refs": [str(uuid4())],
            },
            TemporalReason.END_STATE_INVALID,
        ),
        ({"valid_from_basis": None}, TemporalReason.START_BASIS_INVALID),
        ({"valid_from_basis": "GUESS"}, TemporalReason.START_BASIS_INVALID),
        ({"valid_from_basis": "ATTESTATION_FLOOR"}, TemporalReason.START_BASIS_INVALID),
        ({"valid_from": None}, TemporalReason.START_BASIS_INVALID),  # basis without start
        (
            {"valid_from": None, "valid_from_basis": None},  # unknown start without zone
            TemporalReason.TIME_ZONE_INVALID,
        ),
        ({"model_confidence": 0.99}, TemporalReason.TEMPORAL_FIELDS_REQUIRED),
        ({"contract": "fact-temporal/v2"}, TemporalReason.TEMPORAL_FIELDS_REQUIRED),
    ],
)
def test_s0002_ac1_s0005_ac1_structural_refusals(
    changes: dict[str, object], reason: TemporalReason
) -> None:
    with pytest.raises(TemporalRejected) as refused:
        parse_commit_temporal(_block(**changes))
    assert code(refused) is reason


@pytest.mark.parametrize(
    "basis", ["TEMPLATE_FIELD", "HUMAN", "MENTION_A", "MENTION_B", "MENTION_C"]
)
def test_s0005_ac1_every_caller_basis_is_recorded(basis: str) -> None:
    assert parse_commit_temporal(_block(valid_from_basis=basis)).valid_from_basis is StartBasis(
        basis
    )


# --- S0002 AC4-AC6 and D3: attestation derivation and placement ---------------


def d(value: str) -> DocumentDate:
    precision = {4: DatePrecision.YEAR, 7: DatePrecision.MONTH, 10: DatePrecision.DAY}[len(value)]
    return DocumentDate(value, precision)


def test_d4_attested_from_through_and_to_come_from_document_dates_only() -> None:
    derived = derive_attestation(
        [d("2026-06-01"), None, d("2026-03"), d("2026-05-20")], [d("2026-08-02"), d("2026-09")]
    )
    assert derived.attested_from == d("2026-03")
    assert derived.attested_through == d("2026-06-01")
    assert derived.attested_to == d("2026-08-02")
    assert derive_attestation([None], []).attested_from is None


def test_s0002_ac2_ex_sem_004_unknown_end_window() -> None:
    proposal = parse_commit_temporal(
        _block(
            valid_to_state="UNKNOWN",
            attestation_zone=CHI,
            ending_evidence_refs=[str(uuid4())],
            valid_from={"instant": "2026-01-01T06:00:00Z", "granularity": "DAY", "zone": CHI},
        )
    )
    placement = place(proposal, derive_attestation([d("2026-06-01")], [d("2026-08-02")]))
    assert placement.end_state is EndState.UNKNOWN
    assert placement.end == Bound(utc("2026-08-03T05:00:00Z"), Granularity.DAY, CHI)
    assert placement.validity_unknown_from == utc("2026-06-02T05:00:00Z")


def test_d3_unknown_end_whose_positive_evidence_postdates_the_ending_is_refused() -> None:
    proposal = parse_commit_temporal(
        _block(valid_to_state="UNKNOWN", attestation_zone=CHI, ending_evidence_refs=[str(uuid4())])
    )
    with pytest.raises(TemporalRejected) as refused:
        place(proposal, derive_attestation([d("2026-09-01")], [d("2026-08-02")]))
    assert code(refused) is TemporalReason.END_STATE_INVALID
    with pytest.raises(TemporalRejected) as refused:
        place(proposal, derive_attestation([d("2026-06-01")], [None]))  # ending undated
    assert code(refused) is TemporalReason.END_STATE_INVALID


def test_s0002_ac4_unknown_start_is_floored_at_attested_from() -> None:
    proposal = parse_commit_temporal(
        _block(valid_from=None, valid_from_basis=None, attestation_zone=CHI)
    )
    placement = place(proposal, derive_attestation([d("2025-12-15"), d("2026-02")], []))
    assert placement.basis is StartBasis.ATTESTATION_FLOOR
    assert placement.start == Bound(utc("2025-12-15T06:00:00Z"), Granularity.DAY, CHI)


def test_s0002_ac5_unknown_start_with_undated_evidence_is_refused() -> None:
    proposal = parse_commit_temporal(
        _block(valid_from=None, valid_from_basis=None, attestation_zone=CHI)
    )
    with pytest.raises(TemporalRejected) as refused:
        place(proposal, derive_attestation([None, None], []))
    assert code(refused) is TemporalReason.START_UNATTESTED


def test_s0002_ac6_echo_that_disagrees_is_refused_and_one_that_agrees_passes() -> None:
    derived = derive_attestation([d("2026-06-01")], [])
    agree = parse_commit_temporal(
        _block(expected_attestation={"attested_from": {"value": "2026-06-01", "precision": "DAY"}})
    )
    check_expected(agree, derived)
    disagree = parse_commit_temporal(
        _block(expected_attestation={"attested_from": {"value": "2026-05-01", "precision": "DAY"}})
    )
    with pytest.raises(TemporalRejected) as refused:
        check_expected(disagree, derived)
    assert code(refused) is TemporalReason.ATTESTATION_MISMATCH
    malformed = _block(expected_attestation={"attested_from": {"value": "June", "precision": "X"}})
    with pytest.raises(TemporalRejected) as refused:
        parse_commit_temporal(malformed)
    assert code(refused) is TemporalReason.ATTESTATION_MISMATCH


def test_bounded_placement_refuses_an_end_before_a_floored_start() -> None:
    proposal = parse_commit_temporal(
        _block(
            valid_from=None,
            valid_from_basis=None,
            attestation_zone=CHI,
            valid_to_state="BOUNDED",
            valid_to=END,
        )
    )
    with pytest.raises(TemporalRejected) as refused:
        place(proposal, derive_attestation([d("2026-10-01")], []))
    assert code(refused) is TemporalReason.END_STATE_INVALID


def test_document_date_periods() -> None:
    assert d("2026").next_first_day().isoformat() == "2027-01-01"
    assert d("2026-12").next_first_day().isoformat() == "2027-01-01"
    assert d("2026-02-28").next_first_day().isoformat() == "2026-03-01"
    with pytest.raises(ValueError):
        DocumentDate("2026-13", DatePrecision.MONTH)
    with pytest.raises(ValueError):
        DocumentDate("2026", DatePrecision.DAY)


@pytest.mark.parametrize(
    "raw",
    [
        {"instant": "June first", "granularity": "DAY", "zone": CHI},
        {"instant": 20260601, "granularity": "DAY", "zone": CHI},
        {"instant": "2026-06-01T05:00:00Z", "granularity": "DAY", "zone": CHI, "x": 1},
        "2026-06-01T05:00:00Z",
    ],
)
def test_structurally_malformed_bounds_are_invalid_ranges_not_temporal_reasons(raw: object) -> None:
    from brain_temporal.ranges import InvalidRangeError

    with pytest.raises(InvalidRangeError):
        parse_bound(raw)
