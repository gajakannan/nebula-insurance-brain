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
from brain_domain.facts import ChangeReason, CommitProposal, CommitResult
from brain_domain.principal import Principal
from brain_domain.temporal import TemporalRejected
from brain_factslots.answers import FactAnswerPolicy, FactAnswerReader
from brain_factslots.ports import PredicateContractRegistry
from brain_persistence.fact_slots import SqlAlchemyFactSlotStore
from brain_persistence.repositories import SqlAlchemyFactCommitRepository
from brain_security.execution import AuthorizationExecution
from brain_temporal.commit import (
    CanonicalCommitService,
    FactSlotNotFound,
    LegacyTemporalUnsupported,
    StaleVersionError,
)
from brain_temporal.ranges import InvalidRangeError
from brain_temporal.reader import Resolved, TemporalFactReader, ValidityUnknown
from fastapi import APIRouter, Depends, Query
from sqlalchemy.exc import DBAPIError, IntegrityError
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
    TemporalBlockUnsupportedApiError,
    TemporalConflictApiError,
    TemporalRejectedApiError,
)
from brain_api.schemas.facts import (
    CommitProposalIn,
    CommitResponseOut,
    FactValidityUnknownOut,
    FactVersionOut,
)

EXCLUSION_VIOLATION = "23P01"

router = APIRouter(prefix="/facts", tags=["Facts"])


def _slot(fact_slot_id: UUID) -> ResourceKey:
    return ResourceKey(ResourceType.FACT_SLOT, fact_slot_id)


def _sqlstate(exc: DBAPIError) -> str | None:
    original = getattr(exc, "orig", None)
    for name in ("sqlstate", "pgcode"):
        code = getattr(original, name, None)
        if isinstance(code, str):
            return code
    cause = getattr(original, "__cause__", None)
    code = getattr(cause, "sqlstate", None)
    return code if isinstance(code, str) else None


@router.get("/{fact_slot_id}", response_model=FactVersionOut | FactValidityUnknownOut)
async def get_fact(
    fact_slot_id: UUID,
    valid_as_of: datetime | None = Query(default=None, alias="validAsOf"),
    known_as_of: datetime | None = Query(default=None, alias="knownAsOf"),
    principal: Principal = Depends(current_principal),
    execution: AuthorizationExecution = Depends(get_authorization_execution),
    session: AsyncSession = Depends(get_db_session),
) -> FactVersionOut | FactValidityUnknownOut:
    """Business valid/known coordinates select history only; authorization always
    uses current enforcement time and current grants (S0003 AC4, ADR-0053).

    F0008 (ADR-0078 D9): the internal reader resolves the coordinate. A
    validity-unknown result is an additive 200 with no value; a coordinate with
    no version keeps the pilot 404 (HTTP states stay with F0020)."""
    repository = SqlAlchemyFactCommitRepository(session)
    reader = TemporalFactReader(repository)
    answers = FactAnswerReader(SqlAlchemyFactSlotStore(session))
    now = datetime.now(UTC)
    requested = RequestedScope(
        knowledge_base_ids=None,
        selectors=(),
        business_valid_as_of=valid_as_of,
        business_known_as_of=known_as_of,
    )

    async def load(_decision: AuthorizationDecision) -> Resolved | ValidityUnknown:
        result = await reader.resolve(
            fact_slot_id, valid_at=valid_as_of or now, known_at=known_as_of or now
        )
        if not isinstance(result, Resolved | ValidityUnknown):
            raise NotFoundError()
        return result

    async def scope_reads(result: Resolved | ValidityUnknown) -> Sequence[ResourceKey]:
        # WHY: authorize the scope of this exact payload in the slot read's UoW.
        # A prior independent read commits and releases authority locks, and a
        # second version selection could return a different, unchecked scope.
        version = result.version
        keys: list[ResourceKey] = []
        if isinstance(result, Resolved):
            keys.extend(await answers.scope_keys_for_value(fact_slot_id, version.value))
        temporal = version.temporal
        if temporal is not None and (
            temporal.attested_from or temporal.attested_through or temporal.attested_to
        ):
            # ADR-0078 D4: the documents whose dates are disclosed must be readable;
            # otherwise the whole read is the non-disclosing 404 (SEC-F7-02).
            slot = await repository.get_slot(fact_slot_id)
            assert slot is not None
            keys.extend(
                await repository.evidence_artifact_keys(
                    (*version.evidence_refs, *version.ending_evidence_refs), scope=slot
                )
            )
        return sorted(set(keys), key=lambda k: (k.type.value, str(k.id)))

    result = await execution.read(
        principal,
        _slot(fact_slot_id),
        Action.READ,
        trace_id=new_trace_id(),
        load=load,
        requested=requested,
        additional_reads=scope_reads,
    )
    if isinstance(result, ValidityUnknown):
        return FactValidityUnknownOut.from_domain(result)
    return FactVersionOut.from_domain(result.version)


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
        temporal=proposal_in.temporal,
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
        # F0008: ending evidence joins the same-UoW source READ checks (D4).
        evidence_keys.update(
            await repository.commit_source_keys(
                (*proposal.evidence_refs, *_ending_refs(proposal_in.temporal)),
                proposal.review_decision_id,
            )
        )
        answer_keys = set(await answer_policy.source_keys(fact_slot_id, proposal.value))
        if proposal_in.temporal is not None:
            # F0008 (ADR-0078 D4, S0002): every document whose date can attest this
            # version must be readable by the committer, so no refusal code can
            # reveal the date of a document the caller cannot read (T-08).
            slot = await repository.get_slot(fact_slot_id)
            if slot is not None:
                answer_keys.update(
                    await repository.evidence_artifact_keys(
                        (*proposal.evidence_refs, *_ending_refs(proposal_in.temporal)),
                        scope=slot,
                    )
                )
        return sorted(evidence_keys | answer_keys)

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
    except TemporalRejected as exc:
        raise TemporalRejectedApiError(exc.code.value) from exc
    except LegacyTemporalUnsupported as exc:
        raise TemporalBlockUnsupportedApiError() from exc
    except InvalidRangeError as exc:
        raise InvalidRangeApiError(str(exc)) from exc
    except StaleVersionError as exc:
        raise StaleVersionApiError(str(exc)) from exc
    except FactSlotNotFound as exc:
        raise NotFoundError() from exc
    except IntegrityError as exc:
        # The GiST exclusion constraint is the backstop if the row lock somehow
        # didn't serialize a concurrent commit on this slot (F0001-S0005 AC).
        # F0008 (ADR-0078 D6): `23P01` is the retryable temporal_conflict.
        if _sqlstate(exc) == EXCLUSION_VIOLATION:
            raise TemporalConflictApiError() from exc
        # No database text crosses to the client: constraint messages can quote the
        # failing row (F0008 G3 security review).
        raise ConcurrentCommitApiError(None) from exc
    return CommitResponseOut.from_domain(result)


def _ending_refs(temporal: object) -> tuple[UUID, ...]:
    """Well-formed ending refs for the source READ check. A malformed block is
    refused with its reason code inside the operation, after authorization."""
    if not isinstance(temporal, dict):
        return ()
    refs = temporal.get("ending_evidence_refs")
    if not isinstance(refs, list):
        return ()
    parsed: list[UUID] = []
    for ref in refs:
        try:
            parsed.append(UUID(str(ref)))
        except ValueError:
            return ()
    return tuple(parsed)
