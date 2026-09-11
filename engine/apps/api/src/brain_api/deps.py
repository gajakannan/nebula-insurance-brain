from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence

from brain_content.config import load_local_object_store_config
from brain_content.object_store import LocalFilesystemObjectStore
from brain_content.store import ContentArtifactStore, LocalContentArtifactStore
from brain_domain.principal import Membership, Principal
from brain_persistence.repositories import (
    SqlAlchemyAuditEventRepository,
    SqlAlchemyContentArtifactLookup,
    SqlAlchemyPrincipalRepository,
)
from brain_persistence.session import make_engine, make_session_factory
from brain_security.audit import RepositoryAuditSink
from brain_security.authorization import AuthorizationService
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_security.principals import PrincipalResolver
from brain_security.verification import CredentialError, OidcJwksVerifier
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from brain_api.config import Settings
from brain_api.errors import BrainError

settings = Settings.from_env()
_engine = make_engine(settings.database_url)
_session_factory = make_session_factory(_engine)
_credential_verifier = OidcJwksVerifier(
    issuer=settings.oidc_issuer, audience=settings.oidc_audience
)
_casbin_adapter = CasbinAuthorizationAdapter(
    settings.casbin_model_path, settings.casbin_policy_path
)
_content_store = LocalContentArtifactStore(
    LocalFilesystemObjectStore(load_local_object_store_config())
)


class UnauthenticatedError(BrainError):
    """Bearer extraction -> verify -> resolve failed (F0001-S0006 logic flow steps 1-3).
    The specific reason (expired, wrong_issuer, malformed, ...) is never disclosed in the
    response body — only the stable `unauthenticated` code — per the API contract
    ('reason code recorded in the audit event only')."""

    status_code = 401
    code = "unauthenticated"
    title = "Unauthenticated"

    def __init__(self, internal_reason: str) -> None:
        self.internal_reason = internal_reason
        super().__init__(None)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with _session_factory() as session:
        yield session


def get_credential_verifier() -> OidcJwksVerifier:
    return _credential_verifier


def get_casbin_adapter() -> CasbinAuthorizationAdapter:
    return _casbin_adapter


async def current_principal(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db_session),
    credential_verifier: OidcJwksVerifier = Depends(get_credential_verifier),
) -> Principal:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthenticatedError("malformed")
    token = authorization.removeprefix("Bearer ")
    try:
        credential = await credential_verifier.verify(token)
        resolver = PrincipalResolver(SqlAlchemyPrincipalRepository(session))
        principal = await resolver.resolve(credential)
    except CredentialError as exc:
        raise UnauthenticatedError(exc.code) from exc
    await session.commit()
    return principal


async def current_principal_memberships(
    principal: Principal = Depends(current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Sequence[Membership]:
    resolver = PrincipalResolver(SqlAlchemyPrincipalRepository(session))
    return await resolver.memberships(principal)


async def get_authorization_service(
    session: AsyncSession = Depends(get_db_session),
    casbin_adapter: CasbinAuthorizationAdapter = Depends(get_casbin_adapter),
) -> AuthorizationService:
    audit = RepositoryAuditSink(SqlAlchemyAuditEventRepository(session))
    return AuthorizationService(casbin_adapter, audit)


def get_content_store() -> ContentArtifactStore:
    return _content_store


async def get_content_artifact_lookup(
    session: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyContentArtifactLookup:
    return SqlAlchemyContentArtifactLookup(session)
