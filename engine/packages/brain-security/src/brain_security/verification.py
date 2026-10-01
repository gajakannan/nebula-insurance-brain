from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

import jwt
from jwt import PyJWKClient

from brain_security.identity_profile import IssuerProfile


class CredentialError(Exception):
    """One of the schema `AuthenticationEvent` reason codes: malformed,
    invalid_signature, wrong_issuer, wrong_audience, expired, not_yet_valid,
    invalid_claims, unsupported_token_type, disabled_principal (the last raised by
    `PrincipalResolver`, not here). The message never contains the token."""

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
    client_id: str | None = None


class CredentialVerifier(Protocol):
    async def verify(self, bearer_token: str) -> VerifiedCredential: ...


def _claim_str(payload: dict[str, Any], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value:
        raise CredentialError("invalid_claims", f"claim {name} must be a non-empty string")
    return value


def _claim_time(payload: dict[str, Any], name: str) -> datetime | None:
    value = payload.get(name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise CredentialError("invalid_claims", f"claim {name} must be numeric")
    return datetime.fromtimestamp(value, tz=UTC)


def credential_from_claims(
    payload: dict[str, Any], *, audience: str, key_id: str
) -> VerifiedCredential:
    """Typed claim extraction shared by the real verifier and test harnesses: a
    missing or wrongly typed claim is a sanitized `invalid_claims` failure, never a
    KeyError/500 (assembly plan Step 2.1)."""
    expires_at = _claim_time(payload, "exp")
    if expires_at is None:
        raise CredentialError("invalid_claims", "claim exp is required")
    client = payload.get("azp", payload.get("client_id"))
    if client is not None and (not isinstance(client, str) or not client):
        raise CredentialError("invalid_claims", "client claim must be a non-empty string")
    return VerifiedCredential(
        issuer=_claim_str(payload, "iss"),
        subject=_claim_str(payload, "sub"),
        audience=audience,
        expires_at=expires_at,
        not_before=_claim_time(payload, "nbf"),
        key_id=key_id,
        client_id=client,
    )


def decode_verified(
    bearer_token: str, key: Any, profile: IssuerProfile, *, key_id: str
) -> VerifiedCredential:
    """Signature, algorithm, issuer, audience, time and required-claim checks with
    the trusted profile's constraints — never the token's own `alg` header."""
    try:
        header = jwt.get_unverified_header(bearer_token)
    except jwt.InvalidTokenError as exc:
        raise CredentialError("malformed", "unparseable token header") from exc
    token_type = header.get("typ")
    if token_type is not None and token_type not in profile.accepted_token_types:
        raise CredentialError("unsupported_token_type", "token type not accepted")
    try:
        payload = jwt.decode(
            bearer_token,
            key,
            algorithms=list(profile.algorithms),
            audience=sorted(profile.audiences),
            issuer=profile.issuer,
            options={"require": list(profile.required_claims)},
        )
    except jwt.ExpiredSignatureError as exc:
        raise CredentialError("expired", "token expired") from exc
    except jwt.InvalidAudienceError as exc:
        raise CredentialError("wrong_audience", "audience mismatch") from exc
    except jwt.InvalidIssuerError as exc:
        raise CredentialError("wrong_issuer", "issuer mismatch") from exc
    except jwt.ImmatureSignatureError as exc:
        raise CredentialError("not_yet_valid", "token not yet valid") from exc
    except jwt.MissingRequiredClaimError as exc:
        raise CredentialError("invalid_claims", "required claim missing") from exc
    except (jwt.InvalidAlgorithmError, jwt.InvalidSignatureError) as exc:
        raise CredentialError("invalid_signature", "signature rejected") from exc
    except jwt.DecodeError as exc:
        raise CredentialError("malformed", "token could not be decoded") from exc
    except jwt.InvalidTokenError as exc:
        raise CredentialError("invalid_claims", "token claims rejected") from exc
    token_audience = payload["aud"]
    candidates = [token_audience] if isinstance(token_audience, str) else list(token_audience)
    audience = next(a for a in candidates if a in profile.audiences)
    return credential_from_claims(payload, audience=audience, key_id=key_id)


class OidcJwksVerifier:
    """Verifies an authentik-issued OIDC access token against its published JWKS
    (cached by `PyJWKClient`, which refreshes once on an unknown `kid` — the
    controlled key-rotation path). Never touches storage: verification happens
    before any principal, membership or protected-resource read (ADR-0049). An
    unreachable JWKS denies; there is no fallback."""

    def __init__(
        self,
        *,
        issuer: str | None = None,
        audience: str | None = None,
        jwks_url: str | None = None,
        profile: IssuerProfile | None = None,
    ) -> None:
        if profile is None:
            if not issuer or not audience:
                raise ValueError("an issuer profile or issuer+audience is required")
            profile = IssuerProfile(issuer=issuer, audiences=frozenset({audience}))
        self._profile = profile
        url = jwks_url or profile.jwks_url or f"{profile.issuer.rstrip('/')}/jwks/"
        self._jwk_client = PyJWKClient(url)

    @property
    def profile(self) -> IssuerProfile:
        return self._profile

    async def verify(self, bearer_token: str) -> VerifiedCredential:
        if not bearer_token or bearer_token.count(".") != 2:
            raise CredentialError("malformed", "not a compact JWS")
        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(bearer_token)
        except jwt.PyJWKClientError as exc:
            raise CredentialError("invalid_signature", "no trusted signing key") from exc
        except jwt.DecodeError as exc:
            raise CredentialError("malformed", "unparseable token header") from exc
        return decode_verified(
            bearer_token, signing_key.key, self._profile, key_id=signing_key.key_id or ""
        )
