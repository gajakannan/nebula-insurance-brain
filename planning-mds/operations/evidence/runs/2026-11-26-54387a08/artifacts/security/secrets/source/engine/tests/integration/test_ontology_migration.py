"""F0012-S0007 AC4: migration 0017 on a database holding F0007-F0009 data.

Every pre-existing table keeps the same row count and content checksum across
upgrade, empty downgrade and re-upgrade; the only schema change to an existing
table is the widened `ck_resource_access_type`. A populated downgrade is refused
(`test_downgrade_refused_after_install`)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import psycopg
from alembic import command
from brain_testing.factslots import EFFECTIVE_DATE
from engine.tests.fixtures.factslots.harness import FactSlotWorld, configuration, database

__all__ = ["database"]

ONTOLOGY = {
    "ontology_module_version",
    "ontology_release",
    "ontology_release_module",
    "ontology_term",
    "ontology_change_record",
    "ontology_impact_report",
    "ontology_release_review",
    "ontology_release_selection",
}


def checksums(url: str) -> dict[str, tuple[int, str]]:
    with psycopg.connect(url) as connection:
        tables = [
            r[0]
            for r in connection.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version' "
                "ORDER BY tablename"
            )
        ]
        out = {}
        for table in tables:
            if table in ONTOLOGY:
                continue
            count, digest = connection.execute(
                f"SELECT count(*), md5(coalesce(string_agg(row_to_json(t)::text, '|' "
                f"ORDER BY row_to_json(t)::text), '')) FROM {table} t"
            ).fetchone()
            out[table] = (count, digest)
        return out


def access_check(url: str) -> str:
    with psycopg.connect(url) as connection:
        return connection.execute(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'ck_resource_access_type'"
        ).fetchone()[0]


async def test_0017_preserves_f0007_to_f0009_data(database: Any) -> None:
    command.upgrade(configuration(), "0016")
    world = FactSlotWorld(database)
    try:
        slot = await world.resolve(world.key(world.a, EFFECTIVE_DATE))
        committed = await world.commit(
            slot.slot_id, {
                "answer_contract": "fact-answer/v1",
                "state": "PRESENT",
                "value": {"type": "date", "value": "2026-01-01"},
            },
        )
        assert committed.status_code == 201, committed.text
    finally:
        await world.close()
    before = checksums(database)
    populated = {t: v[0] for t, v in before.items() if v[0]}
    assert populated["fact_slot"] >= 1 and populated["canonical_fact_version"] >= 1
    assert populated["audit_event"] >= 1 and populated["resource_access"] >= 1

    command.upgrade(configuration(), "0017")
    after = checksums(database)
    assert after == before
    assert "ontology_release" in access_check(database)

    command.downgrade(configuration(), "0016")
    assert checksums(database) == before
    assert "ontology_release" not in access_check(database)
    command.upgrade(configuration(), "head")
    assert checksums(database) == before

    evidence = os.environ.get("F0012_EVIDENCE_DIR")
    if evidence:
        Path(evidence, "migration-0017-checksums.json").write_text(
            json.dumps({"before": before, "after_upgrade": after}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
