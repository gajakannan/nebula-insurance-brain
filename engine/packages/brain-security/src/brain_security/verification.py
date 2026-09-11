from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

import jwt
from jwt import PyJWKClient


class CredentialError(Exception):
    """One of: invalid_signature, wrong_issuer, wrong_audience, expired, not_yet_valid,
    malformed, disabled_principal (raised by `PrincipalResolver`, not here)."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or code)


@dataclass(frozen=True, slots=True)
class VerifiedCredential:
    issuer: str
    subject: str
    audience: str
    expires_at: datetime
    not_before: datetime | None
    key_id: str


class CredentialVerifier(Protocol):
    async def verify(self, bearer_token: str) -> VerifiedCredential: ...


class OidcJwksVerifier:
    """Verifies an authentik-issued OIDC access token against its published JWKS
    (cached by `PyJWKClient`). Never touches storage — verification happens before
    any read (F0001-S0006 logic flow step 2)."""

    def __init__(self, *, issuer: str, audience: str, jwks_url: str | None = None) -> None:
        self._issuer = issuer
        self._audience = audience
        self._jwk_client = PyJWKClient(jwks_url or f"{issuer.rstrip('/')}/jwks/")

    async def verify(self, bearer_token: str) -> VerifiedCredential:
        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(bearer_token)
        except jwt.PyJWKClientError as exc:
            raise CredentialError("invalid_signature", str(exc)) from exc

        try:
            payload = jwt.decode(
                bearer_token,
                signing_key.key,
                algorithms=[signing_key.algorithm_name or "RS256"],
                audience=self._audience,
                issuer=self._issuer,
            )
        except jwt.ExpiredSignatureError as exc:
            raise CredentialError("expired", str(exc)) from exc
        except jwt.InvalidAudienceError as exc:
            raise CredentialError("wrong_audience", str(exc)) from exc
        except jwt.InvalidIssuerError as exc:
            raise CredentialError("wrong_issuer", str(exc)) from exc
        except jwt.ImmatureSignatureError as exc:
            raise CredentialError("not_yet_valid", str(exc)) from exc
        except jwt.InvalidTokenError as exc:
            raise CredentialError("invalid_signature", str(exc)) from exc

        return VerifiedCredential(
            issuer=payload["iss"],
            subject=payload["sub"],
            audience=self._audience,
            expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
            not_before=(
                datetime.fromtimestamp(payload["nbf"], tz=UTC) if "nbf" in payload else None
            ),
            key_id=signing_key.key_id or "",
        )
