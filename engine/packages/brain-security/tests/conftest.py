from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from brain_domain.authx import (
    NO_FILTER,
    ActionCeiling,
    AuthorizationContext,
    Delegation,
    RequestedScope,
    ResourceEnvelope,
    ResourceKey,
    ResourceType,
    ScopedId,
    ScopeSlice,
    Selector,
    unrestricted_selectors,
)
from brain_domain.principal import Principal, PrincipalKind, PrincipalStatus
from brain_domain.tenancy import OwnedScope
from brain_security.casbin_adapter import CasbinAuthorizationAdapter

# repo root: tests -> brain-security -> packages -> engine -> nebula-insurance-brain
REPO_ROOT = Path(__file__).resolve().parents[4]
NOW = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)


@pytest.fixture
def model_path() -> Path:
    return REPO_ROOT / "planning-mds" / "security" / "policies" / "model.conf"


@pytest.fixture
def policy_path() -> Path:
    return REPO_ROOT / "planning-mds" / "security" / "policies" / "policy.csv"


@pytest.fixture
def policy(model_path: Path, policy_path: Path) -> CasbinAuthorizationAdapter:
    return CasbinAuthorizationAdapter(model_path, policy_path)


def principal(
    kind: PrincipalKind = PrincipalKind.USER, status: PrincipalStatus = PrincipalStatus.ACTIVE
) -> Principal:
    return Principal(uuid4(), kind, "https://issuer-x", uuid4().hex, status)


def scope(tenant: UUID | None = None, kb: UUID | None = None) -> OwnedScope:
    return OwnedScope(tenant or uuid4(), uuid4(), kb or uuid4())


def grant(
    owned: OwnedScope,
    role: str,
    *,
    selectors: tuple[Selector, ...] | None = None,
    classifications: object = "*",
    source_acl_ids: object = "*",
    valid_from: datetime = NOW - timedelta(days=1),
    expires_at: datetime | None = None,
    membership_id: UUID | None = None,
) -> ScopeSlice:
    return ScopeSlice(
        membership_id=membership_id or uuid4(),
        scope=owned,
        role=role,
        valid_from=valid_from,
        expires_at=expires_at,
        revoked_at=None,
        grant_revision=1,
        selectors=selectors if selectors is not None else unrestricted_selectors(),
        classifications=classifications,  # type: ignore[arg-type]
        source_acl_ids=source_acl_ids,  # type: ignore[arg-type]
    )


def envelope(
    owned: OwnedScope,
    resource_type: ResourceType = ResourceType.CONTENT_ARTIFACT,
    *,
    parents: tuple[ScopedId, ...] = (),
    classifications: tuple[str, ...] = ("internal",),
    source_acl_ids: tuple[str, ...] = (),
    dependencies: tuple[ResourceKey, ...] = (),
    resource_id: UUID | None = None,
) -> ResourceEnvelope:
    return ResourceEnvelope(
        key=ResourceKey(resource_type, resource_id or uuid4()),
        scope=owned,
        parent_chain=frozenset(parents),
        classifications=frozenset(classifications),
        source_acl_ids=frozenset(source_acl_ids),
        dependency_keys=frozenset(dependencies),
        resource_revision=1,
        restriction_revision=1,
    )


def context(
    slices: tuple[ScopeSlice, ...],
    *,
    authenticated: Principal | None = None,
    acting: Principal | None = None,
    delegation: Delegation | None = None,
    requested: RequestedScope = NO_FILTER,
    at: datetime = NOW,
    release: object = None,
) -> AuthorizationContext:
    from brain_security.casbin_adapter import compute_policy_release

    authenticated = authenticated or principal()
    return AuthorizationContext(
        authenticated=authenticated,
        acting=acting or authenticated,
        delegation=delegation,
        authorization_time=at,
        authority_revision=7,
        policy_release=release or compute_policy_release(b"model", b"policy"),  # type: ignore[arg-type]
        scope_slices=slices,
        requested_scope=requested,
        trace_id="trace-1",
    )


def delegation(
    acting: Principal,
    executor: Principal,
    ceilings: tuple[ActionCeiling, ...],
    *,
    not_before: datetime = NOW - timedelta(minutes=5),
    expires_at: datetime = NOW + timedelta(minutes=30),
    revoked_at: datetime | None = None,
) -> Delegation:
    return Delegation(
        id=uuid4(),
        acting_principal_id=acting.id,
        executor_principal_id=executor.id,
        issued_by=uuid4(),
        issued_at=not_before,
        not_before=not_before,
        expires_at=expires_at,
        revoked_at=revoked_at,
        revision=1,
        ceilings=ceilings,
    )


@pytest.fixture
def build() -> SimpleNamespace:
    return SimpleNamespace(
        principal=principal,
        scope=scope,
        grant=grant,
        envelope=envelope,
        context=context,
        delegation=delegation,
        now=NOW,
    )
