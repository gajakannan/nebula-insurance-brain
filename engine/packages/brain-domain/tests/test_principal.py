from __future__ import annotations

from uuid import uuid4

import pytest
from brain_domain.principal import Membership, Principal, PrincipalKind, PrincipalStatus


def test_principal_is_frozen() -> None:
    principal = Principal(
        id=uuid4(),
        kind=PrincipalKind.USER,
        issuer="authentik",
        subject="alice",
        status=PrincipalStatus.ACTIVE,
    )

    with pytest.raises(Exception):  # noqa: B017 — frozen dataclass raises FrozenInstanceError
        principal.status = PrincipalStatus.DISABLED  # type: ignore[misc]


def test_membership_carries_grant_revision_and_revocation() -> None:
    membership = Membership(
        principal_id=uuid4(),
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        role="Reviewer",
        grant_revision=1,
        revoked_at=None,
    )

    assert membership.revoked_at is None
    assert membership.role == "Reviewer"
