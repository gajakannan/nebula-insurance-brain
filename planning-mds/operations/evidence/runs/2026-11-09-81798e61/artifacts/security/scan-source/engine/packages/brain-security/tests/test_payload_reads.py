"""Payload-derived protected reads retain one authority/audit transaction."""

from __future__ import annotations

from datetime import timedelta

import pytest
from brain_domain.authx import Action, OperationOutcome, ResourceType
from brain_security.execution import (
    AuthorizationDenied,
    AuthorizationExecution,
    AuthorizationUnavailable,
    PrincipalAuthority,
)


class ReadStore:
    """Authority fake with an explicit commit boundary and recorded decisions."""

    def __init__(self, build, policy):  # type: ignore[no-untyped-def]
        self.owner = build.scope()
        self.user = build.principal()
        self.release_id = policy.release.release_id
        self.authority = PrincipalAuthority(self.user, 4)
        self.slices = (build.grant(self.owner, "TenantMember"),)
        self.slot = build.envelope(self.owner, ResourceType.FACT_SLOT)
        self.scope = build.envelope(self.owner, classifications=("restricted",))
        self.resources = {self.slot.key: self.slot, self.scope.key: self.scope}
        self.pending = []
        self.committed = []
        self.commits = 0
        self.fail_commit = False
        self.hydrated = []
        self.revocation = None

    def current_policy_release(self):  # type: ignore[no-untyped-def]
        return self.release_id

    def peek_delegation(self, delegation_id):  # type: ignore[no-untyped-def]
        return None

    def lock_authority(self, principal_ids):  # type: ignore[no-untyped-def]
        return {self.user.id: self.authority}

    def lock_delegation(self, delegation_id):  # type: ignore[no-untyped-def]
        return None

    def scope_slices(self, principal_id):  # type: ignore[no-untyped-def]
        return self.slices

    def hydrate(self, key, *, require_record=True):  # type: ignore[no-untyped-def]
        self.hydrated.append(key)
        return self.resources.get(key)

    async def run_sync(self, callback):  # type: ignore[no-untyped-def]
        return callback(self)

    async def append_decision(self, decision):  # type: ignore[no-untyped-def]
        self.pending.append(decision)

    async def commit(self):  # type: ignore[no-untyped-def]
        if self.fail_commit:
            raise OSError("synthetic audit failure")
        self.committed.extend(self.pending)
        self.pending = []
        self.commits += 1
        if self.revocation is not None:
            self.revocation()

    async def rollback(self):  # type: ignore[no-untyped-def]
        self.pending = []


async def test_exact_payload_dependencies_share_one_successful_commit(build, policy):
    store = ReadStore(build, policy)
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: build.now)
    selected = {"scope": store.scope.key, "pages": [7, 8]}
    loads = []

    async def load(decision):
        assert decision.resource == store.slot.key and store.commits == 0
        loads.append(True)
        return selected

    async def scope_reads(payload):
        assert payload is selected and store.commits == 0
        return [payload["scope"], payload["scope"]]

    def revoke_after_locks_release():
        store.authority = PrincipalAuthority(store.user, 5)
        store.slices = (build.grant(store.owner, "TenantMember", classifications=("internal",)),)

    store.revocation = revoke_after_locks_release
    result = await execution.read(
        store.user,
        store.slot.key,
        Action.READ,
        trace_id="group",
        load=load,
        additional_reads=scope_reads,
    )
    assert result is selected and loads == [True] and store.commits == 1
    assert {d.resource for d in store.committed} == {store.slot.key, store.scope.key}
    assert {d.grant_revision for d in store.committed} == {4}
    assert all(d.operation_outcome == OperationOutcome.SUCCEEDED for d in store.committed)
    # Revocation after the completed transaction affects the next operation.
    with pytest.raises(AuthorizationDenied):
        await execution.read(store.user, store.scope.key, Action.READ, trace_id="next", load=load)


async def test_denied_scope_returns_no_payload_and_audits_both_decisions(build, policy):
    store = ReadStore(build, policy)
    store.slices = (build.grant(store.owner, "TenantMember", classifications=("internal",)),)
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: build.now)

    async def load(_decision):
        return {"scope": store.scope.key}

    async def scopes(payload):
        return [payload["scope"]]

    with pytest.raises(AuthorizationDenied) as denied:
        await execution.read(
            store.user,
            store.slot.key,
            Action.READ,
            trace_id="denied",
            load=load,
            additional_reads=scopes,
        )
    assert denied.value.decision.resource == store.scope.key
    assert store.commits == 1
    assert {d.resource: d.operation_outcome for d in store.committed} == {
        store.slot.key: OperationOutcome.FAILED,
        store.scope.key: OperationOutcome.DENIED,
    }


async def test_denied_primary_does_not_load_or_discover_scope(build, policy):
    store = ReadStore(build, policy)
    store.slices = (build.grant(store.owner, "Reviewer"),)
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: build.now)

    async def forbidden(_payload):
        pytest.fail("denied primary must not load a payload or discover its scope")

    with pytest.raises(AuthorizationDenied):
        await execution.read(
            store.user,
            store.slot.key,
            Action.READ,
            trace_id="primary",
            load=forbidden,
            additional_reads=forbidden,
        )
    assert store.scope.key not in store.hydrated
    assert len(store.committed) == 1


async def test_scope_discovery_failure_audits_failed_primary(build, policy):
    store = ReadStore(build, policy)
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: build.now)

    async def load(_decision):
        return {"scope": store.scope.key}

    async def unavailable(_payload):
        raise LookupError("scope ownership metadata unavailable")

    with pytest.raises(LookupError):
        await execution.read(
            store.user,
            store.slot.key,
            Action.READ,
            trace_id="failed",
            load=load,
            additional_reads=unavailable,
        )
    assert [d.operation_outcome for d in store.committed] == [OperationOutcome.FAILED]


async def test_expiry_during_private_load_is_rechecked_before_release(build, policy):
    store = ReadStore(build, policy)
    store.slices = (
        build.grant(store.owner, "TenantMember", expires_at=build.now + timedelta(seconds=1)),
    )
    instant = [build.now]
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: instant[0])

    async def load(_decision):
        return {"scope": store.scope.key}

    async def scopes(payload):
        instant[0] = build.now + timedelta(seconds=2)
        return [payload["scope"]]

    with pytest.raises(AuthorizationDenied):
        await execution.read(
            store.user,
            store.slot.key,
            Action.READ,
            trace_id="expired",
            load=load,
            additional_reads=scopes,
        )
    assert not any(d.operation_outcome == OperationOutcome.SUCCEEDED for d in store.committed)


async def test_group_audit_failure_never_returns_the_private_payload(build, policy):
    store = ReadStore(build, policy)
    store.fail_commit = True
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: build.now)

    async def load(_decision):
        return {"scope": store.scope.key}

    async def scopes(payload):
        return [payload["scope"]]

    with pytest.raises(AuthorizationUnavailable):
        await execution.read(
            store.user,
            store.slot.key,
            Action.READ,
            trace_id="audit",
            load=load,
            additional_reads=scopes,
        )
    assert store.committed == [] and store.pending == [] and store.commits == 0
