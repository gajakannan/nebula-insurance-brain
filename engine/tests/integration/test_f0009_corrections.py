"""F0009 review-boundary proof on PostgreSQL through the unchanged HTTP route.

S0002 AC1-AC8, S0005 AC1-AC5, PR-H1 resubmission, PR-L1 legacy GET, PR-L2 batch
shapes. Every assertion of persistence is a fresh-session query, never a rendered
success alone.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from brain_persistence.models import ReviewBatchRow, ReviewItemRow
from brain_persistence.repositories import SqlAlchemyReviewItemRepository
from engine.tests.fixtures import f0009_provenance as qe
from engine.tests.fixtures.assertions import harness
from sqlalchemy import select
from sqlalchemy.orm import Session

_clean_fact_tables = harness._clean_fact_tables
database = harness.database
world = harness.world
world_factory = harness.world_factory

CORRECTED = {"amount": 2000000, "currency": "USD"}


def batch_items(world, assertion_ids: list[UUID]) -> tuple[UUID, list[UUID]]:
    """Assemble the admitted assertions' review items into one batch."""
    with Session(world.sync_engine) as session, session.begin():
        batch = ReviewBatchRow(
            id=uuid4(),
            assembling_principal_id=world.reviewer.id,
            tenant_id=world.owner[0],
            knowledge_base_id=world.owner[1],
        )
        session.add(batch)
        session.flush()
        items = []
        for assertion_id in assertion_ids:
            item = session.scalars(
                select(ReviewItemRow).where(ReviewItemRow.assertion_id == assertion_id)
            ).first()
            item.review_batch_id = batch.id
            items.append(item.id)
        return batch.id, items


async def admit_items(world, n: int = 1) -> tuple[UUID, list[UUID], list[UUID]]:
    assertions = []
    for index in range(n):
        batch = await world.admit(
            [world.candidate(model_confidence=0.2)], delivery_key=f"f0009-{index}-{uuid4()}"
        )
        assertions.append(batch.accepted[0].record.id)
    batch_id, items = batch_items(world, assertions)
    return batch_id, items, assertions


def decision(item_id: UUID, action: str = "CORRECT", **extra):  # type: ignore[no-untyped-def]
    body = {"review_item_id": str(item_id), "action": action, "assertion_version": 1}
    if action == "CORRECT":
        body.update(reason_code="MISREAD_VALUE", corrected_value=CORRECTED)
    body.update(extra)
    return body


async def post(world, batch_id: UUID, decisions: list[dict], principal=None):  # type: ignore[no-untyped-def]
    async with qe.review_client(world.engine, principal or world.reviewer, world.content) as client:
        return await client.post(
            f"/reviews/batches/{batch_id}/decisions", json={"decisions": decisions}
        )


def q(world, sql: str, *params):  # type: ignore[no-untyped-def]
    return qe.count(world.url, sql, *params)


async def test_effective_correction_appends_lineage_and_one_reservation(world, database):
    """S0002 AC1/AC2/AC3/AC8, S0005 AC1: one atomic append, fresh-session proof."""
    batch_id, (item,), (original,) = await admit_items(world)
    before = qe.snapshot(
        world.url, ["assertion_evidence", "assertion_semantics", "content_artifact"]
    )
    original_row = qe._rows(
        world.url, "SELECT row_to_json(a)::text FROM assertion a WHERE id=%s", original
    )

    response = await post(world, batch_id, [decision(item, reviewer_comment="page 2 says 2M")])
    assert response.status_code == 200, response.text
    receipt = response.json()
    assert set(receipt) == {"decision_ids", "applied", "duplicate", "stale", "blocked"}
    assert receipt["applied"] == 1 and receipt["duplicate"] is False

    (row,) = qe._rows(
        world.url,
        "SELECT d.id, d.corrected_assertion_id, d.reviewer_principal_id, d.reason_code, "
        "d.corrected_value, d.reviewer_comment, d.correction_lineage_contract, d.decided_at, "
        "d.review_batch_id FROM review_decision d WHERE d.review_item_id = %s",
        item,
    )
    decision_id, child, reviewer, reason, value, comment, marker, decided_at, batch = row
    assert str(decision_id) == receipt["decision_ids"][0]
    assert (
        reviewer == world.reviewer.id and reason == "MISREAD_VALUE" and comment == "page 2 says 2M"
    )
    assert value == CORRECTED and marker == 1 and batch == batch_id
    (child_row,) = qe._rows(
        world.url,
        "SELECT origin, original_assertion_id, semantic_contract_version "
        "FROM assertion WHERE id=%s",
        child,
    )
    assert child_row == ("HUMAN_REVIEW", original, 2)  # AC2: v2 child of a v2 original
    (reservation,) = qe._rows(
        world.url,
        "SELECT original_assertion_id, corrected_assertion_id, reviewer_principal_id, "
        "reserved_at = (%s AT TIME ZONE 'UTC') FROM learning_candidate_reservation "
        "WHERE review_decision_id = %s",
        decided_at,
        decision_id,
    )
    assert reservation == (original, child, world.reviewer.id, True)
    assert (
        q(
            world,
            "SELECT count(*) FROM audit_event WHERE event_type='review_decision_recorded' "
            "AND resource_id=%s",
            item,
        )
        == 1
    )
    # Originals, evidence and source artifacts are unchanged; no canonical effect (AC8).
    assert (
        qe._rows(world.url, "SELECT row_to_json(a)::text FROM assertion a WHERE id=%s", original)
        == original_row
    )
    after = qe.snapshot(world.url, ["content_artifact"])
    assert after["content_artifact"] == before["content_artifact"]
    for table in (
        "canonical_fact_version",
        "canonical_fact_change",
        "canonical_commit",
        "outbox_event",
    ):
        assert q(world, f"SELECT count(*) FROM {table}") == 0, table


async def test_replay_returns_prior_outcome_without_new_effects(world, database):
    """S0002 AC4, S0005 AC3."""
    batch_id, (item,), _ = await admit_items(world)
    body = [decision(item)]
    first = (await post(world, batch_id, body)).json()
    effects = (
        q(world, "SELECT count(*) FROM review_decision"),
        q(world, "SELECT count(*) FROM learning_candidate_reservation"),
        q(world, "SELECT count(*) FROM audit_event WHERE event_type='review_decision_recorded'"),
        q(world, "SELECT count(*) FROM assertion"),
    )
    replay = await post(world, batch_id, body)
    assert replay.status_code == 200
    assert replay.json()["decision_ids"] == first["decision_ids"] and replay.json()["duplicate"]
    assert (
        q(world, "SELECT count(*) FROM review_decision"),
        q(world, "SELECT count(*) FROM learning_candidate_reservation"),
        q(world, "SELECT count(*) FROM audit_event WHERE event_type='review_decision_recorded'"),
        q(world, "SELECT count(*) FROM assertion"),
    ) == effects
    # Replay is still authorized under current grants: a durable authorization row.
    assert (
        q(
            world,
            "SELECT count(*) FROM audit_event WHERE event_type='authorization_decision' "
            "AND resource_id=%s AND action='annotate'",
            item,
        )
        == 2
    )


async def test_competing_correction_is_retained_as_a_non_applied_attempt(world, database):
    """S0002 AC6: the first applied decision and child stay; the loser is attributed."""
    batch_id, (item,), (original,) = await admit_items(world)
    first = (await post(world, batch_id, [decision(item)])).json()
    loser = decision(
        item, corrected_value={"amount": 3000000, "currency": "USD"}, reviewer_comment="I read 3M"
    )
    response = await post(world, batch_id, [loser])
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "3000000" not in response.text and "3M" not in response.text
    (attempt,) = qe._rows(
        world.url,
        "SELECT id, outcome, corrected_value, reviewer_comment, reviewer_principal_id, "
        "original_assertion_id FROM review_submission_attempt WHERE review_item_id=%s",
        item,
    )
    assert attempt[1:] == (
        "ALREADY_DECIDED",
        {"amount": 3000000, "currency": "USD"},
        "I read 3M",
        world.reviewer.id,
        original,
    )
    (audit,) = qe._rows(
        world.url,
        "SELECT payload, operation_outcome FROM audit_event "
        "WHERE event_type='review_submission_refused' AND resource_id=%s",
        item,
    )
    assert audit == ({"attempt_id": str(attempt[0]), "outcome": "ALREADY_DECIDED"}, "failed")
    assert [
        str(r[0])
        for r in qe._rows(world.url, "SELECT id FROM review_decision WHERE review_item_id=%s", item)
    ] == first["decision_ids"]
    assert q(world, "SELECT count(*) FROM learning_candidate_reservation") == 1

    # A repeated refusal reuses the row and writes one more audit event.
    assert (await post(world, batch_id, [loser])).status_code == 422
    assert q(world, "SELECT count(*) FROM review_submission_attempt") == 1
    assert (
        q(world, "SELECT count(*) FROM audit_event WHERE event_type='review_submission_refused'")
        == 2
    )


async def test_mixed_batch_refuses_whole_batch_and_sibling_reapplies_alone(world, database):
    """PR-H1 (operator decision 2026-11-24, 'always re-evaluate')."""
    batch_id, (decided, sibling), _ = await admit_items(world, 2)
    assert (await post(world, batch_id, [decision(decided)])).status_code == 200
    mixed = [decision(decided, corrected_value={"amount": 9, "currency": "USD"}), decision(sibling)]
    assert (await post(world, batch_id, mixed)).status_code == 422
    outcomes = dict(
        qe._rows(world.url, "SELECT review_item_id, outcome FROM review_submission_attempt")
    )
    assert outcomes == {decided: "ALREADY_DECIDED", sibling: "BATCH_REFUSED"}
    assert q(world, "SELECT count(*) FROM review_decision WHERE review_item_id=%s", sibling) == 0

    alone = await post(world, batch_id, [decision(sibling)])
    assert alone.status_code == 200 and alone.json()["applied"] == 1
    assert q(world, "SELECT count(*) FROM review_decision WHERE review_item_id=%s", sibling) == 1
    assert q(world, "SELECT count(*) FROM learning_candidate_reservation") == 2
    # The earlier BATCH_REFUSED attempt coexists as history; it was never a replay key.
    assert (
        q(world, "SELECT count(*) FROM review_submission_attempt WHERE review_item_id=%s", sibling)
        == 1
    )


async def test_same_item_twice_in_one_batch_rolls_back_without_attempts(world, database):
    """PR-L2: shipped behavior; no prior decision exists to lose against."""
    batch_id, (item,), _ = await admit_items(world)
    twice = [decision(item), decision(item, corrected_value={"amount": 5, "currency": "USD"})]
    assert (await post(world, batch_id, twice)).status_code == 422
    for table in ("review_decision", "review_submission_attempt", "learning_candidate_reservation"):
        assert q(world, f"SELECT count(*) FROM {table}") == 0, table
    assert q(world, "SELECT count(*) FROM assertion WHERE origin='HUMAN_REVIEW'") == 0


async def test_stale_submission_is_retained_and_legacy_get_is_unchanged(world, database):
    """S0002 AC5, S0005 AC4, PR-L1."""
    batch_id, (item,), _ = await admit_items(world)
    stale = decision(item, assertion_version=2, reviewer_comment="stale view")
    response = await post(world, batch_id, [stale])
    assert response.status_code == 200 and response.json()["stale"] == 1
    (row,) = qe._rows(
        world.url,
        "SELECT stale, corrected_value, reviewer_comment, corrected_assertion_id "
        "FROM review_decision WHERE review_item_id=%s",
        item,
    )
    assert row == (True, CORRECTED, "stale view", None)
    assert q(world, "SELECT count(*) FROM learning_candidate_reservation") == 0
    assert q(world, "SELECT count(*) FROM assertion WHERE origin='HUMAN_REVIEW'") == 0
    async with qe.review_client(world.engine, world.reviewer, world.content) as client:
        body = (await client.get(f"/reviews/{item}")).json()
    assert body["decision"]["stale"] is True
    assert body["decision"]["corrected_value"] is None
    assert body["decision"]["reviewer_comment"] is None and body["decision"]["evidence"] is None


@pytest.mark.parametrize("action", ["ACCEPT", "REJECT"])
async def test_non_correcting_actions_reserve_nothing(world, database, action):
    """S0002 AC7, S0005 AC4."""
    batch_id, (item,), _ = await admit_items(world)
    extra = {"reason_code": "NOT_IN_SOURCE"} if action == "REJECT" else {}
    assert (await post(world, batch_id, [decision(item, action, **extra)])).status_code == 200
    assert q(world, "SELECT count(*) FROM learning_candidate_reservation") == 0
    assert q(world, "SELECT count(*) FROM assertion WHERE origin='HUMAN_REVIEW'") == 0


async def test_unresolved_evidence_requires_blocked_and_creates_nothing(world, database):
    batch_id, (item,), _ = await admit_items(world)
    unresolved = {
        "source": str(world.bundle.key.artifact_id),
        "precision": "unresolved",
        "unresolved_reason": "no anchor",
    }
    refused = await post(world, batch_id, [decision(item, evidence=unresolved)])
    assert refused.status_code == 422
    blocked = await post(
        world,
        batch_id,
        [decision(item, "BLOCKED", reason_code="EVIDENCE_UNRESOLVED", evidence=unresolved)],
    )
    assert blocked.status_code == 200 and blocked.json()["blocked"] == 1
    assert q(world, "SELECT count(*) FROM learning_candidate_reservation") == 0
    assert q(world, "SELECT count(*) FROM assertion WHERE origin='HUMAN_REVIEW'") == 0


async def test_reviewer_identity_cannot_be_supplied(world, database):
    """S0002 AC8: the reviewer comes from the verified principal only."""
    batch_id, (item,), _ = await admit_items(world)
    spoof = decision(item, reviewer_principal_id=str(uuid4()))
    assert (await post(world, batch_id, [spoof])).status_code == 422
    assert q(world, "SELECT count(*) FROM review_decision") == 0


async def test_reservation_failure_rolls_back_the_whole_correction(world, database, monkeypatch):
    """S0002 AC3, S0005 AC2: no effective correction without its reference."""
    batch_id, (item,), _ = await admit_items(world)

    async def fail(self, decision):  # type: ignore[no-untyped-def]
        raise RuntimeError("injected reservation failure")

    monkeypatch.setattr(SqlAlchemyReviewItemRepository, "reserve_learning_reference", fail)
    with pytest.raises(RuntimeError):
        await post(world, batch_id, [decision(item)])
    for table in ("review_decision", "learning_candidate_reservation"):
        assert q(world, f"SELECT count(*) FROM {table}") == 0, table
    assert q(world, "SELECT count(*) FROM assertion WHERE origin='HUMAN_REVIEW'") == 0
    assert (
        q(world, "SELECT count(*) FROM audit_event WHERE event_type='review_decision_recorded'")
        == 0
    )
    # The facade durably audited the failed attempt.
    assert (
        q(
            world,
            "SELECT count(*) FROM audit_event WHERE event_type='authorization_decision' "
            "AND operation_outcome='failed' AND resource_id=%s",
            item,
        )
        == 1
    )


async def test_unauthorized_annotator_leaves_zero_effects(world, database):
    """S0004 AC4/AC6: the service principal cannot annotate."""
    batch_id, (item,), _ = await admit_items(world)
    response = await post(world, batch_id, [decision(item)], principal=world.actor)
    assert response.status_code == 404
    for table in ("review_decision", "review_submission_attempt", "learning_candidate_reservation"):
        assert q(world, f"SELECT count(*) FROM {table}") == 0, table


async def test_learning_effects_are_zero(world, database):
    """S0005 AC5: a reservation is an identity only; nothing else is written."""
    batch_id, (item,), _ = await admit_items(world)
    tables = qe._rows(
        world.url,
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public' "
        "AND (table_name LIKE '%%learning%%' OR table_name LIKE '%%golden%%' "
        "OR table_name LIKE '%%candidate%%')",
    )
    assert {t[0] for t in tables} <= {"learning_candidate_reservation", "document_date_candidate"}
    assert (await post(world, batch_id, [decision(item)])).status_code == 200
    assert q(world, "SELECT count(*) FROM learning_candidate_reservation") == 1
    assert q(world, "SELECT count(*) FROM document_date_candidate") == 0


async def test_source_set_change_after_locks_is_a_fresh_operation_retry(
    world, database, monkeypatch
):
    """PR-L2: a source set that changes between authorization and the item locks is
    never written against an incompletely authorized set. Sanitized 503, zero
    effects, a durable failed authorization audit; the client resubmits."""
    from brain_domain.authx import ResourceKey, ResourceType

    batch_id, (item,), _ = await admit_items(world)
    original = SqlAlchemyReviewItemRepository.source_keys
    calls = []

    async def drifting(self, review_item_ids):  # type: ignore[no-untyped-def]
        keys = await original(self, review_item_ids)
        calls.append(1)
        if len(calls) == 2:  # the post-lock recheck sees a newly linked source
            keys = (*keys, ResourceKey(ResourceType.CONTENT_ARTIFACT, uuid4()))
        return keys

    monkeypatch.setattr(SqlAlchemyReviewItemRepository, "source_keys", drifting)
    response = await post(world, batch_id, [decision(item)])
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    for table in ("review_decision", "review_submission_attempt", "learning_candidate_reservation"):
        assert q(world, f"SELECT count(*) FROM {table}") == 0, table
    assert (
        q(
            world,
            "SELECT count(*) FROM audit_event WHERE event_type='authorization_decision' "
            "AND operation_outcome='failed' AND resource_id=%s",
            item,
        )
        == 1
    )
    monkeypatch.setattr(SqlAlchemyReviewItemRepository, "source_keys", original)
    assert (await post(world, batch_id, [decision(item)])).status_code == 200
