from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from brain_domain.authx import (
    Action,
    AuthorizationDecision,
    RequestedScope,
    ResourceKey,
    ResourceType,
)
from brain_domain.facts import ChangeReason, CommitProposal, CommitResult, FactVersion
from brain_domain.principal import Principal
from brain_persistence.repositories import SqlAlchemyFactCommitRepository
from brain_security.execution import AuthorizationExecution
from brain_temporal.commit import CanonicalCommitService, FactSlotNotFound, StaleVersionError
from brain_temporal.ranges import InvalidRangeError
from fastapi import APIRouter, Depends, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from brain_api.deps import (
    current_principal,
    get_authorization_execution,
    get_db_session,
    new_trace_id,
)
from brain_api.errors import (
    ConcurrentCommitApiError,
    InvalidRangeApiError,
    NotFoundError,
    StaleVersionApiError,
)
from brain_api.schemas.facts import CommitProposalIn, CommitResponseOut, FactVersionOut

router = APIRouter(prefix="/facts", tags=["Facts"])


def _slot(fact_slot_id: UUID) -> ResourceKey:
    return ResourceKey(ResourceType.FACT_SLOT, fact_slot_id)


@router.get("/{fact_slot_id}", response_model=FactVersionOut)
async def get_fact(
    fact_slot_id: UUID,
    valid_as_of: datetime | None = Query(default=None, alias="validAsOf"),
    known_as_of: datetime | None = Query(default=None, alias="knownAsOf"),
    principal: Principal = Depends(current_principal),
    execution: AuthorizationExecution = Depends(get_authorization_execution),
    session: AsyncSession = Depends(get_db_session),
) -> FactVersionOut:
    """Business valid/known coordinates select history only; authorization always
    uses current enforcement time and current grants (S0003 AC4)."""
    repository = SqlAlchemyFactCommitRepository(session)
    now = datetime.now(UTC)
    requested = RequestedScope(
        knowledge_base_ids=None,
        selectors=(),
        business_valid_as_of=valid_as_of,
        business_known_as_of=known_as_of,
    )

    async def load(_decision: AuthorizationDecision) -> FactVersion:
        version = await repository.resolve_at(
            fact_slot_id, valid_as_of=valid_as_of or now, known_as_of=known_as_of or now
        )
        if version is None:
            raise NotFoundError()
        return version

    version = await execution.read(
        principal,
        _slot(fact_slot_id),
        Action.READ,
        trace_id=new_trace_id(),
        load=load,
        requested=requested,
    )
    return FactVersionOut.from_domain(version)


@router.post("/{fact_slot_id}/commits", response_model=CommitResponseOut, status_code=201)
async def commit_fact(
    fact_slot_id: UUID,
    proposal_in: CommitProposalIn,
    principal: Principal = Depends(current_principal),
    execution: AuthorizationExecution = Depends(get_authorization_execution),
    session: AsyncSession = Depends(get_db_session),
) -> CommitResponseOut:
    """The commit independently re-checks current `fact_slot:commit` authority inside
    its own unit of work; a review annotation never implies it (S0006 AC5)."""
    service = CanonicalCommitService(SqlAlchemyFactCommitRepository(session))
    proposal = CommitProposal(
        slot_id=fact_slot_id,
        value=proposal_in.value,
        valid_from=proposal_in.valid_from,
        valid_to=proposal_in.valid_to,
        change_reason=(
            ChangeReason(proposal_in.change_reason) if proposal_in.change_reason else None
        ),
        evidence_refs=tuple(proposal_in.evidence_refs),
        review_decision_id=proposal_in.review_decision_id,
        source_received_at=proposal_in.source_received_at,
        artifact_created_at=proposal_in.artifact_created_at,
        assertion_created_at=proposal_in.assertion_created_at,
        expected_current_version_id=proposal_in.expected_current_version_id,
        idempotency_key=proposal_in.idempotency_key,
    )

    async def operation(decisions: Sequence[AuthorizationDecision]) -> CommitResult:
        (decision,) = decisions
        assert decision.scope is not None
        return await service.commit(
            proposal,
            authorized_scope=(decision.scope.tenant_id, decision.scope.knowledge_base_id),
            authorization_decision_id=decision.decision_id,
        )

    try:
        result = await execution.mutate(
            principal,
            [_slot(fact_slot_id)],
            Action.COMMIT,
            trace_id=new_trace_id(),
            operation=operation,
        )
    except InvalidRangeError as exc:
        raise InvalidRangeApiError(str(exc)) from exc
    except StaleVersionError as exc:
        raise StaleVersionApiError(str(exc)) from exc
    except FactSlotNotFound as exc:
        raise NotFoundError() from exc
    except IntegrityError as exc:
        # The GiST exclusion constraint is the backstop if the row lock somehow
        # didn't serialize a concurrent commit on this slot (F0001-S0005 AC).
        raise ConcurrentCommitApiError(str(exc)) from exc
    return CommitResponseOut.from_domain(result)
