"""F0012-S0005 on PostgreSQL: release-backed predicates and ETERNAL/EVENT/STATE
commits through the real route (AC1-AC6). Fresh-session proof throughout."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from brain_domain.fact_slots import SlotReason
from brain_factslots.predicates import SYSTEM_RELEASE
from engine.tests.fixtures import ontology as fx
from engine.tests.fixtures.factslots.harness import _clean_fact_tables, database

onto_world = fx.onto_world
builder = fx.builder
__all__ = ["_clean_fact_tables", "database"]

ENVELOPE = "fact-answer/v1"
ORG_KEY = "fnd:accountOrganization@v1"


def key(
    w: Any,
    predicate: str,
    release: str,
    subject: UUID | None = None,
    owner: Any = None,
    **extra: Any,
) -> dict:
    owner = owner or w.a
    return {
        "schema_version": 1,
        "knowledge_base_id": str(owner.knowledge_base_id),
        "subject_entity_id": str(subject or w.subject),
        "predicate_key": predicate,
        "predicate_release_ref": release,
        "qualifiers": {},
        **extra,
    }


async def resolve(w: Any, k: dict, *, owner: Any = None, principal: Any = None) -> Any:
    owner = owner or w.a
    async with w.release_slots() as service:
        return await service.resolve(
            principal or w.service, k, source_artifact_ids=[owner.artifact_id], trace_id="f0012"
        )


def present(value: dict) -> dict:
    return {"answer_contract": ENVELOPE, "state": "PRESENT", "value": value}


def entity(entity_id: UUID) -> dict:
    return {"type": "entity_ref", "entity_id": str(entity_id)}


async def commit(w: Any, slot_id: UUID, value: dict, temporal: dict, principal: Any = None) -> Any:
    now = datetime.now(UTC).isoformat()
    body = {
        "value": value,
        "temporal": temporal,
        "change_reason": None,
        "evidence_refs": [],
        "review_decision_id": None,
        "source_received_at": now,
        "artifact_created_at": now,
        "assertion_created_at": now,
        "expected_current_version_id": None,
        "idempotency_key": f"f0012-{uuid4()}",
    }
    async with w.release_client(principal or w.service) as client:
        return await client.post(f"/facts/{slot_id}/commits", json=body)


ETERNAL = {"contract": "fact-temporal/v1", "valid_to_state": "OPEN"}


def day(start: str, end: str | None = None, *, granularity: str = "DAY") -> dict:
    temporal: dict[str, Any] = {
        "contract": "fact-temporal/v1",
        "valid_from": {"instant": start, "granularity": granularity, "zone": "UTC"},
        "valid_from_basis": "TEMPLATE_FIELD",
        "valid_to_state": "OPEN" if end is None else "BOUNDED",
    }
    if end is not None:
        temporal["valid_to"] = {"instant": end, "granularity": granularity, "zone": "UTC"}
    return temporal


async def test_ac2_registry_serves_installed_releases_of_the_scope_only(onto_world: Any) -> None:
    w = onto_world
    release = fx.foundation()
    before = await resolve(w, key(w, ORG_KEY, release.ref))
    assert before.outcome == "REJECTED" and before.reason is SlotReason.PREDICATE_UNREGISTERED
    await w.install(release, owner=w.b, principal=w.service_b)
    other_kb = await resolve(w, key(w, ORG_KEY, release.ref))
    assert other_kb.reason is SlotReason.PREDICATE_UNREGISTERED  # installed in B, not A
    await w.install(release)
    created = await resolve(w, key(w, ORG_KEY, release.ref))
    assert created.outcome == "CREATED"
    unknown = await resolve(w, key(w, "fnd:noSuchPredicate@v1", release.ref))
    assert unknown.reason is SlotReason.PREDICATE_UNREGISTERED
    wrong_ref = await resolve(w, key(w, ORG_KEY, "ontrel:sha256-" + "0" * 64))
    assert wrong_ref.reason is SlotReason.PREDICATE_UNREGISTERED
    legal = await resolve(w, key(w, "sys:hasLegalName@v1", SYSTEM_RELEASE, member=None))
    assert legal.reason is not SlotReason.PREDICATE_UNREGISTERED  # sys is unchanged
    stored = w.rows(
        "SELECT predicate_key, predicate_release_ref, cardinality FROM fact_slot WHERE id = %s",
        created.slot_id,
    )
    assert stored == [(ORG_KEY, release.ref, "SINGLE")]


async def test_ac4_eternal_commit_shape_and_conflict(onto_world: Any) -> None:
    w = onto_world
    release = fx.foundation()
    await w.install(release)
    slot = (await resolve(w, key(w, ORG_KEY, release.ref))).slot_id
    org, other = w.entity(w.a), w.entity(w.a)

    bounded = await commit(w, slot, present(entity(org)), day("2026-01-01T00:00:00+00:00"))
    assert bounded.status_code == 422 and bounded.json()["code"] == "kind_shape_mismatch"
    unknown_end = await commit(
        w, slot, present(entity(org)), {**ETERNAL, "valid_to_state": "UNKNOWN"}
    )
    assert unknown_end.json()["code"] == "kind_shape_mismatch"
    assert w.scalar("SELECT count(*) FROM canonical_fact_version WHERE slot_id = %s", slot) == 0

    ok = await commit(w, slot, present(entity(org)), ETERNAL)
    assert ok.status_code == 201, ok.text
    row = w.rows(
        "SELECT temporal_kind, lower_inf(valid), upper_inf(valid), "
        "valid_to_state, valid_from_granularity, "
        "valid_from_basis, valid_to_granularity FROM canonical_fact_version WHERE slot_id = %s",
        slot,
    )
    assert row == [("ETERNAL", True, True, "OPEN", None, None, None)]
    async with w.release_client(w.service) as client:
        read = await client.get(f"/facts/{slot}")
    assert read.status_code == 200, read.text
    body = read.json()
    assert body["valid_start"] is None and body["valid_end"] is None
    assert body["temporal"]["temporal_kind"] == "ETERNAL" and body["temporal"]["valid_from"] is None

    conflict = await commit(w, slot, present(entity(other)), ETERNAL)
    assert conflict.status_code == 422 and conflict.json()["code"] == "eternal_conflict"
    same = await commit(w, slot, present(entity(org)), ETERNAL)
    assert same.status_code == 201
    assert (
        w.scalar(
            "SELECT count(*) FROM canonical_fact_version WHERE slot_id = %s "
            "AND upper_inf(recorded)",
            slot,
        )
        == 1
    )


async def test_ac4_event_commit_is_one_period(onto_world: Any, builder: Any) -> None:
    w = onto_world
    release = builder.build("evtest", 1, {"evtest": fx.event_module()})
    await w.install(release)
    slot = (await resolve(w, key(w, "evt:happenedOn@v1", release.ref))).slot_id
    value = present({"type": "date", "value": "2026-03-04"})
    open_event = await commit(w, slot, value, day("2026-03-04T00:00:00+00:00"))
    assert open_event.status_code == 422 and open_event.json()["code"] == "kind_shape_mismatch"
    two_days = await commit(
        w, slot, value, day("2026-03-04T00:00:00+00:00", "2026-03-06T00:00:00+00:00")
    )
    assert two_days.json()["code"] == "kind_shape_mismatch"
    eternal_shape = await commit(w, slot, value, ETERNAL)
    assert eternal_shape.status_code == 422
    ok = await commit(w, slot, value, day("2026-03-04T00:00:00+00:00", "2026-03-05T00:00:00+00:00"))
    assert ok.status_code == 201, ok.text
    assert w.rows(
        "SELECT temporal_kind, valid_to_state FROM canonical_fact_version WHERE slot_id = %s", slot
    ) == [("EVENT", "BOUNDED")]


async def test_ac4_state_commit_unchanged(onto_world: Any) -> None:
    w = onto_world
    release = fx.foundation()
    await w.install(release)
    slot = (await resolve(w, key(w, "fnd:accountStatus@v1", release.ref))).slot_id
    ok = await commit(
        w, slot, present({"type": "code", "value": "current"}), day("2026-01-01T00:00:00+00:00")
    )
    assert ok.status_code == 201, ok.text
    eternal_shape = await commit(w, slot, present({"type": "code", "value": "closed"}), ETERNAL)
    assert eternal_shape.status_code == 422  # a STATE commit keeps the F0008 shape rules
    assert w.rows("SELECT temporal_kind FROM canonical_fact_version WHERE slot_id = %s", slot) == [
        ("STATE",)
    ]


async def test_ac3_new_release_keeps_slot_identity(onto_world: Any, builder: Any) -> None:
    w = onto_world
    first = fx.foundation()
    await w.install(first)
    original = await resolve(w, key(w, ORG_KEY, first.ref))
    module = fx.foundation_module()
    module["module"]["version"] = 2
    module["terms"][0]["labels"] = {"en-US": "Thing (renamed)"}
    second = builder.build("foundation", 2, {"foundation": module}, predecessor="../1")
    await w.install(second)
    again = await resolve(w, key(w, ORG_KEY, second.ref))
    assert again.outcome == "RESOLVED" and again.slot_id == original.slot_id
    assert (
        w.scalar("SELECT predicate_release_ref FROM fact_slot WHERE id = %s", original.slot_id)
        == first.ref
    )


async def test_ac6_existing_slot_uses_its_recorded_release(onto_world: Any, builder: Any) -> None:
    """After a new release is activated, an existing slot still resolves its own
    pinned contract: commits and reads go through foundation@1."""
    w = onto_world
    first = fx.foundation()
    await w.install(first)
    _, review = await w.approve(first)
    await w.activate(first, review)
    slot = (await resolve(w, key(w, ORG_KEY, first.ref))).slot_id
    module = fx.foundation_module()
    module["module"]["version"] = 2
    module["terms"][0]["labels"] = {"en-US": "Thing (renamed)"}
    second = builder.build("foundation", 2, {"foundation": module}, predecessor="../1")
    await w.install(second)
    _, review2 = await w.approve(second)
    await w.activate(second, review2)
    ok = await commit(w, slot, present(entity(w.entity(w.a))), ETERNAL)
    assert ok.status_code == 201, ok.text
    assert w.scalar("SELECT predicate_release_ref FROM fact_slot WHERE id = %s", slot) == first.ref


async def test_ac6_commit_authorization_unchanged(onto_world: Any) -> None:
    w = onto_world
    release = fx.foundation()
    await w.install(release)
    slot = (await resolve(w, key(w, ORG_KEY, release.ref))).slot_id
    denied = await commit(w, slot, present(entity(w.entity(w.a))), ETERNAL, principal=w.steward)
    assert denied.status_code == 404  # no fact_slot:commit grant; non-disclosing
    assert w.scalar("SELECT count(*) FROM canonical_fact_version WHERE slot_id = %s", slot) == 0


async def test_ac5_no_legacy_row_rewritten(onto_world: Any) -> None:
    w = onto_world
    before = w.rows("SELECT id, slot_type, identity_version FROM fact_slot ORDER BY id")
    await w.install(fx.foundation())
    assert w.rows("SELECT id, slot_type, identity_version FROM fact_slot ORDER BY id") == before


@pytest.mark.parametrize("strict", [True])
async def test_registry_strict_mode_detects_missing_prepare(strict: bool) -> None:
    from brain_domain.fact_slots import PredicateKey
    from brain_factslots.predicates import RegistryNotPrepared, ReleasePredicateRegistry
    from brain_testing.factslots import test_registry

    class Empty:
        async def predicates(self, scope, refs):  # type: ignore[no-untyped-def]
            return []

    registry = ReleasePredicateRegistry(test_registry(), Empty(), strict=strict)
    with pytest.raises(RegistryNotPrepared):
        registry.find(PredicateKey.parse(ORG_KEY), "ontrel:sha256-" + "1" * 64)
