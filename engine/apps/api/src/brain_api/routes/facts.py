from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

from brain_domain.facts import ChangeReason, CommitProposal
from brain_domain.principal import Membership, Principal
from brain_persistence.repositories import SqlAlchemyFactCommitRepository
from brain_security.authorization import AuthorizationService, ResourceRef
from brain_temporal.commit import CanonicalCommitService, FactSlotNotFound, StaleVersionError
from brain_temporal.ranges import InvalidRangeError
from fastapi import APIRouter, Depends, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from brain_api.deps import (
    current_principal,
    current_principal_memberships,
    get_authorization_service,
    get_db_session,
)
from brain_api.errors import (
    ConcurrentCommitApiError,
    InvalidRangeApiError,
    NotFoundError,
    StaleVersionApiError,
)
from brain_api.schemas.facts import CommitProposalIn, CommitResponseOut, FactVersionOut

router = APIRouter(prefix="/facts", tags=["Facts"])


@router.get("/{fact_slot_id}", response_model=FactVersionOut)
async def get_fact(
    fact_slot_id: UUID,
    valid_as_of: datetime | None = Query(default=None, alias="validAsOf"),
    known_as_of: datetime | None = Query(default=None, alias="knownAsOf"),
    principal: Principal = Depends(current_principal),
    memberships: Sequence[Membership] = Depends(current_principal_memberships),
    authz: AuthorizationService = Depends(get_authorization_service),
    session: AsyncSession = Depends(get_db_session),
) -> FactVersionOut:
    repository = SqlAlchemyFactCommitRepository(session)
    slot = await repository.get_slot(fact_slot_id)
    if slot is None:
        raise NotFoundError()
    tenant_id, knowledge_base_id = slot

    resource = ResourceRef(
        type="fact_slot", id=fact_slot_id, tenant_id=tenant_id, knowledge_base_id=knowledge_base_id
    )
    decision = await authz.authorize(
        principal, memberships, resource, "read", trace_id=str(uuid4())
    )
    if not decision.allowed:
        raise NotFoundError()  # denial -> 404, never disclosed

    now = datetime.now(UTC)
    version = await repository.resolve_at(
        fact_slot_id,
        valid_as_of=valid_as_of or now,
        known_as_of=known_as_of or now,
    )
    if version is None:
        raise NotFoundError()
    return FactVersionOut.from_domain(version)


@router.post("/{fact_slot_id}/commits", response_model=CommitResponseOut, status_code=201)
async def commit_fact(
    fact_slot_id: UUID,
    proposal_in: CommitProposalIn,
    principal: Principal = Depends(current_principal),
    memberships: Sequence[Membership] = Depends(current_principal_memberships),
    authz: AuthorizationService = Depends(get_authorization_service),
    session: AsyncSession = Depends(get_db_session),
) -> CommitResponseOut:
    repository = SqlAlchemyFactCommitRepository(session)
    service = CanonicalCommitService(repository, authz)

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

    try:
        result = await service.commit(principal, memberships, proposal, trace_id=str(uuid4()))
    except InvalidRangeError as exc:
        await session.rollback()
        raise InvalidRangeApiError(str(exc)) from exc
    except StaleVersionError as exc:
        await session.rollback()
        raise StaleVersionApiError(str(exc)) from exc
    except FactSlotNotFound as exc:
        await session.rollback()
        raise NotFoundError() from exc
    except IntegrityError as exc:
        # The GiST exclusion constraint is the backstop if the row lock somehow
        # didn't serialize a concurrent commit on this slot (F0001-S0005 AC).
        await session.rollback()
        raise ConcurrentCommitApiError(str(exc)) from exc

    await session.commit()
    return CommitResponseOut.from_domain(result)
