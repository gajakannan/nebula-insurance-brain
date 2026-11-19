"""F0008 database-enforced immutability and integrity (ADR-0078 D5/D7, S0003
AC5/AC7, S0004 AC2/AC5/AC6). The negatives run as the database owner role, the
most privileged client role the application stack has, so the triggers hold
"whatever the client role". Every test owns its database."""

from __future__ import annotations

from uuid import uuid4

import psycopg
import pytest
from brain_persistence.repositories import SqlAlchemyFactCommitRepository
from engine.tests.fixtures.temporal import harness as h
from engine.tests.fixtures.temporal.harness import bound, money

_clean_fact_tables = h._clean_fact_tables
database = h.database
world = h.world

IMMUTABLE_COLUMNS = {
    "value": "'{}'::jsonb",
    "valid": "'[2026-02-01 06:00:00+00,)'::tstzrange",
    "slot_id": "gen_random_uuid()",
    "tenant_id": "gen_random_uuid()",
    "knowledge_base_id": "gen_random_uuid()",
    "change_reason": "'corrected'",
    "evidence": "'{\"refs\": []}'::jsonb",
    "review_decision_id": "gen_random_uuid()",
    "commit_id": "gen_random_uuid()",
    "source_received_at": "now()",
    "artifact_created_at": "now()",
    "assertion_created_at": "now()",
    "canonical_accepted_at": "now()",
    "temporal_contract": "NULL",
    "temporal_kind": "'EVENT'",
    "valid_from_granularity": "'MONTH'",
    "valid_from_zone": "'UTC'",
    "valid_from_basis": "'HUMAN'",
    "valid_to_state": "'UNKNOWN'",
    "attested_from_value": "'2026'",
    "attested_from_precision": "'YEAR'",
    "validity_unknown_from": "now()",
    "split_of_version_id": "gen_random_uuid()",
}


async def _seeded(w):  # type: ignore[no-untyped-def]
    slot = await w.slot()
    ev = w.evidence(("2026-01-05", "DAY"))
    response = await w.commit_v1(
        slot, money("2000000"), start=bound("2026-01-01T06:00:00Z"), evidence=[ev]
    )
    assert response.status_code == 201, response.text
    return slot, w.versions(slot)[0]["id"]


@pytest.mark.parametrize("column", sorted(IMMUTABLE_COLUMNS))
async def test_s0003_ac5_update_of_any_column_but_the_open_recorded_bound_is_refused(world, column):
    w = world
    slot, version = await _seeded(w)
    before = w.versions(slot)
    with psycopg.connect(w.url) as connection, pytest.raises(psycopg.errors.IntegrityError):
        connection.execute(
            f"UPDATE canonical_fact_version SET {column} = {IMMUTABLE_COLUMNS[column]} "
            "WHERE id = %s",
            (version,),
        )
    assert w.versions(slot) == before


async def test_s0003_ac5_the_single_close_succeeds_and_cannot_be_reopened_or_moved(world):
    w = world
    slot, version = await _seeded(w)
    with psycopg.connect(w.url, autocommit=True) as connection:
        connection.execute(
            "UPDATE canonical_fact_version SET recorded = tstzrange(lower(recorded), "
            "lower(recorded) + interval '1 day', '[)') WHERE id = %s",
            (version,),
        )
        for change in (
            "tstzrange(lower(recorded), NULL, '[)')",  # reopen
            "tstzrange(lower(recorded), upper(recorded) + interval '1 day', '[)')",  # move
            "tstzrange(lower(recorded) - interval '1 day', upper(recorded), '[)')",
        ):
            with pytest.raises(psycopg.errors.RestrictViolation):
                connection.execute(
                    f"UPDATE canonical_fact_version SET recorded = {change} WHERE id = %s",
                    (version,),
                )
    with psycopg.connect(w.url, autocommit=True) as connection:
        # A close that also moves the lower bound is refused even while open.
        _, open_version = await _seeded(w)
        with pytest.raises(psycopg.errors.RestrictViolation):
            connection.execute(
                "UPDATE canonical_fact_version SET recorded = tstzrange(lower(recorded) + "
                "interval '1 second', lower(recorded) + interval '1 day', '[)') WHERE id = %s",
                (open_version,),
            )


async def test_s0003_ac5_delete_and_truncate_are_refused_and_changes_are_append_only(world):
    w = world
    slot, version = await _seeded(w)
    before = w.counts()
    with psycopg.connect(w.url, autocommit=True) as connection:
        with pytest.raises(psycopg.errors.RestrictViolation):
            connection.execute("DELETE FROM canonical_fact_version WHERE id = %s", (version,))
        with pytest.raises(psycopg.errors.RestrictViolation):
            connection.execute("TRUNCATE canonical_fact_version CASCADE")
        with pytest.raises(psycopg.errors.RestrictViolation):
            connection.execute("TRUNCATE canonical_fact_change")
        with pytest.raises(psycopg.errors.RestrictViolation):
            connection.execute("UPDATE canonical_fact_change SET reason = 'merged'")
        with pytest.raises(psycopg.errors.RestrictViolation):
            connection.execute("DELETE FROM canonical_fact_change")
    assert w.counts() == before


async def test_s0003_ac7_fault_before_the_outbox_leaves_no_row_of_the_commit(world):
    w = world
    slot = await w.slot()
    await w.commit_at(
        slot, w.body(money("2000000"), start=bound("2026-01-01T06:00:00Z")), "2026-01-10T00:00:00Z"
    )

    class Fault(Exception):
        pass

    class FaultingRepository(SqlAlchemyFactCommitRepository):
        async def write_outbox(self, commit_id, payload):  # type: ignore[no-untyped-def]
            await self._session.flush()  # the fact and change rows are in the transaction
            raise Fault()

    tables = ("canonical_fact_version", "canonical_fact_change", "canonical_commit", "outbox_event")
    before = {t: w.scalar(f"SELECT count(*) FROM {t}") for t in tables}
    with pytest.raises(Fault):
        await w.commit_at(
            slot,
            w.body(money("5000000"), start=bound("2026-06-01T05:00:00Z")),
            "2026-06-14T00:00:00Z",
            repo=FaultingRepository,
        )
    assert {t: w.scalar(f"SELECT count(*) FROM {t}") for t in tables} == before
    assert all(r["recorded"].endswith(",)") for r in w.versions(slot))


# --- S0004 direct-insert negatives ---------------------------------------------

COPY = (
    "INSERT INTO canonical_fact_version (id, slot_id, tenant_id, knowledge_base_id, value, valid, "
    "recorded, evidence, commit_id, source_received_at, artifact_created_at, assertion_created_at, "
    "canonical_accepted_at, temporal_contract, temporal_kind, valid_from_granularity, "
    "valid_from_zone, valid_from_basis, valid_to_state) "
    "SELECT gen_random_uuid(), {slot}, {tenant}, {kb}, {value}, {valid}, recorded, evidence, "
    "commit_id, source_received_at, artifact_created_at, assertion_created_at, "
    "canonical_accepted_at, temporal_contract, temporal_kind, valid_from_granularity, "
    "valid_from_zone, valid_from_basis, valid_to_state FROM canonical_fact_version WHERE id = %s"
)


def _copy(**overrides: str) -> str:
    defaults = {
        "slot": "slot_id",
        "tenant": "tenant_id",
        "kb": "knowledge_base_id",
        "value": "value",
        "valid": "valid",
    }
    return COPY.format(**{**defaults, **overrides})


async def test_s0004_ac2_direct_overlapping_insert_is_refused_by_the_exclusion(world):
    w = world
    slot, version = await _seeded(w)
    with psycopg.connect(w.url) as connection, pytest.raises(psycopg.errors.ExclusionViolation):
        connection.execute(
            _copy(valid="'[2026-03-01 06:00:00+00,)'::tstzrange", value="value"), (version,)
        )
    assert len(w.versions(slot)) == 1


@pytest.mark.parametrize(
    "value",
    [
        # A value with a non-PRESENT state.
        '\'{"answer_contract": "fact-answer/v1", "state": "NOT_FOUND", '
        '"value": {"type": "money", "amount": "1", "currency": "USD"}}\'::jsonb',
        # PRESENT without a value.
        '\'{"answer_contract": "fact-answer/v1", "state": "PRESENT"}\'::jsonb',
        # Not the envelope at all.
        "'{\"amount\": 1}'::jsonb",
    ],
)
async def test_s0004_ac5_envelope_backstop_refuses_state_value_mismatch(world, value):
    w = world
    slot, version = await _seeded(w)
    other = await w.slot()
    with psycopg.connect(w.url) as connection, pytest.raises(psycopg.errors.CheckViolation):
        connection.execute(_copy(slot=f"'{other}'::uuid", value=value), (version,))
    assert w.versions(other) == []


async def test_s0004_ac5_legacy_pilot_versions_are_not_subject_to_the_envelope(world):
    """A legacy pilot slot keeps accepting pilot values (S0007 AC3)."""
    w = world
    with psycopg.connect(w.url, autocommit=True) as connection:
        from brain_testing import fixtures
        from sqlalchemy.orm import Session

        with Session(w.sync_engine) as session, session.begin():
            legacy = fixtures.seed_fact_slot(session, w.a.tenant_id, w.a.knowledge_base_id)
        commit = uuid4()
        connection.execute(
            "INSERT INTO canonical_commit (id, tenant_id, knowledge_base_id, created_at) "
            "VALUES (%s, %s, %s, now())",
            (commit, w.a.tenant_id, w.a.knowledge_base_id),
        )
        connection.execute(
            "INSERT INTO canonical_fact_version (id, slot_id, tenant_id, knowledge_base_id, value, "
            "valid, recorded, evidence, commit_id, source_received_at, artifact_created_at, "
            "assertion_created_at, canonical_accepted_at) VALUES (gen_random_uuid(), %s, %s, %s, "
            "'{\"amount\": 1}'::jsonb, '[2026-01-01,)', '[2026-01-01,)', '{\"refs\": []}', %s, "
            "now(), now(), now(), now())",
            (legacy, w.a.tenant_id, w.a.knowledge_base_id, commit),
        )
        # A legacy slot refuses temporal-v1 rows (ADR-0078 D1).
        with pytest.raises(psycopg.errors.CheckViolation):
            connection.execute(
                "INSERT INTO canonical_fact_version (id, slot_id, tenant_id, knowledge_base_id, "
                "value, valid, recorded, evidence, commit_id, source_received_at, "
                "artifact_created_at, assertion_created_at, canonical_accepted_at, "
                "temporal_contract, temporal_kind, valid_from_granularity, valid_from_zone, "
                "valid_from_basis, valid_to_state) VALUES (gen_random_uuid(), %s, %s, %s, "
                '\'{"answer_contract": "fact-answer/v1", "state": "NOT_PROCESSED"}\', '
                "'[2027-01-01 06:00:00+00,)', '[2026-01-01,)', '{\"refs\": []}', %s, now(), now(), "
                "now(), now(), 1, 'STATE', 'DAY', 'America/Chicago', 'HUMAN', 'OPEN')",
                (legacy, w.a.tenant_id, w.a.knowledge_base_id, commit),
            )


async def test_d1_identity_v1_slot_refuses_a_legacy_row_that_is_not_a_legacy_remainder(world):
    w = world
    slot, version = await _seeded(w)
    other = await w.slot()
    with psycopg.connect(w.url) as connection, pytest.raises(psycopg.errors.CheckViolation):
        connection.execute(
            "INSERT INTO canonical_fact_version (id, slot_id, tenant_id, knowledge_base_id, value, "
            "valid, recorded, evidence, commit_id, source_received_at, artifact_created_at, "
            "assertion_created_at, canonical_accepted_at) SELECT gen_random_uuid(), %s, "
            "tenant_id, knowledge_base_id, value, valid, recorded, evidence, commit_id, "
            "source_received_at, artifact_created_at, assertion_created_at, canonical_accepted_at "
            "FROM canonical_fact_version WHERE id = %s",
            (other, version),
        )


@pytest.mark.parametrize("target", ["version", "change", "commit"])
async def test_s0004_ac6_cross_scope_rows_are_refused_by_composite_keys(world, target):
    w = world
    slot, version = await _seeded(w)
    other_tenant, other_kb = w.b.tenant_id, w.b.knowledge_base_id
    before = w.counts()
    with psycopg.connect(w.url) as connection, pytest.raises(psycopg.errors.IntegrityError):
        if target == "version":
            connection.execute(
                _copy(
                    kb=f"'{other_kb}'::uuid",
                    tenant=f"'{other_tenant}'::uuid",
                    valid="'[2030-01-01 06:00:00+00,)'::tstzrange",
                ),
                (version,),
            )
        elif target == "change":
            connection.execute(
                "INSERT INTO canonical_fact_change (id, reason, from_version_id, to_version_id, "
                "tenant_id, knowledge_base_id) "
                "VALUES (gen_random_uuid(), 'split', NULL, %s, %s, %s)",
                (version, other_tenant, other_kb),
            )
        else:
            commit = w.scalar("SELECT commit_id FROM canonical_fact_version WHERE id = %s", version)
            connection.execute(
                "INSERT INTO outbox_event (id, commit_id, payload) VALUES (gen_random_uuid(), %s, "
                "'{}'::jsonb)",
                (commit,),
            )
            connection.execute(
                "INSERT INTO canonical_fact_version (id, slot_id, tenant_id, knowledge_base_id, "
                "value, valid, recorded, evidence, commit_id, source_received_at, "
                "artifact_created_at, assertion_created_at, canonical_accepted_at, "
                "temporal_contract, temporal_kind, valid_from_granularity, valid_from_zone, "
                "valid_from_basis, valid_to_state, split_of_version_id) SELECT gen_random_uuid(), "
                "slot_id, tenant_id, knowledge_base_id, value, '[2031-01-01 06:00:00+00,)', "
                "recorded, evidence, commit_id, source_received_at, artifact_created_at, "
                "assertion_created_at, canonical_accepted_at, 1, 'STATE', 'DAY', "
                "'America/Chicago', "
                "'HUMAN', 'OPEN', %s FROM canonical_fact_version WHERE id = %s",
                (uuid4(), version),
            )
    assert w.counts() == before
