"""Transaction-aware authorization execution (F0002-S0006, ADR-0062).

`AuthorizationExecution` is the only way an async consumer performs a protected
operation. It reloads current authority inside the caller's unit of work, evaluates
with the shared pure evaluator, and makes the audit record durable before anything
leaves the process:

| Outcome                  | Behaviour                                                        |
|--------------------------|------------------------------------------------------------------|
| allowed read             | evaluate/lock -> load payload -> append decision -> commit -> return |
| denied / missing read    | append minimal denial -> commit -> `AuthorizationDenied` (404)   |
| allowed mutation         | operation in the same UoW -> append decision -> commit together  |
| failed mutation          | rollback -> append `failed` decision in a fresh transaction      |
| denied mutation          | rollback -> append denial in a fresh transaction                 |
| storage/audit failure    | abort -> `AuthorizationUnavailable` (503); no payload, no success |

Lock order (policy pointer, principal authority rows by ID, delegation row,
resource-access rows by key, then the operation's own rows) is the store's
contract. Nothing is cached across operations.
"""

from __future__ import annotations

import contextlib
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Protocol, TypeVar
from uuid import UUID, uuid4

from brain_domain.authx import (
    NO_FILTER,
    AuthorizationContext,
    AuthorizationDecision,
    Delegation,
    OperationOutcome,
    PolicyRelease,
    RequestedScope,
    ResourceEnvelope,
    ResourceKey,
    ScopeSlice,
)
from brain_domain.principal import Principal

from brain_security.evaluation import (
    DependencySet,
    PolicyEvaluator,
    collect_dependencies,
    evaluate,
    pending_dependency_keys,
)

T = TypeVar("T")


class AuthorizationDenied(Exception):
    """Denied or nonexistent protected resource. Callers map this to the same
    non-disclosing 404 used for a missing resource; the reason stays in audit."""

    def __init__(self, decision: AuthorizationDecision) -> None:
        super().__init__("authorization denied")
        self.decision = decision


class AuthorizationUnavailable(Exception):
    """Current authority or durable audit could not be read/written. Callers map
    this to a sanitized 503; no protected data or successful effect is released."""


@dataclass(frozen=True, slots=True)
class PrincipalAuthority:
    principal: Principal
    revision: int


class AuthorityReader(Protocol):
    """Synchronous trusted reads inside one unit of work (implemented in
    brain_persistence). Both the async API and the sync worker drive the same
    `decide` over this port, so the lock/load orchestration exists exactly once."""

    def current_policy_release(self) -> str | None:
        """Read the current release pointer FOR SHARE."""
        ...

    def peek_delegation(self, delegation_id: UUID) -> Delegation | None:
        """Unlocked read, only to learn the (immutable) acting principal."""
        ...

    def lock_authority(self, principal_ids: Sequence[UUID]) -> dict[UUID, PrincipalAuthority]:
        """Reload principals and FOR SHARE their authority rows in ascending ID order."""
        ...

    def lock_delegation(self, delegation_id: UUID) -> Delegation | None: ...

    def scope_slices(self, principal_id: UUID) -> tuple[ScopeSlice, ...]:
        """Unrevoked grant slices; validity windows are judged by the evaluator."""
        ...

    def hydrate(self, key: ResourceKey, *, require_record: bool = True) -> ResourceEnvelope | None:
        """FOR SHARE the resource-access row and verify it against the semantic row's
        ownership. `None` when missing or inconsistent (fail closed)."""
        ...


class AuthorityStore(Protocol):
    """Async unit of work used by `AuthorizationExecution`."""

    async def run_sync(self, fn: Callable[[AuthorityReader], T]) -> T:
        """Run `fn` against a synchronous reader bound to this unit of work."""
        ...

    async def append_decision(self, decision: AuthorizationDecision) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


@dataclass(frozen=True, slots=True)
class Evaluated:
    """One evaluated resource with the trusted inputs needed for the pre-effect recheck."""

    context: AuthorizationContext
    key: ResourceKey
    envelope: ResourceEnvelope | None
    dependencies: DependencySet
    decision: AuthorizationDecision
    delegation_unresolved: bool = False


def assemble_context(
    *,
    authenticated: PrincipalAuthority,
    acting: PrincipalAuthority,
    delegation: Delegation | None,
    at: datetime,
    release: PolicyRelease,
    slices: tuple[ScopeSlice, ...],
    requested: RequestedScope,
    trace_id: str,
) -> AuthorizationContext:
    """The one context constructor shared by the async and sync adapters."""
    return AuthorizationContext(
        authenticated=authenticated.principal,
        acting=acting.principal,
        delegation=delegation,
        authorization_time=at,
        authority_revision=acting.revision,
        policy_release=release,
        scope_slices=slices,
        requested_scope=requested,
        trace_id=trace_id,
    )


def recheck(evaluated: Evaluated, policy: PolicyEvaluator, at: datetime) -> Evaluated:
    """Re-evaluate the same trusted inputs at the effect time so an expiry that
    passes between decision and effect still denies (assembly plan Step 3.7)."""
    if not evaluated.decision.allowed:
        return evaluated
    context = replace(evaluated.context, authorization_time=at)
    decision = evaluate(
        context,
        evaluated.key,
        evaluated.envelope,
        evaluated.dependencies,
        evaluated.decision.action,
        policy,
        decision_id=evaluated.decision.decision_id,
        delegation_unresolved=evaluated.delegation_unresolved,
    )
    return replace(evaluated, context=context, decision=decision)


def utc_now() -> datetime:
    return datetime.now(UTC)


def decide(
    reader: AuthorityReader,
    policy: PolicyEvaluator,
    release: PolicyRelease,
    *,
    authenticated_id: UUID,
    keys: Sequence[ResourceKey],
    action: str,
    requested: RequestedScope,
    trace_id: str,
    delegation_id: UUID | None,
    clock: Callable[[], datetime],
    new_id: Callable[[], UUID],
    require_record: bool = True,
) -> list[Evaluated]:
    """Lock and load current trusted state, then evaluate every key (ADR-0062).

    The single orchestration shared by the async API facade and the sync worker.
    Lock order: policy pointer, principal authority rows by ID, delegation row,
    resource-access rows by key. The authorization time is read only after the
    locks are held, so a revocation committed before this call is observed.
    `require_record=False` is only for a worker step on an artifact whose trusted
    submitter provisioned its metadata before the record exists."""
    if reader.current_policy_release() != release.release_id:
        raise AuthorizationUnavailable("policy release is not current")

    acting_id = authenticated_id
    peeked: Delegation | None = None
    if delegation_id is not None:
        peeked = reader.peek_delegation(delegation_id)
        if peeked is not None:
            acting_id = peeked.acting_principal_id
    authorities = reader.lock_authority(sorted({authenticated_id, acting_id}, key=str))
    if authenticated_id not in authorities or acting_id not in authorities:
        raise AuthorizationUnavailable("principal authority is missing")

    delegation = reader.lock_delegation(delegation_id) if delegation_id else None
    delegation_valid = delegation_id is None or (
        delegation is not None
        and peeked is not None
        and delegation.acting_principal_id == peeked.acting_principal_id
        and delegation.executor_principal_id == authenticated_id
    )
    at = clock()
    if not delegation_valid:
        # A forged/unknown/mis-bound delegation: evaluate as the executor alone and
        # deny; the executor's own grants are never substituted (S0005 AC4).
        acting_id, delegation = authenticated_id, None
    context = assemble_context(
        authenticated=authorities[authenticated_id],
        acting=authorities[acting_id],
        delegation=delegation,
        at=at,
        release=release,
        slices=reader.scope_slices(acting_id),
        requested=requested,
        trace_id=trace_id,
    )
    results: list[Evaluated] = []
    for key in sorted(set(keys)):
        envelope = reader.hydrate(key, require_record=require_record)
        dependencies = DependencySet()
        if envelope is not None:
            hydrated: dict[ResourceKey, ResourceEnvelope | None] = {}
            while pending := pending_dependency_keys(envelope, hydrated):
                for dependency_key in pending:
                    hydrated[dependency_key] = reader.hydrate(dependency_key)
            dependencies = collect_dependencies(envelope, hydrated)
        decision = evaluate(
            context,
            key,
            envelope,
            dependencies,
            action,
            policy,
            decision_id=new_id(),
            delegation_unresolved=not delegation_valid,
        )
        results.append(
            Evaluated(context, key, envelope, dependencies, decision, not delegation_valid)
        )
    return results


class AuthorizationExecution:
    def __init__(
        self,
        store: AuthorityStore,
        policy: PolicyEvaluator,
        release: PolicyRelease,
        *,
        clock: Callable[[], datetime] = utc_now,
        new_id: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store
        self._policy = policy
        self._release = release
        self._clock = clock
        self._new_id = new_id

    async def _decide(
        self,
        authenticated: Principal,
        keys: Sequence[ResourceKey],
        action: str,
        requested: RequestedScope,
        trace_id: str,
        delegation_id: UUID | None,
    ) -> list[Evaluated]:
        return await self._store.run_sync(
            lambda reader: decide(
                reader,
                self._policy,
                self._release,
                authenticated_id=authenticated.id,
                keys=keys,
                action=action,
                requested=requested,
                trace_id=trace_id,
                delegation_id=delegation_id,
                clock=self._clock,
                new_id=self._new_id,
            )
        )

    async def _guarded_decide(
        self,
        authenticated: Principal,
        keys: Sequence[ResourceKey],
        action: str,
        requested: RequestedScope,
        trace_id: str,
        delegation_id: UUID | None,
    ) -> list[Evaluated]:
        try:
            return await self._decide(
                authenticated, keys, action, requested, trace_id, delegation_id
            )
        except AuthorizationUnavailable:
            await self._safe_rollback()
            raise
        except Exception as exc:  # noqa: BLE001 - any authority read failure fails closed
            await self._safe_rollback()
            raise AuthorizationUnavailable("current authority unavailable") from exc

    async def _safe_rollback(self) -> None:
        # The original failure is what matters; a failed rollback adds nothing.
        with contextlib.suppress(Exception):
            await self._store.rollback()

    async def _persist_fresh(self, decisions: Sequence[AuthorizationDecision]) -> None:
        """Roll back any business work, then durably audit in a new transaction."""
        await self._safe_rollback()
        try:
            for decision in decisions:
                await self._store.append_decision(decision)
            await self._store.commit()
        except Exception as exc:  # noqa: BLE001
            await self._safe_rollback()
            raise AuthorizationUnavailable("decision audit could not be persisted") from exc

    async def _deny(self, evaluated: Sequence[Evaluated]) -> AuthorizationDenied:
        decisions = [
            e.decision
            if not e.decision.allowed
            else e.decision.with_outcome(OperationOutcome.FAILED)
            for e in evaluated
        ]
        await self._persist_fresh(decisions)
        denied = next(d for d in decisions if not d.allowed)
        return AuthorizationDenied(denied)

    def _recheck_all(self, evaluated: Sequence[Evaluated]) -> list[Evaluated]:
        at = self._clock()
        return [recheck(e, self._policy, at) for e in evaluated]

    async def read(
        self,
        authenticated: Principal,
        key: ResourceKey,
        action: str,
        *,
        trace_id: str,
        load: Callable[[AuthorizationDecision], Awaitable[T]],
        requested: RequestedScope = NO_FILTER,
        delegation_id: UUID | None = None,
    ) -> T:
        evaluated = await self._guarded_decide(
            authenticated, [key], action, requested, trace_id, delegation_id
        )
        if not evaluated[0].decision.allowed:
            raise await self._deny(evaluated)
        evaluated = self._recheck_all(evaluated)
        if not evaluated[0].decision.allowed:
            raise await self._deny(evaluated)
        decision = evaluated[0].decision
        try:
            payload = await load(decision)
        except Exception:
            await self._persist_fresh([decision.with_outcome(OperationOutcome.FAILED)])
            raise
        try:
            await self._store.append_decision(decision.with_outcome(OperationOutcome.SUCCEEDED))
            await self._store.commit()
        except Exception as exc:  # noqa: BLE001 - no payload leaves without durable audit
            await self._safe_rollback()
            raise AuthorizationUnavailable("read audit could not be persisted") from exc
        return payload

    async def mutate(
        self,
        authenticated: Principal,
        keys: Sequence[ResourceKey],
        action: str,
        *,
        trace_id: str,
        operation: Callable[[Sequence[AuthorizationDecision]], Awaitable[T]],
        requested: RequestedScope = NO_FILTER,
        delegation_id: UUID | None = None,
    ) -> T:
        """Authorize every key (resolved and locked before any mutation), run the
        operation in the same UoW, and commit its effects with the decisions."""
        if not keys:
            raise ValueError("a protected mutation names at least one resource")
        evaluated = await self._guarded_decide(
            authenticated, keys, action, requested, trace_id, delegation_id
        )
        if not all(e.decision.allowed for e in evaluated):
            raise await self._deny(evaluated)
        evaluated = self._recheck_all(evaluated)
        if not all(e.decision.allowed for e in evaluated):
            raise await self._deny(evaluated)
        decisions = [e.decision for e in evaluated]
        try:
            result = await operation(decisions)
        except Exception:
            await self._persist_fresh([d.with_outcome(OperationOutcome.FAILED) for d in decisions])
            raise
        try:
            for decision in decisions:
                await self._store.append_decision(decision.with_outcome(OperationOutcome.SUCCEEDED))
            await self._store.commit()
        except Exception as exc:  # noqa: BLE001 - no unaudited successful mutation
            await self._safe_rollback()
            raise AuthorizationUnavailable("mutation and audit could not be committed") from exc
        return result
