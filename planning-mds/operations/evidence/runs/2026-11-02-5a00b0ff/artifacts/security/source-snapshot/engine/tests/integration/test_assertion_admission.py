"""Observed F0006 service/PG behavior over independently authored retained sources."""

import asyncio
import copy
from dataclasses import replace
from uuid import UUID, uuid4

import pytest
from brain_domain.assertions import TimeReference
from brain_persistence.assertion_models import AssertionSemantics
from brain_persistence.models import ReviewItemRow
from brain_security.execution import AuthorizationDenied
from engine.tests.fixtures.assertions import harness
from sqlalchemy import event
from sqlalchemy.orm import Session

_clean_fact_tables = harness._clean_fact_tables
database = harness.database
world = harness.world
world_factory = harness.world_factory
counts = harness.counts
configuration = harness.configuration


async def test_typed_competing_claims_reload_without_canonical_effects(world, database):
    first = world.candidate(interpretation_basis="INFERRED", model_confidence=0.91)
    second = world.candidate(
        object={"kind": "LITERAL", "value": {"amount": 1000000}},
        interpretation_basis="AMBIGUOUS",
        model_confidence=None,
    )
    batch = await world.admit([first, second])
    assert len(batch.accepted) == 2 and not batch.outcomes
    async with world.service() as (service, _, _):
        a = await service.read(world.reviewer, UUID(first["id"]))
        b = await service.read(world.reviewer, UUID(second["id"]))
    assert a["record"] == first and b["record"] == second
    assert a["created_by"] == str(world.actor.id)
    assert a["record"]["model_confidence"] == 0.91
    assert b["interpretation_basis"] == "AMBIGUOUS" and b["model_confidence"] is None
    state = counts(database)
    assert state["assertion"] == state["assertion_semantics"] == state["assertion_evidence"] == 2
    assert state["canonical_commit"] == state["canonical_fact_version"] == 0


async def test_two_sources_retain_five_and_ten_million_claims(world_factory, database):
    first = world_factory(text="Cedar Bridge Roofing has a limit of $5,000,000.")
    second = world_factory(
        text="Cedar Bridge Roofing has a limit of $10,000,000.", owner=first.owner
    )
    for world, amount in ((first, 5000000), (second, 10000000)):
        record = world.candidate(object={"kind": "LITERAL", "value": {"amount": amount}})
        admitted = (await world.admit([record])).accepted[0]
        async with world.service() as (service, _, _):
            loaded = await service.read(world.reviewer, admitted.record.id)
        assert loaded["record"] == record
        assert loaded["record"]["subject_ref"] == world.entity["id"]
        assert loaded["record"]["evidence"][0]["artifact_id"] == str(world.bundle.key.artifact_id)
    assert first.bundle.key.artifact_id != second.bundle.key.artifact_id
    assert first.subject_id != second.subject_id  # local identities never silently merge
    state = counts(database)
    assert state["assertion"] == state["assertion_evidence"] == 2
    assert state["canonical_commit"] == state["canonical_fact_version"] == 0


async def test_declared_entity_object_and_time_reference_survive_reload(world_factory):
    world = world_factory(
        text="Cedar Bridge Roofing is insured by Harbor Insurance effective 2026-06-01."
    )
    object_id, time_id = uuid4(), uuid4()
    entity = {
        "id": str(object_id),
        "entity_type": "Carrier",
        "label": "Harbor Insurance",
        "introducing_evidence": [world.evidence(world.text)],
    }
    record = world.candidate(
        assertion_kind="OPEN_STATEMENT",
        predicate_id=None,
        ontology_release=None,
        source_relation="is insured by",
        object={"kind": "ENTITY", "ref": str(object_id), "name": "Harbor Insurance"},
        qualifiers={"role": "insured"},
        time_mention_refs=[str(time_id)],
    )

    async def resolve(context, identifier):
        assert context == world.context and identifier == time_id
        return TimeReference(
            time_id, *world.owner, world.bundle.key.artifact_id, "#/texts/0", "2026-06-01"
        )

    admitted = await world.admit([record], entities=[world.entity, entity], time_resolver=resolve)
    assert not admitted.outcomes and len(admitted.accepted) == 1
    async with world.service() as (service, _, _):
        loaded = await service.read(world.reviewer, UUID(record["id"]))
    assert loaded["record"] == record
    with Session(world.sync_engine) as session:
        sem = session.get(AssertionSemantics, UUID(record["id"]))
        assert {e["id"] for e in sem.entity_snapshots} == {world.entity["id"], str(object_id)}
        assert sem.time_reference_snapshot[0]["words"] == "2026-06-01"


async def test_foreign_time_reference_fails_without_claim_effects(world, database):
    identifier = uuid4()

    async def foreign_time(context, ref):
        return TimeReference(ref, uuid4(), uuid4(), context.artifact_id, "#/texts/0", "2026-06-01")

    before = counts(database)
    with pytest.raises(PermissionError, match="scope mismatch"):
        await world.admit(
            [world.candidate(time_mention_refs=[str(identifier)])], time_resolver=foreign_time
        )
    assert counts(database) == before


async def test_open_storage_and_replay_are_lossless(world, database):
    record = world.candidate(
        assertion_kind="OPEN_STATEMENT",
        predicate_id=None,
        ontology_release=None,
        source_relation="has a limit of",
        object={"kind": "LITERAL", "value": "$500,000"},
        qualifiers={"mood": "offered subject to inspection"},
    )
    first = await world.admit([record])
    second = await world.admit([record])
    assert first.accepted[0].created_at == second.accepted[0].created_at
    assert set(second.accepted[0].blocked_operations) == {
        "RESOLVE",
        "CREATE",
        "AUTO_ACCEPT",
        "CLOSE",
        "SUPERSEDE",
    }
    async with world.service() as (service, _, _):
        loaded = await service.read(world.reviewer, UUID(record["id"]))
    assert loaded["record"] == record and "slot_type" not in loaded
    assert counts(database)["assertion"] == 1


@pytest.mark.parametrize("kind", ["pdf", "docx", "xlsx", "csv"])
async def test_native_formats_derive_locations_from_verified_stored_content(world_factory, kind):
    world = world_factory(kind=kind)
    record = world.candidate()
    batch = await world.admit([record])
    evidence = batch.accepted[0].server_evidence[0]
    assert evidence.selector["format"] == kind
    assert evidence.selector.get("char_start", 0) != 99999
    assert evidence.quote == world.text
    assert evidence.text_origin == "STATED" and evidence.origin_qualification == "qualified"


@pytest.mark.parametrize("origin", ["DESCRIBED", "OCR", "TRANSCRIBED"])
async def test_actual_block_origin_and_producer_confidence_are_retained(world_factory, origin):
    world = world_factory(origin=origin)
    batch = await world.admit([world.candidate()])
    evidence = batch.accepted[0].server_evidence[0]
    assert evidence.text_origin == origin
    if origin == "DESCRIBED":
        assert batch.accepted[0].review_required
        assert "DESCRIBED_EVIDENCE" in batch.accepted[0].reasons
    else:
        assert evidence.producer_confidence == 0.87


async def test_name_conflict_does_not_reserve_failed_references(world, database):
    assert len((await world.admit([world.candidate()])).accepted) == 1
    before = counts(database)
    entity = copy.deepcopy(world.entity)
    entity["id"] = str(uuid4())
    record = world.candidate(subject_ref=entity["id"])
    rejected = await world.admit([record], entities=[entity])
    assert not rejected.accepted
    assert [o.reason for o in rejected.outcomes] == ["NAME_CLAIMED_BY_ANOTHER"]
    assert counts(database) == before


async def test_unauthorized_producer_and_cross_scope_context_have_no_claim_effects(world, database):
    before = counts(database)
    with pytest.raises(AuthorizationDenied):
        await world.admit(
            [world.candidate()],
            principal=world.reviewer,
            context=replace(world.context, actor_id=world.reviewer.id),
        )
    with pytest.raises(PermissionError):
        await world.admit([world.candidate()], context=replace(world.context, tenant_id=uuid4()))
    assert counts(database) == before


async def test_review_failure_rolls_back_claim_evidence_names_and_retry(world, database):
    before = counts(database)
    record = world.candidate(qualifiers={"mood": "subject to inspection"})

    def fail_review(*_args):
        raise RuntimeError("synthetic review insert failure")

    event.listen(ReviewItemRow, "before_insert", fail_review)
    try:
        with pytest.raises(RuntimeError, match="synthetic review"):
            await world.admit([record])
    finally:
        event.remove(ReviewItemRow, "before_insert", fail_review)
    assert counts(database) == before
    assert len((await world.admit([record])).accepted) == 1
    assert len((await world.admit([record])).accepted) == 1
    assert counts(database)["assertion"] == 1


async def test_partial_output_keeps_valid_siblings_and_explicit_outcomes(world, database):
    batch = await world.admit(
        [world.candidate(), b"{"], truncated=True, uninterpreted_blocks=["missing-block"]
    )
    assert len(batch.accepted) == 1 and batch.requires_partial
    assert {o.reason for o in batch.outcomes} == {
        "MALFORMED_ITEM",
        "TRUNCATED_OUTPUT",
        "BLOCK_UNINTERPRETED",
    }
    assert counts(database)["assertion"] == 1


async def test_dimensions_round_trip_independently_with_confidence_boundaries(world, database):
    origins = (
        "DOCUMENT_INTERPRETATION",
        "SYSTEM_OBSERVATION",
        "HUMAN_REVIEW",
        "CONVERSATION_DISCOVERY",
        "RULE_DERIVATION",
        "AGENT_ANALYSIS",
    )
    for index, origin in enumerate(origins):
        for mode in ("ASSERTED", "OBSERVED", "DERIVED"):
            for basis in ("EXPLICIT", "INFERRED", "AMBIGUOUS"):
                confidence = (None, 0.0, 1.0)[index % 3]
                record = world.candidate(
                    origin=origin,
                    mode=mode,
                    interpretation_basis=basis,
                    model_confidence=confidence,
                )
                batch = await world.admit([record], context=replace(world.context, origin=origin))
                assert batch.accepted[0].record.model_dump(mode="json") == record
    assert counts(database)["assertion"] == 54
    assert counts(database)["canonical_fact_version"] == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"mode": "UNKNOWN"},
        {"origin": "MACHINE_EXTRACTION"},
        {"interpretation_basis": "CERTAIN"},
        {"model_confidence": -0.01},
        {"model_confidence": 1.01},
        {"model_confidence": float("nan")},
        {"assertion_kind": "OPEN_STATEMENT", "predicate_id": "invented"},
    ],
)
async def test_invalid_dimensions_and_confidence_have_zero_claim_effects(world, database, changes):
    before = counts(database)
    batch = await world.admit([world.candidate(**changes)])
    assert not batch.accepted and {o.reason for o in batch.outcomes} == {"MALFORMED_ITEM"}
    assert counts(database) == before


async def test_concurrent_document_name_claims_have_one_owner(world, database):
    first_entity, second_entity = copy.deepcopy(world.entity), copy.deepcopy(world.entity)
    second_entity["id"] = str(uuid4())
    results = await asyncio.gather(
        world.admit([world.candidate()], entities=[first_entity]),
        world.admit([world.candidate(subject_ref=second_entity["id"])], entities=[second_entity]),
    )
    assert sum(len(batch.accepted) for batch in results) == 1
    assert [o.reason for batch in results for o in batch.outcomes] == ["NAME_CLAIMED_BY_ANOTHER"]
    assert (
        counts(database)["assertion_document_reference"]
        == counts(database)["assertion_name_claim"]
        == 1
    )
