"""F0008-S0007: migration 0014 is additive, keeps every pre-existing version
byte-for-byte, marks it legacy without inventing fields, and refuses a
downgrade that would lose fact-temporal/v1 data. Every test owns its database.

Seed: the F0007 deterministic pilot rows (applied at 0011) plus F0007-era
identity-v1 versions written at 0013, before F0008 existed."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import psycopg
import pytest
from alembic import command
from brain_domain.temporal import EndState
from brain_persistence.repositories import SqlAlchemyFactCommitRepository
from brain_testing import fixtures
from engine.tests.fixtures.factslots import harness as f0007
from engine.tests.fixtures.temporal import harness as h
from engine.tests.fixtures.temporal.harness import bound, money
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session

_clean_fact_tables = h._clean_fact_tables
database = h.database

TENANT = UUID("00000000-0000-4000-8000-00000000f701")
WORKSPACE = fixtures.workspace_for(TENANT)
KB = UUID("00000000-0000-4000-8000-00000000f703")
PILOT_SLOT = UUID("00000000-0000-4000-8000-00000000f711")

# Every column 0013 has; 0014 must leave them byte-for-byte equal.
PRE_0014 = (
    "id, slot_id, tenant_id, knowledge_base_id, value, valid, recorded, change_reason, evidence, "
    "review_decision_id, commit_id, source_received_at, artifact_created_at, "
    "assertion_created_at, canonical_accepted_at"
)
NEW_COLUMNS = (
    "temporal_contract",
    "temporal_kind",
    "valid_from_granularity",
    "valid_from_zone",
    "valid_from_basis",
    "valid_to_state",
    "valid_to_granularity",
    "valid_to_zone",
    "attested_from_value",
    "attested_from_precision",
    "attested_through_value",
    "attested_through_precision",
    "attested_to_value",
    "attested_to_precision",
    "validity_unknown_from",
    "split_of_version_id",
)


def _upgrade(target: str) -> None:
    command.upgrade(f0007.configuration(), target)


def _downgrade(target: str) -> None:
    command.downgrade(f0007.configuration(), target)


def _snapshot(url: str) -> dict:
    with psycopg.connect(url) as connection:

        def rows(sql: str) -> list:  # type: ignore[type-arg]
            return [r[0] for r in connection.execute(sql).fetchall()]

        return {
            "canonical_fact_version": rows(
                f"SELECT to_jsonb(t)::text FROM (SELECT {PRE_0014} FROM canonical_fact_version "
                "ORDER BY id) t"
            ),
            **{
                table: rows(f"SELECT to_jsonb(t)::text FROM {table} t ORDER BY 1")
                for table in (
                    "canonical_fact_change",
                    "canonical_commit",
                    "outbox_event",
                    "audit_event",
                    "fact_slot",
                    "fact_slot_qualifier",
                )
            },
            "grants": rows(
                "SELECT grantee || ':' || table_name || ':' || privilege_type "
                "FROM information_schema.role_table_grants WHERE table_schema = 'public' "
                "ORDER BY 1"
            ),
            "roles": rows("SELECT rolname FROM pg_roles ORDER BY 1"),
        }


def _seed(url: str) -> dict:
    """Pilot rows at 0011, then F0007 identity-v1 slot versions at 0013."""
    _upgrade("0011")
    engine = create_engine(url.replace("postgresql://", "postgresql+psycopg://"))
    with Session(engine) as session, session.begin():
        fixtures.seed_scope(session, TENANT, KB, WORKSPACE)
    engine.dispose()
    with psycopg.connect(url) as connection:
        connection.execute((f0007.FIXTURES / "pilot-seed.sql").read_text())
    _upgrade("0013")
    return {}


async def _f0007_v1_versions(w: h.TemporalWorld) -> UUID:
    """An identity-v1 slot with versions written the F0007 way (pilot range shape,
    fact-answer/v1 envelope), as they exist before 0014."""
    url = w.url
    if True:
        result = await w.resolve(w.key(w.a, h.AGGREGATE_LIMIT, subject=w.entity(w.a)))
        slot = result.slot_id
        with psycopg.connect(url) as connection:
            for i, (valid, recorded) in enumerate(
                (
                    (
                        "[2026-01-01 00:00:00+00,)",
                        "[2026-01-10 00:00:00+00,2026-06-14 00:00:00+00)",
                    ),
                    (
                        "[2026-01-01 00:00:00+00,2026-06-01 00:00:00+00)",
                        "[2026-06-14 00:00:00+00,)",
                    ),
                    ("[2026-06-01 00:00:00+00,)", "[2026-06-14 00:00:00+00,)"),
                )
            ):
                commit = uuid4()
                connection.execute(
                    "INSERT INTO canonical_commit (id, tenant_id, knowledge_base_id, created_at) "
                    "VALUES (%s, %s, %s, now())",
                    (commit, *w.a.scope),
                )
                connection.execute(
                    "INSERT INTO canonical_fact_version (id, slot_id, tenant_id, "
                    "knowledge_base_id, "
                    "value, valid, recorded, evidence, commit_id, source_received_at, "
                    "artifact_created_at, assertion_created_at, canonical_accepted_at) VALUES "
                    "(gen_random_uuid(), %s, %s, %s, %s::jsonb, %s, %s, '{\"refs\": []}', %s, "
                    "'2026-01-08T00:00:00Z', '2026-01-08T00:00:00Z', '2026-01-08T00:00:00Z', "
                    "lower(%s::tstzrange))",
                    (
                        slot,
                        *w.a.scope,
                        json.dumps(money(str(1000000 * (i + 1)))),
                        valid,
                        recorded,
                        commit,
                        recorded,
                    ),
                )
        return slot


async def test_s0007_ac1_ac2_ac4_ac6_up_down_up_keeps_every_version_identical(database):
    _seed(database)
    w = h.TemporalWorld(database)
    try:
        v1_slot = await _f0007_v1_versions(w)
    finally:
        await w.close()
    before = _snapshot(database)
    assert len(before["canonical_fact_version"]) >= 5  # pilot plus F0007 identity-v1 rows

    _upgrade("head")
    assert _snapshot(database) == before
    with psycopg.connect(database) as connection:
        nulls = connection.execute(
            "SELECT count(*) FROM canonical_fact_version WHERE "
            + " OR ".join(f"{c} IS NOT NULL" for c in NEW_COLUMNS)
        ).fetchone()[0]
    assert nulls == 0  # AC2: legacy marker, nothing defaulted or invented

    _downgrade("0013")
    assert _snapshot(database) == before
    with psycopg.connect(database) as connection:
        assert (
            connection.execute(
                "SELECT count(*) FROM information_schema.columns WHERE table_name = "
                "'canonical_fact_version' AND column_name = 'temporal_contract'"
            ).fetchone()[0]
            == 0
        )
    _upgrade("head")
    assert _snapshot(database) == before

    # AC2: a legacy row with a NULL upper bound reads as OPEN; no temporal block.
    engine = create_async_engine(database.replace("postgresql://", "postgresql+asyncpg://"))
    async with AsyncSession(engine) as session:
        repository = SqlAlchemyFactCommitRepository(session)
        pilot = await repository.resolve_at(
            PILOT_SLOT, valid_as_of=datetime(2026, 7, 1, tzinfo=UTC), known_as_of=datetime.now(UTC)
        )
        legacy_v1 = await repository.current_versions(v1_slot)
    await engine.dispose()
    # The pilot seed's open version ([2026-03-01,)) has a NULL upper bound.
    assert pilot is not None and pilot.temporal is None and pilot.valid_end is None
    assert pilot.valid_to_state is EndState.OPEN
    assert legacy_v1 and all(v.temporal is None for v in legacy_v1)
    assert {v.valid_to_state for v in legacy_v1} == {EndState.OPEN, EndState.BOUNDED}


async def test_s0007_ac4_downgrade_refuses_while_v1_rows_exist_and_names_them(database):
    _seed(database)
    w = h.TemporalWorld(database)
    try:
        v1_slot = await _f0007_v1_versions(w)
        _upgrade("head")
        # A new v1 commit supersedes a legacy F0007 version: the remainder stays legacy
        # (D1) but carries lineage, and the new version is temporal-v1.
        slot = await w.slot()
        response = await w.commit_v1(slot, money("7"), start=bound("2026-06-01T05:00:00Z"))
        assert response.status_code == 201, response.text
        blocking = w.scalar("SELECT id FROM canonical_fact_version WHERE slot_id = %s", slot)
        legacy_split = await w.commit_v1(v1_slot, money("8"), start=bound("2026-09-01T05:00:00Z"))
        assert legacy_split.status_code == 201, legacy_split.text
        remainders = w.rows(
            "SELECT temporal_contract, split_of_version_id IS NOT NULL FROM canonical_fact_version "
            "WHERE slot_id = %s AND change_reason = 'split'",
            v1_slot,
        )
        assert remainders and all(c is None and lineage for c, lineage in remainders)
    finally:
        await w.close()
    before = _snapshot(database)
    with pytest.raises(RuntimeError) as refused:
        _downgrade("0013")
    assert "0014 downgrade refused" in str(refused.value)
    assert str(blocking) in str(refused.value)
    assert _snapshot(database) == before


async def test_d7_upgrade_preflight_refuses_a_bad_identity_v1_envelope(database):
    _seed(database)
    w = h.TemporalWorld(database)
    try:
        v1_slot = await _f0007_v1_versions(w)
    finally:
        await w.close()
    with psycopg.connect(database) as connection:
        bad = connection.execute(
            "SELECT id FROM canonical_fact_version WHERE slot_id = %s LIMIT 1", (v1_slot,)
        ).fetchone()[0]
        # 0007's owner trigger allows a value change; corrupt one row as a pre-0014 bug would.
        connection.execute(
            'UPDATE canonical_fact_version SET value = \'{"answer_contract": "fact-answer/v1", '
            '"state": "PRESENT"}\'::jsonb WHERE id = %s',
            (bad,),
        )
    before = _snapshot(database)
    with pytest.raises(Exception) as refused:
        _upgrade("head")
    assert "0014 upgrade refused: 1 identity-v1 versions" in str(refused.value)
    assert str(bad) in str(refused.value)
    assert _snapshot(database) == before
    with psycopg.connect(database) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0013"


def test_s0007_ac6_no_route_is_added():
    from brain_api.app import create_app

    paths = sorted(p for p in create_app().openapi()["paths"] if p.startswith("/facts"))
    assert paths == ["/facts/{fact_slot_id}", "/facts/{fact_slot_id}/commits"]


async def test_0015_preflight_refuses_cross_slot_lineage_and_cycles_cleanly(database):
    """Review remediation (FR-ARCH-L2): 0015 refuses to install over an existing
    cross-slot split, repairs nothing, and its downgrade drops only its own guard."""
    _seed(database)
    _upgrade("0014")
    w = h.TemporalWorld(database)
    try:
        a, b = await w.slot(), await w.slot()
        for slot in (a, b):
            response = await w.commit_v1(
                slot,
                money("1"),
                start=bound("2026-01-01T06:00:00Z"),
                end_state="BOUNDED",
                end=bound("2027-01-01T06:00:00Z"),
            )
            assert response.status_code == 201, response.text
        pred = w.scalar("SELECT id FROM canonical_fact_version WHERE slot_id = %s", b)
        with psycopg.connect(database) as connection:
            crossing = connection.execute(
                "INSERT INTO canonical_fact_version (id, slot_id, tenant_id, knowledge_base_id, "
                "value, valid, recorded, evidence, commit_id, source_received_at, "
                "artifact_created_at, assertion_created_at, canonical_accepted_at, "
                "temporal_contract, temporal_kind, valid_from_granularity, valid_from_zone, "
                "valid_from_basis, valid_to_state, split_of_version_id) SELECT "
                "gen_random_uuid(), slot_id, tenant_id, knowledge_base_id, value, "
                "'[2031-01-01 06:00:00+00,)', recorded, evidence, commit_id, "
                "source_received_at, artifact_created_at, assertion_created_at, "
                "canonical_accepted_at, 1, 'STATE', 'DAY', 'America/Chicago', 'HUMAN', 'OPEN', "
                "%s FROM canonical_fact_version WHERE slot_id = %s RETURNING id",
                (pred, a),
            ).fetchone()[0]
    finally:
        await w.close()
    before = _snapshot(database)
    with pytest.raises(Exception) as refused:
        _upgrade("0015")
    assert "0015 upgrade refused: 1 versions" in str(refused.value)
    assert str(crossing) in str(refused.value)
    assert _snapshot(database) == before
    with psycopg.connect(database) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0014"
        # Test-only governed repair: superuser replica mode bypasses the 0014 no-delete trigger.
        connection.execute("SET session_replication_role = replica")
        connection.execute("DELETE FROM canonical_fact_version WHERE id = %s", (crossing,))
    _upgrade("head")
    _downgrade("0014")
    with psycopg.connect(database) as connection:
        triggers = {
            r[0]
            for r in connection.execute(
                "SELECT tgname FROM pg_trigger WHERE tgrelid = 'canonical_fact_version'::regclass"
            )
        }
    assert "trg_canonical_fact_version_v1_split_slot" not in triggers
    assert "trg_canonical_fact_version_v1_insert" in triggers
    _upgrade("head")
