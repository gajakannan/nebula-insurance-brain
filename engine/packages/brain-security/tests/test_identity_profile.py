from __future__ import annotations

from pathlib import Path

import pytest
from brain_domain.principal import PrincipalKind
from brain_security.identity_profile import (
    IdentityProfileError,
    IssuerProfile,
    load_identity_profile,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_committed_profile_loads_and_only_human_clients_self_provision() -> None:
    profile = load_identity_profile(REPO_ROOT / "config" / "authx-identity-profile.yaml")
    issuer = profile.issuers[0].issuer
    assert profile.self_provision_kind(issuer, "brain") == PrincipalKind.USER
    assert profile.self_provision_kind(issuer, "brain-service") is None
    assert profile.self_provision_kind(issuer, None) is None
    assert profile.self_provision_kind("https://unknown", "brain") is None
    assert profile.for_issuer(issuer).algorithms == ("RS256",)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"algorithms": ("HS256",)},
        {"algorithms": ("none",)},
        {"algorithms": ()},
        {"required_claims": ("iss", "sub")},
    ],
)
def test_unsafe_issuer_profiles_are_rejected(kwargs: dict) -> None:
    with pytest.raises(IdentityProfileError):
        IssuerProfile("https://issuer", frozenset({"brain"}), **kwargs)


@pytest.mark.parametrize(
    "body",
    [
        "version: 2\nissuers: []\n",
        "version: 1\nissuers: []\n",
        "version: 1\nissuers:\n  - issuer: x\n",
        "version: 1\nissuers:\n  - {issuer: x, audiences: [a]}\n  - {issuer: x, audiences: [a]}\n",
    ],
)
def test_malformed_profile_files_are_rejected(tmp_path: Path, body: str) -> None:
    path = tmp_path / "profile.yaml"
    path.write_text(body)
    with pytest.raises(IdentityProfileError):
        load_identity_profile(path)
