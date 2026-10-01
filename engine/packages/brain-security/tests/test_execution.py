"""F0002-S0006 transaction and audit contract of `AuthorizationExecution`."""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from brain_domain.authx import (
    Action,
    ActionCeiling,
    OperationOutcome,
    ReasonCode,
    ResourceType,
)
from brain_domain.principal import Principal, PrincipalKind, PrincipalStatus
from brain_security.execution import (
    AuthorizationDenied,
    AuthorizationExecution,
    AuthorizationUnavailable,
    PrincipalAuthority,
)


class FakeStore:
    """In-memory AuthorityStore + AuthorityReader that records the order of effects."""

    def __init__(self, release_id: str) -> None:
        self.pointer: str | None = release_id
        self.authorities: dict = {}
        self.slices: dict = {}
        self.resources: dict = {}
        self.delegations: dict = {}
        self.appended: list = []
        self.committed: list = []
        self.log: list[str] = []
        self.fail_commit = False
        self.fail_reads = False
        self._pending: list = []

    def current_policy_release(self):
        if self.fail_reads:
            raise OSError("authority storage down")
        self.log.append("lock:pointer")
        return self.pointer

    def peek_delegation(self, delegation_id):
        return self.delegations.get(delegation_id)

    def lock_authority(self, ids):
        self.log.append("lock:authority")
        return {i: self.authorities[i] for i in ids if i in self.authorities}

    def lock_delegation(self, delegation_id):
        self.log.append("lock:delegation")
        return self.delegations.get(delegation_id)

    def scope_slices(self, principal_id):
        return self.slices.get(principal_id, ())

    def hydrate(self, key, *, require_record=True):
        self.log.append(f"lock:resource:{key.id}")
        return self.resources.get(key)

    async def run_sync(self, fn):
        return fn(self)

    async def append_decision(self, decision):
        self._pending.append(decision)

    async def commit(self):
        if self.fail_commit:
            raise OSError("audit storage down")
        self.committed.extend(self._pending)
        self._pending = []
        self.log.append("commit")

    async def rollback(self):
        self._pending = []
        self.log.append("rollback")


def _world(build, policy, role="TenantMember", resource_type=ResourceType.CONTENT_ARTIFACT):
    owned = build.scope()
    user = build.principal()
    store = FakeStore(policy.release.release_id)
    store.authorities[user.id] = PrincipalAuthority(user, 4)
    store.slices[user.id] = (build.grant(owned, role),)
    resource = build.envelope(owned, resource_type)
    store.resources[resource.key] = resource
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: build.now)
    return store, execution, user, resource


async def test_allowed_read_loads_after_the_decision_and_commits_audit_first(build, policy) -> None:
    store, execution, user, resource = _world(build, policy)

    async def load(decision):
        store.log.append("load")
        assert decision.allowed
        return b"bytes"

    payload = await execution.read(user, resource.key, Action.READ, trace_id="t", load=load)

    assert payload == b"bytes"
    assert store.log.index("load") > store.log.index(f"lock:resource:{resource.key.id}")
    assert store.log[-1] == "commit"
    (decision,) = store.committed
    assert decision.operation_outcome == OperationOutcome.SUCCEEDED and decision.grant_revision == 4


async def test_denied_read_never_loads_and_durably_audits_the_denial(build, policy) -> None:
    store, execution, user, resource = _world(build, policy, role="Reviewer")
    loaded = []

    with pytest.raises(AuthorizationDenied) as exc:
        await execution.read(
            user, resource.key, Action.READ, trace_id="t", load=lambda d: loaded.append(d)
        )
    assert loaded == []
    assert exc.value.decision.reason_code == ReasonCode.POLICY_DENIED
    assert [d.operation_outcome for d in store.committed] == [OperationOutcome.DENIED]


async def test_nonexistent_resource_is_the_same_denial_with_null_scope(build, policy) -> None:
    store, execution, user, resource = _world(build, policy)
    del store.resources[resource.key]
    with pytest.raises(AuthorizationDenied) as exc:
        await execution.read(user, resource.key, Action.READ, trace_id="t", load=None)  # type: ignore[arg-type]
    assert exc.value.decision.reason_code == ReasonCode.MISSING_ATTRIBUTES
    assert store.committed[0].scope is None


async def test_audit_failure_releases_no_payload(build, policy) -> None:
    """EX-AUTHX-018: no success response without the durable decision."""
    store, execution, user, resource = _world(build, policy)
    store.fail_commit = True

    async def load(_decision):
        return b"secret"

    with pytest.raises(AuthorizationUnavailable):
        await execution.read(user, resource.key, Action.READ, trace_id="t", load=load)
    assert store.committed == [] and store.log[-1] == "rollback"


async def test_load_failure_is_audited_as_failed_in_a_fresh_transaction(build, policy) -> None:
    store, execution, user, resource = _world(build, policy)

    async def load(_decision):
        raise LookupError("bundle file missing")

    with pytest.raises(LookupError):
        await execution.read(user, resource.key, Action.READ, trace_id="t", load=load)
    assert [d.operation_outcome for d in store.committed] == [OperationOutcome.FAILED]


async def test_stale_policy_or_unreadable_authority_fails_closed(build, policy) -> None:
    store, execution, user, resource = _world(build, policy)
    store.pointer = "sha256:another-release"
    with pytest.raises(AuthorizationUnavailable):
        await execution.read(user, resource.key, Action.READ, trace_id="t", load=None)  # type: ignore[arg-type]
    store.pointer, store.fail_reads = policy.release.release_id, True
    with pytest.raises(AuthorizationUnavailable):
        await execution.read(user, resource.key, Action.READ, trace_id="t", load=None)  # type: ignore[arg-type]
    store.fail_reads = False
    store.authorities.clear()
    with pytest.raises(AuthorizationUnavailable):
        await execution.read(user, resource.key, Action.READ, trace_id="t", load=None)  # type: ignore[arg-type]
    assert store.committed == []


async def test_mutation_commits_effect_and_decision_together(build, policy) -> None:
    store, execution, user, resource = _world(
        build, policy, "ServicePrincipal", ResourceType.FACT_SLOT
    )

    async def operation(decisions):
        store.log.append("effect")
        return decisions[0].decision_id

    decision_id = await execution.mutate(
        user, [resource.key], Action.COMMIT, trace_id="t", operation=operation
    )
    assert store.log[-2:] == ["effect", "commit"]
    assert store.committed[0].decision_id == decision_id
    assert store.committed[0].operation_outcome == OperationOutcome.SUCCEEDED


async def test_batch_is_all_authorized_before_any_effect(build, policy) -> None:
    store, execution, user, resource = _world(build, policy, "Reviewer", ResourceType.REVIEW_TASK)
    foreign = build.envelope(build.scope(), ResourceType.REVIEW_TASK)
    store.resources[foreign.key] = foreign
    effects = []

    with pytest.raises(AuthorizationDenied):
        await execution.mutate(
            user,
            [resource.key, foreign.key],
            Action.ANNOTATE,
            trace_id="t",
            operation=lambda d: effects.append(d),
        )
    assert effects == []
    outcomes = sorted(d.operation_outcome for d in store.committed)
    assert outcomes == [OperationOutcome.DENIED, OperationOutcome.FAILED]


async def test_failed_mutation_rolls_back_and_audits_failure(build, policy) -> None:
    store, execution, user, resource = _world(
        build, policy, "ServicePrincipal", ResourceType.FACT_SLOT
    )

    async def operation(_decisions):
        store.log.append("effect")
        raise ValueError("stale version")

    with pytest.raises(ValueError):
        await execution.mutate(
            user, [resource.key], Action.COMMIT, trace_id="t", operation=operation
        )
    assert store.log.index("rollback") > store.log.index("effect")
    assert [d.operation_outcome for d in store.committed] == [OperationOutcome.FAILED]


async def test_mutation_commit_failure_is_unavailable_not_success(build, policy) -> None:
    store, execution, user, resource = _world(
        build, policy, "ServicePrincipal", ResourceType.FACT_SLOT
    )
    store.fail_commit = True

    async def operation(_decisions):
        return "receipt"

    with pytest.raises(AuthorizationUnavailable):
        await execution.mutate(
            user, [resource.key], Action.COMMIT, trace_id="t", operation=operation
        )
    with pytest.raises(ValueError):
        await execution.mutate(user, [], Action.COMMIT, trace_id="t", operation=operation)


async def test_expiry_between_decision_and_effect_denies(build, policy) -> None:
    """Assembly plan Step 3.7: validity is rechecked immediately before the effect."""
    store, execution, user, resource = _world(build, policy)
    (slice_,) = store.slices[user.id]
    store.slices[user.id] = (
        build.grant(slice_.scope, "TenantMember", expires_at=build.now + timedelta(seconds=1)),
    )
    times = iter([build.now, build.now + timedelta(seconds=2)])
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: next(times))
    with pytest.raises(AuthorizationDenied) as exc:
        await execution.read(user, resource.key, Action.READ, trace_id="t", load=None)  # type: ignore[arg-type]
    assert exc.value.decision.reason_code == ReasonCode.MEMBERSHIP_EXPIRED


async def test_delegated_read_binds_executor_and_acting_user(build, policy) -> None:
    store, execution, user, resource = _world(build, policy)
    agent = build.principal(PrincipalKind.AGENT)
    store.authorities[agent.id] = PrincipalAuthority(agent, 1)
    ceiling = ActionCeiling(resource.scope, resource.key, frozenset({Action.READ}))
    delegation = build.delegation(user, agent, (ceiling,))
    store.delegations[delegation.id] = delegation

    async def load(decision):
        return decision

    decision = await execution.read(
        agent, resource.key, Action.READ, trace_id="t", load=load, delegation_id=delegation.id
    )
    assert (decision.actor_principal_id, decision.executor_principal_id) == (user.id, agent.id)

    # A delegation bound to another executor, or an unknown ID, cannot be borrowed.
    other_agent = build.principal(PrincipalKind.AGENT)
    store.authorities[other_agent.id] = PrincipalAuthority(other_agent, 1)
    for delegation_id in (delegation.id, uuid4()):
        with pytest.raises(AuthorizationDenied) as exc:
            await execution.read(
                other_agent,
                resource.key,
                Action.READ,
                trace_id="t",
                load=load,
                delegation_id=delegation_id,
            )
        assert exc.value.decision.reason_code == ReasonCode.DELEGATION_DENIED
        assert exc.value.decision.actor_principal_id == other_agent.id

    # Disabling the acting user denies the next delegated operation.
    store.authorities[user.id] = PrincipalAuthority(
        Principal(user.id, user.kind, user.issuer, user.subject, PrincipalStatus.DISABLED),
        5,
    )
    with pytest.raises(AuthorizationDenied) as exc:
        await execution.read(
            agent, resource.key, Action.READ, trace_id="t", load=load, delegation_id=delegation.id
        )
    assert exc.value.decision.reason_code == ReasonCode.INACTIVE_PRINCIPAL


async def test_dependencies_are_hydrated_through_the_store(build, policy) -> None:
    store, execution, user, resource = _world(build, policy)
    evidence = build.envelope(resource.scope, classifications=("loss-notes",))
    derived = build.envelope(resource.scope, ResourceType.FACT_SLOT, dependencies=(evidence.key,))
    store.resources.update({evidence.key: evidence, derived.key: derived})
    (slice_,) = store.slices[user.id]
    store.slices[user.id] = (
        build.grant(slice_.scope, "TenantMember", classifications=frozenset({"internal"})),
    )
    with pytest.raises(AuthorizationDenied) as exc:
        await execution.read(user, derived.key, Action.READ, trace_id="t", load=None)  # type: ignore[arg-type]
    assert exc.value.decision.reason_code == ReasonCode.DEPENDENCY_DENIED
    assert f"lock:resource:{evidence.key.id}" in store.log
