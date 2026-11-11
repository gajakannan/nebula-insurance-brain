"""F0007-S0006 AC4/AC7 and S0002 AC2/AC5: database-enforced ownership and integrity.

Negatives use direct SQL as the application role (`brain`), bypassing the
service, so PostgreSQL itself is shown to reject them. Expectations come from the
story ACs and ADR-0077 D4/D8.
"""

from __future__ import annotations

from uuid import uuid4

import psycopg
import pytest
from brain_testing import fixtures
from brain_testing.factslots import ADDITIONAL_INSURED, AGGREGATE_LIMIT, LIMIT_AMOUNT, RELATED_TO
from engine.tests.fixtures.factslots import harness
from sqlalchemy.orm import Session

_clean_fact_tables = harness._clean_fact_tables
database = harness.database
slot_world = harness.slot_world

ENVELOPE = "fact-answer/v1"
EACH_OCC = {"basis": {"type": "code", "value": "EachOccurrence"}}
MONEY = {"type": "money", "amount": "5", "currency": "USD"}


def _fails(w, sql: str, *params: object, match: str) -> None:  # type: ignore[no-untyped-def]
    with (
        psycopg.connect(w.url) as connection,
        pytest.raises(psycopg.Error, match=match),
        connection.transaction(),
    ):
        connection.execute(sql, params)


def _copy_version(w, version_id, *, slot_id=None):  # type: ignore[no-untyped-def]
    """Insert a copy of an existing version row (optionally onto another slot)."""
    columns = [
        r[0]
        for r in w.rows(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'canonical_fact_version' AND column_name <> 'id' "
            "ORDER BY ordinal_position"
        )
    ]
    selected = ", ".join("%s::uuid" if c == "slot_id" and slot_id else c for c in columns)
    params = [slot_id] if slot_id else []
    sql = (
        f"INSERT INTO canonical_fact_version (id, {', '.join(columns)}) "
        f"SELECT gen_random_uuid(), {selected} FROM canonical_fact_version WHERE id = %s"
    )
    return sql, (*params, version_id)


async def test_s0006_ac4_child_rows_cannot_point_at_another_owner(slot_world):
    w = slot_world
    slot = (await w.resolve(w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC))).slot_id
    other_kb = w.b.knowledge_base_id
    _fails(
        w,
        "INSERT INTO fact_slot_qualifier VALUES (%s, %s, %s, 'currency', 'code', '\"USD\"', now())",
        slot,
        w.a.tenant_id,
        other_kb,
        match="fk_fact_slot_qualifier",
    )
    _fails(
        w,
        "INSERT INTO fact_slot_qualifier VALUES (%s, %s, %s, 'currency', 'code', '\"USD\"', now())",
        slot,
        uuid4(),
        w.a.knowledge_base_id,
        match="fk_fact_slot_qualifier",
    )
    header = (
        await w.resolve(
            w.key(
                w.a,
                ADDITIONAL_INSURED,
                member={"type": "entity_ref", "entity_id": str(w.entity(w.a))},
            )
        )
    ).slot_id
    member_sql = (
        "INSERT INTO fact_slot (id, entity_id, slot_type, tenant_id, knowledge_base_id, "
        "identity_version, slot_role, predicate_key, predicate_release_ref, cardinality, "
        "parent_slot_id, member_key, fingerprint_version, identity_fingerprint, created_by) "
        "VALUES (gen_random_uuid(), %s, 'test:hasAdditionalInsured@v1', %s, %s, 1, 'MEMBER', "
        "'test:hasAdditionalInsured@v1', 'f0007-fixtures/1', 'MULTI', %s, 'k', 1, %s, %s)"
    )
    # A member that names a KB A header while claiming KB B ownership.
    _fails(
        w,
        member_sql,
        w.subject,
        w.a.tenant_id,
        other_kb,
        header,
        "a" * 64,
        w.service.id,
        match="fk_fact_slot_parent_owner",
    )
    # A member whose parent is a SINGLE slot fails the deferred integrity trigger.
    _fails(
        w,
        member_sql,
        w.subject,
        w.a.tenant_id,
        w.a.knowledge_base_id,
        slot,
        "b" * 64,
        w.service.id,
        match="MULTI header",
    )
    # A subject or object outside the slot's KB is rejected by the KB association keys.
    outsider = w.entity(w.b)
    header_sql = (
        "INSERT INTO fact_slot (id, entity_id, slot_type, tenant_id, knowledge_base_id, "
        "identity_version, slot_role, predicate_key, predicate_release_ref, cardinality, "
        "object_entity_id, fingerprint_version, identity_fingerprint, created_by) "
        "VALUES (gen_random_uuid(), %s, %s, %s, %s, 1, 'SLOT', %s, 'f0007-fixtures/1', %s, %s, "
        "1, %s, %s)"
    )
    _fails(
        w,
        header_sql,
        outsider,
        "test:hasAggregateLimit@v1",
        *w.a.scope,
        "test:hasAggregateLimit@v1",
        "SINGLE",
        None,
        "c" * 64,
        w.service.id,
        match="fk_fact_slot_subject_kb",
    )
    _fails(
        w,
        header_sql,
        w.subject,
        "test:relatedTo@v1",
        *w.a.scope,
        "test:relatedTo@v1",
        "RELATIONSHIP",
        outsider,
        "d" * 64,
        w.service.id,
        match="fk_fact_slot_object_kb",
    )
    # A qualifier on a legacy pilot slot is refused at commit (deferred trigger).
    with Session(w.sync_engine) as session, session.begin():
        legacy = fixtures.seed_fact_slot(session, *w.a.scope)
    _fails(
        w,
        "INSERT INTO fact_slot_qualifier VALUES (%s, %s, %s, 'basis', 'code', '\"x\"', now())",
        legacy,
        *w.a.scope,
        match="identity-v1 slot header",
    )
    # Malformed identity rows violate the identity check.
    _fails(
        w,
        header_sql,
        w.subject,
        "other",
        *w.a.scope,
        "test:hasAggregateLimit@v1",
        "SINGLE",
        None,
        "e" * 64,
        w.service.id,
        match="ck_fact_slot_identity",
    )
    _fails(
        w,
        header_sql,
        w.subject,
        "test:relatedTo@v1",
        *w.a.scope,
        "test:relatedTo@v1",
        "RELATIONSHIP",
        None,
        "f" * 64,
        w.service.id,
        match="ck_fact_slot_identity",
    )


async def test_s0006_ac4_identity_and_ownership_columns_are_immutable(slot_world):
    w = slot_world
    slot = (await w.resolve(w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC))).slot_id
    with Session(w.sync_engine) as session, session.begin():
        legacy = fixtures.seed_fact_slot(session, *w.a.scope)
    for column, value in (
        ("predicate_release_ref", "'f0007-fixtures/9'"),
        ("identity_fingerprint", "repeat('0', 64)"),
        ("cardinality", "'MULTI'"),
        ("entity_id", "gen_random_uuid()"),
    ):
        _fails(w, f"UPDATE fact_slot SET {column} = {value} WHERE id = %s", slot, match="immutable")
    _fails(
        w,
        "UPDATE fact_slot SET knowledge_base_id = %s WHERE id = %s",
        w.b.knowledge_base_id,
        slot,
        match="immutable",
    )
    # A legacy row can never acquire an identity (NULL to value is a change too).
    _fails(
        w,
        "UPDATE fact_slot SET identity_version = 1, predicate_key = slot_type WHERE id = %s",
        legacy,
        match="immutable",
    )
    _fails(w, "UPDATE fact_slot SET slot_type = 'renamed' WHERE id = %s", legacy, match="immutable")
    _fails(
        w,
        "UPDATE fact_slot_qualifier SET canonical_value = '\"x\"' WHERE slot_id = %s",
        slot,
        match="append-only",
    )
    _fails(w, "DELETE FROM fact_slot_qualifier WHERE slot_id = %s", slot, match="append-only")


async def test_s0002_ac2_single_slot_overlap_still_hits_the_exclusion(slot_world):
    w = slot_world
    slot = (await w.resolve(w.key(w.a, AGGREGATE_LIMIT))).slot_id
    ok = await w.commit(slot, {"answer_contract": ENVELOPE, "state": "PRESENT", "value": MONEY})
    assert ok.status_code == 201
    version = w.scalar("SELECT id FROM canonical_fact_version WHERE slot_id = %s", slot)
    sql, params = _copy_version(w, version)
    _fails(w, sql, *params, match="exclu")


async def test_s0002_ac3_ac5_members_carry_independent_versions(slot_world):
    w = slot_world
    x, y = w.entity(w.a), w.entity(w.a)
    m1 = await w.resolve(
        w.key(w.a, ADDITIONAL_INSURED, member={"type": "entity_ref", "entity_id": str(x)})
    )
    m2 = await w.resolve(
        w.key(w.a, ADDITIONAL_INSURED, member={"type": "entity_ref", "entity_id": str(y)})
    )
    for member, entity in ((m1.member_slot_id, x), (m2.member_slot_id, y)):
        response = await w.commit(
            member,
            {
                "answer_contract": ENVELOPE,
                "state": "PRESENT",
                "value": {"type": "entity_ref", "entity_id": str(entity)},
            },
        )
        assert response.status_code == 201, response.text
    # Overlapping versions on two members coexist: the exclusion is per member slot.
    version_b = w.scalar(
        "SELECT id FROM canonical_fact_version WHERE slot_id = %s", m2.member_slot_id
    )
    b_before = w.rows(
        "SELECT id, value, valid, recorded FROM canonical_fact_version WHERE slot_id = %s",
        m2.member_slot_id,
    )
    # A change addressed to member A (EX-SLOT-003) touches no row of member B.
    change = await w.commit(
        m1.member_slot_id, {"answer_contract": ENVELOPE, "state": "NOT_APPLICABLE"}
    )
    assert change.status_code == 201
    assert (
        w.rows(
            "SELECT id, value, valid, recorded FROM canonical_fact_version WHERE slot_id = %s",
            m2.member_slot_id,
        )
        == b_before
    )
    touched = w.scalar(
        "SELECT count(*) FROM canonical_fact_change c JOIN canonical_fact_version v "
        "ON v.id IN (c.from_version_id, c.to_version_id) WHERE v.slot_id = %s",
        m2.member_slot_id,
    )
    assert touched == 1  # only member B's own initial insert
    # Member A and member B hold versions that overlap in valid AND recorded time,
    # which the exclusion would refuse within one slot.
    overlapping = w.scalar(
        "SELECT count(*) FROM canonical_fact_version a JOIN canonical_fact_version b "
        "ON a.valid && b.valid AND a.recorded && b.recorded "
        "WHERE a.slot_id = %s AND b.slot_id = %s AND b.id = %s",
        m1.member_slot_id,
        m2.member_slot_id,
        version_b,
    )
    assert overlapping >= 1


async def test_relationship_and_cross_kb_reads_are_not_disclosed(slot_world):
    w = slot_world
    relation = await w.resolve(w.key(w.a, RELATED_TO, object_entity_id=str(w.entity(w.a))))
    for principal in (w.reader_b, w.service_b):
        denied = await w.get(relation.slot_id, principal=principal)
        assert denied.status_code == 404 and denied.json()["code"] == "not_found"
    decisions = w.scalar(
        "SELECT count(*) FROM audit_event WHERE resource_id = %s AND event_type = "
        "'authorization_decision' AND decision = false",
        relation.slot_id,
    )
    assert decisions == 2  # existing durable denial audit is unchanged
