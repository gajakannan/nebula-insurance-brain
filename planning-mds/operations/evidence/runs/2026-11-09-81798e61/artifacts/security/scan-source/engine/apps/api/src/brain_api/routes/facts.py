from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from brain_assertions.eligibility import AssertionIneligible
from brain_domain.authx import (
    Action,
    AuthorizationDecision,
    RequestedScope,
    ResourceKey,
    ResourceType,
)
from brain_domain.fact_answers import FactAnswerRejected
from brain_domain.facts import ChangeReason, CommitProposal, CommitResult, FactVersion
from brain_domain.principal import Principal
from brain_factslots.answers import FactAnswerPolicy, FactAnswerReader
from brain_factslots.ports import PredicateContractRegistry
from brain_persistence.fact_slots import SqlAlchemyFactSlotStore
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
    get_predicate_registry,
    new_trace_id,
)
from brain_api.errors import (
    AssertionIneligibleApiError,
    ConcurrentCommitApiError,
    FactAnswerRejectedApiError,
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
    answers = FactAnswerReader(SqlAlchemyFactSlotStore(session))
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

    async def scope_reads(version: FactVersion) -> Sequence[ResourceKey]:
        # WHY: authorize the scope of this exact payload in the slot read's UoW.
        # A prior independent read commits and releases authority locks, and a
        # second version selection could return a different, unchecked scope.
        return await answers.scope_keys_for_value(fact_slot_id, version.value)

    version = await execution.read(
        principal,
        _slot(fact_slot_id),
        Action.READ,
        trace_id=new_trace_id(),
        load=load,
        requested=requested,
        additional_reads=scope_reads,
    )
    return FactVersionOut.from_domain(version)


@router.post("/{fact_slot_id}/commits", response_model=CommitResponseOut, status_code=201)
async def commit_fact(
    fact_slot_id: UUID,
    proposal_in: CommitProposalIn,
    principal: Principal = Depends(current_principal),
    execution: AuthorizationExecution = Depends(get_authorization_execution),
    session: AsyncSession = Depends(get_db_session),
    registry: PredicateContractRegistry = Depends(get_predicate_registry),
) -> CommitResponseOut:
    """The commit independently re-checks current `fact_slot:commit` authority inside
    its own unit of work; a review annotation never implies it (S0006 AC5).

    F0007: an identity-v1 slot validates the `fact-answer/v1` carrier after the
    slot lock. The answer's scope artifact and name-evidence artifacts join the
    READ checks, so an unreadable scope is denied before any reason (T-08)."""
    repository = SqlAlchemyFactCommitRepository(session)
    answer_policy = FactAnswerPolicy(registry, SqlAlchemyFactSlotStore(session))
    service = CanonicalCommitService(repository, answer_policy=answer_policy)
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

    evidence_keys: set[ResourceKey] = set()

    async def operation(decisions: Sequence[AuthorizationDecision]) -> CommitResult:
        decision = next(
            d for d in decisions if d.resource == _slot(fact_slot_id) and d.action == Action.COMMIT
        )
        assert decision.scope is not None
        # The F0006 source proof covers exactly the evidence-derived reads; reads
        # added for the answer's scope or name evidence are authorized but excluded.
        evidence_reads = [
            d
            for d in decisions
            if d.resource in evidence_keys
            or not (d.action == Action.READ and d.resource.type == ResourceType.CONTENT_ARTIFACT)
        ]
        return await service.commit(
            proposal,
            authorized_scope=(decision.scope.tenant_id, decision.scope.knowledge_base_id),
            authorization_decision_id=decision.decision_id,
            source_access=repository.source_access_proof(evidence_reads),
        )

    async def source_keys() -> Sequence[ResourceKey]:
        evidence_keys.update(
            await repository.commit_source_keys(proposal.evidence_refs, proposal.review_decision_id)
        )
        answer_keys = await answer_policy.source_keys(fact_slot_id, proposal.value)
        return sorted(evidence_keys | set(answer_keys))

    try:
        result = await execution.mutate(
            principal,
            [_slot(fact_slot_id)],
            Action.COMMIT,
            trace_id=new_trace_id(),
            operation=operation,
            additional_reads=source_keys,
        )
    except AssertionIneligible as exc:
        raise AssertionIneligibleApiError() from exc
    except FactAnswerRejected as exc:
        raise FactAnswerRejectedApiError(exc.code) from exc
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
