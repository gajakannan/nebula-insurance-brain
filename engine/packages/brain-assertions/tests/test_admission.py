from hashlib import sha256
from uuid import uuid4

import pytest
from brain_assertions.admission import AssertionAdmissionService
from brain_contracts.assertions import canonical_json
from brain_domain.assertions import ProducerContext, TimeReference, VerifiedBlock


class Sources:
    def __init__(self, context, text):
        self.context = context
        self.text = text
        self.calls = []
        self.time = {}
        self.denied = False

    async def block(self, context, block_id):
        self.calls.append(block_id)
        if self.denied:
            raise PermissionError("source denied")
        if block_id != "b":
            raise LookupError("unknown block")
        return VerifiedBlock(
            context.artifact_id,
            block_id,
            self.text,
            {"block_id": block_id, "native_ref": "#/texts/0"},
            "STATED",
            "qualified",
            None,
            None,
        )

    async def time_reference(self, context, ref):
        if ref not in self.time:
            raise LookupError("unknown reference")
        return self.time[ref]


@pytest.fixture
def sample():
    context = ProducerContext(
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
        "DOCUMENT_INTERPRETATION",
        "fixture-no-model",
        "fixture-prompt",
        "fixture-trace",
    )
    text = "Cedar has a limit of $500,000 effective June 1."
    sources = Sources(context, text)
    entity_id = uuid4()
    evidence = {
        "artifact_id": str(context.artifact_id),
        "block_id": "b",
        "quote": text,
        "model_selector": {"char_start": 9000, "char_end": 9999},
    }
    entity = {
        "id": str(entity_id),
        "entity_type": "Policy",
        "label": "Cedar",
        "introducing_evidence": [evidence],
    }
    record = {
        "id": str(uuid4()),
        "assertion_kind": "TYPED_ASSERTION",
        "subject_ref": str(entity_id),
        "object": {"kind": "LITERAL", "value": {"amount": 5000000}},
        "predicate_id": "limit",
        "ontology_release": "fixture-v1",
        "source_relation": None,
        "qualifiers": {},
        "time_mention_refs": [],
        "valid_time_claim": None,
        "mode": "ASSERTED",
        "origin": context.origin,
        "interpretation_basis": "INFERRED",
        "model_confidence": 0.75,
        "evidence": [evidence],
    }
    return context, sources, entity, record


async def test_genuine_quote_keeps_misread_value_without_claiming_semantic_truth(sample):
    context, sources, entity, record = sample
    raw = canonical_json(record)
    batch = await AssertionAdmissionService(sources).check_items(context, [entity], [raw])
    assert batch.accepted[0].record.object.value == {"amount": 5000000}
    assert batch.accepted[0].record.interpretation_basis == "INFERRED"
    assert batch.accepted[0].metadata.raw_item_sha256 == sha256(raw).hexdigest()
    assert batch.accepted[0].server_evidence[0].selector["char_start"] == 0
    assert batch.accepted[0].server_evidence[0].selector["char_end"] == len(sources.text)
    assert sources.calls == ["b"]


async def test_all_structural_failures_and_partial_outcomes_survive(sample):
    context, sources, entity, record = sample
    time_id = uuid4()
    sources.time[time_id] = TimeReference(
        time_id,
        context.tenant_id,
        context.knowledge_base_id,
        context.artifact_id,
        "b",
        "December 31",
    )
    record["time_mention_refs"] = [str(time_id)]
    record["evidence"][0] = {**record["evidence"][0], "quote": "Cedar invented quote"}
    entity["label"] = "Missing Name"
    batch = await AssertionAdmissionService(sources).check_items(
        context,
        [entity],
        [canonical_json(record), b'{"broken":'],
        truncated=True,
        uninterpreted_blocks=["lost-block"],
    )
    assert not batch.accepted and batch.requires_partial
    assert {o.reason for o in batch.outcomes} == {
        "NAME_NOT_IN_QUOTE",
        "QUOTE_NOT_IN_SOURCE",
        "TIME_NOT_IN_QUOTE",
        "MALFORMED_ITEM",
        "TRUNCATED_OUTPUT",
        "BLOCK_UNINTERPRETED",
    }
    assert all(
        o.model_id == context.model_id and o.prompt_hash == context.prompt_hash
        for o in batch.outcomes
    )


async def test_partial_batch_retains_independent_complete_items(sample):
    context, sources, entity, record = sample
    batch = await AssertionAdmissionService(sources).check_items(
        context,
        [entity],
        [canonical_json(record), b"{"],
        truncated=True,
    )
    assert [str(item.record.id) for item in batch.accepted] == [record["id"]]
    assert {o.reason for o in batch.outcomes} == {"MALFORMED_ITEM", "TRUNCATED_OUTPUT"}


async def test_undeclared_named_object_is_retained_as_literal_signal(sample):
    context, sources, entity, record = sample
    record["object"] = {"kind": "ENTITY", "ref": str(uuid4()), "name": "Cedar"}
    batch = await AssertionAdmissionService(sources).check_items(
        context, [entity], [canonical_json(record)]
    )
    assert batch.accepted[0].record.object.value == "Cedar"
    assert [(o.disposition, o.reason) for o in batch.outcomes] == [("SIGNAL", "OBJECT_UNDECLARED")]


async def test_unknown_subject_and_time_are_not_dropped_silently(sample):
    context, sources, entity, record = sample
    record.update(subject_ref=str(uuid4()), time_mention_refs=[str(uuid4())])
    batch = await AssertionAdmissionService(sources).check_items(
        context, [entity], [canonical_json(record)]
    )
    assert not batch.accepted
    assert len([o for o in batch.outcomes if o.reason == "UNKNOWN_REFERENCE"]) == 2


async def test_foreign_evidence_is_rejected_before_the_source_port(sample):
    context, sources, entity, record = sample
    record["evidence"][0] = {**record["evidence"][0], "artifact_id": str(uuid4())}
    entity["introducing_evidence"] = record["evidence"]
    batch = await AssertionAdmissionService(sources).check_items(
        context, [entity], [canonical_json(record)]
    )
    assert not batch.accepted and not sources.calls
    assert {o.reason for o in batch.outcomes} == {"UNKNOWN_REFERENCE"}


async def test_source_authorization_and_infrastructure_errors_abort_batch(sample):
    context, sources, entity, record = sample
    sources.denied = True
    with pytest.raises(PermissionError):
        await AssertionAdmissionService(sources).check_items(
            context, [entity], [canonical_json(record)]
        )


async def test_model_offsets_do_not_disambiguate_repeated_text(sample):
    context, sources, entity, record = sample
    sources.text += " " + sources.text
    batch = await AssertionAdmissionService(sources).check_items(
        context, [entity], [canonical_json(record)]
    )
    locator = batch.accepted[0].server_evidence[0]
    assert locator.precision == "block" and "char_start" not in locator.selector
