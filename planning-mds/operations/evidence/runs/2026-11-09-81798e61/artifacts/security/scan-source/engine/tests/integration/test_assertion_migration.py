from uuid import uuid4

import psycopg
import pytest
from alembic import command
from brain_testing import fixtures
from engine.tests.fixtures.assertions import harness
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

_clean_fact_tables = harness._clean_fact_tables
database = harness.database
world = harness.world
world_factory = harness.world_factory
counts = harness.counts
configuration = harness.configuration


def clone_claim(connection, identity, *, evidence_changes):
    core = connection.execute("SELECT * FROM assertion WHERE id=%s", (identity,)).fetchone()
    semantics = connection.execute(
        "SELECT * FROM assertion_semantics WHERE assertion_id=%s", (identity,)
    ).fetchone()
    evidence = connection.execute(
        "SELECT * FROM assertion_evidence WHERE assertion_id=%s", (identity,)
    ).fetchone()
    core["id"], evidence["id"] = uuid4(), uuid4()
    semantics["assertion_id"] = evidence["assertion_id"] = core["id"]
    semantics["record"]["id"] = str(core["id"])
    semantics["verified_evidence"][0]["evidence_id"] = str(evidence["id"])
    evidence.update(evidence_changes)
    for table, values in (
        ("assertion", core),
        ("assertion_semantics", semantics),
        ("assertion_evidence", evidence),
    ):
        connection.execute(
            sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table),
                sql.SQL(",").join(sql.Identifier(name) for name in values),
                sql.SQL(",").join(sql.Placeholder() for _ in values),
            ),
            [Jsonb(v) if isinstance(v, (dict, list)) else v for v in values.values()],
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"page": 999},
        {"page": None},
        {"bbox": {"x0": 9999, "y0": 20, "x1": 10000, "y1": 60}},
        {"bbox": None},
    ],
)
async def test_inserted_evidence_page_and_bbox_must_match_server_snapshot(world, database, changes):
    original = (await world.admit([world.candidate()])).accepted[0]
    assert original.server_evidence[0].selector["page"] == 1
    assert original.server_evidence[0].selector["bbox"]
    before = counts(database)
    with (
        pytest.raises(psycopg.errors.CheckViolation, match="verified evidence mismatch"),
        psycopg.connect(database, row_factory=dict_row) as connection,
    ):
        clone_claim(connection, original.record.id, evidence_changes=changes)
    assert counts(database) == before


@pytest.mark.parametrize(
    "origin,json_null_bbox", [("STATED", False), ("TRANSCRIBED", False), ("TRANSCRIBED", True)]
)
async def test_matching_evidence_carriers_accept_honest_and_absent_regions(
    world_factory, database, origin, json_null_bbox
):
    world = world_factory(kind="csv" if origin == "TRANSCRIBED" else "pdf", origin=origin)
    original = (await world.admit([world.candidate()])).accepted[0]
    changes = {"bbox": Jsonb(None)} if json_null_bbox else {}
    if origin == "TRANSCRIBED":
        assert original.server_evidence[0].selector.get("page") is None
        assert original.server_evidence[0].selector.get("bbox") is None
    with psycopg.connect(database, row_factory=dict_row) as connection:
        clone_claim(connection, original.record.id, evidence_changes=changes)
    assert counts(database)["assertion"] == 2


def insert_legacy(connection, identity, owner, *, slot="limit", parent=None, version=1):
    connection.execute(
        "INSERT INTO assertion(id,run_id,origin,original_assertion_id,version,"
        "subject_type,slot_type,"
        "value,model_confidence,interpretation_basis,created_at,tenant_id,knowledge_base_id) "
        "VALUES(%s,NULL,'MACHINE_EXTRACTION',%s,%s,'Policy',%s,"
        "'{\"amount\":500000}',0.6,'INFERRED',now(),%s,%s)",
        (identity, parent, version, slot, *owner),
    )


def test_additive_upgrade_preserves_legacy_identity_and_empty_rollback(database):
    command.upgrade(configuration(), "0010")
    owner, identity = (uuid4(), uuid4()), uuid4()
    engine = create_engine(database.replace("postgresql://", "postgresql+psycopg://"))
    try:
        with Session(engine) as session, session.begin():
            fixtures.seed_scope(session, *owner)
        with psycopg.connect(database) as connection:
            insert_legacy(connection, identity, owner)
            before = connection.execute(
                "SELECT to_jsonb(a) FROM assertion a WHERE id=%s", (identity,)
            ).fetchone()[0]
        command.upgrade(configuration(), "0011")
        with psycopg.connect(database) as connection:
            after = connection.execute(
                "SELECT to_jsonb(a) FROM assertion a WHERE id=%s", (identity,)
            ).fetchone()[0]
        assert after.pop("semantic_contract_version") == 1 and after == before
        command.downgrade(configuration(), "0010")
        command.upgrade(configuration(), "0011")
        with psycopg.connect(database) as connection:
            assert connection.execute(
                "SELECT value,interpretation_basis FROM assertion WHERE id=%s", (identity,)
            ).fetchone() == ({"amount": 500000}, "INFERRED")
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "mutation",
    [
        "UPDATE assertion SET value='{}' WHERE id=%s",
        "DELETE FROM assertion WHERE id=%s",
        "UPDATE assertion SET version=version+2 WHERE id=%s",
        "DELETE FROM assertion_evidence WHERE assertion_id=%s",
        "UPDATE assertion_evidence SET char_start=999 WHERE assertion_id=%s",
        "UPDATE assertion_semantics SET predicate_id='different' WHERE assertion_id=%s",
    ],
)
async def test_original_assertions_extensions_and_evidence_are_immutable(world, database, mutation):
    admitted = (await world.admit([world.candidate()])).accepted[0]
    before = counts(database)
    with pytest.raises(psycopg.errors.CheckViolation), psycopg.connect(database) as connection:
        connection.execute(mutation, (admitted.record.id,))
    assert counts(database) == before
    with psycopg.connect(database) as connection:
        connection.execute(
            "UPDATE assertion SET version=version+1 WHERE id=%s", (admitted.record.id,)
        )
        assert (
            connection.execute(
                "SELECT version FROM assertion WHERE id=%s", (admitted.record.id,)
            ).fetchone()[0]
            == 2
        )


async def test_core_only_v2_and_legacy_sentinel_fail_at_commit(world, database):
    for discriminator, slot in ((2, "limit"), (1, "__OPEN_STATEMENT_V2__")):
        with pytest.raises(psycopg.errors.CheckViolation), psycopg.connect(database) as connection:
            identity = uuid4()
            insert_legacy(connection, identity, world.owner, slot=slot)
            if discriminator == 2:
                # The direct INSERT names v2; updates remain prohibited.
                connection.rollback()
                connection.execute(
                    "INSERT INTO assertion(id,run_id,origin,version,subject_type,slot_type,value,"
                    "model_confidence,interpretation_basis,created_at,tenant_id,knowledge_base_id,"
                    "semantic_contract_version) "
                    "VALUES(%s,NULL,'DOCUMENT_INTERPRETATION',1,'Policy','limit','{}',"
                    "0.5,'EXPLICIT',now(),%s,%s,2)",
                    (identity, *world.owner),
                )
    assert counts(database)["assertion"] == 0


async def test_v1_child_of_v2_parent_is_refused_by_deferred_guard(world, database):
    parent = (await world.admit([world.candidate()])).accepted[0]
    with (
        pytest.raises(psycopg.errors.CheckViolation, match="correction contract mismatch"),
        psycopg.connect(database) as connection,
    ):
        insert_legacy(connection, uuid4(), world.owner, parent=parent.record.id)
    assert counts(database)["assertion"] == 1


async def test_occupied_downgrade_stops_without_erasing_semantics(world, database):
    await world.admit([world.candidate()])
    before = counts(database)
    with psycopg.connect(database) as connection:
        head = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    with pytest.raises(RuntimeError, match="downgrade refused"):
        command.downgrade(configuration(), "0010")
    assert counts(database) == before
    # The refused downgrade leaves the database at the head it started from
    # (0011 when F0006 shipped; later additive heads such as F0007's 0012 too).
    with psycopg.connect(database) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone()[0] == head
