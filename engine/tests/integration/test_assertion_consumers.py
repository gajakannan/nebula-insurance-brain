from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import httpx2 as httpx
import pytest
from brain_assertions.eligibility import AssertionIneligible
from brain_contracts.assertions import wire_value
from brain_domain.authx import Action, ResourceKey, ResourceType
from brain_domain.facts import CommitProposal
from brain_domain.principal import PrincipalKind
from brain_domain.review import EvidenceLocator, ReviewDecisionAction
from brain_persistence.assertion_models import AssertionSemantics
from brain_persistence.assertions import UnsupportedAssertionCorrection
from brain_persistence.authx import SqlAlchemyAuthorityStore
from brain_persistence.models import Assertion, AssertionEvidence, ReviewBatchRow, ReviewItemRow
from brain_persistence.repositories import (
    ReviewDecisionAuditSink,
    SqlAlchemyAuditEventRepository,
    SqlAlchemyFactCommitRepository,
    SqlAlchemyReviewItemRepository,
)
from brain_review.decisions import DecisionRequest, ReviewDecisionService
from brain_security.execution import AuthorizationExecution
from brain_temporal.commit import CanonicalCommitService
from brain_testing import fixtures
from engine.tests.fixtures.assertions import harness
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from brain_api.app import create_app
from brain_api.deps import current_principal, get_db_session

_clean_fact_tables = harness._clean_fact_tables
database = harness.database
world = harness.world
world_factory = harness.world_factory
counts = harness.counts
configuration = harness.configuration


def slot(world):
    with Session(world.sync_engine) as session, session.begin():
        return fixtures.seed_fact_slot(session, *world.owner)


def proposal(slot_id, evidence, review=None):
    now = datetime.now(UTC)
    return CommitProposal(
        slot_id=slot_id,
        value={"amount": 500000},
        valid_from=now,
        valid_to=None,
        change_reason=None,
        evidence_refs=tuple(evidence),
        review_decision_id=review,
        source_received_at=now,
        artifact_created_at=now,
        assertion_created_at=now,
        expected_current_version_id=None,
        idempotency_key=None,
    )


async def commit(world, slot_id, evidence, review=None, *, authorized=True, value=None):
    async with AsyncSession(world.engine, expire_on_commit=False) as session:
        repository = SqlAlchemyFactCommitRepository(session)
        service = CanonicalCommitService(repository)
        request = proposal(slot_id, evidence, review)
        if value is not None:
            request = replace(request, value=value)
        if not authorized:
            return await service.commit(
                request, authorized_scope=world.owner, authorization_decision_id=None
            )
        execution = AuthorizationExecution(
            SqlAlchemyAuthorityStore(session), world.policy, world.policy.release
        )

        async def sources():
            return await repository.commit_source_keys(evidence, review)

        async def effect(decisions):
            primary = next(d for d in decisions if d.action == Action.COMMIT)
            return await service.commit(
                request,
                authorized_scope=world.owner,
                authorization_decision_id=primary.decision_id,
                source_access=repository.source_access_proof(decisions),
            )

        return await execution.mutate(
            world.actor,
            [ResourceKey(ResourceType.FACT_SLOT, slot_id)],
            Action.COMMIT,
            trace_id="independent-commit",
            operation=effect,
            additional_reads=sources,
        )


async def review(world, assertion_id, *, correct=None, evidence_seen=None):
    with Session(world.sync_engine) as session, session.begin():
        item = session.scalars(
            select(ReviewItemRow).where(ReviewItemRow.assertion_id == assertion_id)
        ).first()
        batch = ReviewBatchRow(
            id=uuid4(),
            assembling_principal_id=world.reviewer.id,
            tenant_id=world.owner[0],
            knowledge_base_id=world.owner[1],
        )
        session.add(batch)
        session.flush()
        item.review_batch_id = batch.id
        item_id = item.id
    async with AsyncSession(world.engine, expire_on_commit=False) as session:
        repository = SqlAlchemyReviewItemRepository(
            session, actor_id=world.reviewer.id, content_store=world.content
        )
        execution = AuthorizationExecution(
            SqlAlchemyAuthorityStore(session), world.policy, world.policy.release
        )

        async def sources():
            return await repository.source_keys([item_id])

        async def effect(decisions):
            authorizations = {d.resource.id: d for d in decisions if d.action == Action.ANNOTATE}
            audit = ReviewDecisionAuditSink(SqlAlchemyAuditEventRepository(session), authorizations)
            return await ReviewDecisionService(repository, audit).submit(
                DecisionRequest(
                    review_item_id=item_id,
                    action=ReviewDecisionAction.CORRECT
                    if correct is not None
                    else ReviewDecisionAction.ACCEPT,
                    reviewer_principal_id=world.reviewer.id,
                    assertion_version=1,
                    corrected_value=correct,
                    evidence_seen=evidence_seen,
                )
            )

        return await execution.mutate(
            world.reviewer,
            [ResourceKey(ResourceType.REVIEW_TASK, item_id)],
            Action.ANNOTATE,
            trace_id="independent-review",
            operation=effect,
            additional_reads=sources,
        )


async def test_qualified_typed_commit_uses_same_uow_source_authority(world, database):
    batch = await world.admit([world.candidate()])
    evidence = [batch.accepted[0].server_evidence[0].evidence_id]
    result = await commit(world, slot(world), evidence)
    assert len(result.fact_version_ids) == 1
    assert counts(database)["canonical_commit"] == 1


@pytest.mark.parametrize("kind", ["mood", "open", "described"])
async def test_independent_restrictions_prevent_canonical_effects(world_factory, database, kind):
    world = world_factory(origin="DESCRIBED" if kind == "described" else "STATED")
    updates = {"qualifiers": {"mood": "offered subject to inspection"}} if kind == "mood" else {}
    if kind == "open":
        updates.update(
            assertion_kind="OPEN_STATEMENT",
            predicate_id=None,
            ontology_release=None,
            source_relation="has an offered limit of",
        )
    batch = await world.admit([world.candidate(**updates)])
    evidence = [batch.accepted[0].server_evidence[0].evidence_id]
    with pytest.raises(AssertionIneligible):
        await commit(world, slot(world), evidence)
    assert counts(database)["canonical_commit"] == counts(database)["canonical_fact_version"] == 0


async def test_direct_caller_and_mixed_unknown_refs_cannot_bypass_source_guard(world, database):
    batch = await world.admit([world.candidate()])
    evidence = [batch.accepted[0].server_evidence[0].evidence_id]
    slot_id = slot(world)
    with pytest.raises(AssertionIneligible):
        await commit(world, slot_id, evidence, authorized=False)
    with pytest.raises(AssertionIneligible):
        await commit(world, slot_id, [*evidence, uuid4()])
    assert counts(database)["canonical_commit"] == 0
    # The documented legacy pilot boundary remains for wholly unregistered refs.
    await commit(world, slot_id, [uuid4()])
    assert counts(database)["canonical_commit"] == 1


async def test_operative_policy_terms_do_not_establish_the_embedded_condition(
    world_factory, database
):
    text = (
        "Cedar Bridge Roofing policy provides theft coverage only if the premises alarm "
        "is operating. This provision does not confirm that the alarm is operating."
    )
    world = world_factory(text=text)
    terms = {"operative_provision": "theft coverage only if the premises alarm is operating"}
    term = await world.admit([world.candidate(object={"kind": "LITERAL", "value": terms})])
    condition = await world.admit(
        [
            world.candidate(
                object={"kind": "LITERAL", "value": {"alarm_operating": True}},
                qualifiers={"mood": "only if the premises alarm is operating"},
                mode="OBSERVED",
            )
        ],
        delivery_key="embedded-condition",
    )
    await commit(world, slot(world), [term.accepted[0].server_evidence[0].evidence_id], value=terms)
    with pytest.raises(AssertionIneligible):
        await commit(world, slot(world), [condition.accepted[0].server_evidence[0].evidence_id])
    async with world.service() as (service, _, _):
        loaded = await service.read(world.reviewer, condition.accepted[0].record.id)
    assert loaded["record"]["qualifiers"]["mood"] == "only if the premises alarm is operating"
    assert counts(database)["canonical_fact_version"] == 1


async def test_reviewed_described_initial_use_cannot_close_or_supersede(world_factory, database):
    world = world_factory(origin="DESCRIBED")
    batch = await world.admit([world.candidate()])
    assertion_id = batch.accepted[0].record.id
    evidence = [batch.accepted[0].server_evidence[0].evidence_id]
    decision = (await review(world, assertion_id)).decision
    slot_id = slot(world)
    await commit(world, slot_id, evidence, decision.id)
    with pytest.raises(AssertionIneligible):
        await commit(world, slot_id, evidence, decision.id)
    assert counts(database)["canonical_commit"] == 1


@pytest.mark.parametrize("basis", ["INFERRED", "AMBIGUOUS"])
async def test_v2_correction_preserves_basis_and_owns_new_evidence(world, basis, database):
    record = world.candidate(interpretation_basis=basis, model_confidence=0.2)
    original = (await world.admit([record])).accepted[0]
    outcome = await review(world, original.record.id, correct={"amount": 700000})
    child_id = outcome.decision.corrected_assertion_id
    with Session(world.sync_engine) as session:
        parent = session.get(Assertion, original.record.id)
        child = session.get(Assertion, child_id)
        sem = session.get(AssertionSemantics, child_id)
        evidence = session.scalars(
            select(AssertionEvidence).where(AssertionEvidence.assertion_id == child_id)
        ).all()
        assert parent.value == {"amount": 500000, "currency": "USD"}
        assert child.value == {"amount": 700000} and child.original_assertion_id == parent.id
        assert child.semantic_contract_version == 2 and child.run_id is None
        assert child.subject_type == parent.subject_type == "Policy"
        assert child.interpretation_basis == sem.record["interpretation_basis"] == basis
        assert child.origin == sem.record["origin"] == "HUMAN_REVIEW"
        assert len(evidence) == 1 and evidence[0].id != original.server_evidence[0].evidence_id
        assert len(sem.raw_item_sha256) == len(sem.admission_sha256) == 64
    assert counts(database)["assertion"] == 2


async def test_correction_and_mixed_ancestry_cannot_clear_mood(world, database):
    original = (
        await world.admit([world.candidate(qualifiers={"mood": "subject to inspection"})])
    ).accepted[0]
    decision = (await review(world, original.record.id, correct={"amount": 700000})).decision
    with Session(world.sync_engine) as session:
        child_evidence = session.scalars(
            select(AssertionEvidence).where(
                AssertionEvidence.assertion_id == decision.corrected_assertion_id
            )
        ).one()
        child_id = child_evidence.id
    with pytest.raises(AssertionIneligible):
        await commit(world, slot(world), [child_id], decision.id)
    assert counts(database)["canonical_fact_version"] == 0


async def test_correction_rederives_a_new_locator_instead_of_trusting_offsets(world):
    original = (await world.admit([world.candidate(model_confidence=0.2)])).accepted[0]
    locator = EvidenceLocator(
        source=str(world.bundle.key.artifact_id),
        precision="exact-span",
        part="#/texts/0",
        selector=({"char_start": 99999, "char_end": 100000},),
    )
    result = await review(
        world, original.record.id, correct={"amount": 700000}, evidence_seen=locator
    )
    with Session(world.sync_engine) as session:
        sem = session.get(AssertionSemantics, result.decision.corrected_assertion_id)
        assert sem.verified_evidence[0]["selector"]["char_start"] == 0
        assert sem.verified_evidence[0]["selector"]["char_end"] == len(world.text)
        assert sem.record["evidence"][0]["model_selector"] is None


async def test_invalid_correction_is_refused_without_partial_claims(world, database):
    original = (await world.admit([world.candidate(model_confidence=0.2)])).accepted[0]
    before = counts(database)
    with pytest.raises(UnsupportedAssertionCorrection, match="invalid corrected claim"):
        await review(world, original.record.id, correct={"amount": float("nan")})
    assert counts(database) == before


@pytest.mark.parametrize("proof_kind", ["copied", "previous-transaction"])
async def test_source_authority_cannot_be_copied_or_reused(world, database, proof_kind):
    original = (await world.admit([world.candidate()])).accepted[0]
    evidence = [original.server_evidence[0].evidence_id]
    slot_id = slot(world)
    async with AsyncSession(world.engine, expire_on_commit=False) as session:
        repository = SqlAlchemyFactCommitRepository(session)
        service = CanonicalCommitService(repository)
        execution = AuthorizationExecution(
            SqlAlchemyAuthorityStore(session), world.policy, world.policy.release
        )

        async def sources():
            return await repository.commit_source_keys(evidence, None)

        async def effect(decisions):
            proof = repository.source_access_proof(decisions)
            if proof_kind == "copied":
                return await service.commit(
                    proposal(slot_id, evidence),
                    authorized_scope=world.owner,
                    authorization_decision_id=None,
                    source_access=replace(proof),
                )
            return proof

        if proof_kind == "copied":
            with pytest.raises(AssertionIneligible):
                await execution.mutate(
                    world.actor,
                    [ResourceKey(ResourceType.FACT_SLOT, slot_id)],
                    Action.COMMIT,
                    trace_id="copied-authority",
                    operation=effect,
                    additional_reads=sources,
                )
        else:
            proof = await execution.mutate(
                world.actor,
                [ResourceKey(ResourceType.FACT_SLOT, slot_id)],
                Action.COMMIT,
                trace_id="expired-authority",
                operation=effect,
                additional_reads=sources,
            )
            with pytest.raises(AssertionIneligible):
                await service.commit(
                    proposal(slot_id, evidence),
                    authorized_scope=world.owner,
                    authorization_decision_id=None,
                    source_access=proof,
                )
    assert counts(database)["canonical_commit"] == 0


@pytest.mark.parametrize("deny_source", [True, False])
async def test_http_source_denial_precedes_sanitized_eligibility_error(
    world, database, deny_source
):
    original = (
        await world.admit([world.candidate(qualifiers={"mood": "offered subject to inspection"})])
    ).accepted[0]
    with Session(world.sync_engine) as session, session.begin():
        slot_id = fixtures.seed_fact_slot(session, *world.owner, classifications=("commit-only",))
        principal = world.actor
        if deny_source:
            principal = fixtures.seed_principal(
                session,
                issuer="urn:f0006:limited",
                subject=str(uuid4()),
                kind=PrincipalKind.SERVICE,
            )
            fixtures.seed_grant(
                session,
                principal.id,
                *world.owner,
                "ServicePrincipal",
                classifications={"commit-only"},
            )
    app = create_app()

    async def session_override():
        async with AsyncSession(world.engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db_session] = session_override
    app.dependency_overrides[current_principal] = lambda: principal
    body = wire_value(proposal(slot_id, [original.server_evidence[0].evidence_id]))
    body.pop("slot_id")
    body["idempotency_key"] = "f0006-http-fixture"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(f"/facts/{slot_id}/commits", json=body)
    assert response.status_code == (404 if deny_source else 422)
    assert response.json()["code"] == ("not_found" if deny_source else "ASSERTION_INELIGIBLE")
    assert "application/problem+json" in response.headers["content-type"]
    assert world.text not in response.text and "offered subject to inspection" not in response.text
    assert counts(database)["canonical_fact_version"] == 0
