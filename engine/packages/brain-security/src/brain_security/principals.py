"""Verified credential -> one stable typed principal (F0002-S0002, ADR-0049/0061).

Runs only after `CredentialVerifier.verify` succeeded. Identity is the exact,
case-sensitive `(issuer, subject)` alias in `external_identity`; subjects are never
normalized and email is never an identity. First sight provisions a USER with no
grants only for a trusted human client; service/agent identities must already be
provisioned to their kind. A concurrent first resolution returns the single winner.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from brain_domain.principal import Principal, PrincipalKind, PrincipalStatus

from brain_security.identity_profile import IdentityProfile
from brain_security.verification import CredentialError, VerifiedCredential


class AliasConflict(ValueError):
    """The `(issuer, subject)` pair is already linked to a different principal."""


class IdentityRepository(Protocol):
    async def find_by_alias(self, issuer: str, subject: str) -> Principal | None: ...

    async def resolve_or_create(self, issuer: str, subject: str, kind: PrincipalKind) -> Principal:
        """Unique insert-or-read: exactly one principal survives concurrent first sight;
        creates the principal, its alias and its authority revision (1), no grants."""
        ...

    async def link_identity(
        self,
        principal_id: UUID,
        issuer: str,
        subject: str,
        approval_ref: str,
        operator_id: UUID,
    ) -> None: ...


class PrincipalResolver:
    """Resolve a verified credential; never consult roles, kinds or actor fields a
    client or model supplies (S0002 AC5/AC7)."""

    def __init__(self, repository: IdentityRepository, profile: IdentityProfile) -> None:
        self._repository = repository
        self._profile = profile

    async def resolve(self, credential: VerifiedCredential) -> Principal:
        principal = await self._repository.find_by_alias(credential.issuer, credential.subject)
        if principal is None:
            kind = self._profile.self_provision_kind(credential.issuer, credential.client_id)
            if kind is None:
                # An unprovisioned non-human (or unknown) client cannot become a USER.
                raise CredentialError("unsupported_token_type", "client not provisioned")
            principal = await self._repository.resolve_or_create(
                credential.issuer, credential.subject, kind
            )
        if principal.status != PrincipalStatus.ACTIVE:
            raise CredentialError("disabled_principal")
        return principal
