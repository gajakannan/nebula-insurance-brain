from __future__ import annotations

from typing import Protocol
from uuid import UUID

from brain_domain.principal import Membership, Principal, PrincipalKind, PrincipalStatus

from brain_security.verification import CredentialError, VerifiedCredential


class PrincipalRepository(Protocol):
    async def find_by_issuer_subject(self, issuer: str, subject: str) -> Principal | None: ...

    async def create(self, *, issuer: str, subject: str, kind: PrincipalKind) -> Principal: ...

    async def memberships(self, principal_id: UUID) -> tuple[Membership, ...]: ...


class PrincipalResolver:
    """(issuer, subject) -> a stable internal principal; creates on first sight
    (F0001-S0006 logic flow step 3)."""

    def __init__(self, repository: PrincipalRepository) -> None:
        self._repository = repository

    async def resolve(self, credential: VerifiedCredential) -> Principal:
        principal = await self._repository.find_by_issuer_subject(
            credential.issuer, credential.subject
        )
        if principal is None:
            principal = await self._repository.create(
                issuer=credential.issuer, subject=credential.subject, kind=PrincipalKind.USER
            )
        if principal.status == PrincipalStatus.DISABLED:
            raise CredentialError("disabled_principal")
        return principal

    async def memberships(self, principal: Principal) -> tuple[Membership, ...]:
        """Current grants only; revoked rows excluded."""
        all_memberships = await self._repository.memberships(principal.id)
        return tuple(m for m in all_memberships if m.revoked_at is None)
