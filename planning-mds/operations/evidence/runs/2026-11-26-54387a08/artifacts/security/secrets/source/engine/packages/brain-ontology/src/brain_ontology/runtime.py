"""Runtime composition for the release CLI commands (ADR-0081 D5).

The token is verified by the existing F0002 credential verification and the
principal resolved exactly as the API does. The database, issuer, Casbin model
and policy, and identity profile come from the API's own environment variables,
so the CLI and the API authorize identically. Tokens are read from a file and are
never printed or logged.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from brain_domain.ontology import OntologyRefused
from brain_domain.principal import Principal
from brain_persistence.authx import SqlAlchemyAuthorityStore
from brain_persistence.identity import SqlAlchemyIdentityRepository
from brain_persistence.ontology_releases import OntologyReleaseStore
from brain_persistence.session import make_engine, make_session_factory
from brain_security.casbin_adapter import CasbinAuthorizationAdapter
from brain_security.execution import AuthorizationDenied, AuthorizationExecution
from brain_security.identity_profile import load_identity_profile
from brain_security.principals import PrincipalResolver
from brain_security.verification import CredentialError, OidcJwksVerifier
from sqlalchemy.ext.asyncio import AsyncSession

from brain_ontology.service import OntologyReleaseService, ScopeMismatch


def _find_upward(relative: str) -> str:
    for directory in (Path.cwd(), *Path.cwd().parents):
        if (directory / relative).is_file():
            return str(directory / relative)
    raise FileNotFoundError(relative)


@dataclass(slots=True)
class Runtime:
    session: AsyncSession
    principal: Principal
    service: OntologyReleaseService


ComposeFn = Callable[[argparse.Namespace], Any]


@asynccontextmanager
async def compose(args: argparse.Namespace) -> AsyncIterator[Runtime]:
    """Production composition from the environment. Tests replace `COMPOSE`."""
    engine = make_engine(
        os.environ.get(
            "BRAIN_DATABASE_URL", "postgresql+asyncpg://brain:brain@localhost:5432/brain"
        )
    )
    factory = make_session_factory(engine)
    profile = load_identity_profile(
        os.environ.get("BRAIN_IDENTITY_PROFILE_PATH")
        or _find_upward("config/authx-identity-profile.yaml")
    )
    issuer = profile.for_issuer(
        os.environ.get("BRAIN_OIDC_ISSUER", "http://localhost:9010/application/o/brain/")
    )
    if issuer is None:
        raise CredentialError("wrong_issuer")
    casbin = CasbinAuthorizationAdapter(
        os.environ.get("BRAIN_CASBIN_MODEL_PATH")
        or _find_upward("planning-mds/security/policies/model.conf"),
        os.environ.get("BRAIN_CASBIN_POLICY_PATH")
        or _find_upward("planning-mds/security/policies/policy.csv"),
    )
    token = Path(args.token_file).read_text(encoding="utf-8").strip()
    credential = await OidcJwksVerifier(profile=issuer).verify(token)
    try:
        async with factory() as session:
            principal = await PrincipalResolver(
                SqlAlchemyIdentityRepository(session), profile
            ).resolve(credential)
            await session.commit()
            execution = AuthorizationExecution(
                SqlAlchemyAuthorityStore(session), casbin, casbin.release
            )
            service = OntologyReleaseService(
                execution, OntologyReleaseStore(session), commit=session.commit
            )
            yield Runtime(session, principal, service)
    finally:
        await engine.dispose()


COMPOSE: ComposeFn = compose


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


async def run_command(args: argparse.Namespace, emit: Callable[[dict[str, Any]], None]) -> int:
    scope = (args.tenant, args.kb)
    trace_id = str(uuid4())
    base: dict[str, Any] = {
        "command": args.command,
        "tenant_id": str(args.tenant),
        "knowledge_base_id": str(args.kb),
    }
    try:
        async with COMPOSE(args) as rt:
            result = await _dispatch(rt, args, scope, trace_id)
    except CredentialError as exc:
        emit({**base, "status": "refused", "reason": "UNAUTHENTICATED", "detail": exc.code})
        return 1
    except OntologyRefused as refused:
        emit({**base, "status": "refused", "reason": refused.reason.value})
        return 1
    except (AuthorizationDenied, ScopeMismatch):
        # Non-disclosing: a denial never reveals whether a release exists.
        emit({**base, "status": "refused", "reason": "DENIED"})
        return 1
    emit({**base, "status": "ok", **result})
    return 0


async def _dispatch(
    rt: Runtime, args: argparse.Namespace, scope: tuple[Any, Any], trace_id: str
) -> dict[str, Any]:
    service, principal = rt.service, rt.principal
    match args.command:
        case "install":
            directory = Path(args.release_dir)
            result = await service.install(
                principal,
                scope,
                _read_json(directory / "manifest.json"),
                _read_json(directory / "normalized.json"),
                trace_id=trace_id,
            )
            return {
                "outcome": result.status,
                "release_ref": result.release_ref,
                "release_id": str(result.release_id),
                "manifest_digest": result.manifest_digest,
                "terms": result.terms,
            }
        case "install-extension":
            await service.install_extension(principal, scope, str(args.module), trace_id=trace_id)
            return {}  # pragma: no cover - always refused
        case "report":
            stored = await service.report(principal, scope, args.candidate, trace_id=trace_id)
            return {
                "report_id": str(stored.id),
                "report_status": stored.status,
                "report": stored.report,
            }
        case "review":
            review_id = await service.review(
                principal, scope, args.report, args.decision, args.rationale, trace_id=trace_id
            )
            return {"review_id": str(review_id)}
        case "activate":
            selection = await service.activate(
                principal, scope, args.release, args.review, trace_id=trace_id
            )
            return {
                "sequence": selection.sequence,
                "action": selection.action,
                "release_ref": selection.release_ref,
            }
        case "rollback":
            selection = await service.rollback(principal, scope, args.release, trace_id=trace_id)
            return {
                "sequence": selection.sequence,
                "action": selection.action,
                "release_ref": selection.release_ref,
            }
        case "history":
            rows = await service.history(principal, scope, trace_id=trace_id)
            return {
                "selections": [
                    {
                        "sequence": s.sequence,
                        "action": s.action,
                        "release_ref": s.release_ref,
                        "review_id": str(s.review_id) if s.review_id else None,
                        "actor_principal_id": str(s.actor_principal_id),
                        "selected_at": s.selected_at.isoformat(),
                    }
                    for s in rows
                ]
            }
    raise ValueError(args.command)  # pragma: no cover


__all__ = ["COMPOSE", "Runtime", "compose", "run_command"]
