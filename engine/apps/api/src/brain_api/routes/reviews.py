from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from brain_domain.authx import Action, AuthorizationDecision, ResourceKey, ResourceType
from brain_domain.principal import Principal
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
from brain_security.execution import AuthorizationExecution
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from brain_api.deps import (
    current_principal,
    get_authorization_execution,
    get_db_session,
    new_trace_id,
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


def _task(review_item_id: UUID) -> ResourceKey:
    return ResourceKey(ResourceType.REVIEW_TASK, review_item_id)


@router.get("/{review_item_id}", response_model=ReviewItemOut)
async def get_review_item(
    review_item_id: UUID,
    principal: Principal = Depends(current_principal),
    execution: AuthorizationExecution = Depends(get_authorization_execution),
    session: AsyncSession = Depends(get_db_session),
) -> ReviewItemOut:
    repository = SqlAlchemyReviewItemRepository(session)

    async def load(_decision: AuthorizationDecision) -> ReviewItemOut:
        item = await repository.get(review_item_id)
        if item is None:
            raise NotFoundError()
        latest_decision = await repository.get_latest_decision(review_item_id)
        return ReviewItemOut.from_domain(item, latest_decision)

    # Denial reported as 404, existence never disclosed.
    return await execution.read(
        principal, _task(review_item_id), Action.READ, trace_id=new_trace_id(), load=load
    )


@router.post("/batches/{review_batch_id}/decisions", response_model=ReviewDecisionReceiptOut)
async def submit_review_decisions(
    review_batch_id: UUID,
    batch: ReviewDecisionBatchIn,
    principal: Principal = Depends(current_principal),
    execution: AuthorizationExecution = Depends(get_authorization_execution),
    session: AsyncSession = Depends(get_db_session),
) -> ReviewDecisionReceiptOut:
    """Every item is authorized (current grant, restrictions, `review_task:annotate`)
    and locked before any decision is written; an inaccessible item is a
    non-disclosing 404 before any batch-membership check. The whole batch commits
    with its decisions, or rolls back and durably audits the failure (S0004 AC5/AC6).
    Annotation never grants `fact_slot:commit` and never promotes to canonical truth."""
    repository = SqlAlchemyReviewItemRepository(session, actor_id=principal.id)

    async def operation(
        decisions: Sequence[AuthorizationDecision],
    ) -> ReviewDecisionReceiptOut:
        authorizations = {d.resource.id: d for d in decisions}
        audit = ReviewDecisionAuditSink(SqlAlchemyAuditEventRepository(session), authorizations)
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
            try:
                outcome = await service.submit(_to_decision_request(decision_in, principal.id))
            except (
                ReviewItemNotFound,
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
        return ReviewDecisionReceiptOut(
            decision_ids=decision_ids,
            applied=applied,
            duplicate=any_duplicate,
            stale=stale,
            blocked=blocked,
        )

    return await execution.mutate(
        principal,
        [_task(d.review_item_id) for d in batch.decisions],
        Action.ANNOTATE,
        trace_id=new_trace_id(),
        operation=operation,
    )
