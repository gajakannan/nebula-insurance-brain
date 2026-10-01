from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

from brain_content.config import load_local_object_store_config
from brain_content.object_store import LocalFilesystemObjectStore
from brain_content.store import ContentArtifactStore, LocalContentArtifactStore
from brain_domain.authx import AuthenticationEvent, AuthenticationReason
from brain_domain.principal import Principal
from brain_persistence.authx import SqlAlchemyAuthorityStore
from brain_persistence.identity import (
    SqlAlchemyAuthenticationEventSink,
    SqlAlchemyIdentityRepository,
)
from brain_persistence.session import make_engine, make_session_factory
from brain_security.audit import AuthenticationEventSink
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_security.execution import AuthorizationExecution
from brain_security.identity_profile import IdentityProfile, load_identity_profile
from brain_security.principals import PrincipalResolver
from brain_security.verification import CredentialError, CredentialVerifier, OidcJwksVerifier
from fastapi import Depends, Header, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from brain_api.config import Settings
from brain_api.errors import BrainError, ServiceUnavailableError

logger = logging.getLogger(__name__)

settings = Settings.from_env()
_engine = make_engine(settings.database_url)
_session_factory = make_session_factory(_engine)
_identity_profile = load_identity_profile(settings.identity_profile_path)
_issuer_profile = _identity_profile.for_issuer(settings.oidc_issuer)
if _issuer_profile is None:
    raise RuntimeError("BRAIN_OIDC_ISSUER is not declared in the identity profile")
_credential_verifier = OidcJwksVerifier(profile=_issuer_profile)
_casbin_adapter = CasbinAuthorizationAdapter(
    settings.casbin_model_path, settings.casbin_policy_path
)
_content_store = LocalContentArtifactStore(
    LocalFilesystemObjectStore(load_local_object_store_config())
)


class UnauthenticatedError(BrainError):
    """Bearer extraction -> verify -> resolve failed (F0001-S0006 logic flow steps 1-3).
    The specific reason (expired, wrong_issuer, malformed, disabled_principal, ...) is
    never disclosed in the response body — only the stable `unauthenticated` code;
    the reason is recorded in the durable authentication event only."""

    status_code = 401
    code = "unauthenticated"
    title = "Unauthenticated"

    def __init__(self, internal_reason: str) -> None:
        self.internal_reason = internal_reason
        super().__init__(None)


def new_trace_id() -> str:
    """Server-generated; a caller-supplied header never becomes an audit identifier."""
    return str(uuid4())


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", None) or "unmatched"


def _record_credential_failure(
    request: Request, reason_code: str, event_trace_id: str | None = None
) -> None:
    """Process diagnostics for the verification reason; never logs the bearer token.
    `event_trace_id` correlates this line with the durable authentication event."""

    logger.warning(
        "unauthenticated_request",
        extra={
            "security_event": "credential_verification_failed",
            "reason_code": reason_code,
            "method": request.method,
            "path": request.url.path,
            "trace_id": request.headers.get("x-request-id") or str(uuid4()),
            "event_trace_id": event_trace_id,
        },
    )


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with _session_factory() as session:
        yield session


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return _session_factory


def get_credential_verifier() -> CredentialVerifier:
    return _credential_verifier


def get_identity_profile() -> IdentityProfile:
    return _identity_profile


def get_casbin_adapter() -> CasbinAuthorizationAdapter:
    return _casbin_adapter


def get_authentication_event_sink(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> AuthenticationEventSink:
    return SqlAlchemyAuthenticationEventSink(session_factory)


async def _reject(
    request: Request, sink: AuthenticationEventSink, reason_code: str
) -> UnauthenticatedError:
    """Durably record the rejected credential (no principal or resource lookup), then
    return the generic 401. If the event cannot be persisted, the caller gets a
    sanitized 503 instead and no protected operation runs."""
    trace_id = new_trace_id()
    _record_credential_failure(request, reason_code, trace_id)
    try:
        await sink.record(
            AuthenticationEvent(
                event_id=uuid4(),
                occurred_at=datetime.now(UTC),
                reason_code=AuthenticationReason(reason_code),
                route_template=_route_template(request),
                trace_id=trace_id,
            )
        )
    except Exception as exc:  # noqa: BLE001 - any sink failure is an availability failure
        logger.error("authentication_event_unavailable", extra={"reason_code": reason_code})
        raise ServiceUnavailableError() from exc
    return UnauthenticatedError(reason_code)


async def current_principal(
    request: Request,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db_session),
    credential_verifier: CredentialVerifier = Depends(get_credential_verifier),
    identity_profile: IdentityProfile = Depends(get_identity_profile),
    authentication_sink: AuthenticationEventSink = Depends(get_authentication_event_sink),
) -> Principal:
    """Verify before any storage read, then resolve the stable principal and commit
    the identity mapping before any protected operation (F0002-S0002)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise await _reject(request, authentication_sink, "malformed")
    token = authorization.removeprefix("Bearer ")
    try:
        credential = await credential_verifier.verify(token)
    except CredentialError as exc:
        raise await _reject(request, authentication_sink, exc.code) from exc
    resolver = PrincipalResolver(SqlAlchemyIdentityRepository(session), identity_profile)
    try:
        principal = await resolver.resolve(credential)
        await session.commit()
    except CredentialError as exc:
        await session.rollback()
        raise await _reject(request, authentication_sink, exc.code) from exc
    except SQLAlchemyError as exc:
        await session.rollback()
        raise ServiceUnavailableError() from exc
    return principal


async def get_authorization_execution(
    session: AsyncSession = Depends(get_db_session),
    casbin_adapter: CasbinAuthorizationAdapter = Depends(get_casbin_adapter),
) -> AuthorizationExecution:
    """Composes the shared evaluator, current-state store, clock and policy release
    over the request's unit of work. No caller-assembled membership snapshot."""
    return AuthorizationExecution(
        SqlAlchemyAuthorityStore(session), casbin_adapter, casbin_adapter.release
    )


def get_content_store() -> ContentArtifactStore:
    return _content_store
