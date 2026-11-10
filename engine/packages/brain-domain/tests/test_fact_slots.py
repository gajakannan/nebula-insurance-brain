"""F0007 pure domain: canonical values, qualifier identity, fingerprint and answers.

Expectations come from ADR-0077 D1-D6, ADR-0039 and the F0007 worked examples.
"""

from __future__ import annotations

import hashlib
from uuid import UUID, uuid4

import pytest
from brain_domain.fact_answers import (
    AnswerReason,
    FactAnswerRejected,
    InformationState,
    parse_answer,
    stored_answer,
)
from brain_domain.fact_slots import (
    CanonicalQualifier,
    Cardinality,
    PredicateContract,
    PredicateKey,
    QualifierSpec,
    SlotIdentity,
    SlotReason,
    SlotRejected,
    canonical_qualifiers,
    member_key,
    parse_release_ref,
)
from brain_domain.fact_values import (
    ValueReason,
    ValueRejected,
    ValueType,
    canonical_decimal,
    canonical_identifier,
    canonical_money,
    canonical_name,
    canonical_value,
    iso4217_codes,
    jcs,
    normalize_name,
)

CONTRACT = PredicateContract(
    key=PredicateKey("test", "hasLimitAmount", 1),
    release_ref="f0007-fixtures/1",
    cardinality=Cardinality.SINGLE,
    value_type=ValueType.MONEY,
    qualifiers=(
        QualifierSpec("basis", ValueType.CODE, required=True),
        QualifierSpec("currency", ValueType.CODE),
        QualifierSpec("threshold", ValueType.DECIMAL),
        QualifierSpec("on", ValueType.DATE),
        QualifierSpec("flag", ValueType.BOOLEAN),
        QualifierSpec("who", ValueType.ENTITY_REF),
        QualifierSpec("id", ValueType.IDENTIFIER),
        QualifierSpec("note", ValueType.NAME),
    ),
    basis_required=True,
)


@pytest.mark.parametrize(
    ("raw", "canonical"),
    [
        ("1000000", "1000000"),
        ("1000000.00", "1000000"),
        ("1E+6", "1000000"),
        ("1e6", "1000000"),
        ("0.01", "0.01"),
        ("999999999999999.99", "999999999999999.99"),
        ("9007199254740993", "9007199254740993"),
        ("-0", "0"),
        ("-0.000", "0"),
        ("+12.50", "12.5"),
        (".5", "0.5"),
        ("5.", "5"),
        ("1.5E-3", "0.0015"),
        ("000120", "120"),
        ("12345678901234567890123456789012345", "12345678901234567890123456789012345"),
    ],
)
def test_canonical_decimal_is_exact(raw, canonical):
    assert canonical_decimal(raw) == canonical


@pytest.mark.parametrize(
    "raw", [1000000, 1.5, "1,000", "NaN", "Infinity", "", "1E+999", "--1", "1" * 65]
)
def test_canonical_decimal_rejects(raw):
    with pytest.raises(ValueRejected) as rejected:
        canonical_decimal(raw)
    assert rejected.value.reason == ValueReason.DECIMAL_INVALID


def test_jcs_matches_rfc8785_for_the_f0007_subset():
    assert jcs({"b": 1, "a": [None, True, "é\n\u0001"]}) == (
        '{"a":[null,true,"é\\n\\u0001"],"b":1}'.encode()
    )
    with pytest.raises(TypeError):
        jcs({"a": 1.5})
    with pytest.raises(TypeError):
        jcs({"é": 1})
    with pytest.raises(TypeError):
        jcs({1: 1})  # type: ignore[dict-item]


def test_money_rules_in_order():
    assert canonical_money(
        {"amount": "1E+6", "currency": "USD", "basis": "Each"}, basis_required=True
    ).identity() == {"amount": "1000000", "currency": "USD", "basis": "Each"}
    cases = [
        ({"amount": 1, "currency": "USD"}, ValueReason.MONEY_FLOAT_REJECTED),
        ({"amount": "1", "currency": "usd"}, ValueReason.CURRENCY_INVALID),
        ({"amount": "1", "currency": "ANG"}, ValueReason.CURRENCY_INVALID),  # withdrawn
        (
            {"amount": "1", "currency": "USD", "original_amount": "2"},
            ValueReason.CONVERTED_MONEY_UNSUPPORTED,
        ),
        (
            {"amount": "1", "currency": "USD", "exchange_basis": "x"},
            ValueReason.CONVERTED_MONEY_UNSUPPORTED,
        ),
        ({"amount": "1", "currency": "USD", "extra": "x"}, ValueReason.VALUE_TYPE_MISMATCH),
        ({"amount": "1", "currency": "USD", "basis": "a b"}, ValueReason.VALUE_TYPE_MISMATCH),
        ({"amount": True, "currency": "USD"}, ValueReason.DECIMAL_INVALID),
    ]
    for raw, reason in cases:
        with pytest.raises(ValueRejected) as rejected:
            canonical_money(raw, basis_required=False)
        assert rejected.value.reason == reason, raw
    with pytest.raises(ValueRejected) as rejected:
        canonical_money({"amount": "1", "currency": "USD"}, basis_required=True)
    assert rejected.value.reason == ValueReason.BASIS_REQUIRED
    assert {"USD", "EUR", "XCG", "ZWG"} <= iso4217_codes()


def test_identifiers_are_scheme_scoped_and_normalized_per_type():
    a = canonical_identifier({"scheme": "us-irs", "identifier_type": "fein", "value": "12-3456789"})
    b = canonical_identifier(
        {
            "scheme": "us-irs",
            "identifier_type": "fein",
            "value": "123456789",
            "normalized_value": "123456789",
            "effective": {"from": "2026-01-01", "to": "2026-12-31"},
        }
    )
    other = canonical_identifier(
        {"scheme": "us-state:TX", "identifier_type": "fein", "value": "123456789"}
    )
    assert a.identity() == b.identity() != other.identity()
    assert b.to_json()["effective"] == {"from": "2026-01-01", "to": "2026-12-31"}
    nfc = canonical_identifier(
        {"scheme": "carrier:A", "identifier_type": "policy-number", "value": "GL-1001"}
    )
    assert nfc.normalized_value == "GL-1001" and "effective" not in nfc.to_json()
    bad = [
        ({"identifier_type": "fein", "value": "1"}, ValueReason.IDENTIFIER_SCHEME_REQUIRED),
        (
            {"scheme": "", "identifier_type": "fein", "value": "1"},
            ValueReason.IDENTIFIER_SCHEME_REQUIRED,
        ),
        (
            {"scheme": "US IRS", "identifier_type": "fein", "value": "1"},
            ValueReason.IDENTIFIER_INVALID,
        ),
        (
            {"scheme": "us-irs", "identifier_type": "fein", "value": "12-34"},
            ValueReason.IDENTIFIER_INVALID,
        ),
        (
            {"scheme": "us-irs", "identifier_type": "fein", "value": "１２３４５６７８９"},
            ValueReason.IDENTIFIER_INVALID,
        ),
        (
            {
                "scheme": "us-irs",
                "identifier_type": "fein",
                "value": "123456789",
                "normalized_value": "x",
            },
            ValueReason.IDENTIFIER_INVALID,
        ),
        (
            {"scheme": "us-irs", "identifier_type": "ein", "value": ""},
            ValueReason.IDENTIFIER_INVALID,
        ),
        (
            {"scheme": "us-irs", "identifier_type": "ein", "value": "1", "effective": {"to": "x"}},
            ValueReason.IDENTIFIER_INVALID,
        ),
        (
            {
                "scheme": "us-irs",
                "identifier_type": "ein",
                "value": "1",
                "effective": {"from": "2026-02-01", "to": "2026-01-01"},
            },
            ValueReason.IDENTIFIER_INVALID,
        ),
        (
            {"scheme": "us-irs", "identifier_type": "ein", "value": "1", "effective": "2026"},
            ValueReason.IDENTIFIER_INVALID,
        ),
        (
            {"scheme": "us-irs", "identifier_type": "ein", "value": "1", "bogus": 1},
            ValueReason.IDENTIFIER_INVALID,
        ),
    ]
    for raw, reason in bad:
        with pytest.raises(ValueRejected) as rejected:
            canonical_identifier(raw)
        assert rejected.value.reason == reason, raw


def test_names_normalize_and_require_evidence():
    evidence = {"assertion_id": str(uuid4()), "document_version_id": str(uuid4())}
    name = canonical_name(
        {"verbatim": "  Acme   Roofing\tINC. ", "evidence": evidence, "name_kind": "legal"}
    )
    assert name.normalized == normalize_name("acme roofing inc.") == "acme roofing inc."
    assert name.to_json()["name_kind"] == "legal"
    for raw in (
        {"verbatim": "Acme"},
        {"verbatim": "Acme", "evidence": {"assertion_id": "x", "document_version_id": "y"}},
        {"verbatim": "Acme", "evidence": {"assertion_id": str(uuid4())}},
    ):
        with pytest.raises(ValueRejected) as rejected:
            canonical_name(raw)
        assert rejected.value.reason == ValueReason.NAME_EVIDENCE_REQUIRED
    for raw in (
        {"verbatim": "   ", "evidence": evidence},
        {"verbatim": "Acme", "normalized": "other", "evidence": evidence},
        {"verbatim": "Acme", "name_kind": "a b", "evidence": evidence},
        {"verbatim": "Acme", "evidence": evidence, "alias": 1},
        {"verbatim": "\ud800", "evidence": evidence},
    ):
        with pytest.raises(ValueRejected) as rejected:
            canonical_name(raw)
        assert rejected.value.reason == ValueReason.TEXT_INVALID


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ("x", ValueReason.VALUE_TYPE_MISMATCH),
        ({"type": "nope"}, ValueReason.VALUE_TYPE_MISMATCH),
        ({"type": "text", "value": "x", "extra": 1}, ValueReason.VALUE_TYPE_MISMATCH),
        ({"type": "text", "value": ""}, ValueReason.TEXT_INVALID),
        ({"type": "code", "value": "a b"}, ValueReason.TEXT_INVALID),
        ({"type": "date", "value": "2026-02-30"}, ValueReason.TEXT_INVALID),
        ({"type": "boolean", "value": 1}, ValueReason.VALUE_TYPE_MISMATCH),
        ({"type": "entity_ref", "entity_id": "x"}, ValueReason.VALUE_TYPE_MISMATCH),
        ({"type": "entity_ref", "id": str(uuid4())}, ValueReason.VALUE_TYPE_MISMATCH),
    ],
)
def test_canonical_value_rejections(raw, reason):
    with pytest.raises(ValueRejected) as rejected:
        canonical_value(raw)
    assert rejected.value.reason == reason


def test_canonical_value_accepts_each_scalar():
    entity = str(uuid4())
    assert canonical_value({"type": "date", "value": "2026-06-01"}).identity == "2026-06-01"
    assert canonical_value({"type": "boolean", "value": False}).canonical == {
        "type": "boolean",
        "value": False,
    }
    assert canonical_value({"type": "entity_ref", "entity_id": entity.upper()}).identity == entity
    with pytest.raises(ValueRejected):
        canonical_value({"type": "text", "value": "x"}, expected=ValueType.CODE)


def test_predicate_key_grammar_and_release():
    key = PredicateKey.parse("sys:hasLegalName@v1")
    assert (key.namespace, key.local_name, key.major, str(key)) == (
        "sys",
        "hasLegalName",
        1,
        "sys:hasLegalName@v1",
    )
    for raw in ("hasLegalName", "sys:hasLegalName", "Sys:x@v1", "sys:x@v0", "sys:1x@v1", None, 7):
        with pytest.raises(SlotRejected) as rejected:
            PredicateKey.parse(raw)
        assert rejected.value.reason == SlotReason.PREDICATE_KEY_INVALID
    for raw in (None, "", " x", "a" * 129):
        with pytest.raises(SlotRejected):
            parse_release_ref(raw)


def test_qualifiers_canonical_rows_omitted_null_and_types():
    entity = uuid4()
    rows, entities = canonical_qualifiers(
        {
            "threshold": {"type": "decimal", "value": "1E+6"},
            "basis": {"type": "code", "value": "EachOccurrence"},
            "who": {"type": "entity_ref", "entity_id": str(entity)},
            "id": {
                "type": "identifier",
                "scheme": "carrier:A",
                "identifier_type": "policy-number",
                "value": "GL-1001",
            },
        },
        CONTRACT,
    )
    assert [r.name for r in rows] == ["basis", "id", "threshold", "who"]
    assert rows[0] == CanonicalQualifier("basis", ValueType.CODE, '"EachOccurrence"')
    assert rows[2].canonical == '"1000000"' and entities == (entity,)
    assert rows[1].canonical == (
        '{"identifier_type":"policy-number","normalized_value":"GL-1001","scheme":"carrier:A"}'
    )
    cases = [
        ({"basis": None}, SlotReason.QUALIFIER_NULL_REJECTED),
        ({}, SlotReason.QUALIFIER_REQUIRED),
        (
            {"basis": {"type": "code", "value": "x"}, "nope": {"type": "code", "value": "y"}},
            SlotReason.QUALIFIER_UNDECLARED,
        ),
        (
            {"basis": {"type": "code", "value": "x"}, "Bad": {"type": "code", "value": "y"}},
            SlotReason.QUALIFIER_UNDECLARED,
        ),
        ({"basis": {"type": "text", "value": "x"}}, SlotReason.QUALIFIER_TYPE_INVALID),
        (
            {
                "basis": {"type": "code", "value": "x"},
                "threshold": {"type": "decimal", "value": "1,0"},
            },
            SlotReason.DECIMAL_INVALID,
        ),
        (
            {"basis": {"type": "code", "value": "x"}, "note": {"type": "name", "verbatim": "x"}},
            SlotReason.QUALIFIER_TYPE_INVALID,
        ),
        ("not-a-map", SlotReason.QUALIFIER_TYPE_INVALID),
        (
            {f"q{i}": {"type": "code", "value": "x"} for i in range(17)},
            SlotReason.QUALIFIER_TYPE_INVALID,
        ),
    ]
    for raw, reason in cases:
        with pytest.raises(SlotRejected) as rejected:
            canonical_qualifiers(raw, CONTRACT)
        assert rejected.value.reason == reason, raw
    assert canonical_qualifiers(
        None,
        CONTRACT.__class__(
            key=CONTRACT.key, release_ref="r", cardinality="SINGLE", value_type=ValueType.TEXT
        ),
    ) == ((), ())


def test_fingerprint_document_excludes_release_and_cardinality():
    tenant, kb, subject = (UUID(int=1), UUID(int=2), UUID(int=3))
    rows, _ = canonical_qualifiers(
        {
            "basis": {"type": "code", "value": "EachOccurrence"},
            "currency": {"type": "code", "value": "USD"},
        },
        CONTRACT,
    )
    identity = SlotIdentity(tenant, kb, subject, CONTRACT.key, rows)
    document = identity.document()
    assert document == {
        "fp_version": 1,
        "tenant_id": str(tenant),
        "knowledge_base_id": str(kb),
        "subject_entity_id": str(subject),
        "predicate_key": "test:hasLimitAmount@v1",
        "qualifiers": [["basis", "code", '"EachOccurrence"'], ["currency", "code", '"USD"']],
        "object_entity_id": None,
        "parent_slot_id": None,
        "member_key": None,
    }
    assert identity.fingerprint() == hashlib.sha256(jcs(document)).hexdigest()
    reversed_rows = tuple(reversed(rows))
    assert SlotIdentity(tenant, kb, subject, CONTRACT.key, reversed_rows).fingerprint() == (
        identity.fingerprint()
    )
    member = SlotIdentity(
        tenant,
        kb,
        subject,
        CONTRACT.key,
        (),
        parent_slot_id=UUID(int=9),
        member_key="k",
        object_entity_id=UUID(int=8),
    )
    assert member.document()["parent_slot_id"] == str(UUID(int=9))
    with pytest.raises(SlotRejected) as rejected:
        PredicateContract(CONTRACT.key, "r", "PAIR", ValueType.TEXT).checked_cardinality()
    assert rejected.value.reason == SlotReason.CARDINALITY_INVALID


def test_member_keys():
    entity_contract = PredicateContract(
        CONTRACT.key, "r", Cardinality.MULTI, ValueType.ENTITY_REF, member_key_source="entity"
    )
    entity = str(uuid4())
    assert (
        member_key(canonical_value({"type": "entity_ref", "entity_id": entity}), entity_contract)
        == entity
    )
    with pytest.raises(SlotRejected):
        member_key(canonical_value({"type": "text", "value": "x"}), entity_contract)
    value_contract = PredicateContract(
        CONTRACT.key, "r", Cardinality.MULTI, ValueType.TEXT, member_key_source="value"
    )
    assert member_key(canonical_value({"type": "text", "value": "x"}), value_contract) == '"x"'
    name = canonical_value(
        {
            "type": "name",
            "verbatim": "Acme  Co",
            "evidence": {"assertion_id": str(uuid4()), "document_version_id": str(uuid4())},
        }
    )
    assert member_key(name, value_contract) == "acme co"


SCOPE = {
    "content_artifact_id": str(uuid4()),
    "profile_release_ref": "gl-policy-profile/1",
    "pages": [1, 2, 3],
}


def _answer(**fields):  # type: ignore[no-untyped-def]
    return {"answer_contract": "fact-answer/v1", **fields}


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ("x", AnswerReason.ANSWER_CONTRACT_UNSUPPORTED),
        ({"state": "PRESENT"}, AnswerReason.ANSWER_CONTRACT_UNSUPPORTED),
        (_answer(state="PRESENT", extra=1), AnswerReason.ANSWER_CONTRACT_UNSUPPORTED),
        (_answer(state="ACCESS_DENIED"), AnswerReason.INFORMATION_STATE_INVALID),
        (_answer(state="PRESENT"), AnswerReason.STATE_VALUE_MISMATCH),
        (
            _answer(state="NOT_STATED", value={"type": "text", "value": "x"}, scope=SCOPE),
            AnswerReason.STATE_VALUE_MISMATCH,
        ),
        (_answer(state="NOT_APPLICABLE", scope=SCOPE), AnswerReason.STATE_VALUE_MISMATCH),
        (_answer(state="NOT_FOUND"), AnswerReason.ABSENCE_SCOPE_REQUIRED),
        (
            _answer(state="NOT_FOUND", scope={**SCOPE, "pages": []}),
            AnswerReason.ABSENCE_SCOPE_REQUIRED,
        ),
        (
            _answer(state="NOT_FOUND", scope={**SCOPE, "pages": [0]}),
            AnswerReason.ABSENCE_SCOPE_REQUIRED,
        ),
        (
            _answer(state="NOT_FOUND", scope={**SCOPE, "pages": [1, 1]}),
            AnswerReason.ABSENCE_SCOPE_REQUIRED,
        ),
        (
            _answer(state="NOT_FOUND", scope={**SCOPE, "pages": [True]}),
            AnswerReason.ABSENCE_SCOPE_REQUIRED,
        ),
        (
            _answer(state="NOT_FOUND", scope={**SCOPE, "block_ids": ["x"]}),
            AnswerReason.ABSENCE_SCOPE_REQUIRED,
        ),
        (
            _answer(state="NOT_FOUND", scope={**SCOPE, "content_artifact_id": "x"}),
            AnswerReason.ABSENCE_SCOPE_REQUIRED,
        ),
        (
            _answer(state="NOT_FOUND", scope={**SCOPE, "profile_release_ref": "/x"}),
            AnswerReason.ABSENCE_SCOPE_REQUIRED,
        ),
        (
            _answer(state="NOT_FOUND", scope={**SCOPE, "other": 1}),
            AnswerReason.ABSENCE_SCOPE_REQUIRED,
        ),
        (_answer(state="NOT_FOUND", scope="pages 1-3"), AnswerReason.ABSENCE_SCOPE_REQUIRED),
        (
            _answer(state="PRESENT", value={"type": "text", "value": "x"}),
            AnswerReason.VALUE_TYPE_MISMATCH,
        ),
        (
            _answer(state="PRESENT", value={"type": "money", "amount": 5, "currency": "USD"}),
            AnswerReason.MONEY_FLOAT_REJECTED,
        ),
    ],
)
def test_answer_reasons_follow_precedence(raw, reason):
    with pytest.raises(FactAnswerRejected) as rejected:
        parse_answer(raw, value_type=ValueType.MONEY)
    assert rejected.value.reason == reason
    assert rejected.value.code == reason.value.lower()


def test_answer_multi_header_and_round_trip():
    with pytest.raises(FactAnswerRejected) as rejected:
        parse_answer(_answer(state="NOT_APPLICABLE"), value_type=ValueType.TEXT, multi_header=True)
    assert rejected.value.reason == AnswerReason.MULTI_SLOT_REQUIRES_MEMBER
    block = str(uuid4())
    scoped = parse_answer(
        _answer(state="NOT_STATED", scope={**SCOPE, "block_ids": [block]}),
        value_type=ValueType.MONEY,
    )
    assert scoped.scope.block_ids == (UUID(block),)
    assert stored_answer(scoped.to_json()) == scoped
    present = parse_answer(
        _answer(state="PRESENT", value={"type": "money", "amount": "1E+6", "currency": "USD"}),
        value_type=ValueType.MONEY,
    )
    assert present.to_json()["value"] == {"type": "money", "amount": "1000000", "currency": "USD"}
    assert stored_answer(present.to_json()).value == present.value
    assert present.name is None
    for state in ("ILLEGIBLE", "AMBIGUOUS", "CONFLICTING", "EXPLICIT_NEGATIVE"):
        assert parse_answer(_answer(state=state), value_type=ValueType.TEXT).scope is None
        assert parse_answer(
            _answer(state=state, scope=SCOPE), value_type=ValueType.TEXT
        ).state == InformationState(state)
    assert {s.value for s in InformationState} == {
        "PRESENT",
        "NOT_PROCESSED",
        "NOT_FOUND",
        "NOT_STATED",
        "ILLEGIBLE",
        "AMBIGUOUS",
        "CONFLICTING",
        "EXPLICIT_NEGATIVE",
        "NOT_APPLICABLE",
    }
