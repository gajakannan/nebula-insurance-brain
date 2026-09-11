from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from brain_domain.principal import Membership, Principal, PrincipalKind, PrincipalStatus
from brain_security.principals import PrincipalResolver
from brain_security.verification import CredentialError, VerifiedCredential


class _FakeRepository:
    def __init__(self) -> None:
        self.principals: dict[tuple[str, str], Principal] = {}
        self._memberships: dict[object, list[Membership]] = {}
        self.created = 0

    async def find_by_issuer_subject(self, issuer: str, subject: str) -> Principal | None:
        return self.principals.get((issuer, subject))

    async def create(self, *, issuer: str, subject: str, kind: PrincipalKind) -> Principal:
        self.created += 1
        principal = Principal(
            id=uuid4(), kind=kind, issuer=issuer, subject=subject, status=PrincipalStatus.ACTIVE
        )
        self.principals[(issuer, subject)] = principal
        return principal

    async def memberships(self, principal_id) -> tuple[Membership, ...]:
        return tuple(self._memberships.get(principal_id, []))


def _credential(subject: str = "alice") -> VerifiedCredential:
    return VerifiedCredential(
        issuer="https://authentik.local",
        subject=subject,
        audience="brain",
        expires_at=datetime.now(UTC),
        not_before=None,
        key_id="key-1",
    )


async def test_resolve_creates_a_principal_on_first_sight() -> None:
    repo = _FakeRepository()
    resolver = PrincipalResolver(repo)

    principal = await resolver.resolve(_credential())

    assert repo.created == 1
    assert principal.subject == "alice"


async def test_resolve_returns_the_same_principal_on_second_sight() -> None:
    repo = _FakeRepository()
    resolver = PrincipalResolver(repo)

    first = await resolver.resolve(_credential())
    second = await resolver.resolve(_credential())

    assert repo.created == 1
    assert first.id == second.id


async def test_resolve_raises_for_a_disabled_principal() -> None:
    repo = _FakeRepository()
    disabled = Principal(
        id=uuid4(),
        kind=PrincipalKind.USER,
        issuer="https://authentik.local",
        subject="bob",
        status=PrincipalStatus.DISABLED,
    )
    repo.principals[("https://authentik.local", "bob")] = disabled
    resolver = PrincipalResolver(repo)

    with pytest.raises(CredentialError) as exc_info:
        await resolver.resolve(_credential(subject="bob"))
    assert exc_info.value.code == "disabled_principal"


async def test_same_subject_from_a_different_issuer_resolves_to_a_different_principal() -> None:
    """F0001-S0006 AC: issuer-namespaced identity — `(issuer, subject)` is the key,
    not `subject` alone, so two IdPs never collide on a shared username."""
    repo = _FakeRepository()
    resolver = PrincipalResolver(repo)

    from_authentik = await resolver.resolve(
        VerifiedCredential(
            issuer="https://authentik.local",
            subject="shared-username",
            audience="brain",
            expires_at=datetime.now(UTC),
            not_before=None,
            key_id="key-1",
        )
    )
    from_other_issuer = await resolver.resolve(
        VerifiedCredential(
            issuer="https://other-idp.example",
            subject="shared-username",
            audience="brain",
            expires_at=datetime.now(UTC),
            not_before=None,
            key_id="key-1",
        )
    )

    assert from_authentik.id != from_other_issuer.id
    assert repo.created == 2


async def test_memberships_excludes_revoked_rows() -> None:
    repo = _FakeRepository()
    resolver = PrincipalResolver(repo)
    principal = await resolver.resolve(_credential())
    active = Membership(
        principal_id=principal.id,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        role="TenantMember",
        grant_revision=1,
        revoked_at=None,
    )
    revoked = Membership(
        principal_id=principal.id,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        role="TenantMember",
        grant_revision=1,
        revoked_at=datetime.now(UTC),
    )
    repo._memberships[principal.id] = [active, revoked]

    result = await resolver.memberships(principal)

    assert result == (active,)
