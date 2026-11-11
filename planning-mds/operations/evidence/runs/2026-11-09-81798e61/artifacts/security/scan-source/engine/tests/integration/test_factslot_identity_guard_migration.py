"""F0007 review remediation: identity shapes are enforced by PostgreSQL itself.

Each test owns a disposable database. Migration 0013 never repairs or deletes a
malformed 0012 row; an operator must resolve it explicitly before retrying.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import psycopg
import pytest
from alembic import command
from brain_testing import fixtures
from brain_testing.factslots import seed_subject
from engine.tests.fixtures.factslots import harness
from engine.tests.integration import test_factslot_migration as pilot
from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

_clean_fact_tables = harness._clean_fact_tables
database = harness.database


def _upgrade(revision: str) -> None:
    command.upgrade(harness.configuration(), revision)


def _downgrade(revision: str) -> None:
    command.downgrade(harness.configuration(), revision)


def _owner(url: str) -> tuple[UUID, UUID, UUID, UUID]:
    engine = create_engine(url.replace("postgresql://", "postgresql+psycopg://"))
    try:
        with Session(engine) as session, session.begin():
            tenant, kb = uuid4(), uuid4()
            fixtures.seed_scope(session, tenant, kb)
            principal = fixtures.seed_principal(
                session, issuer="urn:f0007:identity-guard", subject=str(uuid4())
            )
            entity = seed_subject(session, tenant, [kb])
            return tenant, kb, entity, principal.id
    finally:
        engine.dispose()


def _slot(owner: tuple[UUID, UUID, UUID, UUID], **changes: object) -> dict[str, object]:
    tenant, kb, entity, principal = owner
    row: dict[str, object] = {
        "id": uuid4(),
        "entity_id": entity,
        "slot_type": "test:hasAggregateLimit@v1",
        "tenant_id": tenant,
        "knowledge_base_id": kb,
        "identity_version": 1,
        "slot_role": "SLOT",
        "predicate_key": "test:hasAggregateLimit@v1",
        "predicate_release_ref": "f0007-fixtures/1",
        "cardinality": "SINGLE",
        "object_entity_id": None,
        "parent_slot_id": None,
        "member_key": None,
        "fingerprint_version": 1,
        "identity_fingerprint": uuid4().hex * 2,
        "created_by": principal,
    }
    row.update(changes)
    return row


def _insert(url: str, row: dict[str, object]) -> None:
    with psycopg.connect(url) as connection:
        connection.execute(
            sql.SQL("INSERT INTO fact_slot ({}) VALUES ({})").format(
                sql.SQL(", ").join(map(sql.Identifier, row)),
                sql.SQL(", ").join(sql.Placeholder() for _ in row),
            ),
            list(row.values()),
        )


def _rows(url: str) -> dict[str, list[str]]:
    with psycopg.connect(url) as connection:
        return {
            table: [
                row[0]
                for row in connection.execute(
                    sql.SQL("SELECT to_jsonb(t)::text FROM {} t ORDER BY to_jsonb(t)::text").format(
                        sql.Identifier(table)
                    )
                )
            ]
            for table in (
                "fact_slot",
                "fact_slot_qualifier",
                "canonical_fact_version",
                "canonical_commit",
                "canonical_fact_change",
                "outbox_event",
            )
        }


def _revision_and_guard(url: str) -> tuple[str, str]:
    with psycopg.connect(url) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        guard = connection.execute(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conname = 'ck_fact_slot_identity' AND conrelid = 'fact_slot'::regclass"
        ).fetchone()[0]
        return revision, guard


def test_0013_up_down_up_preserves_pilot_and_all_valid_identity_shapes(database):
    _upgrade("0011")
    pilot._seed_pilot(database)
    _upgrade("0012")
    owner = _owner(database)
    _insert(database, _slot(owner))
    header = _slot(owner, cardinality="MULTI")
    _insert(database, header)
    _insert(
        database,
        _slot(
            owner,
            cardinality="MULTI",
            slot_role="MEMBER",
            parent_slot_id=header["id"],
            member_key="a",
        ),
    )
    _insert(database, _slot(owner, cardinality="RELATIONSHIP", object_entity_id=owner[2]))
    with psycopg.connect(database) as connection:
        connection.execute(
            "INSERT INTO fact_slot_qualifier VALUES "
            "(%s, %s, %s, 'basis', 'code', '\"USD\"', now())",
            (header["id"], owner[0], owner[1]),
        )
    before = _rows(database)
    original_guard = _revision_and_guard(database)[1]

    _upgrade("0013")
    assert _rows(database) == before
    revision, strict_guard = _revision_and_guard(database)
    assert revision == "0013" and "IS TRUE" in strict_guard
    _downgrade("0012")
    assert _rows(database) == before
    assert _revision_and_guard(database) == ("0012", original_guard)
    _upgrade("0013")
    assert _rows(database) == before
    assert _revision_and_guard(database) == ("0013", strict_guard)


@pytest.mark.parametrize(
    "field",
    [
        "identity_version",
        "slot_role",
        "predicate_key",
        "predicate_release_ref",
        "cardinality",
        "fingerprint_version",
        "identity_fingerprint",
        "created_by",
    ],
)
def test_0013_rejects_each_missing_mandatory_v1_field(database, field):
    _upgrade("0013")
    owner = _owner(database)
    before = _rows(database)
    with pytest.raises(psycopg.errors.CheckViolation, match="ck_fact_slot_identity"):
        _insert(database, _slot(owner, **{field: None}))
    assert _rows(database) == before


def test_0013_rejects_null_member_key_and_relationship_without_object(database):
    _upgrade("0013")
    owner = _owner(database)
    header = _slot(owner, cardinality="MULTI")
    _insert(database, header)
    before = _rows(database)
    with pytest.raises(psycopg.errors.CheckViolation, match="ck_fact_slot_identity"):
        _insert(
            database,
            _slot(owner, cardinality="MULTI", slot_role="MEMBER", parent_slot_id=header["id"]),
        )
    with pytest.raises(psycopg.errors.CheckViolation, match="ck_fact_slot_identity"):
        _insert(database, _slot(owner, cardinality="RELATIONSHIP"))
    assert _rows(database) == before


@pytest.mark.parametrize("populated_field", ["slot_role", "identity_fingerprint", "created_by"])
def test_0013_rejects_partially_populated_legacy_rows(database, populated_field):
    _upgrade("0013")
    owner = _owner(database)
    row = _slot(owner)
    populated_value = row[populated_field]
    for field in (
        "identity_version",
        "slot_role",
        "predicate_key",
        "predicate_release_ref",
        "cardinality",
        "object_entity_id",
        "parent_slot_id",
        "member_key",
        "fingerprint_version",
        "identity_fingerprint",
        "created_by",
    ):
        row[field] = None
    row[populated_field] = populated_value
    before = _rows(database)
    with pytest.raises(psycopg.errors.CheckViolation, match="ck_fact_slot_identity"):
        _insert(database, row)
    assert _rows(database) == before


def test_0013_preserves_fingerprint_uniqueness(database):
    _upgrade("0013")
    owner = _owner(database)
    first = _slot(owner)
    _insert(database, first)
    before = _rows(database)
    with pytest.raises(psycopg.errors.UniqueViolation, match="uq_fact_slot_identity"):
        _insert(database, _slot(owner, identity_fingerprint=first["identity_fingerprint"]))
    assert _rows(database) == before


@pytest.mark.parametrize("missing_field", ["identity_fingerprint", "identity_version"])
def test_0013_refuses_existing_malformed_0012_rows_without_changing_data(database, missing_field):
    _upgrade("0011")
    pilot._seed_pilot(database)
    _upgrade("0012")
    owner = _owner(database)
    malformed = _slot(owner, **{missing_field: None})
    _insert(database, malformed)  # The shipped 0012 CHECK admitted UNKNOWN.
    before = _rows(database)
    old_revision_guard = _revision_and_guard(database)

    with pytest.raises(RuntimeError, match="0013 upgrade refused.*1 malformed") as rejected:
        _upgrade("0013")
    assert str(malformed["id"]) in str(rejected.value)
    assert str(owner[2]) not in str(rejected.value)  # no subject/value details in diagnostics
    assert _rows(database) == before
    assert _revision_and_guard(database) == old_revision_guard
