from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from brain_domain.authx import (
    AuthorizationDecision,
    OperationOutcome,
    ReasonCode,
    ResourceKey,
    ResourceType,
)
from brain_domain.principal import PrincipalKind
from brain_domain.review import (
    EvidenceLocator,
    ReviewDecisionAction,
    ReviewDecisionReasonCode,
    ReviewItemStatus,
    ReviewItemType,
)
from brain_domain.tenancy import OwnedScope
from brain_persistence.base import Base, sqlite_test_tables
from brain_persistence.identity import SqlAlchemyIdentityRepository
from brain_persistence.models import (
    Assertion,
    AuditEventRow,
    ContentArtifact,
    DocumentVersion,
    ExternalIdentityRow,
    PrincipalAuthorityRow,
    ReviewItemRow,
    SourceDocument,
)
from brain_persistence.repositories import (
    ReviewDecisionAuditSink,
    SqlAlchemyAuditEventRepository,
    SqlAlchemyReviewItemRepository,
)
from brain_persistence.session import make_engine, make_session_factory, session_scope
from brain_review.decisions import DecisionRequest, ReviewDecisionService
from sqlalchemy import select


@pytest.fixture
async def session_factory():
    engine = make_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all, tables=sqlite_test_tables())
    yield make_session_factory(engine)
    await engine.dispose()


async def _seed_assertion(session, *, confidence: float = 0.41) -> tuple:
    owner = {"tenant_id": uuid4(), "knowledge_base_id": uuid4()}
    source = SourceDocument(source_sha256="a" * 64, **owner)
    session.add(source)
    await session.flush()
    version = DocumentVersion(source_document_id=source.id, **owner)
    session.add(version)
    await session.flush()
    artifact = ContentArtifact(
        id=uuid4(),
        document_version_id=version.id,
        artifact_sha256="b" * 64,
        page_count=1,
        extraction_status="complete",
        **owner,
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
        **owner,
    )
    session.add(assertion)
    await session.flush()
    return source, artifact, assertion


async def test_identity_repository_resolves_one_stable_principal(session_factory) -> None:
    """F0002-S0002 AC1/AC2: first verified sight creates principal + alias + authority
    revision 1 with no grants; later sessions return the same ID; the same subject
    at another issuer is a different principal."""
    async with session_scope(session_factory) as session:
        first = await SqlAlchemyIdentityRepository(session).resolve_or_create(
            "https://issuer-x", "alice.tenant-a", PrincipalKind.USER
        )
    async with session_scope(session_factory) as session:
        repo = SqlAlchemyIdentityRepository(session)
        second = await repo.find_by_alias("https://issuer-x", "alice.tenant-a")
        other = await repo.resolve_or_create(
            "https://issuer-y", "alice.tenant-a", PrincipalKind.USER
        )
        authority = await session.get(PrincipalAuthorityRow, first.id)
        alias = await session.get(ExternalIdentityRow, ("https://issuer-x", "alice.tenant-a"))

    assert second is not None and second.id == first.id
    assert first.kind == PrincipalKind.USER
    assert other.id != first.id
    assert authority is not None and authority.revision == 1
    assert alias is not None and alias.approval_ref is None


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
            tenant_id=assertion.tenant_id,
            knowledge_base_id=assertion.knowledge_base_id,
            review_batch_id=None,
        )
        session.add(review_item)
        await session.flush()
        review_item.review_batch_id = uuid4()
        await session.flush()
        review_item_id = review_item.id

    reviewer_id = uuid4()
    authorization = AuthorizationDecision(
        decision_id=uuid4(),
        occurred_at=datetime.now(UTC),
        authenticated_principal_id=reviewer_id,
        actor_principal_id=reviewer_id,
        actor_kind=PrincipalKind.USER,
        executor_principal_id=None,
        delegation_id=None,
        delegation_revision=None,
        scope=OwnedScope(assertion.tenant_id, uuid4(), assertion.knowledge_base_id),
        resource=ResourceKey(ResourceType.REVIEW_TASK, review_item_id),
        resource_revision=1,
        restriction_revision=1,
        action="annotate",
        allowed=True,
        reason_code=ReasonCode.ALLOWED,
        policy_hash="a" * 64,
        policy_release="sha256:" + "b" * 64,
        grant_revision=3,
        matched_membership_ids=(uuid4(),),
        trace_id="trace-review",
        operation_outcome=OperationOutcome.ATTEMPTED,
    )
    async with session_scope(session_factory) as session:
        repository = SqlAlchemyReviewItemRepository(session)
        audit = ReviewDecisionAuditSink(
            SqlAlchemyAuditEventRepository(session), {review_item_id: authorization}
        )
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
        # A correction inherits its original's ownership (F0002-S0001).
        assert (corrected_row.tenant_id, corrected_row.knowledge_base_id) == (
            original_row.tenant_id,
            original_row.knowledge_base_id,
        )
        # The review-outcome audit references the durable authorization decision and
        # carries its policy hash and authority revision, not "n/a"/0 (F0002-S0006).
        review_audit = (
            await session.execute(
                select(AuditEventRow).where(AuditEventRow.event_type == "review_decision_recorded")
            )
        ).scalar_one()
        assert review_audit.decision_id == authorization.decision_id
        assert review_audit.policy_hash == "a" * 64
        assert review_audit.grant_revision == 3
