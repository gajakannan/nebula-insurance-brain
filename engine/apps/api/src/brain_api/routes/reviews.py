from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID, uuid4

from brain_domain.principal import Membership, Principal
from brain_domain.review import (
    EvidenceLocator,
    ReviewDecisionAction,
    ReviewDecisionReasonCode,
)
from brain_persistence.repositories import (
    ReviewDecisionAuditSink,
    SqlAlchemyAuditEventRepository,
    SqlAlchemyReviewItemRepository,
)
from brain_review.decisions import (
    DecisionRequest,
    InvalidBlockedReasonCode,
    ReviewDecisionService,
    ReviewItemAlreadyDecided,
    ReviewItemNotFound,
    UnresolvedEvidenceRequiresBlocked,
)
from brain_security.authorization import AuthorizationService, ResourceRef
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from brain_api.deps import (
    current_principal,
    current_principal_memberships,
    get_authorization_service,
    get_db_session,
)
from brain_api.errors import NotFoundError, UnprocessableError
from brain_api.schemas.review import (
    EvidenceLocatorOut,
    ReviewDecisionBatchIn,
    ReviewDecisionIn,
    ReviewDecisionReceiptOut,
    ReviewItemOut,
)

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def _to_domain_evidence(evidence: EvidenceLocatorOut | None) -> EvidenceLocator | None:
    if evidence is None:
        return None
    return EvidenceLocator(
        source=evidence.source,
        precision=evidence.precision,
        part=evidence.part,
        unresolved_reason=evidence.unresolved_reason,
        selector=tuple(evidence.selector),
    )


def _to_decision_request(
    decision_in: ReviewDecisionIn, reviewer_principal_id: UUID
) -> DecisionRequest:
    return DecisionRequest(
        review_item_id=decision_in.review_item_id,
        action=ReviewDecisionAction(decision_in.action),
        reviewer_principal_id=reviewer_principal_id,
        assertion_version=decision_in.assertion_version,
        reason_code=ReviewDecisionReasonCode(decision_in.reason_code)
        if decision_in.reason_code
        else None,
        corrected_value=decision_in.corrected_value,
        evidence_seen=_to_domain_evidence(decision_in.evidence),
        reviewer_comment=decision_in.reviewer_comment,
    )


@router.get("/{review_item_id}", response_model=ReviewItemOut)
async def get_review_item(
    review_item_id: UUID,
    principal: Principal = Depends(current_principal),
    memberships: Sequence[Membership] = Depends(current_principal_memberships),
    authz: AuthorizationService = Depends(get_authorization_service),
    session: AsyncSession = Depends(get_db_session),
) -> ReviewItemOut:
    repository = SqlAlchemyReviewItemRepository(session)
    item = await repository.get(review_item_id)
    if item is None:
        raise NotFoundError()

    resource = ResourceRef(
        type="review_task",
        id=item.id,
        tenant_id=item.tenant_id,
        knowledge_base_id=item.knowledge_base_id,
    )
    decision = await authz.authorize(
        principal, memberships, resource, "read", trace_id=str(uuid4())
    )
    if not decision.allowed:
        raise NotFoundError()  # denial reported as 404, existence never disclosed

    latest_decision = await repository.get_latest_decision(review_item_id)
    return ReviewItemOut.from_domain(item, latest_decision)


@router.post("/batches/{review_batch_id}/decisions", response_model=ReviewDecisionReceiptOut)
async def submit_review_decisions(
    review_batch_id: UUID,
    batch: ReviewDecisionBatchIn,
    principal: Principal = Depends(current_principal),
    memberships: Sequence[Membership] = Depends(current_principal_memberships),
    authz: AuthorizationService = Depends(get_authorization_service),
    session: AsyncSession = Depends(get_db_session),
) -> ReviewDecisionReceiptOut:
    repository = SqlAlchemyReviewItemRepository(session)
    audit = ReviewDecisionAuditSink(SqlAlchemyAuditEventRepository(session))
    service = ReviewDecisionService(repository, audit)

    decision_ids: list[UUID] = []
    applied = 0
    any_duplicate = False
    stale = 0
    blocked = 0

    for decision_in in batch.decisions:
        item = await repository.get(decision_in.review_item_id)
        if item is None or item.review_batch_id != review_batch_id:
            raise UnprocessableError()

        resource = ResourceRef(
            type="review_task",
            id=item.id,
            tenant_id=item.tenant_id,
            knowledge_base_id=item.knowledge_base_id,
        )
        authz_decision = await authz.authorize(
            principal, memberships, resource, "annotate", trace_id=str(uuid4())
        )
        if not authz_decision.allowed:
            raise NotFoundError()

        try:
            outcome = await service.submit(_to_decision_request(decision_in, principal.id))
        except ReviewItemNotFound as exc:
            raise UnprocessableError() from exc
        except (
            ReviewItemAlreadyDecided,
            UnresolvedEvidenceRequiresBlocked,
            InvalidBlockedReasonCode,
        ) as exc:
            raise UnprocessableError() from exc

        decision_ids.append(outcome.decision.id)
        if outcome.duplicate:
            any_duplicate = True
        elif outcome.decision.stale:
            stale += 1
        elif outcome.decision.action == ReviewDecisionAction.BLOCKED:
            blocked += 1
            applied += 1
        elif outcome.applied:
            applied += 1

    await session.commit()
    return ReviewDecisionReceiptOut(
        decision_ids=decision_ids,
        applied=applied,
        duplicate=any_duplicate,
        stale=stale,
        blocked=blocked,
    )
