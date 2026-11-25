"""F0009 provenance reader on PostgreSQL over F0006 v2 assertions and review history.

EX-PROV-001 (S0001 AC1-AC7), EX-PROV-002 lineage (S0002/S0005 read side), the
recorded-decision link (S0003 AC5) and current authority (S0004 AC1/AC2/AC4-AC7).
Expected edges come from `qe.expected_*` (stored-basis SQL), not the reader.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from brain_domain.authx import ResourceType
from brain_domain.provenance import LineageNotFound, LineageUnavailable
from brain_persistence.assertion_models import AssertionSemantics
from brain_security.execution import AuthorizationDenied
from brain_testing import fixtures
from engine.tests.fixtures import f0009_provenance as qe
from engine.tests.fixtures.assertions import harness
from engine.tests.integration.test_assertion_consumers import commit
from engine.tests.integration.test_f0009_corrections import admit_items, decision, post
from sqlalchemy.orm import Session

_clean_fact_tables = harness._clean_fact_tables
database = harness.database
world = harness.world
world_factory = harness.world_factory

CANONICAL = ("canonical_fact_version", "canonical_fact_change", "canonical_commit", "outbox_event")
NOT_FOUND = (AuthorizationDenied, LineageNotFound)


async def admitted(world):  # type: ignore[no-untyped-def]
    batch = await world.admit([world.candidate()], delivery_key=f"f0009-{uuid4()}")
    return batch.accepted[0].record.id


async def test_ex_prov_001_exact_source_chain_is_complete(world, database):
    """S0001 AC1/AC3/AC6: exact stored identities and metadata, no parse/model/write."""
    assertion_id = await admitted(world)
    artifact = world.bundle.key.artifact_id
    before = qe.snapshot(world.url, ["assertion", "assertion_evidence", *CANONICAL])

    result = await qe.read_lineage(
        world.engine,
        world.policy,
        world.reviewer,
        ("assertion", assertion_id),
        (ResourceType.CONTENT_ARTIFACT, artifact),
        trace_id="ex-prov-001",
    )

    expected = qe.expected_source_chain(world.url, [assertion_id])
    expected |= qe.expected_review_history(world.url, [assertion_id])
    assert qe.result_edges(result) == expected
    assert {k for k, _ in qe.result_refs(result)} == {
        "assertion",
        "evidence",
        "content_artifact",
        "document_version",
        "source_document",
        "interpretation_run",
    }
    assert result.completeness == "COMPLETE" and result.gaps == ()
    assert (result.tenant_id, result.knowledge_base_id) == world.owner
    records = {r.kind: r for r in result.records}
    with Session(world.sync_engine) as session:
        sem = session.get(AssertionSemantics, assertion_id)
        assert records["assertion"].data["semantics"] == sem.record
        (verified,) = sem.verified_evidence
        assert records["evidence"].data["stored_content_record"] == verified
    run = records["interpretation_run"].data
    assert run["profile_id"] == "f0006-independent" and run["profile_version"] == "1"
    assert records["assertion"].data["model_confidence"] == 0.98
    assert records["content_artifact"].data["artifact_contract_version"] == 2
    # AC6: read-only, and the read used the existing authorization audit.
    assert qe.snapshot(world.url, ["assertion", "assertion_evidence", *CANONICAL]) == before
    audited = qe._rows(
        world.url,
        "SELECT resource_type, operation_outcome FROM audit_event "
        "WHERE trace_id='ex-prov-001' AND event_type='authorization_decision'",
    )
    assert sorted(audited) == [("content_artifact", "succeeded")]


async def test_ex_prov_002_correction_lineage_and_reservation(world, database):
    """S0002 AC1, S0003 AC5, S0005 AC1/AC6: corrected child, decision, reservation;
    a reviewed assertion with no commit is explained as reviewed only."""
    batch_id, (item,), (original,) = await admit_items(world)
    assert (await post(world, batch_id, [decision(item)])).status_code == 200
    ((child, decision_id, reservation_id),) = qe._rows(
        world.url,
        "SELECT d.corrected_assertion_id, d.id, r.id FROM review_decision d "
        "JOIN learning_candidate_reservation r ON r.review_decision_id = d.id",
    )
    result = await qe.read_lineage(
        world.engine,
        world.policy,
        world.reviewer,
        ("assertion", child),
        (ResourceType.REVIEW_TASK, item),
    )
    expected = qe.expected_source_chain(world.url, [child, original])
    expected |= qe.expected_review_history(world.url, [child, original])
    assert qe.result_edges(result) == expected
    assert qe.edge("corrected_from", ("assertion", child), ("assertion", original)) in expected
    assert (
        qe.edge(
            "reserved_learning",
            ("review_decision", decision_id),
            ("learning_reservation", reservation_id),
        )
        in expected
    )
    kinds = {k for k, _ in qe.result_refs(result)}
    assert "fact_version" not in kinds and "fact_change" not in kinds
    reservation = next(r for r in result.records if r.kind == "learning_reservation")
    assert reservation.data["corrected_assertion_id"] == str(child)
    assert reservation.data["reviewer_principal_id"] == str(world.reviewer.id)
    decision_record = next(r for r in result.records if r.kind == "review_decision")
    assert decision_record.data["corrected_value"] == {"amount": 2000000, "currency": "USD"}


async def test_refused_attempt_is_exposed_only_as_history(world, database):
    batch_id, (item,), (original,) = await admit_items(world)
    await post(world, batch_id, [decision(item)])
    await post(world, batch_id, [decision(item, corrected_value={"amount": 1, "currency": "USD"})])
    result = await qe.read_lineage(
        world.engine,
        world.policy,
        world.reviewer,
        ("assertion", original),
        (ResourceType.REVIEW_TASK, item),
    )
    (attempt,) = [r for r in result.records if r.kind == "review_attempt"]
    assert attempt.data["outcome"] == "ALREADY_DECIDED"
    assert qe.edge(
        "reviews", ("review_attempt", attempt.id), ("assertion", original)
    ) in qe.result_edges(result)


async def test_recorded_decision_link_follows_an_independent_commit(world, database):
    """S0003 AC5: the reader follows a stored decision link on a version; the review
    itself created no version."""
    batch_id, (item,), (original,) = await admit_items(world)
    await post(world, batch_id, [decision(item, "ACCEPT")])
    ((decision_id,),) = qe._rows(world.url, "SELECT id FROM review_decision")
    ((evidence_id,),) = qe._rows(
        world.url, "SELECT id FROM assertion_evidence WHERE assertion_id=%s", original
    )
    with Session(world.sync_engine) as session, session.begin():
        slot_id = fixtures.seed_fact_slot(session, *world.owner)
    committed = await commit(world, slot_id, [evidence_id], decision_id)
    (version_id,) = committed.fact_version_ids
    result = await qe.read_lineage(
        world.engine,
        world.policy,
        world.reviewer,
        ("fact_version", version_id),
        (ResourceType.FACT_SLOT, slot_id),
    )
    edges = qe.result_edges(result)
    assert (
        qe.edge("recorded_decision", ("fact_version", version_id), ("review_decision", decision_id))
        in edges
    )
    assert qe.edge("supported_by", ("fact_version", version_id), ("evidence", evidence_id)) in edges
    (change,) = [r for r in result.records if r.kind == "fact_change"]
    assert change.data["from_version_id"] is None  # creation change
    assert change.data["commit_id"] == str(committed.commit_id)
    assert change.data["actor_principal_id"] == str(world.actor.id)
    assert qe.edge("changed_to", ("fact_change", change.id), ("fact_version", version_id)) in edges
    # The legacy pilot version is labelled, never upgraded.
    assert result.completeness == "INCOMPLETE"
    assert {(g.record.kind, g.field) for g in result.gaps} == {("fact_version", "temporal")}


async def test_unknown_inaccessible_and_mismatched_anchors_are_indistinguishable(world, database):
    """S0001 AC7, S0004 AC2/AC5: no partial graph, no hidden identity."""
    assertion_id = await admitted(world)
    artifact = world.bundle.key.artifact_id
    with Session(world.sync_engine) as session, session.begin():
        other_artifact = fixtures.seed_content_artifact(session, *world.owner)
        foreign_artifact = fixtures.seed_content_artifact(session, uuid4(), uuid4())
        slot_id = fixtures.seed_fact_slot(session, *world.owner)
    cases = [
        (("assertion", uuid4()), (ResourceType.CONTENT_ARTIFACT, artifact)),  # unknown root
        (("assertion", assertion_id), (ResourceType.CONTENT_ARTIFACT, uuid4())),  # unknown anchor
        (("assertion", assertion_id), (ResourceType.CONTENT_ARTIFACT, other_artifact)),  # arbitrary
        (("assertion", assertion_id), (ResourceType.CONTENT_ARTIFACT, foreign_artifact)),  # foreign
        (("assertion", assertion_id), (ResourceType.FACT_SLOT, slot_id)),  # wrong anchor kind
        (("fact_version", uuid4()), (ResourceType.FACT_SLOT, slot_id)),  # unknown version
    ]
    for root, anchor in cases:
        with pytest.raises(NOT_FOUND) as refused:
            await qe.read_lineage(world.engine, world.policy, world.reviewer, root, anchor)
        assert str(assertion_id) not in str(refused.value)


async def test_review_records_need_current_review_task_read(world, database):
    """S0004 AC4: a ServicePrincipal-only principal reads sources and slots but not
    review tasks, so a lineage that exposes a decision is refused as a whole."""
    from brain_domain.principal import PrincipalKind

    batch_id, (item,), (original,) = await admit_items(world)
    await post(world, batch_id, [decision(item)])
    artifact = world.bundle.key.artifact_id
    with Session(world.sync_engine) as session, session.begin():
        service_only = fixtures.seed_principal(
            session, issuer="urn:f0009:test", subject=str(uuid4()), kind=PrincipalKind.SERVICE
        )
        fixtures.seed_grant(session, service_only.id, *world.owner, "ServicePrincipal")
    with pytest.raises(NOT_FOUND):
        await qe.read_lineage(
            world.engine,
            world.policy,
            service_only,
            ("assertion", original),
            (ResourceType.CONTENT_ARTIFACT, artifact),
        )
    # A lineage with no review history is readable by the same principal.
    clean = await admitted(world)
    result = await qe.read_lineage(
        world.engine,
        world.policy,
        service_only,
        ("assertion", clean),
        (ResourceType.CONTENT_ARTIFACT, artifact),
    )
    assert result.completeness == "COMPLETE"


async def test_revoked_grant_refuses_old_history_without_leaking(world, database, caplog):
    """S0004 AC3/AC6/AC7: a later revocation refuses a previously readable lineage;
    the denial is audited and nothing protected reaches logs or the exception."""
    assertion_id = await admitted(world)
    artifact = world.bundle.key.artifact_id
    anchor = (ResourceType.CONTENT_ARTIFACT, artifact)
    await qe.read_lineage(
        world.engine, world.policy, world.reviewer, ("assertion", assertion_id), anchor
    )
    from brain_persistence.grants import revoke_membership
    from brain_persistence.models import MembershipRow
    from sqlalchemy import select

    with Session(world.sync_engine) as session, session.begin():
        memberships = list(
            session.scalars(
                select(MembershipRow).where(MembershipRow.principal_id == world.reviewer.id)
            )
        )
        for membership in memberships:
            revoke_membership(
                session,
                membership.id,
                operator_id=fixtures.SYNTHETIC_OPERATOR,
                approval_ref=fixtures.FIXTURE_APPROVAL,
                at=datetime.now(UTC),
            )
    caplog.set_level(logging.DEBUG)
    with pytest.raises(NOT_FOUND) as refused:
        await qe.read_lineage(
            world.engine,
            world.policy,
            world.reviewer,
            ("assertion", assertion_id),
            anchor,
            trace_id="revoked",
        )
    assert "500000" not in caplog.text and "Cedar Bridge" not in caplog.text
    assert "500000" not in repr(refused.value)
    denied = qe._rows(
        world.url,
        "SELECT decision FROM audit_event WHERE trace_id='revoked' "
        "AND event_type='authorization_decision'",
    )
    assert denied and not any(row[0] for row in denied)


async def test_correction_chain_limit_refuses_at_limit_plus_one(world, database):
    """S0001 AC5: 256 correction links are explained; 257 refuse with no partial graph."""
    import psycopg

    artifact = world.bundle.key.artifact_id
    assertion_id = uuid4()  # a legacy v1 base; v1 corrections must have a v1 parent
    with psycopg.connect(world.url) as connection:
        connection.execute(
            "INSERT INTO assertion (id, origin, version, subject_type, slot_type, value, "
            "interpretation_basis, tenant_id, knowledge_base_id, semantic_contract_version) "
            "VALUES (%s, 'MACHINE_EXTRACTION', 1, 'Policy', 'each_occurrence_limit', "
            "'{}'::jsonb, 'EXPLICIT', %s, %s, 1)",
            (assertion_id, *world.owner),
        )
        connection.execute(
            "INSERT INTO assertion_evidence (id, assertion_id, artifact_id, precision, tenant_id, "
            "knowledge_base_id) VALUES (%s, %s, %s, 'block', %s, %s)",
            (uuid4(), assertion_id, artifact, *world.owner),
        )

    def chain(links: int):  # type: ignore[no-untyped-def]
        previous = assertion_id
        with psycopg.connect(world.url) as connection:
            for _ in range(links):
                child = uuid4()
                connection.execute(
                    "INSERT INTO assertion (id, origin, original_assertion_id, version, "
                    "subject_type, slot_type, value, interpretation_basis, tenant_id, "
                    "knowledge_base_id, semantic_contract_version) VALUES (%s, 'HUMAN_REVIEW', "
                    "%s, 1, 'Policy', 'each_occurrence_limit', '{}'::jsonb, 'EXPLICIT', %s, %s, 1)",
                    (child, previous, *world.owner),
                )
                previous = child
        return previous

    anchor = (ResourceType.CONTENT_ARTIFACT, artifact)
    at_limit = chain(256)
    result = await qe.read_lineage(
        world.engine, world.policy, world.reviewer, ("assertion", at_limit), anchor
    )
    assert sum(1 for r in result.records if r.kind == "assertion") == 257
    over = chain(257)
    with pytest.raises(LineageUnavailable):
        await qe.read_lineage(
            world.engine, world.policy, world.reviewer, ("assertion", over), anchor
        )


async def test_legacy_assertion_is_authorized_then_labelled_incomplete(world, database):
    """S0001 AC7, S0006 AC1: no fabricated semantics, run or content record."""
    import psycopg

    legacy, evidence = uuid4(), uuid4()
    artifact = world.bundle.key.artifact_id
    with psycopg.connect(world.url) as connection:
        connection.execute(
            "INSERT INTO assertion (id, origin, version, subject_type, slot_type, value, "
            "interpretation_basis, tenant_id, knowledge_base_id, semantic_contract_version) "
            "VALUES (%s, 'MACHINE_EXTRACTION', 1, 'Policy', 'each_occurrence_limit', "
            "'{}'::jsonb, 'EXPLICIT', %s, %s, 1)",
            (legacy, *world.owner),
        )
        connection.execute(
            "INSERT INTO assertion_evidence (id, assertion_id, artifact_id, precision, tenant_id, "
            "knowledge_base_id) VALUES (%s, %s, %s, 'block', %s, %s)",
            (evidence, legacy, artifact, *world.owner),
        )
    result = await qe.read_lineage(
        world.engine,
        world.policy,
        world.reviewer,
        ("assertion", legacy),
        (ResourceType.CONTENT_ARTIFACT, artifact),
    )
    assert result.completeness == "INCOMPLETE"
    assert {(g.record.kind, g.field, g.reason) for g in result.gaps} == {
        ("assertion", "semantics", "LEGACY_UNQUALIFIED"),
        ("assertion", "run_id", "METADATA_UNAVAILABLE"),
        ("evidence", "stored_content_record", "LEGACY_UNQUALIFIED"),
    }
