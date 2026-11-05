"""Protected claim payloads are never selected during authority discovery."""

from contextlib import contextmanager
from uuid import uuid4

import pytest
from brain_assertions.eligibility import AssertionIneligible
from brain_domain.authx import ResourceKey, ResourceType
from brain_persistence.assertions import SqlAlchemyAssertionRepository, discover_sources
from brain_persistence.models import Assertion, ReviewItemRow
from brain_persistence.repositories import (
    SqlAlchemyFactCommitRepository,
    SqlAlchemyReviewItemRepository,
)
from brain_security.execution import AuthorizationDenied
from brain_testing import fixtures
from engine.tests.fixtures.assertions import harness
from engine.tests.integration.test_assertion_consumers import commit, review, slot
from sqlalchemy import event, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

_clean_fact_tables = harness._clean_fact_tables
database = harness.database
world = harness.world
world_factory = harness.world_factory
counts = harness.counts


@contextmanager
def capture_selects(world):
    statements = []

    def observe(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().lower().startswith("select"):
            statements.append(statement.lower().replace('"', ""))

    event.listen(world.engine.sync_engine, "before_cursor_execute", observe)
    try:
        yield statements
    finally:
        event.remove(world.engine.sync_engine, "before_cursor_execute", observe)


def assert_no_protected_projection(statements):
    assert statements
    forbidden = (
        "assertion.value",
        "assertion_semantics",
        "review_item.evidence",
        "review_decision.corrected_value",
        "review_decision.evidence_seen",
    )
    for statement in statements:
        assert not any(column in statement for column in forbidden), statement


@pytest.mark.parametrize("consumer", ["read", "commit", "review", "decision-lineage"])
async def test_source_discovery_selects_only_linkage_metadata(world, consumer):
    original = (await world.admit([world.candidate(model_confidence=0.2)])).accepted[0]
    decision = None
    if consumer == "decision-lineage":
        decision = (await review(world, original.record.id, correct={"amount": 700000})).decision
    with Session(world.sync_engine) as session:
        item_id = session.scalar(
            select(ReviewItemRow.id).where(ReviewItemRow.assertion_id == original.record.id)
        )
    evidence = [original.server_evidence[0].evidence_id]
    with capture_selects(world) as statements:
        async with AsyncSession(world.engine) as session:
            if consumer == "read":
                keys = await SqlAlchemyAssertionRepository(session).source_keys(original.record.id)
            elif consumer == "review":
                keys = await SqlAlchemyReviewItemRepository(session).source_keys([item_id])
            else:
                keys = await SqlAlchemyFactCommitRepository(session).commit_source_keys(
                    evidence, decision.id if decision else None
                )
    assert keys == (ResourceKey(ResourceType.CONTENT_ARTIFACT, world.context.artifact_id),)
    assert_no_protected_projection(statements)


async def test_direct_commit_without_source_proof_reads_no_claim_payload(world, database):
    original = (await world.admit([world.candidate()])).accepted[0]
    slot_id = slot(world)
    with capture_selects(world) as statements, pytest.raises(AssertionIneligible):
        await commit(world, slot_id, [original.server_evidence[0].evidence_id], authorized=False)
    assert_no_protected_projection(statements)
    assert counts(database)["canonical_fact_version"] == 0


async def test_denied_internal_read_never_materializes_value_or_excerpt(world):
    original = (await world.admit([world.candidate()])).accepted[0]
    with Session(world.sync_engine) as session, session.begin():
        denied = fixtures.seed_principal(session, issuer="urn:f0006:denied", subject=str(uuid4()))
    with capture_selects(world) as statements, pytest.raises(AuthorizationDenied):
        async with world.service() as (service, _, _):
            await service.read(denied, original.record.id)
    assert_no_protected_projection(statements)


@pytest.mark.parametrize("corruption", ["missing", "cycle", "overlong"])
async def test_corrupt_discovery_fails_closed_without_payload_reads(world, database, corruption):
    identities = [uuid4() for _ in range(257 if corruption == "overlong" else 2)]
    with capture_selects(world) as statements:
        async with AsyncSession(world.engine) as session:
            try:
                if corruption != "missing":
                    await session.execute(text("SET CONSTRAINTS ALL DEFERRED"))
                    records = []
                    for index, identity in enumerate(identities):
                        parent = (
                            identities[1 - index]
                            if corruption == "cycle"
                            else identities[index - 1]
                            if index
                            else None
                        )
                        records.append(
                            dict(
                                id=identity,
                                run_id=None,
                                origin="HUMAN_REVIEW",
                                version=1,
                                original_assertion_id=parent,
                                subject_type="Policy",
                                slot_type="limit",
                                value={"amount": 1},
                                model_confidence=None,
                                interpretation_basis="EXPLICIT",
                                tenant_id=world.owner[0],
                                knowledge_base_id=world.owner[1],
                            )
                        )
                    await session.execute(Assertion.__table__.insert(), records)
                with pytest.raises(AssertionIneligible):
                    await discover_sources(session, (), None, assertion_ids=(identities[-1],))
            finally:
                await session.rollback()
    assert_no_protected_projection(statements)
    assert counts(database)["assertion"] == 0
