"""F0006 PostgreSQL ownership backstops, independent of application checks."""

from __future__ import annotations

import copy
import secrets
from uuid import uuid4

import psycopg
import pytest
from engine.tests.fixtures.assertions import harness
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

_clean_fact_tables = harness._clean_fact_tables
database = harness.database
world = harness.world
world_factory = harness.world_factory
counts = harness.counts


def row(connection, table, identity, *, key="id"):
    return connection.execute(
        sql.SQL("SELECT * FROM {} WHERE {}=%s").format(sql.Identifier(table), sql.Identifier(key)),
        (identity,),
    ).fetchone()


def insert(connection, table, values):
    connection.execute(
        sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(",").join(sql.Identifier(name) for name in values),
            sql.SQL(",").join(sql.Placeholder() for _ in values),
        ),
        [Jsonb(value) if isinstance(value, (dict, list)) else value for value in values.values()],
    )


CONSTRAINTS = {
    "run": "fk_assertion_run_id_owner",
    "correction": "fk_assertion_original_assertion_id_owner",
    "evidence": "fk_assertion_evidence_artifact_id_owner",
    "reference": "fk_assertion_reference_document",
    "name": "fk_assertion_name_reference",
    "subject": "fk_assertion_semantics_subject",
    "object": "fk_assertion_semantics_object",
}


def attempt_foreign_link(connection, own, foreign, own_assertion, foreign_assertion, target):
    core = copy.deepcopy(row(connection, "assertion", own_assertion))
    core["id"] = uuid4()
    if target == "run":
        # Use a valid v1 carrier so only the structural owner FK rejects it.
        core.update(
            semantic_contract_version=1,
            origin="MACHINE_EXTRACTION",
            run_id=foreign.context.run_id,
        )
        insert(connection, "assertion", core)
    elif target == "correction":
        core.update(
            semantic_contract_version=1,
            origin="HUMAN_REVIEW",
            run_id=None,
            original_assertion_id=foreign_assertion,
        )
        insert(connection, "assertion", core)
    elif target == "evidence":
        evidence = connection.execute(
            "SELECT * FROM assertion_evidence WHERE assertion_id=%s", (own_assertion,)
        ).fetchone()
        evidence.update(id=uuid4(), artifact_id=foreign.bundle.key.artifact_id)
        insert(connection, "assertion_evidence", evidence)
    elif target == "reference":
        reference = copy.deepcopy(row(connection, "assertion_document_reference", own.subject_id))
        reference.update(id=uuid4(), document_version_id=foreign.context.document_version_id)
        insert(connection, "assertion_document_reference", reference)
    elif target == "name":
        claim = connection.execute(
            "SELECT * FROM assertion_name_claim WHERE entity_ref=%s", (own.subject_id,)
        ).fetchone()
        claim.update(normalized_name="foreign fixture attempt", entity_ref=foreign.subject_id)
        insert(connection, "assertion_name_claim", claim)
    else:
        semantics = copy.deepcopy(
            row(connection, "assertion_semantics", own_assertion, key="assertion_id")
        )
        semantics["assertion_id"] = core["id"]
        semantics["record"]["id"] = str(core["id"])
        if target == "subject":
            semantics["subject_ref"] = foreign.subject_id
            semantics["record"]["subject_ref"] = str(foreign.subject_id)
        elif target == "object":
            semantics["object_ref"] = foreign.subject_id
            semantics["record"]["object"] = {
                "kind": "ENTITY",
                "ref": str(foreign.subject_id),
                "name": foreign.entity["label"],
            }
            core["value"] = {"object_ref": str(foreign.subject_id)}
        else:
            raise AssertionError(target)
        insert(connection, "assertion", core)
        insert(connection, "assertion_semantics", semantics)


@pytest.mark.parametrize("scope", ["tenant", "knowledge-base"])
@pytest.mark.parametrize("target", list(CONSTRAINTS))
async def test_composite_foreign_keys_reject_cross_scope_claim_links(
    world, world_factory, database, scope, target
):
    foreign = world_factory(owner=(world.owner[0], uuid4()) if scope == "knowledge-base" else None)
    own_assertion = (await world.admit([world.candidate()])).accepted[0].record.id
    foreign_assertion = (await foreign.admit([foreign.candidate()])).accepted[0].record.id
    before = counts(database)
    with (
        pytest.raises(psycopg.errors.ForeignKeyViolation) as failure,
        psycopg.connect(database, row_factory=dict_row) as connection,
    ):
        attempt_foreign_link(connection, world, foreign, own_assertion, foreign_assertion, target)
    assert failure.value.diag.constraint_name == CONSTRAINTS[target]
    assert counts(database) == before


@pytest.fixture
def restricted_sql_role(database):
    role = "f0006_qe_sql_" + secrets.token_hex(6)
    with psycopg.connect(database, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
        connection.execute(
            sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role))
        )
        connection.execute(
            sql.SQL(
                "GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO {}"
            ).format(sql.Identifier(role))
        )
    try:
        yield role
    finally:
        with psycopg.connect(database, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            connection.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


async def test_service_sql_role_cannot_bypass_append_only_or_source_ownership(
    world, world_factory, database, restricted_sql_role
):
    foreign = world_factory()
    own_assertion = (await world.admit([world.candidate()])).accepted[0].record.id
    foreign_assertion = (await foreign.admit([foreign.candidate()])).accepted[0].record.id
    before = counts(database)
    for target in ("evidence", "subject", "object"):
        with (
            pytest.raises(psycopg.errors.ForeignKeyViolation) as failure,
            psycopg.connect(database, row_factory=dict_row) as connection,
        ):
            connection.execute(
                sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(restricted_sql_role))
            )
            assert (
                connection.execute("SELECT current_user").fetchone()["current_user"]
                == restricted_sql_role
            )
            attempt_foreign_link(
                connection, world, foreign, own_assertion, foreign_assertion, target
            )
        assert failure.value.diag.constraint_name == CONSTRAINTS[target]
    with pytest.raises(psycopg.errors.CheckViolation), psycopg.connect(database) as connection:
        connection.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(restricted_sql_role)))
        connection.execute(
            "UPDATE assertion_evidence SET char_start=999 WHERE assertion_id=%s",
            (own_assertion,),
        )
    assert counts(database) == before
