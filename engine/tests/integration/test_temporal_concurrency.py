"""F0008-S0004 under real concurrency on PostgreSQL 18 (ADR-0078 D6): the slot
row lock serializes writers under READ COMMITTED, and the exclusion constraint is
the backstop. Every test owns its database."""

from __future__ import annotations

import asyncio

import psycopg
import pytest
from brain_testing.factslots import ADDITIONAL_INSURED, RELATED_TO
from engine.tests.fixtures.temporal import harness as h
from engine.tests.fixtures.temporal.harness import bound, money

_clean_fact_tables = h._clean_fact_tables
database = h.database
world = h.world

RACERS = 12
STARTS = [f"2026-{m:02d}-01T05:00:00Z" for m in range(4, 10)]  # Chicago midnights (CDT)


def grid_violations(w, slot) -> tuple[int, int]:  # type: ignore[no-untyped-def]
    """(coordinates checked, coordinates resolving to more than one version) over a
    dense grid: every 5 days of valid time x every recorded boundary and midpoint."""
    row = w.rows(
        """
        WITH known AS (
            SELECT DISTINCT k FROM (
                SELECT lower(recorded) AS k FROM canonical_fact_version WHERE slot_id = %s
                UNION SELECT lower(recorded) + interval '1 microsecond'
                  FROM canonical_fact_version WHERE slot_id = %s
                UNION SELECT now() + interval '1 day'
            ) s
        ), valid AS (
            SELECT generate_series(timestamptz '2025-12-01', timestamptz '2026-12-31',
                                   interval '5 days') AS v
        ), hits AS (
            SELECT v, k, (SELECT count(*) FROM canonical_fact_version f
                           WHERE f.slot_id = %s AND f.valid @> v AND f.recorded @> k) AS n
            FROM valid CROSS JOIN known
        )
        SELECT count(*), count(*) FILTER (WHERE n > 1) FROM hits
        """,
        slot,
        slot,
        slot,
    )[0]
    return row[0], row[1]


def audit_successes(w, slot) -> int:  # type: ignore[no-untyped-def]
    return w.scalar(
        "SELECT count(*) FROM audit_event WHERE resource_id = %s AND action = 'commit' "
        "AND operation_outcome = 'succeeded'",
        slot,
    )


async def test_s0004_ac1_racing_commits_leave_one_answer_per_coordinate(world):
    w = world
    slot = await w.slot()
    first = await w.commit_v1(slot, money("1000000"), start=bound("2026-01-01T06:00:00Z"))
    assert first.status_code == 201
    initial = w.versions(slot)[0]["id"]

    async def racer(i: int):  # type: ignore[no-untyped-def]
        return await w.commit_v1(
            slot,
            money(str(2000000 + i)),
            start=bound(STARTS[i % len(STARTS)]),
            expected_current=initial,
        )

    responses = await asyncio.gather(*(racer(i) for i in range(RACERS)))
    winners = [r for r in responses if r.status_code == 201]
    losers = [r for r in responses if r.status_code != 201]
    assert len(winners) == 1, [r.text for r in responses]
    assert {r.status_code for r in losers} == {409}
    assert {r.json()["code"] for r in losers} <= {"stale_version", "temporal_conflict"}

    checked, overlapping = grid_violations(w, slot)
    assert checked >= 200 and overlapping == 0
    # Each winner wrote exactly one commit audit and one outbox event; losers none.
    assert audit_successes(w, slot) == 2
    # Amended S0004 AC1 (operator, 2026-11-18): each loser writes no successful commit
    # audit, and its authorization decision is durably recorded with outcome `failed`
    # (the F0002 guarantee that every authorization decision is audited).
    assert w.scalar(
        "SELECT count(*) FROM audit_event WHERE resource_id = %s AND action = 'commit' "
        "AND operation_outcome = 'failed'",
        slot,
    ) == len(losers)
    assert (
        w.scalar(
            "SELECT count(*) FROM outbox_event o JOIN canonical_commit c ON c.id = o.commit_id "
            "JOIN canonical_fact_version v ON v.commit_id = c.id WHERE v.slot_id = %s",
            slot,
        )
        >= 2
    )
    assert (
        w.scalar(
            "SELECT count(DISTINCT commit_id) FROM canonical_fact_version WHERE slot_id = %s", slot
        )
        == 2
    )
    assert (
        w.scalar(
            "SELECT count(*) FROM outbox_event WHERE commit_id IN "
            "(SELECT commit_id FROM canonical_fact_version WHERE slot_id = %s)",
            slot,
        )
        == 2
    )


async def test_s0004_ac1_unconditional_racers_serialize_without_overlap(world):
    """Without an optimistic check every racer wins in turn; the slot lock orders
    them and no coordinate ever holds two answers."""
    w = world
    slot = await w.slot()
    responses = await asyncio.gather(
        *(
            w.commit_v1(slot, money(str(100 + i)), start=bound(STARTS[i % len(STARTS)]))
            for i in range(RACERS)
        )
    )
    assert all(r.status_code == 201 for r in responses), [r.text for r in responses]
    checked, overlapping = grid_violations(w, slot)
    assert checked >= 200 and overlapping == 0
    assert audit_successes(w, slot) == RACERS


async def test_s0004_ac3_multi_members_commit_concurrently_and_independently(world):
    w = world
    subject = w.entity(w.a)
    members = []
    for _ in range(2):
        entity = w.entity(w.a)
        result = await w.resolve(
            w.key(
                w.a,
                ADDITIONAL_INSURED,
                subject=subject,
                member={"type": "entity_ref", "entity_id": str(entity)},
            )
        )
        members.append((result.member_slot_id, entity))

    def present(entity):  # type: ignore[no-untyped-def]
        return {
            "answer_contract": h.ENVELOPE,
            "state": "PRESENT",
            "value": {"type": "entity_ref", "entity_id": str(entity)},
        }

    responses = await asyncio.gather(
        *(
            w.commit_v1(member, present(entity), start=bound("2026-01-01T06:00:00Z"))
            for member, entity in members
        )
    )
    assert all(r.status_code == 201 for r in responses), [r.text for r in responses]
    (m1, _), (m2, _) = members
    m2_before = w.versions(m2)
    # Overlapping valid and recorded time across members is legal (EX-SLOT-003).
    assert (
        w.scalar(
            "SELECT count(*) FROM canonical_fact_version a JOIN canonical_fact_version b "
            "ON a.valid && b.valid AND a.recorded && b.recorded WHERE a.slot_id = %s "
            "AND b.slot_id = %s",
            m1,
            m2,
        )
        == 1
    )
    close = await w.commit_v1(
        m1,
        {"answer_contract": h.ENVELOPE, "state": "EXPLICIT_NEGATIVE"},
        start=bound("2026-06-01T05:00:00Z"),
    )
    assert close.status_code == 201, close.text
    assert w.versions(m2) == m2_before
    assert (
        w.scalar(
            "SELECT count(*) FROM canonical_fact_change c JOIN canonical_fact_version v "
            "ON v.id IN (c.from_version_id, c.to_version_id) WHERE v.slot_id = %s",
            m2,
        )
        == 1
    )


async def test_s0004_ac4_relationship_slot_obeys_the_same_exclusion_and_close(world):
    w = world
    slot = await w.slot(RELATED_TO, object_entity_id=str(w.entity(w.a)))

    def decimal(text: str):  # type: ignore[no-untyped-def]
        return {
            "answer_contract": h.ENVELOPE,
            "state": "PRESENT",
            "value": {"type": "decimal", "value": text},
        }

    responses = await asyncio.gather(
        *(
            w.commit_v1(slot, decimal(str(i)), start=bound(STARTS[i % len(STARTS)]))
            for i in range(8)
        )
    )
    assert all(r.status_code == 201 for r in responses), [r.text for r in responses]
    checked, overlapping = grid_violations(w, slot)
    assert checked >= 200 and overlapping == 0
    assert any(not r["recorded"].endswith(",)") for r in w.versions(slot))  # closes happened
    current = next(r for r in w.versions(slot) if r["recorded"].endswith(",)"))
    with psycopg.connect(w.url) as connection, pytest.raises(psycopg.errors.ExclusionViolation):
        connection.execute(
            "INSERT INTO canonical_fact_version (id, slot_id, tenant_id, knowledge_base_id, value, "
            "valid, recorded, evidence, commit_id, source_received_at, artifact_created_at, "
            "assertion_created_at, canonical_accepted_at, temporal_contract, temporal_kind, "
            "valid_from_granularity, valid_from_zone, valid_from_basis, valid_to_state, "
            "valid_to_granularity, valid_to_zone) "
            "SELECT gen_random_uuid(), slot_id, tenant_id, knowledge_base_id, value, valid, "
            "recorded, evidence, commit_id, source_received_at, artifact_created_at, "
            "assertion_created_at, canonical_accepted_at, temporal_contract, temporal_kind, "
            "valid_from_granularity, valid_from_zone, valid_from_basis, valid_to_state, "
            "valid_to_granularity, valid_to_zone FROM canonical_fact_version WHERE id = %s",
            (current["id"],),
        )


async def test_d6_exclusion_violation_maps_to_temporal_conflict(world, monkeypatch):
    """If the row lock were bypassed, `23P01` is a retryable 409 temporal_conflict
    with no row written (ADR-0078 D6)."""
    from brain_persistence.repositories import SqlAlchemyFactCommitRepository

    w = world
    slot = await w.slot()
    assert (
        await w.commit_v1(slot, money("1"), start=bound("2026-01-01T06:00:00Z"))
    ).status_code == 201

    async def no_current(self, slot_id):  # type: ignore[no-untyped-def]
        return ()  # pretend nothing is current, so the insert overlaps the existing row

    monkeypatch.setattr(SqlAlchemyFactCommitRepository, "current_versions", no_current)
    before = w.counts()
    response = await w.commit_v1(slot, money("2"), start=bound("2026-06-01T05:00:00Z"))
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "temporal_conflict"
    assert w.counts() == before


async def test_other_integrity_errors_do_not_echo_database_text(world, monkeypatch):
    """G3 security review: a constraint message can quote the failing row, so a
    non-exclusion IntegrityError is a 409 with no detail and no row written."""
    from brain_persistence.repositories import SqlAlchemyFactCommitRepository
    from sqlalchemy.exc import IntegrityError

    w = world
    slot = await w.slot()

    async def failing_insert(self, **kwargs):  # type: ignore[no-untyped-def]
        raise IntegrityError("INSERT ...", {}, Exception('Failing row contains ("5000000")'))

    monkeypatch.setattr(SqlAlchemyFactCommitRepository, "insert_version", failing_insert)
    before = w.counts()
    response = await w.commit_v1(slot, money("5000000"), start=bound("2026-01-01T06:00:00Z"))
    assert response.status_code == 409
    assert response.json()["code"] == "concurrent_commit"
    assert "5000000" not in response.text and "Failing row" not in response.text
    assert w.counts() == before
