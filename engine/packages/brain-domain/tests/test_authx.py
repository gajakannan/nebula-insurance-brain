"""F0002 v1 carrier invariants, independent of any adapter."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from brain_domain.authx import (
    NO_FILTER,
    WILDCARD,
    Action,
    ActionCeiling,
    AuthenticationEvent,
    AuthorizationContext,
    AuthorizationDecision,
    Delegation,
    OperationOutcome,
    PolicyRelease,
    ReasonCode,
    RequestedScope,
    ResourceEnvelope,
    ResourceKey,
    ResourceType,
    ScopedId,
    ScopedKind,
    ScopeSlice,
    Selector,
    SelectorMode,
    admits,
    is_active,
    labels,
    principal_to_json,
    unrestricted_selectors,
)
from brain_domain.principal import Principal, PrincipalKind, PrincipalStatus
from brain_domain.tenancy import OwnedScope

NOW = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)
SCOPE = OwnedScope(uuid4(), uuid4(), uuid4())
KEY = ResourceKey(ResourceType.CONTENT_ARTIFACT, uuid4())
RELEASE = PolicyRelease("sha256:" + "a" * 64, "a" * 64, "b" * 64, "c" * 64, "authx-kernel:v1")


def _principal(kind=PrincipalKind.USER, status=PrincipalStatus.ACTIVE) -> Principal:
    return Principal(uuid4(), kind, "https://issuer", "subject", status)


def _slice(**changes) -> ScopeSlice:
    fields = dict(
        membership_id=uuid4(),
        scope=SCOPE,
        role="TenantMember",
        valid_from=NOW,
        expires_at=None,
        revoked_at=None,
        grant_revision=1,
        selectors=unrestricted_selectors(),
        classifications=WILDCARD,
        source_acl_ids=frozenset(),
    )
    fields.update(changes)
    return ScopeSlice(**fields)


def test_labels_are_exact_and_the_wildcard_is_explicit() -> None:
    assert labels("*") == WILDCARD
    assert labels(["b", "a"]) == frozenset({"a", "b"})
    with pytest.raises(ValueError):
        labels("internal")  # a bare string is not a set of labels
    with pytest.raises(ValueError):
        labels(["", "a"])
    assert admits(WILDCARD, ["anything"])
    assert admits(frozenset({"a", "b"}), ["a"]) and not admits(frozenset({"a"}), ["a", "b"])
    assert admits(frozenset(), [])  # no required labels


def test_selectors() -> None:
    account = uuid4()
    only = Selector(ScopedKind.ACCOUNT, SelectorMode.ONLY, frozenset({account}))
    assert only.admits(account) and not only.admits(uuid4())
    assert Selector(ScopedKind.BROKER, SelectorMode.ALL).admits(uuid4())
    assert not Selector(ScopedKind.POLICY, SelectorMode.ONLY).admits(uuid4())
    with pytest.raises(ValueError):
        Selector(ScopedKind.BROKER, SelectorMode.ALL, frozenset({uuid4()}))
    assert only.to_json() == {"kind": "account", "mode": "only", "ids": [str(account)]}
    assert {s.kind for s in unrestricted_selectors()} == set(ScopedKind)


def test_grant_slice_invariants_and_currency() -> None:
    current = _slice(expires_at=NOW + timedelta(hours=1))
    assert current.current_at(NOW) and not current.current_at(NOW + timedelta(hours=1))
    assert not current.current_at(NOW - timedelta(seconds=1))
    revoked = _slice(revoked_at=NOW + timedelta(minutes=1))
    assert revoked.current_at(NOW) and not revoked.current_at(NOW + timedelta(minutes=1))
    assert current.selector(ScopedKind.ACCOUNT).mode == SelectorMode.ALL
    payload = current.to_json()
    assert payload["classifications"] == "*" and payload["source_acl_ids"] == []
    for bad in (
        {"role": "Administrator"},
        {"grant_revision": 0},
        {"expires_at": NOW},
        {"selectors": unrestricted_selectors()[:2]},
        {"valid_from": datetime(2026, 1, 1)},  # noqa: DTZ001 - naive is rejected
    ):
        with pytest.raises(ValueError):
            _slice(**bad)


def test_resource_envelope_invariants() -> None:
    parent = ScopedId(ScopedKind.ACCOUNT, uuid4())
    envelope = ResourceEnvelope(
        KEY, SCOPE, frozenset({parent}), frozenset({"internal"}), frozenset(), frozenset(), 1, 1
    )
    assert envelope.parents(ScopedKind.ACCOUNT) == (parent.id,)
    assert envelope.parents(ScopedKind.BROKER) == ()
    base = dict(
        key=KEY,
        scope=SCOPE,
        parent_chain=frozenset(),
        classifications=frozenset({"i"}),
        source_acl_ids=frozenset(),
        dependency_keys=frozenset(),
        resource_revision=1,
        restriction_revision=1,
    )
    for bad in (
        {"classifications": frozenset()},
        {"classifications": frozenset({""})},
        {"source_acl_ids": frozenset({""})},
        {"resource_revision": 0},
        {"dependency_keys": frozenset({KEY})},
    ):
        with pytest.raises(ValueError):
            ResourceEnvelope(**{**base, **bad})


def test_requested_scope_is_narrowing_input_only() -> None:
    kb = uuid4()
    requested = RequestedScope(
        frozenset({kb}), (Selector(ScopedKind.BROKER, SelectorMode.ALL),), NOW, None
    )
    assert requested.to_json()["knowledge_base_ids"] == [str(kb)]
    assert NO_FILTER.to_json()["knowledge_base_ids"] is None
    with pytest.raises(ValueError):
        RequestedScope(None, (Selector(ScopedKind.BROKER, SelectorMode.ALL),) * 2, None, None)


def test_delegation_window_and_ceiling() -> None:
    user, agent = _principal(), _principal(PrincipalKind.AGENT)
    ceiling = ActionCeiling(SCOPE, KEY, frozenset({Action.READ}))
    delegation = Delegation(
        uuid4(),
        user.id,
        agent.id,
        uuid4(),
        NOW,
        NOW,
        NOW + timedelta(minutes=5),
        None,
        1,
        (ceiling,),
    )
    assert delegation.active_at(NOW) and not delegation.active_at(NOW + timedelta(minutes=5))
    assert delegation.permits(SCOPE, KEY, Action.READ)
    assert not delegation.permits(SCOPE, KEY, Action.COMMIT)
    assert not delegation.permits(OwnedScope(uuid4(), uuid4(), uuid4()), KEY, Action.READ)
    revoked = Delegation(
        uuid4(),
        user.id,
        agent.id,
        uuid4(),
        NOW,
        NOW,
        NOW + timedelta(hours=1),
        NOW + timedelta(minutes=1),
        2,
        (ceiling,),
    )
    assert not revoked.active_at(NOW + timedelta(minutes=2))
    assert delegation.to_json()["onward_delegation"] is False


def test_context_binds_authenticated_acting_and_delegation() -> None:
    user, agent = _principal(), _principal(PrincipalKind.AGENT)
    ceiling = ActionCeiling(SCOPE, KEY, frozenset({Action.READ}))
    delegation = Delegation(
        uuid4(),
        user.id,
        agent.id,
        uuid4(),
        NOW,
        NOW,
        NOW + timedelta(minutes=5),
        None,
        1,
        (ceiling,),
    )
    context = AuthorizationContext(
        agent, user, delegation, NOW, 2, RELEASE, (_slice(),), NO_FILTER, "t"
    )
    assert context.to_json()["delegation"]["id"] == str(delegation.id)
    stranger = _principal(PrincipalKind.AGENT)
    for kwargs in (
        {"authenticated": stranger, "acting": user, "delegation": delegation},
        {"authenticated": agent, "acting": user, "delegation": None},
        {"authenticated": user, "acting": user, "delegation": None, "authority_revision": 0},
        {"authenticated": user, "acting": user, "delegation": None, "trace_id": ""},
    ):
        base = dict(
            authorization_time=NOW,
            authority_revision=2,
            policy_release=RELEASE,
            scope_slices=(),
            requested_scope=NO_FILTER,
            trace_id="t",
        )
        with pytest.raises(ValueError):
            AuthorizationContext(**{**base, **kwargs})
    assert principal_to_json(user)["kind"] == "user"
    assert is_active(user) and not is_active(_principal(status=PrincipalStatus.DISABLED))


def _decision(**changes) -> AuthorizationDecision:
    user = _principal()
    fields = dict(
        decision_id=uuid4(),
        occurred_at=NOW,
        authenticated_principal_id=user.id,
        actor_principal_id=user.id,
        actor_kind=PrincipalKind.USER,
        executor_principal_id=None,
        delegation_id=None,
        delegation_revision=None,
        scope=SCOPE,
        resource=KEY,
        resource_revision=1,
        restriction_revision=1,
        action="read",
        allowed=True,
        reason_code=ReasonCode.ALLOWED,
        policy_hash="a" * 64,
        policy_release="r",
        grant_revision=1,
        matched_membership_ids=(uuid4(),),
        trace_id="t",
        operation_outcome=OperationOutcome.ATTEMPTED,
    )
    fields.update(changes)
    return AuthorizationDecision(**fields)


def test_decision_rules() -> None:
    allowed = _decision()
    assert allowed.with_outcome(OperationOutcome.SUCCEEDED).operation_outcome == "succeeded"
    denied = _decision(
        allowed=False,
        reason_code=ReasonCode.POLICY_DENIED,
        scope=None,
        matched_membership_ids=(),
        operation_outcome=OperationOutcome.DENIED,
    )
    with pytest.raises(ValueError):
        denied.with_outcome(OperationOutcome.SUCCEEDED)
    for bad in (
        {"scope": None},
        {"matched_membership_ids": ()},
        {"reason_code": ReasonCode.POLICY_DENIED},
        {"action": "delete"},
        {"grant_revision": 0},
        {"allowed": False},  # a denial cannot carry `allowed`
        {"allowed": False, "reason_code": ReasonCode.POLICY_DENIED},  # ...nor `attempted`
    ):
        with pytest.raises(ValueError):
            _decision(**bad)
    assert denied.to_json()["scope"] is None


def test_authentication_event() -> None:
    event = AuthenticationEvent(uuid4(), NOW, "expired", "/x", "t")
    assert event.to_json()["principal_id"] is None
    for bad in (
        {"reason_code": "stolen"},
        {"route_template": ""},
    ):
        base = dict(
            event_id=uuid4(),
            occurred_at=NOW,
            reason_code="expired",
            route_template="/x",
            trace_id="t",
        )
        with pytest.raises(ValueError):
            AuthenticationEvent(**{**base, **bad})
