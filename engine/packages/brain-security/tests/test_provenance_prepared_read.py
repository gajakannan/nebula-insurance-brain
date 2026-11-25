"""F0009 opt-in `prepare_reads`: every metadata-derived requirement is decided
before the protected load, in one authority/audit transaction (S0004 AC1/AC6)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from brain_domain.authx import Action, OperationOutcome
from brain_security.execution import AuthorizationDenied, AuthorizationExecution

from .test_payload_reads import ReadStore


async def test_prepared_sources_are_decided_before_the_single_load(build, policy):
    store = ReadStore(build, policy)
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: build.now)
    order: list[str] = []

    async def prepare():
        order.append("prepare")
        assert store.scope.key not in store.hydrated
        return [store.scope.key, store.scope.key]

    async def load(decision):
        order.append("load")
        # Both the anchor and the prepared source were hydrated before the load.
        assert store.scope.key in store.hydrated and decision.resource == store.slot.key
        assert store.commits == 0
        return {"payload": "protected"}

    result = await execution.read(
        store.user,
        store.slot.key,
        Action.READ,
        trace_id="prepared",
        load=load,
        prepare_reads=prepare,
    )
    assert result == {"payload": "protected"} and order == ["prepare", "load"]
    assert store.commits == 1
    assert {d.resource for d in store.committed} == {store.slot.key, store.scope.key}
    assert all(d.operation_outcome == OperationOutcome.SUCCEEDED for d in store.committed)


async def test_denied_prepared_source_means_zero_protected_loads(build, policy):
    store = ReadStore(build, policy)
    store.slices = (build.grant(store.owner, "TenantMember", classifications=("internal",)),)
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: build.now)

    async def prepare():
        return [store.scope.key]

    async def load(_decision):
        pytest.fail("a denied source must refuse before any protected load")

    with pytest.raises(AuthorizationDenied) as denied:
        await execution.read(
            store.user,
            store.slot.key,
            Action.READ,
            trace_id="deny",
            load=load,
            prepare_reads=prepare,
        )
    assert denied.value.decision.resource == store.scope.key
    assert store.commits == 1
    assert {d.resource: d.operation_outcome for d in store.committed} == {
        store.slot.key: OperationOutcome.FAILED,
        store.scope.key: OperationOutcome.DENIED,
    }


async def test_missing_prepared_source_refuses_like_a_denial(build, policy):
    store = ReadStore(build, policy)
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: build.now)
    missing = build.envelope(store.owner).key  # never registered in the store

    async def prepare():
        return [missing]

    async def load(_decision):
        pytest.fail("a missing source must refuse before any protected load")

    with pytest.raises(AuthorizationDenied):
        await execution.read(
            store.user,
            store.slot.key,
            Action.READ,
            trace_id="missing",
            load=load,
            prepare_reads=prepare,
        )
    assert store.commits == 1


async def test_discovery_failure_audits_failed_anchor_and_loads_nothing(build, policy):
    store = ReadStore(build, policy)
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: build.now)

    async def prepare():
        raise LookupError("lineage metadata unavailable")

    async def load(_decision):
        pytest.fail("no load after a failed discovery")

    with pytest.raises(LookupError):
        await execution.read(
            store.user,
            store.slot.key,
            Action.READ,
            trace_id="fail",
            load=load,
            prepare_reads=prepare,
        )
    assert [d.operation_outcome for d in store.committed] == [OperationOutcome.FAILED]


async def test_load_failure_audits_every_prepared_decision_failed(build, policy):
    store = ReadStore(build, policy)
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: build.now)

    async def prepare():
        return [store.scope.key]

    async def load(_decision):
        raise RuntimeError("topology changed")

    with pytest.raises(RuntimeError):
        await execution.read(
            store.user, store.slot.key, Action.READ, trace_id="lf", load=load, prepare_reads=prepare
        )
    assert {d.resource: d.operation_outcome for d in store.committed} == {
        store.slot.key: OperationOutcome.FAILED,
        store.scope.key: OperationOutcome.FAILED,
    }


async def test_expiry_during_the_load_is_rechecked_without_additional_reads(build, policy):
    """Step 4.6: the final recheck runs even when no payload-derived callback exists."""
    store = ReadStore(build, policy)
    store.slices = (
        build.grant(store.owner, "TenantMember", expires_at=build.now + timedelta(seconds=1)),
    )
    instant = [build.now]
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: instant[0])

    async def prepare():
        return [store.scope.key]

    async def load(_decision):
        instant[0] = build.now + timedelta(seconds=2)
        return {"payload": "protected"}

    with pytest.raises(AuthorizationDenied):
        await execution.read(
            store.user,
            store.slot.key,
            Action.READ,
            trace_id="exp",
            load=load,
            prepare_reads=prepare,
        )
    assert store.commits == 1
    assert all(d.operation_outcome != OperationOutcome.SUCCEEDED for d in store.committed)


async def test_existing_read_without_prepare_is_unchanged(build, policy):
    store = ReadStore(build, policy)
    execution = AuthorizationExecution(store, policy, policy.release, clock=lambda: build.now)

    async def load(_decision):
        return 7

    assert (
        await execution.read(store.user, store.slot.key, Action.READ, trace_id="old", load=load)
        == 7
    )
    assert [d.resource for d in store.committed] == [store.slot.key]
