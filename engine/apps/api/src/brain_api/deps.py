from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Sequence
from uuid import uuid4

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
from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from brain_api.config import Settings
from brain_api.errors import BrainError

logger = logging.getLogger(__name__)

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


def _record_credential_failure(request: Request, reason_code: str) -> None:
    """Record the verification reason without ever logging the bearer token."""

    logger.warning(
        "unauthenticated_request",
        extra={
            "security_event": "credential_verification_failed",
            "reason_code": reason_code,
            "method": request.method,
            "path": request.url.path,
            "trace_id": request.headers.get("x-request-id") or str(uuid4()),
        },
    )


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with _session_factory() as session:
        yield session


def get_credential_verifier() -> OidcJwksVerifier:
    return _credential_verifier


def get_casbin_adapter() -> CasbinAuthorizationAdapter:
    return _casbin_adapter


async def current_principal(
    request: Request,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db_session),
    credential_verifier: OidcJwksVerifier = Depends(get_credential_verifier),
) -> Principal:
    if not authorization or not authorization.startswith("Bearer "):
        _record_credential_failure(request, "malformed")
        raise UnauthenticatedError("malformed")
    token = authorization.removeprefix("Bearer ")
    try:
        credential = await credential_verifier.verify(token)
        resolver = PrincipalResolver(SqlAlchemyPrincipalRepository(session))
        principal = await resolver.resolve(credential)
    except CredentialError as exc:
        _record_credential_failure(request, exc.code)
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
