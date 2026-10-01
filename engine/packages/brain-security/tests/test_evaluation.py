"""Pure evaluator proofs (F0002-S0003/S0004/S0005). Each restriction is exercised
independently while every other condition allows; EX-AUTHX case IDs are cited where a
test is the kernel-level half of an independently authored expectation."""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from brain_domain.authx import (
    Action,
    ActionCeiling,
    OperationOutcome,
    ReasonCode,
    RequestedScope,
    ResourceKey,
    ResourceType,
    ScopedId,
    ScopedKind,
    Selector,
    SelectorMode,
)
from brain_domain.principal import PrincipalKind, PrincipalStatus
from brain_security.evaluation import (
    MAX_DEPENDENCIES,
    MAX_DEPENDENCY_DEPTH,
    NO_DEPENDENCIES,
    DependencySet,
    collect_dependencies,
    evaluate,
    pending_dependency_keys,
)

ACCOUNT_X, ACCOUNT_Y, BROKER_1, BROKER_2 = uuid4(), uuid4(), uuid4(), uuid4()


def only(kind: ScopedKind, *ids):
    return Selector(kind, SelectorMode.ONLY, frozenset(ids))


def all_(kind: ScopedKind):
    return Selector(kind, SelectorMode.ALL)


def selectors(**modes):
    return tuple(modes.get(kind.value, all_(kind)) for kind in ScopedKind)


def decide(build, policy, slices, resource, action="read", deps=NO_DEPENDENCIES, **ctx):
    context = build.context(tuple(slices), **ctx)
    key = (
        resource.key
        if resource is not None
        else ResourceKey(ResourceType.CONTENT_ARTIFACT, uuid4())
    )
    return evaluate(context, key, resource, deps, action, policy, decision_id=uuid4())


def test_current_member_reads_content_in_its_own_kb(build, policy) -> None:
    owned = build.scope()
    slice_ = build.grant(owned, "TenantMember")
    decision = decide(build, policy, [slice_], build.envelope(owned))

    assert decision.allowed and decision.reason_code == ReasonCode.ALLOWED
    assert decision.matched_membership_ids == (slice_.membership_id,)
    assert decision.operation_outcome == OperationOutcome.ATTEMPTED
    assert decision.grant_revision == 7  # the principal-authority revision, never 0
    assert decision.scope == owned


def test_unknown_action_is_denied_before_anything_else(build, policy) -> None:
    owned = build.scope()
    decision = decide(
        build,
        policy,
        [build.grant(owned, "ServicePrincipal")],
        build.envelope(owned),
        action="delete",
    )
    assert decision.reason_code == ReasonCode.UNKNOWN_ACTION and not decision.allowed


def test_disabled_principal_is_denied(build, policy) -> None:
    owned = build.scope()
    disabled = build.principal(status=PrincipalStatus.DISABLED)
    decision = decide(
        build,
        policy,
        [build.grant(owned, "TenantMember")],
        build.envelope(owned),
        authenticated=disabled,
    )
    assert decision.reason_code == ReasonCode.INACTIVE_PRINCIPAL


def test_unresolved_resource_denies_with_null_scope(build, policy) -> None:
    decision = decide(build, policy, [build.grant(build.scope(), "TenantMember")], None)
    assert decision.reason_code == ReasonCode.MISSING_ATTRIBUTES
    assert decision.scope is None and decision.resource_revision is None


def test_sibling_kb_grant_gives_nothing_in_this_kb(build, policy) -> None:
    """EX-AUTHX-002: a grant in KB A2 is irrelevant to KB A1 in the same tenant."""
    tenant = uuid4()
    a1, a2 = build.scope(tenant), build.scope(tenant)
    decision = decide(build, policy, [build.grant(a2, "TenantMember")], build.envelope(a1))
    assert decision.reason_code == ReasonCode.NO_MEMBERSHIP


def test_expired_and_not_yet_valid_grants_deny(build, policy) -> None:
    """EX-AUTHX-008: an expired grant denies the next operation."""
    owned = build.scope()
    expired = build.grant(owned, "TenantMember", expires_at=build.now - timedelta(seconds=1))
    future = build.grant(owned, "TenantMember", valid_from=build.now + timedelta(minutes=1))
    for slice_ in (expired, future):
        decision = decide(build, policy, [slice_], build.envelope(owned))
        assert decision.reason_code == ReasonCode.MEMBERSHIP_EXPIRED


def test_past_business_time_never_reinstates_an_expired_grant(build, policy) -> None:
    """EX-AUTHX-008 boundary: business valid/known time is not authorization time."""
    owned = build.scope()
    expired = build.grant(
        owned,
        "TenantMember",
        valid_from=build.now - timedelta(days=60),
        expires_at=build.now - timedelta(days=1),
    )
    requested = RequestedScope(
        None, (), build.now - timedelta(days=30), build.now - timedelta(days=30)
    )
    decision = decide(build, policy, [expired], build.envelope(owned), requested=requested)
    assert decision.reason_code == ReasonCode.MEMBERSHIP_EXPIRED


def test_role_without_the_action_is_policy_denied(build, policy) -> None:
    """A Reviewer-only principal has no content_artifact:read (PRD role table)."""
    owned = build.scope()
    decision = decide(build, policy, [build.grant(owned, "Reviewer")], build.envelope(owned))
    assert decision.reason_code == ReasonCode.POLICY_DENIED


def test_role_granted_in_another_kb_cannot_annotate_here(build, policy) -> None:
    """EX-AUTHX-009: Reviewer in A1 and read-only in A2 cannot annotate in A2."""
    tenant = uuid4()
    a1, a2 = build.scope(tenant), build.scope(tenant)
    slices = [build.grant(a1, "Reviewer"), build.grant(a2, "TenantMember")]
    task_a2 = build.envelope(a2, ResourceType.REVIEW_TASK)
    assert (
        decide(build, policy, slices, task_a2, "annotate").reason_code == ReasonCode.POLICY_DENIED
    )
    task_a1 = build.envelope(a1, ResourceType.REVIEW_TASK)
    assert decide(build, policy, slices, task_a1, "annotate").allowed


def test_parent_restriction_alone_denies(build, policy) -> None:
    """EX-AUTHX-010 inverted: membership/action/classification allow; parent denies."""
    owned = build.scope()
    slice_ = build.grant(
        owned, "TenantMember", selectors=selectors(account=only(ScopedKind.ACCOUNT, ACCOUNT_X))
    )
    resource = build.envelope(owned, parents=(ScopedId(ScopedKind.ACCOUNT, ACCOUNT_Y),))
    assert decide(build, policy, [slice_], resource).reason_code == ReasonCode.PARENT_DENIED
    permitted = build.envelope(owned, parents=(ScopedId(ScopedKind.ACCOUNT, ACCOUNT_X),))
    assert decide(build, policy, [slice_], permitted).allowed


def test_empty_only_selector_admits_no_parent_of_that_kind(build, policy) -> None:
    owned = build.scope()
    slice_ = build.grant(owned, "TenantMember", selectors=selectors(broker=only(ScopedKind.BROKER)))
    with_broker = build.envelope(owned, parents=(ScopedId(ScopedKind.BROKER, BROKER_1),))
    without_broker = build.envelope(owned)
    assert decide(build, policy, [slice_], with_broker).reason_code == ReasonCode.PARENT_DENIED
    assert decide(build, policy, [slice_], without_broker).allowed


def test_classification_restriction_alone_denies(build, policy) -> None:
    """EX-AUTHX-010: membership, action and parent allow; classification denies."""
    owned = build.scope()
    slice_ = build.grant(owned, "TenantMember", classifications=frozenset({"internal"}))
    restricted = build.envelope(owned, classifications=("internal", "loss-notes"))
    assert (
        decide(build, policy, [slice_], restricted).reason_code == ReasonCode.CLASSIFICATION_DENIED
    )


def test_source_restriction_alone_denies(build, policy) -> None:
    """EX-AUTHX-011: permitted classification, denied source ACL."""
    owned = build.scope()
    slice_ = build.grant(owned, "TenantMember", source_acl_ids=frozenset({"acl-broker-portal"}))
    resource = build.envelope(owned, source_acl_ids=("acl-claims-system",))
    assert decide(build, policy, [slice_], resource).reason_code == ReasonCode.SOURCE_DENIED
    no_acl = build.envelope(owned)  # empty required list = the resource declares no ACL
    assert decide(build, policy, [slice_], no_acl).allowed


def test_attributes_are_never_borrowed_across_slices(build, policy) -> None:
    """ADR-0062 no-mixed-slice: slice A admits the parent but not the label; slice B
    admits the label but not the parent. Neither slice alone passes -> deny."""
    owned = build.scope()
    slice_a = build.grant(owned, "TenantMember", classifications=frozenset({"internal"}))
    slice_b = build.grant(
        owned, "TenantMember", selectors=selectors(account=only(ScopedKind.ACCOUNT, ACCOUNT_X))
    )
    resource = build.envelope(
        owned, parents=(ScopedId(ScopedKind.ACCOUNT, ACCOUNT_Y),), classifications=("loss-notes",)
    )
    decision = decide(build, policy, [slice_a, slice_b], resource)
    assert not decision.allowed
    assert decision.reason_code in {ReasonCode.PARENT_DENIED, ReasonCode.CLASSIFICATION_DENIED}


def test_fully_valid_slices_form_a_union(build, policy) -> None:
    """EX-AUTHX-007: two permitted slices; each allows its own account."""
    owned = build.scope()
    slice_x = build.grant(
        owned, "TenantMember", selectors=selectors(account=only(ScopedKind.ACCOUNT, ACCOUNT_X))
    )
    slice_y = build.grant(
        owned, "TenantMember", selectors=selectors(account=only(ScopedKind.ACCOUNT, ACCOUNT_Y))
    )
    for account, expected in ((ACCOUNT_X, slice_x), (ACCOUNT_Y, slice_y)):
        resource = build.envelope(owned, parents=(ScopedId(ScopedKind.ACCOUNT, account),))
        decision = decide(build, policy, [slice_x, slice_y], resource)
        assert decision.allowed and decision.matched_membership_ids == (expected.membership_id,)


def test_request_filter_only_narrows(build, policy) -> None:
    """EX-AUTHX-007: a filter intersects authority; it never adds a KB or account."""
    owned = build.scope()
    slice_ = build.grant(
        owned, "TenantMember", selectors=selectors(account=only(ScopedKind.ACCOUNT, ACCOUNT_X))
    )
    in_x = build.envelope(owned, parents=(ScopedId(ScopedKind.ACCOUNT, ACCOUNT_X),))
    in_y = build.envelope(owned, parents=(ScopedId(ScopedKind.ACCOUNT, ACCOUNT_Y),))

    narrow_to_y = RequestedScope(None, (only(ScopedKind.ACCOUNT, ACCOUNT_Y),), None, None)
    assert (
        decide(build, policy, [slice_], in_x, requested=narrow_to_y).reason_code
        == ReasonCode.SCOPE_DENIED
    )
    assert (
        decide(build, policy, [slice_], in_y, requested=narrow_to_y).reason_code
        == ReasonCode.PARENT_DENIED
    )

    other_kb = RequestedScope(frozenset({uuid4()}), (), None, None)
    assert (
        decide(build, policy, [slice_], in_x, requested=other_kb).reason_code
        == ReasonCode.SCOPE_DENIED
    )
    empty = RequestedScope(frozenset(), (), None, None)
    assert (
        decide(build, policy, [slice_], in_x, requested=empty).reason_code
        == ReasonCode.SCOPE_DENIED
    )
    same_kb = RequestedScope(frozenset({owned.knowledge_base_id}), (), None, None)
    assert decide(build, policy, [slice_], in_x, requested=same_kb).allowed


def test_broker_filter_never_substitutes_for_tenant(build, policy) -> None:
    """S0003 AC3: two broker relationships in one KB; authority covers only broker 1."""
    owned = build.scope()
    slice_ = build.grant(
        owned, "TenantMember", selectors=selectors(broker=only(ScopedKind.BROKER, BROKER_1))
    )
    broker_two = build.envelope(owned, parents=(ScopedId(ScopedKind.BROKER, BROKER_2),))
    requested = RequestedScope(None, (only(ScopedKind.BROKER, BROKER_2),), None, None)
    assert not decide(build, policy, [slice_], broker_two, requested=requested).allowed


def test_one_denied_evidence_dependency_denies_the_derived_resource(build, policy) -> None:
    """EX-AUTHX-012: two dependencies, access to only one -> deny; both -> allow."""
    owned = build.scope()
    slice_ = build.grant(owned, "TenantMember", classifications=frozenset({"internal"}))
    visible = build.envelope(owned, classifications=("internal",))
    hidden = build.envelope(owned, classifications=("loss-notes",))
    derived = build.envelope(owned, ResourceType.FACT_SLOT, dependencies=(visible.key, hidden.key))
    denied = decide(build, policy, [slice_], derived, deps=DependencySet((visible, hidden)))
    assert denied.reason_code == ReasonCode.DEPENDENCY_DENIED
    also_visible = build.envelope(owned, classifications=("internal",))
    allowed = decide(build, policy, [slice_], derived, deps=DependencySet((visible, also_visible)))
    assert allowed.allowed


def test_dependency_rules_cross_kb_cross_tenant_and_incomplete(build, policy) -> None:
    tenant = uuid4()
    a1, a2 = build.scope(tenant), build.scope(tenant)
    reader = build.grant(a1, "TenantMember")
    derived = build.envelope(a1, ResourceType.FACT_SLOT)
    sibling_evidence = build.envelope(a2)
    foreign_evidence = build.envelope(build.scope())

    deps = DependencySet((sibling_evidence,))
    assert (
        decide(build, policy, [reader], derived, deps=deps).reason_code
        == ReasonCode.DEPENDENCY_DENIED
    )
    with_a2_grant = [reader, build.grant(a2, "Reviewer")]  # visibility, not a read permission
    assert decide(build, policy, with_a2_grant, derived, deps=deps).allowed
    cross = DependencySet((foreign_evidence,))
    assert (
        decide(build, policy, [reader], derived, deps=cross).reason_code
        == ReasonCode.DEPENDENCY_DENIED
    )
    incomplete = DependencySet((), complete=False)
    assert (
        decide(build, policy, [reader], derived, deps=incomplete).reason_code
        == ReasonCode.MISSING_ATTRIBUTES
    )


def test_delegated_authority_is_the_intersection(build, policy) -> None:
    """EX-AUTHX-014: allow only where the actor's current grant AND the ceiling allow."""
    owned = build.scope()
    user, agent = build.principal(), build.principal(PrincipalKind.AGENT)
    resource = build.envelope(owned)
    ceiling = ActionCeiling(owned, resource.key, frozenset({Action.READ}))
    delegation = build.delegation(user, agent, (ceiling,))
    user_grant = build.grant(owned, "TenantMember")

    allowed = decide(
        build,
        policy,
        [user_grant],
        resource,
        authenticated=agent,
        acting=user,
        delegation=delegation,
    )
    assert allowed.allowed
    assert allowed.actor_principal_id == user.id and allowed.executor_principal_id == agent.id
    assert allowed.delegation_id == delegation.id and allowed.actor_kind == PrincipalKind.USER

    # Allowed by the delegation but not by the actor's current grant -> deny.
    no_grant = decide(
        build, policy, [], resource, authenticated=agent, acting=user, delegation=delegation
    )
    assert no_grant.reason_code == ReasonCode.NO_MEMBERSHIP
    # Allowed by the actor but outside the ceiling (other resource / action) -> deny.
    other = build.envelope(owned)
    assert (
        decide(
            build,
            policy,
            [user_grant],
            other,
            authenticated=agent,
            acting=user,
            delegation=delegation,
        ).reason_code
        == ReasonCode.DELEGATION_DENIED
    )
    reviewer = build.grant(owned, "Reviewer")
    task = build.envelope(owned, ResourceType.REVIEW_TASK)
    read_only_ceiling = build.delegation(
        user, agent, (ActionCeiling(owned, task.key, frozenset({Action.READ})),)
    )
    assert (
        decide(
            build,
            policy,
            [reviewer],
            task,
            "annotate",
            authenticated=agent,
            acting=user,
            delegation=read_only_ceiling,
        ).reason_code
        == ReasonCode.DELEGATION_DENIED
    )


def test_expired_revoked_or_unresolved_delegation_denies(build, policy) -> None:
    """EX-AUTHX-015/S0005 AC4: no continuing authority past expiry or revocation."""
    owned = build.scope()
    user, agent = build.principal(), build.principal(PrincipalKind.AGENT)
    resource = build.envelope(owned)
    ceiling = (ActionCeiling(owned, resource.key, frozenset({Action.READ})),)
    grants = [build.grant(owned, "TenantMember")]
    expired = build.delegation(
        user,
        agent,
        ceiling,
        expires_at=build.now - timedelta(seconds=1),
        not_before=build.now - timedelta(hours=1),
    )
    revoked = build.delegation(user, agent, ceiling, revoked_at=build.now - timedelta(seconds=1))
    for delegation in (expired, revoked):
        decision = decide(
            build, policy, grants, resource, authenticated=agent, acting=user, delegation=delegation
        )
        assert decision.reason_code == ReasonCode.DELEGATION_EXPIRED

    context = build.context(tuple(grants), authenticated=agent)
    forged = evaluate(
        context,
        resource.key,
        resource,
        NO_DEPENDENCIES,
        "read",
        policy,
        decision_id=uuid4(),
        delegation_unresolved=True,
    )
    assert forged.reason_code == ReasonCode.DELEGATION_DENIED


def test_autonomous_service_uses_only_its_own_grant(build, policy) -> None:
    """EX-AUTHX-016: a ServicePrincipal commits under its own explicit grant; an
    agent with no delegation and no grant has nothing."""
    owned = build.scope()
    service = build.principal(PrincipalKind.SERVICE)
    slot = build.envelope(owned, ResourceType.FACT_SLOT)
    own = decide(
        build,
        policy,
        [build.grant(owned, "ServicePrincipal")],
        slot,
        "commit",
        authenticated=service,
    )
    assert own.allowed and own.delegation_id is None and own.actor_kind == PrincipalKind.SERVICE
    agent = build.principal(PrincipalKind.AGENT)
    assert (
        decide(build, policy, [], slot, "read", authenticated=agent).reason_code
        == ReasonCode.NO_MEMBERSHIP
    )


def test_annotation_grant_never_implies_commit(build, policy) -> None:
    """EX-AUTHX-013 boundary: a Reviewer grant is not fact_slot:commit."""
    owned = build.scope()
    slot = build.envelope(owned, ResourceType.FACT_SLOT)
    decision = decide(build, policy, [build.grant(owned, "Reviewer")], slot, "commit")
    assert decision.reason_code == ReasonCode.POLICY_DENIED


def test_decision_json_carries_no_secret_or_payload_fields(build, policy) -> None:
    owned = build.scope()
    decision = decide(build, policy, [build.grant(owned, "TenantMember")], build.envelope(owned))
    payload = decision.to_json()
    assert set(payload) == {
        "schema_version",
        "decision_id",
        "occurred_at",
        "authenticated_principal_id",
        "actor_principal_id",
        "actor_kind",
        "executor_principal_id",
        "delegation_id",
        "delegation_revision",
        "scope",
        "resource",
        "resource_revision",
        "restriction_revision",
        "action",
        "allowed",
        "reason_code",
        "policy_hash",
        "policy_release",
        "grant_revision",
        "matched_membership_ids",
        "trace_id",
        "operation_outcome",
    }


def test_dependency_traversal_is_bounded_and_cycle_safe(build) -> None:
    owned = build.scope()
    leaves = [build.envelope(owned) for _ in range(MAX_DEPENDENCIES + 1)]
    wide = build.envelope(owned, dependencies=tuple(leaf.key for leaf in leaves))
    hydrated = {leaf.key: leaf for leaf in leaves}
    assert not collect_dependencies(wide, hydrated).complete
    assert pending_dependency_keys(wide, {}) == []  # stops expanding past the bound

    chain = [build.envelope(owned)]
    for _ in range(MAX_DEPENDENCY_DEPTH + 1):
        chain.append(build.envelope(owned, dependencies=(chain[-1].key,)))
    root, rest = chain[-1], {e.key: e for e in chain[:-1]}
    assert not collect_dependencies(root, rest).complete

    leaf = build.envelope(owned)
    middle = build.envelope(owned, dependencies=(leaf.key,))
    top = build.envelope(owned, dependencies=(middle.key,))
    assert pending_dependency_keys(top, {}) == [middle.key]
    assert pending_dependency_keys(top, {middle.key: middle}) == [leaf.key]
    done = collect_dependencies(top, {middle.key: middle, leaf.key: leaf})
    assert done.complete and {e.key for e in done.envelopes} == {middle.key, leaf.key}
    assert not collect_dependencies(top, {middle.key: middle}).complete  # leaf missing
    assert not collect_dependencies(top, {middle.key: None}).complete  # unresolved

    cyclic = build.envelope(owned, resource_id=uuid4())
    back = build.envelope(owned, dependencies=(cyclic.key,))
    looped = build.envelope(owned, resource_id=cyclic.key.id, dependencies=(back.key,))
    assert not collect_dependencies(looped, {back.key: back}).complete
