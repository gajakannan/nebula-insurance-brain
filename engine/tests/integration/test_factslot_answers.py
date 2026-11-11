"""F0007-S0003/S0004: the fact-answer/v1 carrier through the existing commit route.

Expectations come from the story ACs, ADR-0039/ADR-0077 and EX-OWN-003 /
EX-MONEY-001 / EX-ID-001. Every test owns its database.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from brain_domain.fact_answers import InformationState
from brain_factslots.service import SlotNotFound
from brain_testing import fixtures
from brain_testing.factslots import (
    ADDITIONAL_INSURED,
    AGGREGATE_LIMIT,
    LIMIT_AMOUNT,
    POLICY_NUMBER,
    RELATED_TO,
    TAX_ID,
)
from engine.tests.fixtures.factslots import harness
from sqlalchemy.orm import Session

_clean_fact_tables = harness._clean_fact_tables
database = harness.database
slot_world = harness.slot_world

ENVELOPE = "fact-answer/v1"
EACH_OCC = {
    "basis": {"type": "code", "value": "EachOccurrence"},
    "currency": {"type": "code", "value": "USD"},
}


async def _slot(w, predicate=AGGREGATE_LIMIT, **kwargs):  # type: ignore[no-untyped-def]
    result = await w.resolve(w.key(w.a, predicate, subject=w.entity(w.a), **kwargs))
    assert result.outcome == "CREATED"
    return result.slot_id


def _scope(artifact, **extra):  # type: ignore[no-untyped-def]
    return {
        "content_artifact_id": str(artifact),
        "profile_release_ref": "gl-policy-profile/1",
        **extra,
    }


async def _read(w, slot_id, principal=None):  # type: ignore[no-untyped-def]
    now = datetime.now(UTC)
    async with w.slots() as service:
        return await service.read_answer(
            principal or w.service, slot_id, valid_at=now, known_at=now, trace_id="f0007-read"
        )


@pytest.mark.parametrize("state", [s.value for s in InformationState])
async def test_s0003_ac1_all_nine_states_are_accepted(slot_world, state):
    w = slot_world
    slot = await _slot(w)
    envelope = {"answer_contract": ENVELOPE, "state": state}
    if state == "PRESENT":
        envelope["value"] = {"type": "money", "amount": "2000000", "currency": "USD"}
    if state in ("NOT_FOUND", "NOT_STATED"):
        envelope["scope"] = _scope(w.a.artifact_id, pages=[1, 2, 3])
    response = await w.commit(slot, envelope)
    assert response.status_code == 201, response.text
    answer = await _read(w, slot)
    assert answer.state.value == state


@pytest.mark.parametrize("state", ["ACCESS_DENIED", "RESTRICTED", "present", ""])
async def test_s0003_ac1_any_other_state_is_rejected(slot_world, state):
    w = slot_world
    slot = await _slot(w)
    before = w.counts()
    response = await w.commit(slot, {"answer_contract": ENVELOPE, "state": state})
    assert response.status_code == 422
    assert response.json()["code"] == "information_state_invalid"
    assert response.json()["detail"] is None
    assert w.counts() == before


@pytest.mark.parametrize(
    "envelope",
    [
        {"state": "PRESENT"},
        {
            "state": "EXPLICIT_NEGATIVE",
            "value": {"type": "money", "amount": "1", "currency": "USD"},
        },
        {"state": "NOT_PROCESSED", "value": {"type": "money", "amount": "1", "currency": "USD"}},
        {"state": "NOT_APPLICABLE", "scope": {"content_artifact_id": "x"}},
    ],
)
async def test_s0003_ac2_state_value_mismatch_writes_no_version(slot_world, envelope):
    w = slot_world
    slot = await _slot(w)
    before = w.counts()
    response = await w.commit(slot, {"answer_contract": ENVELOPE, **envelope})
    assert response.status_code == 422
    assert response.json()["code"] == "state_value_mismatch"
    assert w.counts() == before


async def test_s0003_ac3_absence_scope_required_and_owned(slot_world):
    w = slot_world
    slot = await _slot(w)
    before = w.counts()
    for state in ("NOT_FOUND", "NOT_STATED"):
        for scope in (
            None,
            _scope(w.a.artifact_id),
            _scope(w.a.artifact_id, pages=[]),
            {"profile_release_ref": "p/1", "pages": [1]},
        ):
            envelope = {"answer_contract": ENVELOPE, "state": state}
            if scope is not None:
                envelope["scope"] = scope
            response = await w.commit(slot, envelope)
            assert response.status_code == 422, (state, scope)
            assert response.json()["code"] == "absence_scope_required"
    assert w.counts() == before
    # A scope artifact the caller can read but that belongs to another KB.
    with Session(w.sync_engine) as session, session.begin():
        fixtures.seed_grant(session, w.service.id, *w.b.scope, "ServicePrincipal")
    response = await w.commit(
        slot,
        {
            "answer_contract": ENVELOPE,
            "state": "NOT_FOUND",
            "scope": _scope(w.b.artifact_id, pages=[1]),
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "absence_scope_out_of_scope"
    assert w.counts() == before


async def test_s0003_ac4_unread_slot_reads_not_processed_never_null(slot_world):
    w = slot_world
    slot = await _slot(w)
    answer = await _read(w, slot)
    assert answer.state == InformationState.NOT_PROCESSED
    assert answer.to_json() == {"answer_contract": ENVELOPE, "state": "NOT_PROCESSED"}
    with pytest.raises(SlotNotFound):
        await _read(w, slot, principal=w.reader_b)


async def test_s0003_ac5_ex_own_003_three_kinds_of_no_value(slot_world):
    w = slot_world
    slots = [await _slot(w) for _ in range(3)]
    reviewed = w.artifact(w.a)
    answers = [
        {"answer_contract": ENVELOPE, "state": "NOT_PROCESSED"},
        {
            "answer_contract": ENVELOPE,
            "state": "NOT_FOUND",
            "scope": _scope(w.a.artifact_id, pages=[3, 1, 2]),
        },
        {
            "answer_contract": ENVELOPE,
            "state": "NOT_STATED",
            "scope": _scope(reviewed, pages=[4], block_ids=[str(harness.uuid4())]),
        },
    ]
    for slot, answer in zip(slots, answers, strict=True):
        assert (await w.commit(slot, answer)).status_code == 201
    reloaded = [await _read(w, s) for s in slots]
    assert [a.state.value for a in reloaded] == ["NOT_PROCESSED", "NOT_FOUND", "NOT_STATED"]
    assert reloaded[1].scope.pages == (3, 1, 2)
    assert reloaded[1].scope.content_artifact_id == w.a.artifact_id
    assert reloaded[2].scope.content_artifact_id == reviewed
    # The pilot GET contract is unchanged and returns the stored envelope.
    body = (await w.get(slots[1])).json()
    assert body["value"] == {**answers[1], "scope": {**answers[1]["scope"]}}


async def test_s0003_ac6_unreadable_scope_is_denied_before_any_explanation(slot_world):
    w = slot_world
    slot = await _slot(w)
    secret = w.artifact(w.a, classifications=("restricted",))
    with Session(w.sync_engine) as session, session.begin():
        limited = fixtures.seed_principal(session, issuer="urn:f0007:test", subject="limited")
        fixtures.seed_grant(
            session, limited.id, *w.a.scope, "ServicePrincipal", classifications=("internal",)
        )
    before = w.counts()
    for envelope in (
        {"answer_contract": ENVELOPE, "state": "NOT_FOUND", "scope": _scope(secret, pages=[1])},
        {"answer_contract": ENVELOPE, "state": "NOT_FOUND", "scope": _scope(secret)},
    ):
        response = await w.commit(slot, envelope, principal=limited)
        assert response.status_code == 404
        assert response.json()["code"] == "not_found"
        assert "1" not in (response.json()["detail"] or "")
    assert w.counts() == before
    # The same principal can commit with a scope it may read.
    ok = await w.commit(
        slot,
        {
            "answer_contract": ENVELOPE,
            "state": "NOT_FOUND",
            "scope": _scope(w.a.artifact_id, pages=[1]),
        },
        principal=limited,
    )
    assert ok.status_code == 201


async def test_s0003_ac7_accepted_answer_is_audited_and_rejection_writes_nothing(slot_world):
    w = slot_world
    slot = await _slot(w)
    ok = await w.commit(slot, {"answer_contract": ENVELOPE, "state": "NOT_APPLICABLE"})
    commit_id = ok.json()["commitId"] if "commitId" in ok.json() else ok.json()["commit_id"]
    assert w.scalar("SELECT count(*) FROM canonical_commit WHERE id = %s", commit_id) == 1
    assert (
        w.scalar(
            "SELECT count(*) FROM audit_event WHERE resource_id = %s AND action = 'commit' "
            "AND operation_outcome = 'succeeded'",
            slot,
        )
        == 1
    )
    before = w.counts()
    bad = await w.commit(slot, {"answer_contract": "fact-answer/v2", "state": "PRESENT"})
    assert bad.status_code == 422 and bad.json()["code"] == "answer_contract_unsupported"
    assert w.counts() == before


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ({"type": "money", "amount": 1000000, "currency": "USD"}, "money_float_rejected"),
        ({"type": "money", "amount": 1000000.0, "currency": "USD"}, "money_float_rejected"),
        ({"type": "money", "amount": "1000000", "currency": "US$"}, "currency_invalid"),
        ({"type": "money", "amount": "1000000", "currency": "ABC"}, "currency_invalid"),
        (
            {
                "type": "money",
                "amount": "1000000",
                "currency": "USD",
                "converted_from": {"amount": "900000", "currency": "EUR"},
            },
            "converted_money_unsupported",
        ),
        ({"type": "money", "amount": "1,000,000", "currency": "USD"}, "decimal_invalid"),
        ({"type": "text", "value": "one million"}, "value_type_mismatch"),
    ],
)
async def test_s0004_ac1_ac3_money_rejections(slot_world, value, code):
    w = slot_world
    slot = await _slot(w)
    before = w.counts()
    response = await w.commit(
        slot, {"answer_contract": ENVELOPE, "state": "PRESENT", "value": value}
    )
    assert response.status_code == 422 and response.json()["code"] == code
    assert w.counts() == before


async def test_s0004_ac1_basis_required_where_the_predicate_requires_it(slot_world):
    w = slot_world
    slot = await _slot(w, LIMIT_AMOUNT, qualifiers=EACH_OCC)
    response = await w.commit(
        slot,
        {
            "answer_contract": ENVELOPE,
            "state": "PRESENT",
            "value": {"type": "money", "amount": "1000000", "currency": "USD"},
        },
    )
    assert response.status_code == 422 and response.json()["code"] == "basis_required"
    ok = await w.commit(
        slot,
        {
            "answer_contract": ENVELOPE,
            "state": "PRESENT",
            "value": {
                "type": "money",
                "amount": "1000000",
                "currency": "USD",
                "basis": "EachOccurrence",
            },
        },
    )
    assert ok.status_code == 201


async def test_s0004_ac2_exact_decimal_canonical_form_and_round_trip(slot_world):
    w = slot_world
    stored = []
    for amount in ("1000000", "1000000.00", "1E+6"):
        slot = await _slot(w)
        await w.commit(
            slot,
            {
                "answer_contract": ENVELOPE,
                "state": "PRESENT",
                "value": {"type": "money", "amount": amount, "currency": "USD"},
            },
        )
        stored.append((await _read(w, slot)).value.canonical["amount"])
    assert stored == ["1000000"] * 3
    for amount in ("0.01", "999999999999999.99", "9007199254740993", "-12.5"):
        slot = await _slot(w)
        await w.commit(
            slot,
            {
                "answer_contract": ENVELOPE,
                "state": "PRESENT",
                "value": {"type": "money", "amount": amount, "currency": "USD"},
            },
        )
        text = w.scalar(
            "SELECT value->'value'->>'amount' FROM canonical_fact_version WHERE slot_id = %s", slot
        )
        assert text == amount
        assert (await _read(w, slot)).value.canonical["amount"] == amount


@pytest.mark.parametrize("kind", ["money", "decimal"])
async def test_numeric_answer_canonical_bound_round_trips_or_rejects_without_writes(
    slot_world, kind
):
    w = slot_world
    predicate = AGGREGATE_LIMIT if kind == "money" else RELATED_TO
    for amount in ("1E+63", "-1E+62", "1E-62", "-1E-61"):
        kwargs = {"object_entity_id": str(w.entity(w.a))} if kind == "decimal" else {}
        slot = await _slot(w, predicate, **kwargs)
        value = (
            {"type": "money", "amount": amount, "currency": "USD"}
            if kind == "money"
            else {"type": "decimal", "value": amount}
        )
        response = await w.commit(
            slot, {"answer_contract": ENVELOPE, "state": "PRESENT", "value": value}
        )
        assert response.status_code == 201, response.text
        reloaded = (await _read(w, slot)).to_json()
        text = reloaded["value"]["amount" if kind == "money" else "value"]
        assert len(text) == 64
        assert (await w.get(slot)).json()["value"] == reloaded
    for amount in ("1E+64", "-1E+63", "1E-63", "-1E-62", "1e999999999", "1e-999999999"):
        kwargs = {"object_entity_id": str(w.entity(w.a))} if kind == "decimal" else {}
        slot = await _slot(w, predicate, **kwargs)
        value = (
            {"type": "money", "amount": amount, "currency": "USD"}
            if kind == "money"
            else {"type": "decimal", "value": amount}
        )
        before = w.counts()
        response = await w.commit(
            slot, {"answer_contract": ENVELOPE, "state": "PRESENT", "value": value}
        )
        assert response.status_code == 422, response.text
        assert response.json()["code"] == "decimal_invalid"
        assert w.counts() == before


async def test_s0004_ac4_ac5_identifier_values(slot_world):
    w = slot_world
    slot = await _slot(w, TAX_ID)
    response = await w.commit(
        slot,
        {
            "answer_contract": ENVELOPE,
            "state": "PRESENT",
            "value": {"type": "identifier", "identifier_type": "fein", "value": "12-3456789"},
        },
    )
    assert response.status_code == 422 and response.json()["code"] == "identifier_scheme_required"
    bad = await w.commit(
        slot,
        {
            "answer_contract": ENVELOPE,
            "state": "PRESENT",
            "value": {
                "type": "identifier",
                "scheme": "us-irs",
                "identifier_type": "fein",
                "value": "12-345",
            },
        },
    )
    assert bad.status_code == 422 and bad.json()["code"] == "identifier_invalid"
    ok = await w.commit(
        slot,
        {
            "answer_contract": ENVELOPE,
            "state": "PRESENT",
            "value": {
                "type": "identifier",
                "scheme": "us-irs",
                "identifier_type": "fein",
                "value": "12-3456789",
            },
        },
    )
    assert ok.status_code == 201
    value = (await _read(w, slot)).value.canonical
    assert value["normalized_value"] == "123456789" and value["value"] == "12-3456789"


async def test_s0004_ac7_unauthorized_caller_gets_denial_before_value_detail(slot_world):
    w = slot_world
    slot = await _slot(w)
    before = w.counts()
    response = await w.commit(
        slot,
        {
            "answer_contract": ENVELOPE,
            "state": "PRESENT",
            "value": {"type": "money", "amount": 1.5, "currency": "US$"},
        },
        principal=w.reader_b,
    )
    assert response.status_code == 404 and response.json()["code"] == "not_found"
    assert w.counts() == before


async def test_multi_header_and_unregistered_contract_are_rejected(slot_world):
    w = slot_world
    insured = w.entity(w.a)
    member = await w.resolve(
        w.key(w.a, ADDITIONAL_INSURED, member={"type": "entity_ref", "entity_id": str(insured)})
    )
    header = await w.commit(
        member.slot_id, {"answer_contract": ENVELOPE, "state": "NOT_APPLICABLE"}
    )
    assert header.status_code == 422 and header.json()["code"] == "multi_slot_requires_member"
    ok = await w.commit(
        member.member_slot_id,
        {
            "answer_contract": ENVELOPE,
            "state": "PRESENT",
            "value": {"type": "entity_ref", "entity_id": str(insured)},
        },
    )
    assert ok.status_code == 201
    outside = await w.commit(
        member.member_slot_id,
        {
            "answer_contract": ENVELOPE,
            "state": "PRESENT",
            "value": {"type": "entity_ref", "entity_id": str(w.entity(w.b))},
        },
        valid_from=datetime.now(UTC) + timedelta(days=30),
    )
    assert outside.status_code == 422
    assert outside.json()["code"] == "relationship_object_out_of_scope"
    # Production composition does not register the `test` namespace.
    from brain_factslots.predicates import production_registry

    w.registry = production_registry()
    slot = member.member_slot_id
    unsupported = await w.commit(slot, {"answer_contract": ENVELOPE, "state": "NOT_APPLICABLE"})
    assert unsupported.status_code == 422
    assert unsupported.json()["code"] == "answer_contract_unsupported"


async def test_member_commit_rejects_another_entity_before_writing(slot_world):
    w = slot_world
    insured = w.entity(w.a)
    member = await w.resolve(
        w.key(w.a, ADDITIONAL_INSURED, member={"type": "entity_ref", "entity_id": str(insured)})
    )
    envelope = {
        "answer_contract": ENVELOPE,
        "state": "PRESENT",
        "value": {"type": "entity_ref", "entity_id": str(w.subject)},
    }
    before = w.counts()
    denied = await w.commit(member.member_slot_id, envelope, principal=w.reader_b)
    assert denied.status_code == 404 and denied.json()["code"] == "not_found"
    rejected = await w.commit(member.member_slot_id, envelope)
    assert rejected.status_code == 422 and rejected.json()["code"] == "member_value_mismatch"
    assert rejected.json()["detail"] is None
    assert w.counts() == before
    accepted = await w.commit(
        member.member_slot_id,
        {**envelope, "value": {"type": "entity_ref", "entity_id": str(insured)}},
    )
    assert accepted.status_code == 201, accepted.text
    assert (await _read(w, member.member_slot_id)).value.canonical["entity_id"] == str(insured)


async def test_identifier_member_commit_accepts_equivalence_but_rejects_issuer_change(slot_world):
    w = slot_world
    value = {
        "type": "identifier",
        "scheme": "us-irs",
        "identifier_type": "fein",
        "value": "12-3456789",
    }
    member = await w.resolve(w.key(w.a, POLICY_NUMBER, member=value))
    envelope = {"answer_contract": ENVELOPE, "state": "PRESENT", "value": value}
    before = w.counts()
    rejected = await w.commit(
        member.member_slot_id, {**envelope, "value": {**value, "scheme": "carrier:B"}}
    )
    assert rejected.status_code == 422 and rejected.json()["code"] == "member_value_mismatch"
    assert w.counts() == before
    accepted = await w.commit(
        member.member_slot_id, {**envelope, "value": {**value, "value": "123456789"}}
    )
    assert accepted.status_code == 201, accepted.text
    reloaded = (await _read(w, member.member_slot_id)).value.canonical
    assert reloaded["scheme"] == "us-irs" and reloaded["normalized_value"] == "123456789"


async def test_s0003_ac6_reads_never_expose_a_scope_the_reader_cannot_read(slot_world):
    """G3 security fix (SEC-F7-02): T-08 also holds on the read path. A reader who
    may read the slot but not the scope's artifact gets the non-disclosing 404 from
    GET /facts/{id} and from the internal reader, never the pages or block IDs."""
    w = slot_world
    slot = await _slot(w)
    secret = w.artifact(w.a, classifications=("restricted",))
    committed = await w.commit(
        slot,
        {"answer_contract": ENVELOPE, "state": "NOT_FOUND", "scope": _scope(secret, pages=[7, 8])},
    )
    assert committed.status_code == 201
    with Session(w.sync_engine) as session, session.begin():
        internal = fixtures.seed_principal(session, issuer="urn:f0007:test", subject="internal")
        fixtures.seed_grant(
            session, internal.id, *w.a.scope, "TenantMember", classifications=("internal",)
        )
    hidden = await w.get(slot, principal=internal)
    missing = await w.get(harness.uuid4(), principal=internal)
    assert hidden.status_code == missing.status_code == 404
    assert hidden.json()["code"] == missing.json()["code"] == "not_found"
    assert "pages" not in hidden.text and "scope" not in hidden.text
    assert str(secret) not in hidden.text and hidden.json()["detail"] is None
    with pytest.raises(SlotNotFound):
        await _read(w, slot, principal=internal)
    # A reader cleared for the scope's artifact sees the answer and its scope.
    shown = await w.get(slot)
    assert shown.status_code == 200 and shown.json()["value"]["scope"]["pages"] == [7, 8]
    # An answer without a scope needs no extra check (and legacy slots are untouched).
    plain = await _slot(w)
    assert (
        await w.commit(plain, {"answer_contract": ENVELOPE, "state": "NOT_APPLICABLE"})
    ).status_code == 201
    assert (await w.get(plain, principal=internal)).status_code == 200
