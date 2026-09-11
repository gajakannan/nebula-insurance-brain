from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from brain_domain.principal import PrincipalKind
from brain_domain.review import (
    EvidenceLocator,
    ReviewDecisionAction,
    ReviewDecisionReasonCode,
    ReviewItemStatus,
    ReviewItemType,
)
from brain_persistence.base import Base, sqlite_test_tables
from brain_persistence.models import (
    Assertion,
    ContentArtifact,
    DocumentVersion,
    ReviewItemRow,
    SourceDocument,
)
from brain_persistence.repositories import (
    ReviewDecisionAuditSink,
    SqlAlchemyAuditEventRepository,
    SqlAlchemyPrincipalRepository,
    SqlAlchemyReviewItemRepository,
)
from brain_persistence.session import make_engine, make_session_factory, session_scope
from brain_review.decisions import DecisionRequest, ReviewDecisionService
from brain_security.principals import PrincipalResolver
from brain_security.verification import VerifiedCredential


@pytest.fixture
async def session_factory():
    engine = make_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all, tables=sqlite_test_tables())
    yield make_session_factory(engine)
    await engine.dispose()


async def _seed_assertion(session, *, confidence: float = 0.41) -> tuple:
    source = SourceDocument(tenant_id=uuid4(), knowledge_base_id=uuid4(), source_sha256="a" * 64)
    session.add(source)
    await session.flush()
    version = DocumentVersion(source_document_id=source.id)
    session.add(version)
    await session.flush()
    artifact = ContentArtifact(
        id=uuid4(),
        document_version_id=version.id,
        artifact_sha256="b" * 64,
        page_count=1,
        extraction_status="complete",
    )
    session.add(artifact)
    await session.flush()
    assertion = Assertion(
        id=uuid4(),
        run_id=None,
        origin="MACHINE_EXTRACTION",
        subject_type="Policy",
        slot_type="each_occurrence_limit",
        value={"value": "$20,000,000"},
        model_confidence=confidence,
        interpretation_basis="EXPLICIT",
    )
    session.add(assertion)
    await session.flush()
    return source, artifact, assertion


async def test_principal_repository_creates_and_finds(session_factory) -> None:
    async with session_scope(session_factory) as session:
        repo = SqlAlchemyPrincipalRepository(session)
        resolver = PrincipalResolver(repo)
        credential = VerifiedCredential(
            issuer="https://authentik.local",
            subject="alice.tenant-a",
            audience="brain",
            expires_at=datetime.now(UTC),
            not_before=None,
            key_id="k1",
        )
        first = await resolver.resolve(credential)

    async with session_scope(session_factory) as session:
        repo = SqlAlchemyPrincipalRepository(session)
        resolver = PrincipalResolver(repo)
        second = await resolver.resolve(credential)

    assert first.id == second.id
    assert first.kind == PrincipalKind.USER


async def test_full_review_round_trip_across_two_transactions(session_factory) -> None:
    """F0001-S0004: submit a correction, then — in a *new* session, simulating a
    service restart — verify the decision and corrected assertion both persisted."""
    async with session_scope(session_factory) as session:
        _source, artifact, assertion = await _seed_assertion(session)
        review_item = ReviewItemRow(
            id=uuid4(),
            type=ReviewItemType.LOW_CONFIDENCE_ASSERTION.value,
            status=ReviewItemStatus.OPEN.value,
            assertion_id=assertion.id,
            assertion_version=1,
            tenant_id=uuid4(),
            knowledge_base_id=uuid4(),
            review_batch_id=None,
        )
        session.add(review_item)
        await session.flush()
        review_item.review_batch_id = uuid4()
        await session.flush()
        review_item_id = review_item.id

    reviewer_id = uuid4()
    async with session_scope(session_factory) as session:
        repository = SqlAlchemyReviewItemRepository(session)
        audit = ReviewDecisionAuditSink(SqlAlchemyAuditEventRepository(session))
        service = ReviewDecisionService(repository, audit)
        outcome = await service.submit(
            DecisionRequest(
                review_item_id=review_item_id,
                action=ReviewDecisionAction.CORRECT,
                reviewer_principal_id=reviewer_id,
                assertion_version=1,
                reason_code=ReviewDecisionReasonCode.MISREAD_VALUE,
                corrected_value={"value": "$2,000,000"},
                evidence_seen=EvidenceLocator(source=str(artifact.id), precision="exact-span"),
            )
        )
        assert outcome.applied is True
        corrected_assertion_id = outcome.decision.corrected_assertion_id

    # New session/transaction — proves durability, not an in-memory artifact of the first.
    async with session_scope(session_factory) as session:
        repository = SqlAlchemyReviewItemRepository(session)
        reloaded_decision = await repository.get_decision_by_event_sha256(
            review_item_id, outcome.decision.event_sha256
        )
        assert reloaded_decision is not None
        assert reloaded_decision.corrected_assertion_id == corrected_assertion_id

        corrected_row = await session.get(Assertion, corrected_assertion_id)
        assert corrected_row.origin == "HUMAN_REVIEW"
        assert corrected_row.original_assertion_id == assertion.id
        assert corrected_row.value == {"value": "$2,000,000"}

        original_row = await session.get(Assertion, assertion.id)
        assert original_row.value == {"value": "$20,000,000"}
        assert original_row.model_confidence == 0.41
