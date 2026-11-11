"""F0007-S0006: migration 0012 is additive and leaves pilot data byte-identical.

Seeds deterministic pilot rows at revision 0011, snapshots them, then proves
upgrade, downgrade and upgrade again keep them identical, that the committed
`pilot-before.json` matches, that legacy slots stay legacy, and that downgrade
refuses while identity-v1 rows exist. Set `F0007_WRITE_PILOT_SNAPSHOT=1` once to
regenerate the committed snapshot.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from uuid import UUID

import psycopg
import pytest
from alembic import command
from brain_domain.authx import ResourceKey, ResourceType
from brain_domain.fact_answers import InformationState
from brain_testing import fixtures
from brain_testing.factslots import LIMIT_AMOUNT
from engine.tests.fixtures.factslots import harness
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

_clean_fact_tables = harness._clean_fact_tables
database = harness.database

TENANT = UUID("00000000-0000-4000-8000-00000000f701")
WORKSPACE = fixtures.workspace_for(TENANT)  # the default protect() and seed_grant() derive
KB = UUID("00000000-0000-4000-8000-00000000f703")
ENTITY = UUID("00000000-0000-4000-8000-00000000f704")
SLOTS = (UUID("00000000-0000-4000-8000-00000000f711"), UUID("00000000-0000-4000-8000-00000000f712"))
SNAPSHOT = harness.FIXTURES / "pilot-before.json"
PILOT_SLOT_COLUMNS = (
    "id",
    "entity_id",
    "slot_type",
    "tenant_id",
    "knowledge_base_id",
    "created_at",
)
PILOT_TABLES = (
    "canonical_commit",
    "canonical_fact_version",
    "canonical_fact_change",
    "outbox_event",
)


def _snapshot(url: str) -> dict:
    with psycopg.connect(url) as connection:

        def rows(sql: str) -> list:  # type: ignore[type-arg]
            return [r[0] for r in connection.execute(sql).fetchall()]

        slot_cols = ", ".join(PILOT_SLOT_COLUMNS)
        data = {
            "fact_slot": rows(
                f"SELECT to_jsonb(s)::text FROM (SELECT {slot_cols} FROM fact_slot ORDER BY id) s"
            ),
            **{t: rows(f"SELECT to_jsonb(t)::text FROM {t} t ORDER BY id") for t in PILOT_TABLES},
        }
        schema = rows(
            "SELECT table_name || '.' || column_name || ':' || data_type || ':' || is_nullable "
            "FROM information_schema.columns WHERE table_schema = 'public' AND (table_name IN "
            "('canonical_commit','canonical_fact_version','canonical_fact_change','outbox_event') "
            "OR (table_name = 'fact_slot' AND column_name IN "
            "('id','entity_id','slot_type','tenant_id','knowledge_base_id','created_at'))) "
            "ORDER BY table_name, column_name"
        )
        constraints = rows(
            "SELECT conrelid::regclass || ':' || conname || ':' || pg_get_constraintdef(oid) "
            "FROM pg_constraint WHERE conrelid = 'canonical_fact_version'::regclass "
            "ORDER BY conname"
        )
    return {
        "provenance": "F0007-S0006 deterministic pilot seed (engine/tests/fixtures/factslots/"
        "pilot-seed.sql), captured at revision 0011",
        "rows": data,
        "schema_sha256": hashlib.sha256("\n".join(schema + constraints).encode()).hexdigest(),
    }


def _encode(snapshot: dict) -> bytes:
    return (json.dumps(snapshot, indent=2, sort_keys=True) + "\n").encode()


def _seed_pilot(url: str) -> None:
    engine = create_engine(url.replace("postgresql://", "postgresql+psycopg://"))
    with Session(engine) as session, session.begin():
        fixtures.seed_scope(session, TENANT, KB, WORKSPACE)
    engine.dispose()
    with psycopg.connect(url) as connection:
        connection.execute((harness.FIXTURES / "pilot-seed.sql").read_text())


def _upgrade(target: str) -> None:
    command.upgrade(harness.configuration(), target)


def _downgrade(target: str) -> None:
    command.downgrade(harness.configuration(), target)


async def test_s0006_ac1_ac6_up_down_up_keeps_pilot_rows_identical(database):
    _upgrade("0011")
    _seed_pilot(database)
    before = _snapshot(database)
    if os.environ.get("F0007_WRITE_PILOT_SNAPSHOT") == "1":
        SNAPSHOT.write_bytes(_encode(before))
    assert _encode(before) == SNAPSHOT.read_bytes(), "pilot-before.json drifted from the seed"

    _upgrade("0012")
    assert _snapshot(database) == before
    _downgrade("0011")
    assert _snapshot(database) == before
    with psycopg.connect(database) as connection:
        assert connection.execute("SELECT to_regclass('fact_slot_qualifier') IS NULL").fetchone()[0]
    _upgrade("head")
    assert _snapshot(database) == before


async def test_s0006_ac1_ac2_legacy_slots_read_back_unchanged_and_stay_legacy(database):
    _upgrade("0011")
    _seed_pilot(database)
    before = _snapshot(database)
    _upgrade("head")
    world = harness.FactSlotWorld(database)
    try:
        legacy_identity = world.rows(
            "SELECT id, identity_version, slot_role, predicate_key, cardinality, "
            "identity_fingerprint, subject_kb_entity_id FROM fact_slot ORDER BY id"
        )
        assert legacy_identity == [(s, None, None, None, None, None, None) for s in SLOTS]
        assert world.scalar("SELECT count(*) FROM fact_slot_qualifier") == 0
        # GET /facts/{id} reads the pilot values, ranges and evidence unchanged.
        with Session(world.sync_engine) as session, session.begin():
            for slot in SLOTS:
                fixtures.protect(session, ResourceKey(ResourceType.FACT_SLOT, slot), TENANT, KB)
            reader = fixtures.seed_principal(session, issuer="urn:f0007:test", subject="pilot")
            fixtures.seed_grant(session, reader.id, TENANT, KB, "TenantMember")
        body = (await world.get(SLOTS[0], principal=reader)).json()
        assert body["value"] == {"amount": 2000000.5, "currency": "USD"}
        assert body["evidenceRefs" if "evidenceRefs" in body else "evidence_refs"] == [
            "00000000-0000-4000-8000-00000000f782"
        ]
        async with world.client(reader) as client:
            past = await client.get(
                f"/facts/{SLOTS[0]}",
                params={"validAsOf": "2026-02-01T00:00:00Z", "knownAsOf": "2026-02-15T00:00:00Z"},
            )
        assert past.json()["value"] == {"amount": 1000000, "currency": "USD"}
        # The internal reader labels a legacy slot instead of inventing a state.
        now = datetime.now(UTC)
        async with world.slots() as service:
            legacy = await service.read_answer(
                reader, SLOTS[1], valid_at=now, known_at=now, trace_id="pilot"
            )
        assert legacy.state == InformationState.PRESENT
        assert legacy.legacy_value == {"value": "$2,000,000"}
        # A legacy commit keeps its unwrapped pilot value (no envelope required).
        with Session(world.sync_engine) as session, session.begin():
            fixtures.seed_grant(session, world.service.id, TENANT, KB, "ServicePrincipal")
        legacy_commit = await world.commit(
            SLOTS[1], {"value": "$3,000,000"}, principal=world.service
        )
        assert legacy_commit.status_code == 201, legacy_commit.text
        # Identity resolution never matches a legacy slot implicitly.
        with Session(world.sync_engine) as session, session.begin():
            fixtures.seed_content_artifact(session, TENANT, KB)
            from brain_persistence.tenancy import associate_entity

            associate_entity(
                session, ENTITY, TENANT, KB, actor_id=fixtures.SYNTHETIC_OPERATOR, at=now
            )
        artifact = world.scalar("SELECT id FROM content_artifact WHERE knowledge_base_id = %s", KB)
        key = harness.slot_key(
            KB,
            ENTITY,
            LIMIT_AMOUNT,
            qualifiers={"basis": {"type": "code", "value": "EachOccurrence"}},
        )
        created = await world.resolve(key, sources=[artifact])
        assert created.outcome == "CREATED" and created.slot_id not in SLOTS
        after = _snapshot(database)["rows"]
        assert all(row in after["fact_slot"] for row in before["rows"]["fact_slot"])
    finally:
        await world.close()


async def test_s0006_ac6_downgrade_refuses_while_identity_rows_exist(database):
    _upgrade("head")
    world = harness.FactSlotWorld(database)
    try:
        starting_revision = world.scalar("SELECT version_num FROM alembic_version")
        result = await world.resolve(
            world.key(
                world.a,
                LIMIT_AMOUNT,
                qualifiers={"basis": {"type": "code", "value": "EachOccurrence"}},
            )
        )
        assert result.outcome == "CREATED"
        with pytest.raises(RuntimeError, match="downgrade refused"):
            _downgrade("0011")
        assert world.scalar("SELECT count(*) FROM fact_slot_qualifier") == 1
        assert world.scalar("SELECT version_num FROM alembic_version") == starting_revision
    finally:
        await world.close()
