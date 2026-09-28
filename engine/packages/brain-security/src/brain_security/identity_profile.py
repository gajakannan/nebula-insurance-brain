"""Trusted, non-secret identity profile (F0002-S0002, `config/authx-identity-profile.yaml`).

Declares which issuers, audiences, algorithms, token types and claims a credential
must carry, and which client IDs are human clients allowed to self-provision a USER
principal on first verified sight. Service and agent clients are never
self-provisioned: they must be explicitly provisioned to their kind, so an unknown
non-human client cannot fall through to USER creation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from brain_domain.principal import PrincipalKind

DEFAULT_REQUIRED_CLAIMS = ("iss", "sub", "aud", "exp", "iat")


class IdentityProfileError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class IssuerProfile:
    issuer: str
    audiences: frozenset[str]
    algorithms: tuple[str, ...] = ("RS256",)
    accepted_token_types: frozenset[str] = frozenset({"JWT", "at+jwt"})
    required_claims: tuple[str, ...] = DEFAULT_REQUIRED_CLAIMS
    human_clients: frozenset[str] = field(default_factory=frozenset)
    jwks_url: str | None = None

    def __post_init__(self) -> None:
        if not self.issuer or not self.audiences:
            raise IdentityProfileError("an issuer profile needs an issuer and an audience")
        if not self.algorithms or any(
            a.lower() == "none" or a.startswith("HS") for a in self.algorithms
        ):
            raise IdentityProfileError("only asymmetric signature algorithms are accepted")
        missing = {"iss", "sub", "aud", "exp"} - set(self.required_claims)
        if missing:
            raise IdentityProfileError(f"required claims must include {sorted(missing)}")


@dataclass(frozen=True, slots=True)
class IdentityProfile:
    issuers: tuple[IssuerProfile, ...]

    def for_issuer(self, issuer: str) -> IssuerProfile | None:
        return next((p for p in self.issuers if p.issuer == issuer), None)

    def self_provision_kind(self, issuer: str, client_id: str | None) -> PrincipalKind | None:
        """USER for a configured human client; otherwise no self-provisioning."""
        profile = self.for_issuer(issuer)
        if profile is None or client_id is None or client_id not in profile.human_clients:
            return None
        return PrincipalKind.USER


def _issuer_from_mapping(data: dict[str, Any]) -> IssuerProfile:
    try:
        return IssuerProfile(
            issuer=str(data["issuer"]),
            audiences=frozenset(str(a) for a in data["audiences"]),
            algorithms=tuple(str(a) for a in data.get("algorithms", ("RS256",))),
            accepted_token_types=frozenset(
                str(t) for t in data.get("accepted_token_types", ("JWT", "at+jwt"))
            ),
            required_claims=tuple(
                str(c) for c in data.get("required_claims", DEFAULT_REQUIRED_CLAIMS)
            ),
            human_clients=frozenset(str(c) for c in data.get("human_clients", ())),
            jwks_url=str(data["jwks_url"]) if data.get("jwks_url") else None,
        )
    except (KeyError, TypeError) as exc:
        raise IdentityProfileError(f"malformed issuer profile: {exc}") from exc


def load_identity_profile(path: str | Path) -> IdentityProfile:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("version") != 1:
        raise IdentityProfileError("identity profile must declare version: 1")
    issuers = raw.get("issuers")
    if not isinstance(issuers, list) or not issuers:
        raise IdentityProfileError("identity profile needs at least one issuer")
    profile = IdentityProfile(tuple(_issuer_from_mapping(item) for item in issuers))
    if len({p.issuer for p in profile.issuers}) != len(profile.issuers):
        raise IdentityProfileError("duplicate issuer profile")
    return profile
