"""The shared pure authorization decision (F0002-S0003/S0004/S0005, ADR-0062).

Every allow/deny rule lives here and only here. The async API adapter and the sync
worker adapter load trusted state (principal status, current grant slices, resource
envelopes, delegation) and call `evaluate`; neither re-implements a rule.

Decision order (the first failing check supplies the internal reason code):

1. action is a known pilot action
2. authenticated and acting principals are active
3. delegation (when present) is active and its ceiling names this resource/action
4. the resource and every dependency were hydrated completely
5. the request filter admits the resource (filters only narrow)
6. a current grant slice exists in the resource's exact tenant/workspace/KB
7. Casbin permits that slice's role/resource/action
8. the SAME slice admits every parent, classification and source restriction
9. every evidence dependency is admitted by current authority

Allow requires at least one slice to pass 6-9 entirely. Multiple fully valid slices
form the permitted union; attributes are never combined across slices.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from brain_domain.authx import (
    Action,
    AuthorizationContext,
    AuthorizationDecision,
    OperationOutcome,
    ReasonCode,
    RequestedScope,
    ResourceEnvelope,
    ResourceKey,
    ScopedKind,
    ScopeSlice,
    admits,
    is_active,
)
from brain_domain.tenancy import OwnedScope

MAX_DEPENDENCIES = 64
MAX_DEPENDENCY_DEPTH = 8


class PolicyEvaluator(Protocol):
    """Role/resource/action evaluation (the unchanged Casbin pilot policy)."""

    def permits(
        self,
        role: str,
        grant_scope: OwnedScope,
        resource_scope: OwnedScope,
        resource: ResourceKey,
        action: str,
    ) -> bool: ...


@dataclass(frozen=True, slots=True)
class DependencySet:
    """Hydrated evidence dependencies of a resource.

    `complete=False` means at least one dependency could not be hydrated, formed a
    cycle, or exceeded the v1 traversal bound — the decision then denies rather
    than evaluating partially."""

    envelopes: tuple[ResourceEnvelope, ...] = ()
    complete: bool = True


NO_DEPENDENCIES = DependencySet()


def _slice_admits_restrictions(slice_: ScopeSlice, resource: ResourceEnvelope) -> ReasonCode | None:
    for kind in ScopedKind:
        selector = slice_.selector(kind)
        if not all(selector.admits(parent) for parent in resource.parents(kind)):
            return ReasonCode.PARENT_DENIED
    if not admits(slice_.classifications, resource.classifications):
        return ReasonCode.CLASSIFICATION_DENIED
    if not admits(slice_.source_acl_ids, resource.source_acl_ids):
        return ReasonCode.SOURCE_DENIED
    return None


def _filter_admits(requested: RequestedScope, resource: ResourceEnvelope) -> bool:
    if (
        requested.knowledge_base_ids is not None
        and resource.scope.knowledge_base_id not in requested.knowledge_base_ids
    ):
        return False
    for selector in requested.selectors:
        parents = resource.parents(selector.kind)
        if selector.mode.value == "only" and (
            not parents or not all(selector.admits(p) for p in parents)
        ):
            return False
    return True


def _dependency_admitted(
    grant: ScopeSlice,
    dependency: ResourceEnvelope,
    resource: ResourceEnvelope,
    current: Iterable[ScopeSlice],
) -> bool:
    if dependency.scope.tenant_id != resource.scope.tenant_id:
        return False  # cross-tenant evidence is never visible
    if dependency.scope == grant.scope:
        # Same KB: the slice that authorizes the resource must also admit its evidence.
        return _slice_admits_restrictions(grant, dependency) is None
    # Evidence in a sibling KB needs a current grant there; no role/action is implied
    # (this is visibility of evidence, not a standalone content read permission).
    return any(
        s.scope == dependency.scope and _slice_admits_restrictions(s, dependency) is None
        for s in current
    )


def _decision(
    context: AuthorizationContext,
    decision_id: UUID,
    key: ResourceKey,
    resource: ResourceEnvelope | None,
    action: str,
    reason: ReasonCode,
    matched: tuple[UUID, ...] = (),
) -> AuthorizationDecision:
    allowed = reason == ReasonCode.ALLOWED
    delegation = context.delegation
    return AuthorizationDecision(
        decision_id=decision_id,
        occurred_at=context.authorization_time,
        authenticated_principal_id=context.authenticated.id,
        actor_principal_id=context.acting.id,
        actor_kind=context.acting.kind,
        executor_principal_id=context.authenticated.id if delegation else None,
        delegation_id=delegation.id if delegation else None,
        delegation_revision=delegation.revision if delegation else None,
        scope=resource.scope if resource else None,
        resource=key,
        resource_revision=resource.resource_revision if resource else None,
        restriction_revision=resource.restriction_revision if resource else None,
        action=action,
        allowed=allowed,
        reason_code=reason,
        policy_hash=context.policy_release.policy_sha256,
        policy_release=context.policy_release.release_id,
        grant_revision=context.authority_revision,
        matched_membership_ids=matched,
        trace_id=context.trace_id,
        operation_outcome=OperationOutcome.ATTEMPTED if allowed else OperationOutcome.DENIED,
    )


def evaluate(
    context: AuthorizationContext,
    key: ResourceKey,
    resource: ResourceEnvelope | None,
    dependencies: DependencySet,
    action: str,
    policy: PolicyEvaluator,
    *,
    decision_id: UUID,
    delegation_unresolved: bool = False,
) -> AuthorizationDecision:
    """Pure decision over trusted inputs. Never raises for a denial.

    `delegation_unresolved` marks a request that named a delegation the trusted
    store could not bind to this executor (unknown, forged or mis-bound): the
    context then carries the executor alone and the decision denies, so the
    executor's own grants are never substituted for the delegated authority."""

    def deny(reason: ReasonCode) -> AuthorizationDecision:
        return _decision(context, decision_id, key, resource, action, reason)

    try:
        typed_action = Action(action)
    except ValueError:
        return deny(ReasonCode.UNKNOWN_ACTION)

    if not is_active(context.authenticated) or not is_active(context.acting):
        return deny(ReasonCode.INACTIVE_PRINCIPAL)

    at = context.authorization_time
    delegation = context.delegation
    if delegation_unresolved:
        return deny(ReasonCode.DELEGATION_DENIED)
    if delegation is not None and not delegation.active_at(at):
        return deny(ReasonCode.DELEGATION_EXPIRED)

    if resource is None or resource.key != key:
        return deny(ReasonCode.MISSING_ATTRIBUTES)

    if delegation is not None and not delegation.permits(resource.scope, key, typed_action):
        return deny(ReasonCode.DELEGATION_DENIED)

    if not dependencies.complete or len(dependencies.envelopes) > MAX_DEPENDENCIES:
        return deny(ReasonCode.MISSING_ATTRIBUTES)

    if not _filter_admits(context.requested_scope, resource):
        return deny(ReasonCode.SCOPE_DENIED)

    in_scope = [s for s in context.scope_slices if s.scope == resource.scope]
    if not in_scope:
        return deny(ReasonCode.NO_MEMBERSHIP)
    current = [s for s in context.scope_slices if s.current_at(at)]
    candidates = [s for s in in_scope if s.current_at(at)]
    if not candidates:
        return deny(ReasonCode.MEMBERSHIP_EXPIRED)

    permitted = [
        s
        for s in candidates
        if policy.permits(s.role.value, s.scope, resource.scope, key, typed_action.value)
    ]
    if not permitted:
        return deny(ReasonCode.POLICY_DENIED)

    matched: list[UUID] = []
    first_failure: ReasonCode | None = None
    for grant in permitted:  # already in canonical membership-id order
        failure = _slice_admits_restrictions(grant, resource)
        if failure is None and not all(
            _dependency_admitted(grant, dependency, resource, current)
            for dependency in dependencies.envelopes
        ):
            failure = ReasonCode.DEPENDENCY_DENIED
        if failure is None:
            matched.append(grant.membership_id)
        elif first_failure is None:
            first_failure = failure

    if not matched:
        assert first_failure is not None
        return deny(first_failure)
    return _decision(
        context, decision_id, key, resource, action, ReasonCode.ALLOWED, tuple(matched)
    )


def collect_dependencies(
    root: ResourceEnvelope,
    hydrated: Mapping[ResourceKey, ResourceEnvelope | None],
) -> DependencySet:
    """Walk `root`'s dependency graph over already-hydrated envelopes.

    Returns an incomplete set when any key is missing from `hydrated` or `None`,
    when a cycle returns to the root, or when the v1 bounds (64 resources, depth 8)
    are exceeded. Adapters use `plan_dependency_loads` to decide what to hydrate."""
    seen: dict[ResourceKey, ResourceEnvelope] = {}
    frontier = sorted(root.dependency_keys)
    depth = 0
    while frontier:
        depth += 1
        if depth > MAX_DEPENDENCY_DEPTH:
            return DependencySet(tuple(seen.values()), complete=False)
        following: list[ResourceKey] = []
        for key in frontier:
            if key == root.key:
                return DependencySet(tuple(seen.values()), complete=False)
            if key in seen:
                continue
            envelope = hydrated.get(key)
            if envelope is None:
                return DependencySet(tuple(seen.values()), complete=False)
            seen[key] = envelope
            if len(seen) > MAX_DEPENDENCIES:
                return DependencySet(tuple(seen.values()), complete=False)
            following.extend(k for k in envelope.dependency_keys if k not in seen)
        frontier = sorted(set(following))
    return DependencySet(tuple(seen[k] for k in sorted(seen)), complete=True)


def pending_dependency_keys(
    root: ResourceEnvelope,
    hydrated: Mapping[ResourceKey, ResourceEnvelope | None],
) -> list[ResourceKey]:
    """Keys reachable from `root` that an adapter still needs to hydrate.

    Adapters loop `pending -> hydrate -> pending` until empty, then call
    `collect_dependencies`. Traversal stops expanding at the v1 bounds so an
    oversized graph costs bounded work and is reported incomplete."""
    reachable: set[ResourceKey] = set()
    pending: list[ResourceKey] = []
    frontier = sorted(root.dependency_keys)
    depth = 0
    while frontier and depth < MAX_DEPENDENCY_DEPTH:
        depth += 1
        following: list[ResourceKey] = []
        for key in frontier:
            if key == root.key or key in reachable:
                continue
            reachable.add(key)
            if len(reachable) > MAX_DEPENDENCIES:
                return []
            if key not in hydrated:
                pending.append(key)
                continue
            envelope = hydrated[key]
            if envelope is not None:
                following.extend(envelope.dependency_keys)
        frontier = sorted(set(following) - reachable)
    return pending
