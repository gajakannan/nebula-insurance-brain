"""F0007 application services over an in-memory store: resolver branches, answer
policy, name hook and the predicate registry. Expectations from ADR-0077."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from brain_domain.authx import ResourceKey, ResourceType
from brain_domain.fact_answers import AnswerReason, FactAnswerRejected, InformationState
from brain_domain.fact_slots import Cardinality, PredicateKey, SlotReason, SlotRejected
from brain_factslots.answers import FactAnswerPolicy, FactAnswerReader
from brain_factslots.names import NameFactReader
from brain_factslots.predicates import (
    SYSTEM_PREDICATES,
    StaticPredicateRegistry,
    production_registry,
)
from brain_factslots.resolution import FactSlotResolver, ResolutionResult
from brain_testing.factslots import (
    ADDITIONAL_INSURED,
    LIMIT_AMOUNT,
    POLICY_NUMBER,
    RELATED_TO,
    slot_key,
    test_registry,
)

NOW = datetime(2026, 11, 9, tzinfo=UTC)
SOURCE = (ResourceKey(ResourceType.CONTENT_ARTIFACT, UUID(int=7)),)
BASIS = {"basis": {"type": "code", "value": "EachOccurrence"}}
LEGAL, TRADE, _FORMER, KNOWN = SYSTEM_PREDICATES


def _resolver(scene, **kwargs):  # type: ignore[no-untyped-def]
    return FactSlotResolver(test_registry(), scene.store, clock=lambda: NOW, **kwargs)


async def _resolve(scene, key, **kwargs):  # type: ignore[no-untyped-def]
    return await _resolver(scene, **kwargs).resolve(
        key, authorized_scope=(scene.tenant, scene.kb), source_keys=SOURCE, actor_id=uuid4()
    )


def _key(scene, predicate, **kwargs):  # type: ignore[no-untyped-def]
    return slot_key(scene.kb, scene.subject, predicate, **kwargs)


async def test_create_then_resolve_and_result_shape(scene):
    created = await _resolve(scene, _key(scene, LIMIT_AMOUNT, qualifiers=BASIS))
    again = await _resolve(scene, _key(scene, LIMIT_AMOUNT, qualifiers=BASIS))
    assert (created.outcome, again.outcome) == ("CREATED", "RESOLVED")
    assert created.target_slot_id == created.slot_id == again.slot_id
    assert created.to_json() == {
        "schema_version": 1,
        "outcome": "CREATED",
        "slot_id": str(created.slot_id),
        "predicate_key": "test:hasLimitAmount@v1",
        "cardinality": "SINGLE",
        "fingerprint_version": 1,
        "fingerprint": created.fingerprint,
    }
    assert scene.store.events == [("fact_slot_created", created.slot_id)]
    assert scene.store.access[created.slot_id] == (SOURCE, None)
    assert ResolutionResult.rejected(SlotReason.SUBJECT_NOT_FOUND).to_json() == {
        "schema_version": 1,
        "outcome": "REJECTED",
        "reason": "SUBJECT_NOT_FOUND",
    }


async def test_member_result_and_inheritance(scene):
    insured = scene.entity()
    result = await _resolve(
        scene,
        _key(scene, ADDITIONAL_INSURED, member={"type": "entity_ref", "entity_id": str(insured)}),
    )
    assert result.target_slot_id == result.member_slot_id
    body = result.to_json()
    assert body["member_slot_id"] == str(result.member_slot_id) and body["member_created"] is True
    assert scene.store.access[result.member_slot_id] == (SOURCE, result.slot_id)
    assert [e for e, _ in scene.store.events] == ["fact_slot_created", "fact_slot_member_created"]


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"schema_version": 2}, SlotReason.PREDICATE_KEY_INVALID),
        ({"tenant_id": str(uuid4())}, SlotReason.PREDICATE_KEY_INVALID),
        ({"subject_entity_id": "not-a-uuid"}, SlotReason.SUBJECT_NOT_FOUND),
        ({"knowledge_base_id": str(uuid4())}, SlotReason.SUBJECT_NOT_FOUND),
        ({"subject_entity_id": str(uuid4())}, SlotReason.SUBJECT_NOT_FOUND),
    ],
)
async def test_key_and_scope_rejections(scene, change, reason):
    with pytest.raises(SlotRejected) as rejected:
        await _resolve(scene, {**_key(scene, LIMIT_AMOUNT, qualifiers=BASIS), **change})
    assert rejected.value.reason == reason
    assert scene.store.slots == {}


async def test_non_mapping_key_and_bad_object(scene):
    with pytest.raises(SlotRejected) as rejected:
        await _resolve(scene, ["not", "a", "key"])
    assert rejected.value.reason == SlotReason.PREDICATE_KEY_INVALID
    with pytest.raises(SlotRejected) as rejected:
        await _resolve(scene, _key(scene, RELATED_TO, object_entity_id="nope"))
    assert rejected.value.reason == SlotReason.RELATIONSHIP_OBJECT_OUT_OF_SCOPE
    with pytest.raises(SlotRejected) as rejected:
        await _resolve(
            scene,
            _key(
                scene,
                LIMIT_AMOUNT,
                qualifiers={
                    **BASIS,
                    "location": {
                        "type": "entity_ref",
                        "entity_id": str(scene.entity(scene.other_kb)),
                    },
                },
            ),
        )
    assert rejected.value.reason == SlotReason.RELATIONSHIP_OBJECT_OUT_OF_SCOPE


async def test_collision_and_cardinality_conflict_roll_back(scene):
    def fixed(identity):  # type: ignore[no-untyped-def]
        return "f" * 64

    await _resolve(scene, _key(scene, LIMIT_AMOUNT, qualifiers=BASIS), fingerprint=fixed)
    before = dict(scene.store.slots)
    with pytest.raises(SlotRejected) as rejected:
        await _resolve(
            scene, _key(scene, RELATED_TO, object_entity_id=str(scene.entity())), fingerprint=fixed
        )
    assert rejected.value.reason == SlotReason.FINGERPRINT_COLLISION
    assert scene.store.slots == before
    # The same identity under a contract with another cardinality.
    await _resolve(scene, _key(scene, LIMIT_AMOUNT, qualifiers=BASIS))
    alt = replace(
        LIMIT_AMOUNT, release_ref="alt/1", cardinality=Cardinality.MULTI, member_key_source="value"
    )
    resolver = FactSlotResolver(test_registry([alt]), scene.store)
    with pytest.raises(SlotRejected) as rejected:
        await resolver.resolve(
            {
                **_key(scene, alt, qualifiers=BASIS),
                "member": {"type": "money", "amount": "1", "currency": "USD", "basis": "x"},
            },
            authorized_scope=(scene.tenant, scene.kb),
            source_keys=SOURCE,
            actor_id=uuid4(),
        )
    assert rejected.value.reason == SlotReason.CARDINALITY_CONFLICT


async def test_identifier_and_money_members(scene):
    a = await _resolve(
        scene,
        _key(
            scene,
            POLICY_NUMBER,
            member={
                "type": "identifier",
                "scheme": "carrier:A",
                "identifier_type": "policy-number",
                "value": "GL-1001",
            },
        ),
    )
    b = await _resolve(
        scene,
        _key(
            scene,
            POLICY_NUMBER,
            member={
                "type": "identifier",
                "scheme": "carrier:B",
                "identifier_type": "policy-number",
                "value": "GL-1001",
            },
        ),
    )
    assert a.slot_id == b.slot_id and a.member_slot_id != b.member_slot_id
    with pytest.raises(SlotRejected) as rejected:
        await _resolve(
            scene,
            _key(
                scene,
                POLICY_NUMBER,
                member={
                    "type": "identifier",
                    "scheme": "carrier:A",
                    "identifier_type": "policy-number",
                    "value": "",
                },
            ),
        )
    assert rejected.value.reason == SlotReason.IDENTIFIER_INVALID


async def test_name_members_require_evidence(scene):
    assertion, version = uuid4(), uuid4()
    name = {
        "type": "name",
        "verbatim": "Acme Storm",
        "evidence": {"assertion_id": str(assertion), "document_version_id": str(version)},
    }
    with pytest.raises(SlotRejected) as rejected:
        await _resolve(scene, _key(scene, TRADE, member=name))
    assert rejected.value.reason == SlotReason.NAME_EVIDENCE_REQUIRED
    scene.store.evidence[assertion] = (version, (scene.tenant, scene.kb), (UUID(int=7),))
    member = await _resolve(scene, _key(scene, TRADE, member=name))
    assert scene.store.slots[member.member_slot_id].member_key == "acme storm"


def test_registry_rules():
    registry = production_registry()
    assert (
        registry.contract(
            PredicateKey.parse("sys:knownAs@v1"), "f0007-system-predicates/1"
        ).cardinality
        == Cardinality.MULTI
    )
    with pytest.raises(SlotRejected) as rejected:
        registry.contract(PredicateKey.parse("test:hasLimitAmount@v1"), "f0007-fixtures/1")
    assert rejected.value.reason == SlotReason.PREDICATE_UNREGISTERED
    with pytest.raises(SlotRejected) as rejected:
        StaticPredicateRegistry([replace(LEGAL, cardinality=Cardinality.MULTI)])
    assert rejected.value.reason == SlotReason.CARDINALITY_CONFLICT
    with pytest.raises(SlotRejected):
        StaticPredicateRegistry([replace(LEGAL, key=PredicateKey("sys", "invented", 1))])


async def _policy_slot(scene, predicate=LIMIT_AMOUNT, **kwargs):  # type: ignore[no-untyped-def]
    result = await _resolve(scene, _key(scene, predicate, **kwargs))
    return result.target_slot_id


async def test_answer_policy_paths(scene):
    policy = FactAnswerPolicy(test_registry(), scene.store)
    owner = (scene.tenant, scene.kb)
    slot = await _policy_slot(scene, qualifiers=BASIS)
    assert await policy.canonical_value(uuid4(), {}, authorized_scope=owner) is None
    artifact, foreign = uuid4(), uuid4()
    scene.store.artifacts[artifact] = owner
    scene.store.artifacts[foreign] = (scene.tenant, scene.other_kb)
    scope = {"content_artifact_id": str(artifact), "profile_release_ref": "p/1", "pages": [1]}
    envelope = {"answer_contract": "fact-answer/v1", "state": "NOT_FOUND", "scope": scope}
    assert await policy.canonical_value(slot, envelope, authorized_scope=owner) == envelope
    assert await policy.source_keys(slot, envelope) == (
        ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact),
    )
    with pytest.raises(FactAnswerRejected) as rejected:
        await policy.canonical_value(
            slot,
            {**envelope, "scope": {**scope, "content_artifact_id": str(foreign)}},
            authorized_scope=owner,
        )
    assert rejected.value.reason == AnswerReason.ABSENCE_SCOPE_OUT_OF_SCOPE
    # The deployed registry no longer has the slot's contract.
    production = FactAnswerPolicy(production_registry(), scene.store)
    with pytest.raises(FactAnswerRejected) as rejected:
        await production.canonical_value(slot, envelope, authorized_scope=owner)
    assert rejected.value.reason == AnswerReason.ANSWER_CONTRACT_UNSUPPORTED
    # Malformed values add no read keys; legacy and missing slots add none either.
    assert (
        await policy.source_keys(slot, {"scope": {"content_artifact_id": "x"}, "value": "x"}) == ()
    )
    assert await policy.source_keys(uuid4(), envelope) == ()


async def test_answer_policy_names_and_entity_refs(scene):
    policy = FactAnswerPolicy(test_registry(), scene.store)
    owner = (scene.tenant, scene.kb)
    legal = await _policy_slot(scene, LEGAL)
    assertion, version, artifact = uuid4(), uuid4(), uuid4()
    name = {
        "type": "name",
        "verbatim": "Acme Roofing Inc.",
        "evidence": {"assertion_id": str(assertion), "document_version_id": str(version)},
    }
    envelope = {"answer_contract": "fact-answer/v1", "state": "PRESENT", "value": name}
    with pytest.raises(FactAnswerRejected) as rejected:
        await policy.canonical_value(legal, envelope, authorized_scope=owner)
    assert rejected.value.reason == AnswerReason.NAME_EVIDENCE_REQUIRED
    assert await policy.source_keys(legal, envelope) == ()
    scene.store.evidence[assertion] = (version, owner, (artifact,))
    stored = await policy.canonical_value(legal, envelope, authorized_scope=owner)
    assert stored["value"]["normalized"] == "acme roofing inc."
    assert await policy.source_keys(legal, envelope) == (
        ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact),
    )
    member = await _policy_slot(
        scene, ADDITIONAL_INSURED, member={"type": "entity_ref", "entity_id": str(scene.entity())}
    )
    outside = {
        "answer_contract": "fact-answer/v1",
        "state": "PRESENT",
        "value": {"type": "entity_ref", "entity_id": str(scene.entity(scene.other_kb))},
    }
    with pytest.raises(FactAnswerRejected) as rejected:
        await policy.canonical_value(member, outside, authorized_scope=owner)
    assert rejected.value.reason == AnswerReason.RELATIONSHIP_OBJECT_OUT_OF_SCOPE


async def test_present_entity_answer_must_match_the_immutable_member_key(scene):
    policy = FactAnswerPolicy(test_registry(), scene.store)
    owner = (scene.tenant, scene.kb)
    insured = scene.entity()
    member = await _policy_slot(
        scene, ADDITIONAL_INSURED, member={"type": "entity_ref", "entity_id": str(insured)}
    )
    envelope = {
        "answer_contract": "fact-answer/v1",
        "state": "PRESENT",
        "value": {"type": "entity_ref", "entity_id": str(insured)},
    }
    assert await policy.canonical_value(member, envelope, authorized_scope=owner) == envelope
    other = {**envelope, "value": {"type": "entity_ref", "entity_id": str(scene.entity())}}
    with pytest.raises(FactAnswerRejected) as rejected:
        await policy.canonical_value(member, other, authorized_scope=owner)
    assert rejected.value.code == "member_value_mismatch"
    assert scene.store.slots[member].member_key == str(insured)
    assert await policy.canonical_value(
        member,
        {"answer_contract": "fact-answer/v1", "state": "NOT_APPLICABLE"},
        authorized_scope=owner,
    ) == {"answer_contract": "fact-answer/v1", "state": "NOT_APPLICABLE"}


async def test_name_member_accepts_equivalent_spelling_and_rejects_a_different_name(scene):
    policy = FactAnswerPolicy(test_registry(), scene.store)
    owner = (scene.tenant, scene.kb)
    assertion, version = uuid4(), uuid4()
    scene.store.evidence[assertion] = (version, owner, ())
    evidence = {"assertion_id": str(assertion), "document_version_id": str(version)}
    value = {"type": "name", "verbatim": "Acme Restoration", "evidence": evidence}
    member = await _policy_slot(scene, TRADE, member=value)
    envelope = {"answer_contract": "fact-answer/v1", "state": "PRESENT", "value": value}
    equivalent = {**value, "verbatim": "  ACME   restoration "}
    accepted = await policy.canonical_value(
        member, {**envelope, "value": equivalent}, authorized_scope=owner
    )
    assert accepted["value"]["normalized"] == "acme restoration"
    with pytest.raises(FactAnswerRejected) as rejected:
        await policy.canonical_value(
            member,
            {**envelope, "value": {**value, "verbatim": "Zed Services"}},
            authorized_scope=owner,
        )
    assert rejected.value.code == "member_value_mismatch"
    assert scene.store.slots[member].member_key == "acme restoration"


async def test_identifier_member_uses_normalized_value_and_keeps_issuer_identity(scene):
    policy = FactAnswerPolicy(test_registry(), scene.store)
    owner = (scene.tenant, scene.kb)
    value = {
        "type": "identifier",
        "scheme": "us-irs",
        "identifier_type": "fein",
        "value": "12-3456789",
    }
    member = await _policy_slot(scene, POLICY_NUMBER, member=value)
    envelope = {"answer_contract": "fact-answer/v1", "state": "PRESENT", "value": value}
    accepted = await policy.canonical_value(
        member, {**envelope, "value": {**value, "value": "123456789"}}, authorized_scope=owner
    )
    assert accepted["value"]["normalized_value"] == "123456789"
    for changed in ({"scheme": "carrier:B"}, {"value": "987654321"}):
        with pytest.raises(FactAnswerRejected) as rejected:
            await policy.canonical_value(
                member, {**envelope, "value": {**value, **changed}}, authorized_scope=owner
            )
        assert rejected.value.code == "member_value_mismatch"


async def test_reader_and_name_hook(scene):
    reader = FactAnswerReader(scene.store)
    with pytest.raises(LookupError):
        await reader.read(uuid4(), valid_at=NOW, known_at=NOW)
    legal = await _policy_slot(scene, LEGAL)
    assert (await reader.read(legal, valid_at=NOW, known_at=NOW)).state == (
        InformationState.NOT_PROCESSED
    )
    assertion, version = uuid4(), uuid4()
    scene.store.evidence[assertion] = (version, (scene.tenant, scene.kb), ())
    policy = FactAnswerPolicy(test_registry(), scene.store)

    async def name(slot, verbatim):  # type: ignore[no-untyped-def]
        scene.store.answers[slot] = await policy.canonical_value(
            slot,
            {
                "answer_contract": "fact-answer/v1",
                "state": "PRESENT",
                "value": {
                    "type": "name",
                    "verbatim": verbatim,
                    "evidence": {
                        "assertion_id": str(assertion),
                        "document_version_id": str(version),
                    },
                },
            },
            authorized_scope=(scene.tenant, scene.kb),
        )

    await name(legal, "Acme Roofing Inc.")
    known = await _policy_slot(
        scene,
        KNOWN,
        member={
            "type": "name",
            "verbatim": "ACME",
            "evidence": {"assertion_id": str(assertion), "document_version_id": str(version)},
        },
    )
    await name(known, "ACME")
    absent = await _policy_slot(
        scene,
        TRADE,
        member={
            "type": "name",
            "verbatim": "Zed",
            "evidence": {"assertion_id": str(assertion), "document_version_id": str(version)},
        },
    )
    scene.store.answers[absent] = {"answer_contract": "fact-answer/v1", "state": "NOT_APPLICABLE"}
    names = NameFactReader(scene.store)
    facts = await names.current_names(
        authorized_scope=(scene.tenant, scene.kb),
        entity_id=scene.subject,
        valid_at=NOW,
        known_at=NOW,
    )
    assert [(f.predicate_key, f.verbatim, f.normalized) for f in facts] == [
        ("sys:hasLegalName@v1", "Acme Roofing Inc.", "acme roofing inc."),
        ("sys:knownAs@v1", "ACME", "acme"),
    ]
    assert await names.name_fact(uuid4(), valid_at=NOW, known_at=NOW) is None
    # A legacy slot reads its raw value under a legacy label.
    legacy = uuid4()
    from brain_factslots.ports import StoredSlot

    scene.store.slots[legacy] = StoredSlot(legacy, scene.tenant, scene.kb, scene.subject, "pilot")
    assert (await reader.read(legacy, valid_at=NOW, known_at=NOW)).state == (
        InformationState.NOT_PROCESSED
    )
    scene.store.answers[legacy] = {"amount": 1}
    pilot = await reader.read(legacy, valid_at=NOW, known_at=NOW)
    assert pilot.legacy_value == {"amount": 1}
    assert (
        await FactAnswerPolicy(test_registry(), scene.store).canonical_value(
            legacy, {"amount": 2}, authorized_scope=(scene.tenant, scene.kb)
        )
        is None
    )


async def test_g3_evidence_and_payload_scope_keys(scene):
    resolver = _resolver(scene)
    assertion, version, artifact = uuid4(), uuid4(), uuid4()
    scene.store.evidence[assertion] = (version, (scene.tenant, scene.kb), (artifact,))
    name = {
        "type": "name",
        "verbatim": "Acme",
        "evidence": {"assertion_id": str(assertion), "document_version_id": str(version)},
    }
    key = _key(scene, TRADE, member=name)
    assert await resolver.evidence_source_keys(key) == (
        ResourceKey(ResourceType.CONTENT_ARTIFACT, artifact),
    )
    for other in (
        None,
        [],
        _key(scene, LIMIT_AMOUNT),
        {"member": {"type": "name"}},
        {"member": {"type": "name", "evidence": {"assertion_id": "x"}}},
    ):
        assert await resolver.evidence_source_keys(other) == ()
    reader = FactAnswerReader(scene.store)
    slot = await _policy_slot(scene, qualifiers=BASIS)
    assert await reader.scope_keys_for_value(slot, None) == ()
    scope_artifact = uuid4()
    payload = {
        "answer_contract": "fact-answer/v1",
        "state": "NOT_FOUND",
        "scope": {"content_artifact_id": str(scope_artifact)},
    }
    # The selected payload determines the scope, even if the store now has
    # another answer. Permission checks must not select the answer a second time.
    scene.store.answers[slot] = {"scope": {"content_artifact_id": str(uuid4())}}
    assert await reader.scope_keys_for_value(slot, payload) == (
        ResourceKey(ResourceType.CONTENT_ARTIFACT, scope_artifact),
    )
    assert await reader.scope_keys_for_value(uuid4(), payload) == ()
