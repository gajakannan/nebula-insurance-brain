"""F0002-S0005 issuance rules: never wider than the actor's current authority."""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from brain_domain.authx import Action, ActionCeiling, Delegation, ResourceType
from brain_domain.principal import PrincipalKind, PrincipalStatus
from brain_security.delegation import DelegationRejected, validate_issuance


def _setup(build):
    owned = build.scope()
    user, agent = build.principal(), build.principal(PrincipalKind.AGENT)
    resource = build.envelope(owned)
    ceiling = ActionCeiling(owned, resource.key, frozenset({Action.READ}))
    return owned, user, agent, resource, ceiling


def test_issuance_within_current_authority_is_accepted(build, policy) -> None:
    owned, user, agent, _resource, ceiling = _setup(build)
    delegation = build.delegation(user, agent, (ceiling,))
    validate_issuance(
        delegation,
        acting=user,
        executor=agent,
        acting_slices=[build.grant(owned, "TenantMember")],
        policy=policy,
        now=build.now,
    )


def test_issuance_rules(build, policy) -> None:
    owned, user, agent, resource, ceiling = _setup(build)
    reader = [build.grant(owned, "TenantMember")]
    wider = ActionCeiling(owned, resource.key, frozenset({Action.READ, Action.COMMIT}))
    cases = [
        (build.delegation(user, agent, (wider,)), user, agent, reader),  # exceeds authority
        (build.delegation(user, agent, (ceiling,)), user, agent, []),  # actor has no grant
        (
            build.delegation(user, agent, (ceiling,)),
            user,
            build.principal(),
            reader,
        ),  # USER executor
        (
            build.delegation(user, agent, (ceiling,)),
            user,
            build.principal(PrincipalKind.AGENT, PrincipalStatus.DISABLED),
            reader,
        ),
        (
            build.delegation(
                user,
                agent,
                (ceiling,),
                not_before=build.now - timedelta(hours=2),
                expires_at=build.now - timedelta(hours=1),
            ),
            user,
            agent,
            reader,
        ),
        (build.delegation(user, agent, (ceiling,), revoked_at=build.now), user, agent, reader),
    ]
    for delegation, acting, executor, slices in cases:
        with pytest.raises(DelegationRejected):
            validate_issuance(
                delegation,
                acting=acting,
                executor=executor,
                acting_slices=slices,
                policy=policy,
                now=build.now,
            )
    onward_agent = build.principal(PrincipalKind.AGENT)
    with pytest.raises(DelegationRejected):
        validate_issuance(
            build.delegation(onward_agent, agent, (ceiling,)),
            acting=onward_agent,
            executor=agent,
            acting_slices=reader,
            policy=policy,
            now=build.now,
        )


def test_delegation_carrier_rejects_unbounded_shapes(build) -> None:
    owned, user, agent, resource, ceiling = _setup(build)
    base = dict(
        id=uuid4(),
        acting_principal_id=user.id,
        executor_principal_id=agent.id,
        issued_by=uuid4(),
        issued_at=build.now,
        not_before=build.now,
        expires_at=build.now + timedelta(minutes=5),
        revoked_at=None,
        revision=1,
        ceilings=(ceiling,),
    )
    for change in (
        {"expires_at": build.now},
        {"ceilings": ()},
        {"revision": 0},
        {"onward_delegation": True},
        {"executor_principal_id": user.id},
    ):
        with pytest.raises(ValueError):
            Delegation(**{**base, **change})
    with pytest.raises(ValueError):
        ActionCeiling(owned, resource.key, frozenset())
    assert ResourceType(resource.key.type) == ResourceType.CONTENT_ARTIFACT
