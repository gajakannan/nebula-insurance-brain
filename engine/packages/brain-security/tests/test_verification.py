from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from brain_security.verification import CredentialError, OidcJwksVerifier
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWK

ISSUER = "https://authentik.local/application/o/brain/"
AUDIENCE = "brain"


@pytest.fixture(scope="module")
def rsa_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _make_token(rsa_key: rsa.RSAPrivateKey, **claim_overrides: object) -> str:
    now = datetime.now(UTC)
    claims: dict[str, object] = {
        "iss": ISSUER,
        "sub": "alice.tenant-a",
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    claims.update(claim_overrides)
    return jwt.encode(claims, rsa_key, algorithm="RS256", headers={"kid": "test-key-1"})


def _verifier_with_fixed_key(rsa_key: rsa.RSAPrivateKey) -> OidcJwksVerifier:
    verifier = OidcJwksVerifier(
        issuer=ISSUER, audience=AUDIENCE, jwks_url="https://unused.local/jwks/"
    )
    signing_key = PyJWK.from_json(
        __import__("json").dumps(
            {
                "kty": "RSA",
                "kid": "test-key-1",
                "n": jwt.utils.to_base64url_uint(rsa_key.public_key().public_numbers().n).decode(),
                "e": jwt.utils.to_base64url_uint(rsa_key.public_key().public_numbers().e).decode(),
            }
        ),
        algorithm="RS256",
    )
    verifier._jwk_client.get_signing_key_from_jwt = lambda _token: signing_key  # type: ignore[method-assign]
    return verifier


async def test_valid_token_verifies_and_returns_credential(rsa_key: rsa.RSAPrivateKey) -> None:
    token = _make_token(rsa_key)
    verifier = _verifier_with_fixed_key(rsa_key)

    credential = await verifier.verify(token)

    assert credential.issuer == ISSUER
    assert credential.subject == "alice.tenant-a"
    assert credential.audience == AUDIENCE


async def test_expired_token_raises_credential_error(rsa_key: rsa.RSAPrivateKey) -> None:
    token = _make_token(
        rsa_key,
        iat=datetime.now(UTC) - timedelta(hours=1),
        exp=datetime.now(UTC) - timedelta(minutes=1),
    )
    verifier = _verifier_with_fixed_key(rsa_key)

    with pytest.raises(CredentialError) as exc_info:
        await verifier.verify(token)
    assert exc_info.value.code == "expired"


async def test_wrong_audience_raises_credential_error(rsa_key: rsa.RSAPrivateKey) -> None:
    token = _make_token(rsa_key, aud="someone-else")
    verifier = _verifier_with_fixed_key(rsa_key)

    with pytest.raises(CredentialError) as exc_info:
        await verifier.verify(token)
    assert exc_info.value.code == "wrong_audience"


async def test_wrong_issuer_raises_credential_error(rsa_key: rsa.RSAPrivateKey) -> None:
    token = _make_token(rsa_key, iss="https://not-authentik.local/")
    verifier = _verifier_with_fixed_key(rsa_key)

    with pytest.raises(CredentialError) as exc_info:
        await verifier.verify(token)
    assert exc_info.value.code == "wrong_issuer"


async def test_not_yet_valid_token_raises_credential_error(rsa_key: rsa.RSAPrivateKey) -> None:
    token = _make_token(rsa_key, nbf=datetime.now(UTC) + timedelta(minutes=5))
    verifier = _verifier_with_fixed_key(rsa_key)

    with pytest.raises(CredentialError) as exc_info:
        await verifier.verify(token)
    assert exc_info.value.code == "not_yet_valid"


async def test_signature_from_a_different_key_is_rejected(rsa_key: rsa.RSAPrivateKey) -> None:
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = _make_token(other_key)
    verifier = _verifier_with_fixed_key(
        rsa_key
    )  # verifier trusts rsa_key's public key, not other_key's

    with pytest.raises(CredentialError) as exc_info:
        await verifier.verify(token)
    assert exc_info.value.code == "invalid_signature"


async def test_required_claims_and_types_fail_as_sanitized_invalid_claims(
    rsa_key: rsa.RSAPrivateKey,
) -> None:
    """F0002-S0002: missing/mistyped claims are `invalid_claims`, never KeyError/500."""
    verifier = _verifier_with_fixed_key(rsa_key)
    now = datetime.now(UTC)
    no_iat = jwt.encode(
        {"iss": ISSUER, "sub": "a", "aud": AUDIENCE, "exp": now + timedelta(minutes=5)},
        rsa_key,
        algorithm="RS256",
        headers={"kid": "test-key-1"},
    )
    numeric_sub = _make_token(rsa_key, sub=12345)
    for token in (no_iat, numeric_sub):
        with pytest.raises(CredentialError) as exc:
            await verifier.verify(token)
        assert exc.value.code in {"invalid_claims", "malformed"}
        assert token not in str(exc.value)


async def test_unaccepted_token_type_and_non_jws_are_rejected(rsa_key: rsa.RSAPrivateKey) -> None:
    verifier = _verifier_with_fixed_key(rsa_key)
    now = datetime.now(UTC)
    id_token_type = jwt.encode(
        {"iss": ISSUER, "sub": "a", "aud": AUDIENCE, "iat": now, "exp": now + timedelta(minutes=5)},
        rsa_key,
        algorithm="RS256",
        headers={"kid": "test-key-1", "typ": "logout+jwt"},
    )
    with pytest.raises(CredentialError) as exc:
        await verifier.verify(id_token_type)
    assert exc.value.code == "unsupported_token_type"
    with pytest.raises(CredentialError) as exc:
        await verifier.verify("not-a-jwt")
    assert exc.value.code == "malformed"


async def test_symmetric_algorithm_confusion_is_rejected(rsa_key: rsa.RSAPrivateKey) -> None:
    """The profile's algorithm allow-list wins over the token's own `alg` header."""
    verifier = _verifier_with_fixed_key(rsa_key)
    now = datetime.now(UTC)
    forged = jwt.encode(
        {"iss": ISSUER, "sub": "a", "aud": AUDIENCE, "iat": now, "exp": now + timedelta(minutes=5)},
        "shared-secret-guess",
        algorithm="HS256",
        headers={"kid": "test-key-1"},
    )
    with pytest.raises(CredentialError) as exc:
        await verifier.verify(forged)
    assert exc.value.code in {"invalid_signature", "malformed"}


async def test_client_claim_is_carried_for_self_provisioning(rsa_key: rsa.RSAPrivateKey) -> None:
    verifier = _verifier_with_fixed_key(rsa_key)
    credential = await verifier.verify(_make_token(rsa_key, azp="brain"))
    assert credential.client_id == "brain"
