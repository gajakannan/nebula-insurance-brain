"""F0007-S0001/S0002: FactSlot identity resolution against real PostgreSQL.

Expectations come from the story ACs, ADR-0077 and worked examples EX-SLOT-001..004,
not from the implementation. Every test owns its database.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from brain_domain.fact_slots import SlotReason
from brain_security.execution import AuthorizationDenied
from brain_testing.factslots import (
    ADDITIONAL_INSURED,
    BAD_CARDINALITY,
    LIMIT_AMOUNT,
    LIMIT_AMOUNT_AS_MULTI,
    POLICY_NUMBER,
    RELATED_TO,
)
from engine.tests.fixtures.factslots import harness

_clean_fact_tables = harness._clean_fact_tables
database = harness.database
slot_world = harness.slot_world

EACH_OCC = {
    "basis": {"type": "code", "value": "EachOccurrence"},
    "currency": {"type": "code", "value": "USD"},
}


async def test_s0001_ac1_resolving_twice_and_concurrently_returns_one_slot(slot_world):
    w = slot_world
    first = await w.resolve(w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC))
    again = await w.resolve(w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC))
    assert first.outcome == "CREATED" and again.outcome == "RESOLVED"
    assert first.slot_id == again.slot_id

    # Two sessions racing on a fresh identity converge on one row.
    other = w.entity(w.a)
    key = w.key(w.a, LIMIT_AMOUNT, subject=other, qualifiers=EACH_OCC)
    results = await asyncio.gather(*(w.resolve(key) for _ in range(6)))
    assert len({r.slot_id for r in results}) == 1
    assert sorted(r.outcome for r in results).count("CREATED") == 1
    slot = results[0].slot_id
    assert w.scalar("SELECT count(*) FROM fact_slot WHERE entity_id = %s", other) == 1
    assert w.scalar("SELECT count(*) FROM fact_slot_qualifier WHERE slot_id = %s", slot) == 2


async def test_s0001_ac2_basis_splits_and_input_order_does_not(slot_world):
    w = slot_world
    each = await w.resolve(w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC))
    aggregate = await w.resolve(
        w.key(
            w.a,
            LIMIT_AMOUNT,
            qualifiers={**EACH_OCC, "basis": {"type": "code", "value": "GeneralAggregate"}},
        )
    )
    reordered = dict(reversed(list(EACH_OCC.items())))
    again = await w.resolve(w.key(w.a, LIMIT_AMOUNT, qualifiers=reordered))
    assert each.slot_id != aggregate.slot_id
    assert again.slot_id == each.slot_id


async def test_s0001_ac3_typed_normalization_and_stored_qualifier_rows(slot_world):
    w = slot_world
    forms = ["1000000", "1000000.00", "1E+6"]
    results = [
        await w.resolve(
            w.key(
                w.a,
                LIMIT_AMOUNT,
                qualifiers={**EACH_OCC, "threshold": {"type": "decimal", "value": form}},
            )
        )
        for form in forms
    ]
    assert len({r.slot_id for r in results}) == 1
    decomposed = "Café"  # NFD; NFC is "Café"
    text_a = await w.resolve(
        w.key(
            w.a,
            LIMIT_AMOUNT,
            qualifiers={**EACH_OCC, "label": {"type": "text", "value": decomposed}},
        )
    )
    text_b = await w.resolve(
        w.key(
            w.a, LIMIT_AMOUNT, qualifiers={**EACH_OCC, "label": {"type": "text", "value": "Café"}}
        )
    )
    assert text_a.slot_id == text_b.slot_id
    stored = dict(
        w.rows(
            "SELECT qualifier_name, canonical_value FROM fact_slot_qualifier WHERE slot_id = %s",
            results[0].slot_id,
        )
    )
    assert stored == {"basis": '"EachOccurrence"', "currency": '"USD"', "threshold": '"1000000"'}
    assert (
        w.scalar("SELECT fingerprint_version FROM fact_slot WHERE id = %s", results[0].slot_id) == 1
    )
    assert results[0].fingerprint and len(results[0].fingerprint) == 64


async def test_s0001_ac3_forced_collision_is_rejected_never_merged(slot_world):
    w = slot_world
    first = await w.resolve(
        w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC), fingerprint=lambda identity: "0" * 64
    )
    before = w.counts()
    other = {**EACH_OCC, "basis": {"type": "code", "value": "GeneralAggregate"}}
    second = await w.resolve(
        w.key(w.a, LIMIT_AMOUNT, qualifiers=other), fingerprint=lambda identity: "0" * 64
    )
    assert first.outcome == "CREATED"
    assert second.outcome == "REJECTED" and second.reason == SlotReason.FINGERPRINT_COLLISION
    assert second.slot_id is None
    assert w.counts() == before


async def test_s0001_ac4_omitted_and_explicit_null_are_distinct(slot_world):
    w = slot_world
    omitted = await w.resolve(w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC))
    before = w.counts()
    null = await w.resolve(w.key(w.a, LIMIT_AMOUNT, qualifiers={**EACH_OCC, "threshold": None}))
    assert omitted.outcome == "CREATED"
    assert null.outcome == "REJECTED" and null.reason == SlotReason.QUALIFIER_NULL_REJECTED
    assert w.counts() == before
    missing_required = await w.resolve(
        w.key(w.a, LIMIT_AMOUNT, qualifiers={"currency": EACH_OCC["currency"]})
    )
    assert missing_required.reason == SlotReason.QUALIFIER_REQUIRED
    undeclared = await w.resolve(
        w.key(w.a, LIMIT_AMOUNT, qualifiers={**EACH_OCC, "mood": {"type": "code", "value": "x"}})
    )
    assert undeclared.reason == SlotReason.QUALIFIER_UNDECLARED
    wrong_type = await w.resolve(
        w.key(
            w.a, LIMIT_AMOUNT, qualifiers={**EACH_OCC, "threshold": {"type": "text", "value": "1"}}
        )
    )
    assert wrong_type.reason == SlotReason.QUALIFIER_TYPE_INVALID


async def test_s0001_ac5_two_kbs_two_slots_and_kb_b_principal_sees_not_found(slot_world):
    w = slot_world
    in_a = await w.resolve(w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC))
    in_b = await w.resolve(
        w.key(w.b, LIMIT_AMOUNT, qualifiers=EACH_OCC), principal=w.service_b, owner=w.b
    )
    assert in_a.slot_id != in_b.slot_id
    assert w.rows(
        "SELECT knowledge_base_id FROM fact_slot WHERE id IN (%s, %s) ORDER BY 1",
        in_a.slot_id,
        in_b.slot_id,
    ) == sorted([(w.a.knowledge_base_id,), (w.b.knowledge_base_id,)])
    # A KB-B-only principal cannot interpret KB A sources: non-disclosing denial.
    with pytest.raises(AuthorizationDenied):
        await w.resolve(w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC), principal=w.service_b)
    # Using its own KB B sources while naming KB A resolves nothing in KB A.
    crossed = await w.resolve(
        w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC), principal=w.service_b, owner=w.b
    )
    assert crossed.reason == SlotReason.SUBJECT_NOT_FOUND
    # Reads of the KB A slot are indistinguishable from a slot that does not exist.
    denied = await w.get(in_a.slot_id, principal=w.reader_b)
    missing = await w.get(harness.uuid4(), principal=w.reader_b)
    assert denied.status_code == missing.status_code == 404
    assert denied.json()["code"] == missing.json()["code"] == "not_found"


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        ({"predicate_key": "hasLimitAmount"}, SlotReason.PREDICATE_KEY_INVALID),
        ({"predicate_key": "test:hasLimitAmount"}, SlotReason.PREDICATE_KEY_INVALID),
        ({"predicate_release_ref": None}, SlotReason.PREDICATE_KEY_INVALID),
        ({"predicate_release_ref": ""}, SlotReason.PREDICATE_KEY_INVALID),
        ({"predicate_key": "acme:hasLimitAmount@v1"}, SlotReason.PREDICATE_UNREGISTERED),
    ],
)
async def test_s0001_ac6_malformed_or_unpinned_key_writes_no_row(slot_world, mutate, reason):
    w = slot_world
    before = w.counts()
    result = await w.resolve({**w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC), **mutate})
    assert result.outcome == "REJECTED" and result.reason == reason
    assert w.counts() == before


async def test_s0001_ac6_predicate_key_is_exposed_unchanged(slot_world):
    w = slot_world
    result = await w.resolve(w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC))
    assert result.predicate_key == "test:hasLimitAmount@v1"
    assert w.rows(
        "SELECT predicate_key, slot_type, predicate_release_ref FROM fact_slot WHERE id = %s",
        result.slot_id,
    ) == [("test:hasLimitAmount@v1", "test:hasLimitAmount@v1", "f0007-fixtures/1")]
    assert result.to_json()["fingerprint_version"] == 1


async def test_s0001_ac7_creation_is_audited_and_unauthorized_writes_nothing(slot_world):
    w = slot_world
    result = await w.resolve(w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC))
    events = w.rows(
        "SELECT actor_principal_id, payload FROM audit_event "
        "WHERE event_type = 'fact_slot_created' AND resource_id = %s",
        result.slot_id,
    )
    assert len(events) == 1
    actor, payload = events[0]
    payload = payload if isinstance(payload, dict) else json.loads(payload)
    assert actor == w.service.id
    assert payload["tenant_id"] == str(w.a.tenant_id)
    assert payload["knowledge_base_id"] == str(w.a.knowledge_base_id)
    assert payload["slot_id"] == str(result.slot_id)
    assert payload["fingerprint_version"] == 1
    assert payload["authorization_decision_id"]
    # Derived restrictions: the slot depends on its source artifact.
    classifications, _acl, dependencies = w.access(result.slot_id)
    assert classifications == ["internal"]
    assert {"type": "content_artifact", "id": str(w.a.artifact_id)} in dependencies

    before = w.counts()
    with pytest.raises(AuthorizationDenied):
        await w.resolve(
            w.key(w.a, LIMIT_AMOUNT, subject=w.entity(w.a), qualifiers=EACH_OCC),
            principal=w.reader_b,
        )
    stranger = w.entity(w.b)  # exists in the tenant but not in KB A
    cross = await w.resolve(w.key(w.a, LIMIT_AMOUNT, subject=stranger, qualifiers=EACH_OCC))
    assert cross.reason == SlotReason.SUBJECT_NOT_FOUND
    assert w.counts() == before
    with pytest.raises(Exception, match="immutable"):
        w.scalar(
            "UPDATE fact_slot SET predicate_key = 'test:other@v1' WHERE id = %s RETURNING 1",
            result.slot_id,
        )


async def test_s0001_restrictions_union_of_sources(slot_world):
    w = slot_world
    restricted = w.artifact(w.a, classifications=("restricted",), source_acl_ids=("acl-1",))
    result = await w.resolve(
        w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC), sources=[w.a.artifact_id, restricted]
    )
    classifications, acl, dependencies = w.access(result.slot_id)
    assert classifications == ["internal", "restricted"]
    assert acl == ["acl-1"]
    assert len(dependencies) == 2


async def test_s0002_ac1_cardinality_conflict_and_invalid(slot_world):
    w = slot_world
    single = await w.resolve(w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC))
    assert single.cardinality.value == "SINGLE"
    before = w.counts()
    as_multi = await w.resolve(
        w.key(
            w.a,
            LIMIT_AMOUNT_AS_MULTI,
            qualifiers=EACH_OCC,
            member={"type": "money", "amount": "1", "currency": "USD", "basis": "x"},
        )
    )
    assert as_multi.reason == SlotReason.CARDINALITY_CONFLICT
    invalid = await w.resolve(w.key(w.a, BAD_CARDINALITY))
    assert invalid.reason == SlotReason.CARDINALITY_INVALID
    assert w.counts() == before


async def test_s0002_ac3_two_insureds_two_members_and_duplicate_resolves(slot_world):
    w = slot_world
    x, y = w.entity(w.a), w.entity(w.a)
    m1 = await w.resolve(
        w.key(w.a, ADDITIONAL_INSURED, member={"type": "entity_ref", "entity_id": str(x)})
    )
    m2 = await w.resolve(
        w.key(w.a, ADDITIONAL_INSURED, member={"type": "entity_ref", "entity_id": str(y)})
    )
    again = await w.resolve(
        w.key(w.a, ADDITIONAL_INSURED, member={"type": "entity_ref", "entity_id": str(x)})
    )
    assert m1.slot_id == m2.slot_id == again.slot_id  # one header
    assert len({m1.member_slot_id, m2.member_slot_id}) == 2
    assert again.member_slot_id == m1.member_slot_id and again.member_created is False
    assert m1.member_created and m2.member_created
    rows = w.rows(
        "SELECT slot_role, parent_slot_id, member_key FROM fact_slot WHERE id = %s",
        m1.member_slot_id,
    )
    assert rows == [("MEMBER", m1.slot_id, str(x))]
    events = w.scalar(
        "SELECT count(*) FROM audit_event WHERE event_type = 'fact_slot_member_created'"
    )
    assert events == 2


async def test_s0002_ac4_relationship_identity_includes_object(slot_world):
    w = slot_world
    o1, o2 = w.entity(w.a), w.entity(w.a)
    r1 = await w.resolve(w.key(w.a, RELATED_TO, object_entity_id=str(o1)))
    r2 = await w.resolve(w.key(w.a, RELATED_TO, object_entity_id=str(o2)))
    again = await w.resolve(w.key(w.a, RELATED_TO, object_entity_id=str(o1)))
    assert r1.slot_id != r2.slot_id and again.slot_id == r1.slot_id
    before = w.counts()
    outsider = w.entity(w.b)
    out = await w.resolve(w.key(w.a, RELATED_TO, object_entity_id=str(outsider)))
    assert out.reason == SlotReason.RELATIONSHIP_OBJECT_OUT_OF_SCOPE
    assert w.counts() == before


async def test_s0002_ac6_named_rejections_write_no_rows(slot_world):
    w = slot_world
    before = w.counts()
    cases = [
        (w.key(w.a, ADDITIONAL_INSURED), SlotReason.MEMBER_KEY_REQUIRED),
        (w.key(w.a, ADDITIONAL_INSURED, member=None), SlotReason.MEMBER_KEY_REQUIRED),
        (w.key(w.a, RELATED_TO), SlotReason.RELATIONSHIP_OBJECT_REQUIRED),
        (
            w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC, member={"type": "text", "value": "x"}),
            SlotReason.MEMBER_NOT_ALLOWED,
        ),
        (
            w.key(w.a, LIMIT_AMOUNT, qualifiers=EACH_OCC, object_entity_id=str(w.subject)),
            SlotReason.RELATIONSHIP_OBJECT_NOT_ALLOWED,
        ),
        (
            w.key(w.a, ADDITIONAL_INSURED, member={"type": "text", "value": "x"}),
            SlotReason.QUALIFIER_TYPE_INVALID,
        ),
        (
            w.key(
                w.a,
                ADDITIONAL_INSURED,
                member={"type": "entity_ref", "entity_id": str(w.entity(w.b))},
            ),
            SlotReason.RELATIONSHIP_OBJECT_OUT_OF_SCOPE,
        ),
    ]
    for key, reason in cases:
        result = await w.resolve(key)
        assert (result.outcome, result.reason) == ("REJECTED", reason), key
    assert w.counts() == before
    with pytest.raises(AuthorizationDenied):
        await w.resolve(
            w.key(
                w.a, ADDITIONAL_INSURED, member={"type": "entity_ref", "entity_id": str(w.subject)}
            ),
            principal=w.reader_b,
        )
    assert w.counts() == before


async def test_s0004_ac4_ac6_identifier_members_are_scheme_scoped(slot_world):
    w = slot_world

    def number(scheme, value, kind="policy-number"):  # type: ignore[no-untyped-def]
        return w.key(
            w.a,
            POLICY_NUMBER,
            member={
                "type": "identifier",
                "scheme": scheme,
                "identifier_type": kind,
                "value": value,
            },
        )

    carrier_a = await w.resolve(number("carrier:A", "GL-1001"))
    carrier_b = await w.resolve(number("carrier:B", "GL-1001"))
    assert carrier_a.member_slot_id != carrier_b.member_slot_id
    fein_1 = await w.resolve(number("us-irs", "12-3456789", "fein"))
    fein_2 = await w.resolve(number("us-irs", "123456789", "fein"))
    assert fein_1.member_slot_id == fein_2.member_slot_id
    no_scheme = await w.resolve(
        w.key(
            w.a,
            POLICY_NUMBER,
            member={"type": "identifier", "identifier_type": "policy-number", "value": "GL-1001"},
        )
    )
    assert no_scheme.reason == SlotReason.IDENTIFIER_SCHEME_REQUIRED
    # Money as a qualifier contributes its canonical encoding to identity.
    m1 = await w.resolve(
        w.key(
            w.a,
            LIMIT_AMOUNT,
            qualifiers={
                **EACH_OCC,
                "attachment": {"type": "money", "amount": "1E+6", "currency": "USD"},
            },
        )
    )
    m2 = await w.resolve(
        w.key(
            w.a,
            LIMIT_AMOUNT,
            qualifiers={
                **EACH_OCC,
                "attachment": {"type": "money", "amount": "1000000.00", "currency": "USD"},
            },
        )
    )
    assert m1.slot_id == m2.slot_id
    float_money = await w.resolve(
        w.key(
            w.a,
            LIMIT_AMOUNT,
            qualifiers={
                **EACH_OCC,
                "attachment": {"type": "money", "amount": 1000000, "currency": "USD"},
            },
        )
    )
    assert float_money.reason == SlotReason.MONEY_FLOAT_REJECTED
