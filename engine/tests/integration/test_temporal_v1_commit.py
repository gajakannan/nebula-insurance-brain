"""F0008 fact-temporal/v1 commits on PostgreSQL 18: S0001 bounds, S0002 end
states and attestation, S0003 split and recorded close, S0005 guards.

Expectations come from the story ACs, ADR-0078 and the worked examples (§87 and
§115.4, EX-SEM-003/004, EX-OWN-003), not from the implementation. Every test
owns its database."""

from __future__ import annotations

from datetime import UTC, datetime

import psycopg
import pytest
from brain_domain.temporal import TemporalReason, TemporalRejected
from brain_testing.factslots import ADDITIONAL_INSURED, RELATED_TO
from engine.tests.fixtures.temporal import harness as h
from engine.tests.fixtures.temporal.harness import CHICAGO, bound, money

_clean_fact_tables = h._clean_fact_tables
database = h.database
world = h.world

LATER = "2031-01-01T00:00:00Z"  # a recorded coordinate after every fixed-clock commit


def problem_code(response) -> str:  # type: ignore[no-untyped-def]
    return response.json()["code"]


def refused(response, reason: TemporalReason) -> None:  # type: ignore[no-untyped-def]
    assert response.status_code == 422, response.text
    assert problem_code(response) == reason.value
    assert "detail" not in response.json() or response.json()["detail"] is None


def state(name: str, **extra: object) -> dict:
    return {"answer_contract": h.ENVELOPE, "state": name, **extra}


# --- S0001: precision and zone -----------------------------------------------


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ({"instant": "2026-06-01T05:00:00Z", "zone": CHICAGO}, TemporalReason.GRANULARITY_INVALID),
        (
            {"instant": "2026-06-01T05:00:00Z", "granularity": "FORTNIGHT", "zone": CHICAGO},
            TemporalReason.GRANULARITY_INVALID,
        ),
        (
            {"instant": "2026-06-01T05:00:00Z", "granularity": "DAY"},
            TemporalReason.TIME_ZONE_INVALID,
        ),
        (
            {"instant": "2026-06-01T05:00:00Z", "granularity": "DAY", "zone": "Nowhere/City"},
            TemporalReason.TIME_ZONE_INVALID,
        ),
        (
            {"instant": "2026-06-01T05:00:00Z", "granularity": "DAY", "zone": "UTC"},
            TemporalReason.BOUND_NOT_TRUNCATED,
        ),
    ],
)
async def test_s0001_ac1_ac2_invalid_bounds_are_refused_and_write_nothing(world, raw, reason):
    w = world
    slot = await w.slot()
    before = w.counts()
    response = await w.commit_v1(slot, money("5000000"), start=raw)
    refused(response, reason)
    assert w.counts() == before


async def test_s0001_ac2_chicago_midnight_is_accepted(world):
    w = world
    slot = await w.slot()
    response = await w.commit_v1(slot, money("5000000"), start=bound("2026-06-01T05:00:00Z"))
    assert response.status_code == 201, response.text


async def test_s0001_ac3_ex_sem_003_minute_in_standard_time_round_trips(world):
    w = world
    slot = await w.slot()
    start = bound("2026-07-01T06:01:00Z", "MINUTE", "Etc/GMT+6")
    response = await w.commit_v1(slot, money("1000000"), start=start)
    assert response.status_code == 201, response.text
    read = await w.read(slot, "2026-07-01T06:01:00Z")
    assert read.status_code == 200, read.text
    temporal = read.json()["temporal"]
    assert h.at(temporal["valid_from"]["instant"]) == h.at("2026-07-01T06:01:00Z")
    assert temporal["valid_from"]["granularity"] == "MINUTE"
    assert temporal["valid_from"]["zone"] == "Etc/GMT+6"


@pytest.mark.parametrize(
    ("granularity", "instant"),
    [
        ("YEAR", "2026-01-01T06:00:00Z"),
        ("QUARTER", "2026-04-01T05:00:00Z"),
        ("MONTH", "2026-06-01T05:00:00Z"),
        ("DAY", "2026-06-01T05:00:00Z"),
        ("HOUR", "2026-06-01T07:00:00Z"),
        ("MINUTE", "2026-06-01T07:01:00Z"),
        ("SECOND", "2026-06-01T07:01:30Z"),
    ],
)
async def test_s0001_ac4_every_granularity_round_trips_exactly(world, granularity, instant):
    w = world
    slot = await w.slot()
    response = await w.commit_v1(slot, money("1"), start=bound(instant, granularity))
    assert response.status_code == 201, response.text
    temporal = (await w.read(slot, instant)).json()["temporal"]
    assert temporal["valid_from"] == {
        "instant": h.at(instant).isoformat(),
        "granularity": granularity,
        "zone": CHICAGO,
    }
    local_day = h.at(temporal["valid_from"]["instant"]).astimezone(
        __import__("zoneinfo").ZoneInfo(CHICAGO)
    )
    if granularity == "DAY":
        assert local_day.date().isoformat() == "2026-06-01"  # never 2026-05-31


async def test_s0001_ac5_start_and_end_granularities_are_independent(world):
    w = world
    slot = await w.slot()
    response = await w.commit_v1(
        slot,
        money("1"),
        start=bound("2026-06-01T05:00:00Z", "DAY"),
        end_state="BOUNDED",
        end=bound("2027-01-01T06:00:00Z", "MONTH"),
    )
    assert response.status_code == 201, response.text
    temporal = (await w.read(slot, "2026-06-02T00:00:00Z")).json()["temporal"]
    assert (temporal["valid_from"]["granularity"], temporal["valid_to"]["granularity"]) == (
        "DAY",
        "MONTH",
    )


async def test_s0001_ac6_event_and_eternal_shapes_need_no_ddl_and_state_is_written(world):
    w = world
    slot = await w.slot()
    assert (
        await w.commit_v1(slot, money("1"), start=bound("2026-06-01T05:00:00Z"))
    ).status_code == 201
    assert {v["temporal_kind"] for v in w.versions(slot)} == {"STATE"}
    version = w.versions(slot)[0]
    # EVENT and ETERNAL rows are representable in the same row design (D10).
    with psycopg.connect(w.url) as connection:
        for kind, valid, columns in (
            (
                "EVENT",
                "[2026-06-02 05:00:00+00,2026-06-03 05:00:00+00)",
                "'DAY', 'America/Chicago', 'TEMPLATE_FIELD', 'BOUNDED', 'DAY', 'America/Chicago'",
            ),
            ("ETERNAL", "(,)", "NULL, NULL, NULL, 'OPEN', NULL, NULL"),
        ):
            other = await w.slot()
            connection.execute(
                "INSERT INTO canonical_fact_version (id, slot_id, tenant_id, knowledge_base_id, "
                "value, valid, recorded, evidence, commit_id, source_received_at, "
                "artifact_created_at, assertion_created_at, canonical_accepted_at, "
                "temporal_contract, temporal_kind, valid_from_granularity, valid_from_zone, "
                "valid_from_basis, valid_to_state, valid_to_granularity, valid_to_zone) "
                "SELECT gen_random_uuid(), %s, tenant_id, knowledge_base_id, value, "
                "%s::tstzrange, "
                "recorded, evidence, commit_id, source_received_at, artifact_created_at, "
                f"assertion_created_at, canonical_accepted_at, 1, %s, {columns} "
                "FROM canonical_fact_version WHERE id = %s",
                (other, valid, kind, version["id"]),
            )
        # An EVENT longer than one granularity period is refused by the trigger.
        third = await w.slot()
        with pytest.raises(psycopg.errors.CheckViolation):
            connection.execute(
                "INSERT INTO canonical_fact_version (id, slot_id, tenant_id, knowledge_base_id, "
                "value, valid, recorded, evidence, commit_id, source_received_at, "
                "artifact_created_at, assertion_created_at, canonical_accepted_at, "
                "temporal_contract, temporal_kind, valid_from_granularity, valid_from_zone, "
                "valid_from_basis, valid_to_state, valid_to_granularity, valid_to_zone) "
                "SELECT gen_random_uuid(), %s, tenant_id, knowledge_base_id, value, "
                "'[2026-06-02 05:00:00+00,2026-06-04 05:00:00+00)', recorded, evidence, commit_id, "
                "source_received_at, artifact_created_at, assertion_created_at, "
                "canonical_accepted_at, 1, 'EVENT', 'DAY', 'America/Chicago', 'TEMPLATE_FIELD', "
                "'BOUNDED', 'DAY', 'America/Chicago' FROM canonical_fact_version WHERE id = %s",
                (third, version["id"]),
            )


@pytest.mark.parametrize(
    ("valid", "granularity", "zone"),
    [
        ("[2026-06-01 06:00:00+00,)", "DAY", "America/Chicago"),  # not Chicago midnight
        ("[2026-06-01 05:00:00+00,)", "DAY", "UTC"),
        ("[2026-06-01 05:00:00+00,)", "DAY", "Nowhere/City"),
        ("[2026-05-01 05:00:00+00,)", "QUARTER", "America/Chicago"),
    ],
)
async def test_s0001_database_trigger_is_authoritative_for_zone_and_truncation(
    world, valid, granularity, zone
):
    w = world
    slot = await w.slot()
    assert (
        await w.commit_v1(slot, money("1"), start=bound("2026-06-01T05:00:00Z"))
    ).status_code == 201
    other = await w.slot()
    with psycopg.connect(w.url) as connection, pytest.raises(psycopg.errors.CheckViolation):
        connection.execute(
            "INSERT INTO canonical_fact_version (id, slot_id, tenant_id, knowledge_base_id, value, "
            "valid, recorded, evidence, commit_id, source_received_at, artifact_created_at, "
            "assertion_created_at, canonical_accepted_at, temporal_contract, temporal_kind, "
            "valid_from_granularity, valid_from_zone, valid_from_basis, valid_to_state) "
            "SELECT gen_random_uuid(), %s, tenant_id, knowledge_base_id, value, %s::tstzrange, "
            "recorded, evidence, commit_id, source_received_at, artifact_created_at, "
            "assertion_created_at, canonical_accepted_at, 1, 'STATE', %s, %s, 'TEMPLATE_FIELD', "
            "'OPEN' FROM canonical_fact_version WHERE slot_id = %s",
            (other, valid, granularity, zone, slot),
        )


# --- S0002: open, bounded and unknown ends -------------------------------------


async def test_s0002_ac1_each_end_state_is_stored_and_others_refused(world):
    w = world
    for end_state, extra in (
        ("OPEN", {}),
        ("BOUNDED", {"end": bound("2026-09-01T05:00:00Z")}),
    ):
        slot = await w.slot()
        response = await w.commit_v1(
            slot, money("1"), start=bound("2026-06-01T05:00:00Z"), end_state=end_state, **extra
        )
        assert response.status_code == 201, response.text
        assert w.versions(slot)[0]["valid_to_state"] == end_state
    slot = await w.slot()
    before = w.counts()
    for end_state, extra in (
        ("CLOSED", {}),
        ("OPEN", {"end": bound("2026-09-01T05:00:00Z")}),
        ("BOUNDED", {}),
        ("UNKNOWN", {"attestation_zone": CHICAGO}),  # no ending evidence -> no attested_to
    ):
        response = await w.commit_v1(
            slot, money("1"), start=bound("2026-06-01T05:00:00Z"), end_state=end_state, **extra
        )
        refused(response, TemporalReason.END_STATE_INVALID)
    ending_undated = w.evidence(None)
    response = await w.commit_v1(
        slot,
        money("1"),
        start=bound("2026-06-01T05:00:00Z"),
        end_state="UNKNOWN",
        attestation_zone=CHICAGO,
        ending=[ending_undated],
    )
    refused(response, TemporalReason.END_STATE_INVALID)
    assert w.counts() == before


async def test_s0002_ac2_ac3_ac7_ex_sem_004_prior_carrier(world):
    """EX-SEM-004: attested positively 2026-06-01, ended by a broker note dated
    2026-08-02 with the end date unknown."""
    w = world
    slot = await w.slot()
    positive = w.evidence(("2026-06-01", "DAY"))
    note = w.evidence(("2026-08-02", "DAY"))
    response = await w.commit_v1(
        slot,
        money("1000000"),
        start=bound("2026-01-01T06:00:00Z"),
        end_state="UNKNOWN",
        attestation_zone=CHICAGO,
        evidence=[positive],
        ending=[note],
    )
    assert response.status_code == 201, response.text
    (row,) = w.versions(slot)
    assert row["valid_to_state"] == "UNKNOWN"
    assert row["valid"] == '["2026-01-01 06:00:00+00","2026-08-03 05:00:00+00")'
    assert h.at(row["validity_unknown_from"]) == h.at("2026-06-02T05:00:00Z")
    assert (row["attested_to_value"], row["attested_from_value"]) == ("2026-08-02", "2026-06-01")

    carrier = await w.read(slot, "2026-05-15T12:00:00Z")
    assert carrier.status_code == 200 and carrier.json()["value"]["value"]["amount"] == "1000000"
    unknown = await w.read(slot, "2026-07-15T12:00:00Z")
    assert unknown.status_code == 200, unknown.text
    assert unknown.json()["validity"] == "UNKNOWN"
    assert unknown.json()["reason"] == "UNKNOWN_END_WINDOW"
    assert "value" not in unknown.json()
    # AC7: end state, attestation and start marker are returned without nulls to interpret.
    temporal = carrier.json()["temporal"]
    assert temporal["valid_to_state"] == "UNKNOWN"
    assert temporal["attested_to"] == {"value": "2026-08-02", "precision": "DAY"}
    assert temporal["attested_from"] == {"value": "2026-06-01", "precision": "DAY"}
    assert temporal["valid_from_basis"] == "TEMPLATE_FIELD"

    # AC3: the UNKNOWN end still takes part in the exclusion.
    with psycopg.connect(w.url) as connection, pytest.raises(psycopg.errors.ExclusionViolation):
        connection.execute(
            "INSERT INTO canonical_fact_version (id, slot_id, tenant_id, knowledge_base_id, value, "
            "valid, recorded, evidence, commit_id, source_received_at, artifact_created_at, "
            "assertion_created_at, canonical_accepted_at, temporal_contract, temporal_kind, "
            "valid_from_granularity, valid_from_zone, valid_from_basis, valid_to_state) "
            "SELECT gen_random_uuid(), slot_id, tenant_id, knowledge_base_id, value, "
            "'[2026-08-02 05:00:00+00,)', recorded, evidence, commit_id, source_received_at, "
            "artifact_created_at, assertion_created_at, canonical_accepted_at, 1, 'STATE', 'DAY', "
            "'America/Chicago', 'TEMPLATE_FIELD', 'OPEN' FROM canonical_fact_version "
            "WHERE slot_id = %s",
            (slot,),
        )


async def test_s0002_ac4_unknown_start_is_floored_and_never_reaches_minus_infinity(world):
    w = world
    slot = await w.slot()
    first = w.evidence(("2026-02", "MONTH"))
    second = w.evidence(("2025-12-15", "DAY"))
    response = await w.commit_v1(
        slot, money("750000"), start=None, attestation_zone=CHICAGO, evidence=[first, second]
    )
    assert response.status_code == 201, response.text
    (row,) = w.versions(slot)
    assert row["valid"] == '["2025-12-15 06:00:00+00",)'
    assert row["valid_from_basis"] == "ATTESTATION_FLOOR"
    assert row["valid_from_granularity"] == "DAY"
    before_floor = await w.read(slot, "2025-03-01T12:00:00Z")
    assert before_floor.status_code == 200, before_floor.text
    assert before_floor.json()["reason"] == "BEFORE_ATTESTATION_FLOOR"
    assert "value" not in before_floor.json()


async def test_s0002_ac5_unknown_start_with_undated_evidence_is_refused(world):
    w = world
    slot = await w.slot()
    undated = w.evidence(None)
    cleared = w.evidence(("2026-01-01", "DAY"))
    w.select_date(cleared, None)  # F0004: a later clear leaves the document undated
    before = w.counts()
    for evidence in ([undated], [cleared], []):
        response = await w.commit_v1(
            slot, money("1"), start=None, attestation_zone=CHICAGO, evidence=evidence
        )
        refused(response, TemporalReason.START_UNATTESTED)
    assert w.counts() == before


async def test_s0002_ac6_attestation_is_derived_and_a_disagreeing_echo_is_refused(world):
    w = world
    slot = await w.slot()
    ev = w.evidence(("2026-06-01", "DAY"))
    w.select_date(ev, ("2026-06-03", "DAY"))  # the latest selection is current
    before = w.counts()
    response = await w.commit_v1(
        slot,
        money("1"),
        start=bound("2026-06-01T05:00:00Z"),
        evidence=[ev],
        expected={"attested_from": {"value": "2026-06-01", "precision": "DAY"}},
    )
    refused(response, TemporalReason.ATTESTATION_MISMATCH)
    assert w.counts() == before
    response = await w.commit_v1(
        slot,
        money("1"),
        start=bound("2026-06-01T05:00:00Z"),
        evidence=[ev],
        expected={
            "attested_from": {"value": "2026-06-03", "precision": "DAY"},
            "attested_to": None,
        },
    )
    assert response.status_code == 201, response.text
    assert w.versions(slot)[0]["attested_from_value"] == "2026-06-03"


async def test_s0002_ac6_receipt_and_acceptance_times_are_never_attestation(world):
    """ADR-0064 §8: an undated document with receipt timestamps stays undated."""
    w = world
    slot = await w.slot()
    response = await w.commit_v1(
        slot,
        money("1"),
        start=bound("2026-06-01T05:00:00Z"),
        evidence=[w.evidence(None)],
        received="2026-06-12T14:00:00Z",
    )
    assert response.status_code == 201
    (row,) = w.versions(slot)
    assert row["attested_from_value"] is None and row["attested_through_value"] is None


# --- S0003: split intervals and close recorded time ------------------------------


async def _section_87(w):  # type: ignore[no-untyped-def]
    slot = await w.slot()
    original = w.body(
        money("2000000"),
        start=bound("2026-01-01T06:00:00Z"),
        received="2026-01-08T15:00:00Z",
    )
    first = await w.commit_at(slot, original, "2026-01-10T16:00:00Z")
    endorsement = w.body(
        money("5000000"),
        start=bound("2026-06-01T05:00:00Z"),
        received="2026-06-12T14:00:00Z",
    )
    second = await w.commit_at(slot, endorsement, "2026-06-14T15:00:00Z")
    return slot, first, second


async def test_s0003_ac1_ac6_retroactive_endorsement_splits_and_keeps_distinct_times(world):
    w = world
    slot, first, second = await _section_87(w)
    rows = w.versions(slot)
    assert len(rows) == 3
    original, remainder, endorsement = (
        next(r for r in rows if r["id"] == str(first.fact_version_ids[0])),
        next(r for r in rows if r["change_reason"] == "split"),
        next(r for r in rows if r["value"]["value"]["amount"] == "5000000"),
    )
    assert original["recorded"] == '["2026-01-10 16:00:00+00","2026-06-14 15:00:00+00")'
    assert remainder["valid"] == '["2026-01-01 06:00:00+00","2026-06-01 05:00:00+00")'
    assert remainder["value"]["value"]["amount"] == "2000000"
    assert endorsement["valid"] == '["2026-06-01 05:00:00+00",)'
    # AC6: receipt 2026-06-12, recorded time starts at acceptance 2026-06-14.
    assert h.at(endorsement["source_received_at"]) == h.at("2026-06-12T14:00:00Z")
    assert endorsement["recorded"] == '["2026-06-14 15:00:00+00",)'
    assert h.at(endorsement["canonical_accepted_at"]) == h.at("2026-06-14T15:00:00Z")


async def test_s0003_ac3_remainder_keeps_predecessor_payload_lineage_and_timestamps(world):
    w = world
    slot, first, _ = await _section_87(w)
    rows = w.versions(slot)
    original = next(r for r in rows if r["id"] == str(first.fact_version_ids[0]))
    remainder = next(r for r in rows if r["change_reason"] == "split")
    for column in (
        "value",
        "evidence",
        "review_decision_id",
        "source_received_at",
        "artifact_created_at",
        "assertion_created_at",
        "valid_from_granularity",
        "valid_from_zone",
        "valid_from_basis",
        "attested_from_value",
        "temporal_kind",
    ):
        assert remainder[column] == original[column], column
    # Not the new proposal's receipt (the pilot defect this story fixes).
    assert h.at(remainder["source_received_at"]) == h.at("2026-01-08T15:00:00Z")
    assert remainder["split_of_version_id"] == original["id"]
    assert remainder["recorded"] == '["2026-06-14 15:00:00+00",)'
    assert remainder["valid_to_state"] == "BOUNDED"
    assert (remainder["valid_to_granularity"], remainder["valid_to_zone"]) == ("DAY", CHICAGO)


async def test_s0003_ac2_correction_splits_again_and_links_every_closed_version(world):
    w = world
    slot, _, second = await _section_87(w)
    correction = w.body(
        money("5000000"),
        start=bound("2026-06-03T05:00:00Z"),
        received="2026-06-20T14:00:00Z",
        change_reason="corrected",
    )
    third = await w.commit_at(slot, correction, "2026-06-21T15:00:00Z")
    current = [
        r for r in w.versions(slot) if r["recorded"].endswith(",)") and r["valid"] is not None
    ]
    assert sorted((r["valid"], r["value"]["value"]["amount"]) for r in current) == [
        ('["2026-01-01 06:00:00+00","2026-06-01 05:00:00+00")', "2000000"),
        ('["2026-06-01 05:00:00+00","2026-06-03 05:00:00+00")', "5000000"),
        ('["2026-06-03 05:00:00+00",)', "5000000"),
    ]
    # Every earlier belief is still readable at its own recorded coordinates.
    assert (await w.read(slot, "2026-06-02T12:00:00Z", "2026-06-15T00:00:00Z")).json()["value"][
        "value"
    ]["amount"] == "5000000"
    assert (await w.read(slot, "2026-06-02T12:00:00Z", "2026-06-05T00:00:00Z")).json()["value"][
        "value"
    ]["amount"] == "2000000"
    closed = {r["id"] for r in w.versions(slot) if not r["recorded"].endswith(",)")}
    new_id = str(third.fact_version_ids[-1])
    links = {(str(f), str(t), reason) for reason, f, t in w.changes(slot) if f is not None}
    for version_id in closed:
        assert any(f == version_id for f, _, _ in links), version_id
    assert (str(second.fact_version_ids[-1]), new_id, "corrected") in links


async def test_s0003_ac4_non_overlapping_intervals_are_not_touched(world):
    w = world
    slot = await w.slot()
    early = w.body(
        money("1"),
        start=bound("2026-01-01T06:00:00Z"),
        end_state="BOUNDED",
        end=bound("2026-03-01T06:00:00Z"),
    )
    await w.commit_at(slot, early, "2026-01-10T00:00:00Z")
    before = w.versions(slot)
    later = w.body(money("2"), start=bound("2026-06-01T05:00:00Z"))
    await w.commit_at(slot, later, "2026-06-14T00:00:00Z")
    after = w.versions(slot)
    assert [r for r in after if r["id"] == before[0]["id"]] == before
    assert len(after) == 2


# --- S0005: guard succession by start basis and state ----------------------------


@pytest.mark.parametrize("basis", ["TEMPLATE_FIELD", "HUMAN", "MENTION_A", "MENTION_B"])
async def test_s0005_ac2_anchored_bases_close_and_split(world, basis):
    w = world
    slot = await w.slot()
    assert (
        await w.commit_v1(slot, money("2000000"), start=bound("2026-01-01T06:00:00Z"))
    ).status_code == 201
    response = await w.commit_v1(
        slot, money("5000000"), start=bound("2026-06-01T05:00:00Z"), basis=basis
    )
    assert response.status_code == 201, response.text
    assert len(w.versions(slot)) == 3


async def test_s0005_ac3_mention_c_and_floor_cannot_succeed_but_may_stand_alone(world):
    w = world
    slot = await w.slot()
    assert (
        await w.commit_v1(slot, money("2000000"), start=bound("2026-01-01T06:00:00Z"))
    ).status_code == 201
    before = w.versions(slot)
    counts = w.counts()
    refused(
        await w.commit_v1(
            slot, money("5000000"), start=bound("2026-06-01T05:00:00Z"), basis="MENTION_C"
        ),
        TemporalReason.SUCCESSION_START_UNANCHORED,
    )
    refused(
        await w.commit_v1(
            slot,
            money("5000000"),
            start=None,
            attestation_zone=CHICAGO,
            evidence=[w.evidence(("2026-06-01", "DAY"))],
        ),
        TemporalReason.SUCCESSION_START_UNANCHORED,
    )
    assert w.versions(slot) == before and w.counts() == counts
    # The refusal is audited as a failed commit decision (G0 reconciliation 5).
    failed = w.scalar(
        "SELECT count(*) FROM audit_event WHERE resource_id = %s AND action = 'commit' "
        "AND operation_outcome = 'failed'",
        slot,
    )
    assert failed == 2
    # The same MENTION_C proposal on an empty slot is accepted.
    empty = await w.slot()
    assert (
        await w.commit_v1(
            empty, money("5000000"), start=bound("2026-06-01T05:00:00Z"), basis="MENTION_C"
        )
    ).status_code == 201


async def test_s0005_ac3_end_revision_of_a_floored_start_is_not_a_succession(world):
    """EX-PC-014: OPEN -> UNKNOWN keeps the answer, start, basis and attested_from."""
    w = world
    slot = await w.slot()
    found = w.evidence(("2025-12-15", "DAY"))
    first = await w.commit_v1(
        slot, money("750000"), start=None, attestation_zone=CHICAGO, evidence=[found]
    )
    assert first.status_code == 201, first.text
    request = w.evidence(("2026-05-15", "DAY"))
    revision = await w.commit_v1(
        slot,
        money("750000"),
        start=None,
        attestation_zone=CHICAGO,
        evidence=[found],
        end_state="UNKNOWN",
        ending=[request],
    )
    assert revision.status_code == 201, revision.text
    current = [r for r in w.versions(slot) if r["recorded"].endswith(",)")]
    assert len(current) == 1  # replaced whole: no remainder of the open version
    assert current[0]["valid_to_state"] == "UNKNOWN"
    # A different answer from a floored start is a succession and is refused.
    refused(
        await w.commit_v1(
            slot,
            money("900000"),
            start=None,
            attestation_zone=CHICAGO,
            evidence=[found],
            end_state="UNKNOWN",
            ending=[request],
        ),
        TemporalReason.SUCCESSION_START_UNANCHORED,
    )


async def test_s0005_ac4_ex_own_003_states_supersede_and_stay_readable(world):
    w = world
    slot = await w.slot()
    artifact = w.a.artifact_id
    scope = {
        "content_artifact_id": str(artifact),
        "profile_release_ref": "gl-policy-profile/1",
        "pages": [1, 2, 3],
    }
    steps = [
        (state("NOT_PROCESSED"), "2026-02-01T00:00:00Z"),
        (state("NOT_STATED", scope=scope), "2026-03-01T00:00:00Z"),
        (state("EXPLICIT_NEGATIVE"), "2026-04-01T00:00:00Z"),
    ]
    for value, accepted in steps:
        await w.commit_at(slot, w.body(value, start=bound("2026-01-01T06:00:00Z")), accepted)
    for (value, accepted), _ in zip(steps, range(3), strict=True):
        read = await w.read(slot, "2026-06-01T12:00:00Z", accepted)
        assert read.status_code == 200, read.text
        assert read.json()["value"]["state"] == value["state"]


@pytest.mark.parametrize(
    "successor",
    ["NOT_FOUND", "NOT_STATED", "ILLEGIBLE", "AMBIGUOUS", "CONFLICTING", "NOT_APPLICABLE"],
)
async def test_s0005_ac5_present_is_not_replaced_by_a_non_value_state(world, successor):
    w = world
    slot = await w.slot()
    assert (
        await w.commit_v1(slot, money("5000000"), start=bound("2026-01-01T06:00:00Z"))
    ).status_code == 201
    before = w.versions(slot)
    extra = (
        {
            "scope": {
                "content_artifact_id": str(w.a.artifact_id),
                "profile_release_ref": "gl-policy-profile/1",
                "pages": [1, 2, 3],
            }
        }
        if successor in ("NOT_FOUND", "NOT_STATED")
        else {}
    )
    response = await w.commit_v1(
        slot, state(successor, **extra), start=bound("2026-06-01T05:00:00Z")
    )
    refused(response, TemporalReason.STATE_SUPERSESSION_REFUSED)
    assert w.versions(slot) == before


@pytest.mark.parametrize("successor", ["PRESENT", "EXPLICIT_NEGATIVE"])
async def test_s0005_ac6_present_closes_to_present_or_explicit_negative(world, successor):
    w = world
    slot = await w.slot()
    assert (
        await w.commit_v1(slot, money("5000000"), start=bound("2026-01-01T06:00:00Z"))
    ).status_code == 201
    value = money("6000000") if successor == "PRESENT" else state("EXPLICIT_NEGATIVE")
    response = await w.commit_v1(slot, value, start=bound("2026-06-01T05:00:00Z"))
    assert response.status_code == 201, response.text


async def test_s0005_ac6_non_present_predecessor_closes_to_any_state(world):
    w = world
    slot = await w.slot()
    assert (
        await w.commit_v1(slot, state("NOT_PROCESSED"), start=bound("2026-01-01T06:00:00Z"))
    ).status_code == 201
    response = await w.commit_v1(slot, state("ILLEGIBLE"), start=bound("2026-06-01T05:00:00Z"))
    assert response.status_code == 201, response.text


async def test_s0005_ac7_guards_apply_per_member(world):
    w = world
    subject = w.entity(w.a)
    x, y = w.entity(w.a), w.entity(w.a)
    members = []
    for entity in (x, y):
        result = await w.resolve(
            w.key(
                w.a,
                ADDITIONAL_INSURED,
                subject=subject,
                member={"type": "entity_ref", "entity_id": str(entity)},
            )
        )
        members.append((result.member_slot_id, entity))
    for member, entity in members:
        value = {
            "answer_contract": h.ENVELOPE,
            "state": "PRESENT",
            "value": {"type": "entity_ref", "entity_id": str(entity)},
        }
        response = await w.commit_v1(member, value, start=bound("2026-01-01T06:00:00Z"))
        assert response.status_code == 201, response.text
    (m1, _), (m2, _) = members
    m2_before = w.versions(m2)
    refused(
        await w.commit_v1(m1, state("NOT_APPLICABLE"), start=bound("2026-06-01T05:00:00Z")),
        TemporalReason.STATE_SUPERSESSION_REFUSED,
    )
    assert w.versions(m2) == m2_before


# --- S0007 AC3 and D1 at the commit boundary --------------------------------------


async def test_s0007_ac3_pilot_shape_to_identity_v1_slot_is_refused(world):
    w = world
    slot = await w.slot()
    before = w.counts()
    response = await w.commit(slot, money("1"))  # F0007 helper switches to v1 for v1 slots
    assert response.status_code == 201
    body = w.body(money("1"), start=bound("2026-06-01T05:00:00Z"))
    del body["temporal"]
    body["valid_from"] = "2026-06-01T05:00:00Z"
    refused(await w.post(slot, body), TemporalReason.TEMPORAL_FIELDS_REQUIRED)
    assert w.counts()["canonical_fact_version"] == before["canonical_fact_version"] + 1


async def test_relationship_slot_versions_share_the_table(world):
    """S0004 AC4 (commit half): a RELATIONSHIP slot takes the same v1 path."""
    w = world
    slot = await w.slot(RELATED_TO, object_entity_id=str(w.entity(w.a)))
    value = {
        "answer_contract": h.ENVELOPE,
        "state": "PRESENT",
        "value": {"type": "decimal", "value": "1"},
    }
    assert (await w.commit_v1(slot, value, start=bound("2026-01-01T06:00:00Z"))).status_code == 201
    value["value"]["value"] = "2"
    assert (await w.commit_v1(slot, value, start=bound("2026-06-01T05:00:00Z"))).status_code == 201
    assert len(w.versions(slot)) == 3
    assert w.scalar("SELECT to_regclass('canonical_relationship_version')") is None


async def test_service_refusal_is_raised_before_any_effect(world):
    """The guard runs inside the unit of work; the service raises and the caller's
    transaction writes nothing (S0005 Non-Functional)."""
    w = world
    slot = await w.slot()
    await w.commit_at(
        slot, w.body(money("5"), start=bound("2026-01-01T06:00:00Z")), "2026-01-10T00:00:00Z"
    )
    before = w.counts()
    with pytest.raises(TemporalRejected) as exc:
        await w.commit_at(
            slot,
            w.body(state("NOT_APPLICABLE"), start=bound("2026-06-01T05:00:00Z")),
            "2026-06-14T00:00:00Z",
        )
    assert exc.value.code is TemporalReason.STATE_SUPERSESSION_REFUSED
    assert w.counts() == before
    assert datetime.now(UTC) > h.at("2026-06-14T00:00:00Z")


async def test_s0002_ac7_commit_response_returns_temporal_metadata(world):
    """S0002 AC7 (remediation 2026-11-18): the commit response returns, per version
    written, the end state, attestation dates and start marker, in
    `fact_version_ids` order. A remainder carries its own block and lineage."""
    w = world
    slot = await w.slot()
    positive, note = w.evidence(("2026-06-01", "DAY")), w.evidence(("2026-08-02", "DAY"))
    first = await w.commit_v1(
        slot, money("2000000"), start=bound("2026-01-01T06:00:00Z"), evidence=[positive]
    )
    assert first.status_code == 201, first.text
    (only,) = first.json()["versions"]
    assert only["fact_version_id"] == first.json()["fact_version_ids"][0]
    assert only["temporal"]["valid_to_state"] == "OPEN"
    assert only["temporal"]["valid_from_basis"] == "TEMPLATE_FIELD"
    assert only["temporal"]["attested_from"] == {"value": "2026-06-01", "precision": "DAY"}

    second = await w.commit_v1(
        slot,
        money("5000000"),
        start=bound("2026-03-01T06:00:00Z"),
        evidence=[positive],
        end_state="UNKNOWN",
        attestation_zone=CHICAGO,
        ending=[note],
    )
    assert second.status_code == 201, second.text
    body = second.json()
    assert [v["fact_version_id"] for v in body["versions"]] == body["fact_version_ids"]
    remainder, new = body["versions"]
    assert remainder["temporal"]["valid_to_state"] == "BOUNDED"
    assert remainder["temporal"]["split_of_version_id"] == only["fact_version_id"]
    assert new["temporal"]["valid_to_state"] == "UNKNOWN"
    assert new["temporal"]["attested_to"] == {"value": "2026-08-02", "precision": "DAY"}
    assert new["temporal"]["split_of_version_id"] is None
    # The response matches what the read returns for the same version.
    read = await w.read(slot, "2026-04-01T12:00:00Z")
    assert read.json()["temporal"] == new["temporal"]
