"""F0002-S0002: verified credential -> one stable typed principal."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from brain_domain.principal import Principal, PrincipalKind, PrincipalStatus
from brain_security.identity_profile import IdentityProfile, IssuerProfile
from brain_security.principals import PrincipalResolver
from brain_security.verification import CredentialError, VerifiedCredential

ISSUER_X, ISSUER_Y = "https://issuer-x", "https://issuer-y"
PROFILE = IdentityProfile(
    (
        IssuerProfile(ISSUER_X, frozenset({"brain"}), human_clients=frozenset({"brain-web"})),
        IssuerProfile(ISSUER_Y, frozenset({"brain"}), human_clients=frozenset({"brain-web"})),
    )
)


class _FakeIdentities:
    def __init__(self) -> None:
        self.aliases: dict[tuple[str, str], Principal] = {}
        self.created = 0

    async def find_by_alias(self, issuer: str, subject: str) -> Principal | None:
        return self.aliases.get((issuer, subject))

    async def resolve_or_create(self, issuer: str, subject: str, kind: PrincipalKind) -> Principal:
        existing = self.aliases.get((issuer, subject))
        if existing is not None:
            return existing
        self.created += 1
        principal = Principal(uuid4(), kind, issuer, subject, PrincipalStatus.ACTIVE)
        self.aliases[(issuer, subject)] = principal
        return principal

    async def link_identity(self, *args: object) -> None:  # pragma: no cover - unused here
        raise NotImplementedError


def _credential(subject: str = "alice", issuer: str = ISSUER_X, client: str | None = "brain-web"):
    return VerifiedCredential(
        issuer=issuer,
        subject=subject,
        audience="brain",
        expires_at=datetime.now(UTC),
        not_before=None,
        key_id="key-1",
        client_id=client,
    )


async def test_first_sight_from_a_human_client_provisions_one_user() -> None:
    repo = _FakeIdentities()
    resolver = PrincipalResolver(repo, PROFILE)
    first = await resolver.resolve(_credential())
    second = await resolver.resolve(_credential())
    assert first.id == second.id and first.kind == PrincipalKind.USER and repo.created == 1


async def test_same_subject_at_another_issuer_is_a_different_principal() -> None:
    """EX-AUTHX-004 boundary: no cross-issuer link without an approved mapping."""
    resolver = PrincipalResolver(_FakeIdentities(), PROFILE)
    x = await resolver.resolve(_credential(issuer=ISSUER_X))
    y = await resolver.resolve(_credential(issuer=ISSUER_Y))
    assert x.id != y.id


async def test_unprovisioned_non_human_client_is_never_a_user() -> None:
    """Assembly plan Step 2.4: an unknown service/agent client cannot fall through."""
    repo = _FakeIdentities()
    resolver = PrincipalResolver(repo, PROFILE)
    for client in ("brain-worker", None):
        with pytest.raises(CredentialError) as exc:
            await resolver.resolve(_credential(subject="svc", client=client))
        assert exc.value.code == "unsupported_token_type"
    assert repo.created == 0


async def test_provisioned_service_resolves_to_its_trusted_kind() -> None:
    repo = _FakeIdentities()
    service = Principal(uuid4(), PrincipalKind.SERVICE, ISSUER_X, "svc", PrincipalStatus.ACTIVE)
    repo.aliases[(ISSUER_X, "svc")] = service
    resolved = await PrincipalResolver(repo, PROFILE).resolve(
        _credential(subject="svc", client="brain-worker")
    )
    assert resolved == service


async def test_disabled_principal_is_rejected_even_through_an_alias() -> None:
    """EX-AUTHX-006."""
    repo = _FakeIdentities()
    disabled = Principal(uuid4(), PrincipalKind.USER, ISSUER_X, "bob", PrincipalStatus.DISABLED)
    repo.aliases[(ISSUER_X, "bob")] = disabled
    repo.aliases[(ISSUER_Y, "bob-new")] = disabled
    for credential in (_credential("bob"), _credential("bob-new", ISSUER_Y)):
        with pytest.raises(CredentialError) as exc:
            await PrincipalResolver(repo, PROFILE).resolve(credential)
        assert exc.value.code == "disabled_principal"
