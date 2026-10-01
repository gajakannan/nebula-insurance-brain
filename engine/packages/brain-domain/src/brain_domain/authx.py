"""AuthX kernel v1 carriers (F0002, `planning-mds/schemas/authx-kernel.schema.json`).

Frozen, I/O-free types that mirror the schema field-for-field. Structural
validation here rejects malformed carriers; it cannot establish trust — every
`AuthorizationContext` is assembled from trusted repositories, never deserialized
from a client or model (ADR-0062). Collection order carries no authorization
meaning, so collections are stored as frozensets or canonically sorted tuples.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from brain_domain.principal import Principal, PrincipalKind, PrincipalStatus
from brain_domain.tenancy import OwnedScope

SCHEMA_VERSION = 1
CONTRACT_VERSION = "authx-kernel:v1"


class ResourceType(StrEnum):
    CONTENT_ARTIFACT = "content_artifact"
    REVIEW_TASK = "review_task"
    FACT_SLOT = "fact_slot"


class Action(StrEnum):
    READ = "read"
    ANNOTATE = "annotate"
    INGEST = "ingest"
    INTERPRET = "interpret"
    COMMIT = "commit"


class PilotRole(StrEnum):
    """The three existing F0001 roles; F0002 adds none (PRD, G1 decision)."""

    TENANT_MEMBER = "TenantMember"
    REVIEWER = "Reviewer"
    SERVICE_PRINCIPAL = "ServicePrincipal"


class ScopedKind(StrEnum):
    BROKER = "broker"
    ACCOUNT = "account"
    POLICY = "policy"


class SelectorMode(StrEnum):
    ALL = "all"
    ONLY = "only"


class ReasonCode(StrEnum):
    ALLOWED = "allowed"
    INACTIVE_PRINCIPAL = "inactive_principal"
    NO_MEMBERSHIP = "no_membership"
    MEMBERSHIP_EXPIRED = "membership_expired"
    POLICY_DENIED = "policy_denied"
    SCOPE_DENIED = "scope_denied"
    PARENT_DENIED = "parent_denied"
    CLASSIFICATION_DENIED = "classification_denied"
    SOURCE_DENIED = "source_denied"
    DEPENDENCY_DENIED = "dependency_denied"
    DELEGATION_DENIED = "delegation_denied"
    DELEGATION_EXPIRED = "delegation_expired"
    STALE_AUTHORITY = "stale_authority"
    MISSING_ATTRIBUTES = "missing_attributes"
    UNKNOWN_ACTION = "unknown_action"


class OperationOutcome(StrEnum):
    ATTEMPTED = "attempted"
    SUCCEEDED = "succeeded"
    DENIED = "denied"
    FAILED = "failed"


class AuthenticationReason(StrEnum):
    MALFORMED = "malformed"
    INVALID_SIGNATURE = "invalid_signature"
    WRONG_ISSUER = "wrong_issuer"
    WRONG_AUDIENCE = "wrong_audience"
    EXPIRED = "expired"
    NOT_YET_VALID = "not_yet_valid"
    INVALID_CLAIMS = "invalid_claims"
    UNSUPPORTED_TOKEN_TYPE = "unsupported_token_type"
    DISABLED_PRINCIPAL = "disabled_principal"


WILDCARD: Literal["*"] = "*"
LabelSet = frozenset[str] | Literal["*"]


def labels(values: Iterable[str] | Literal["*"]) -> LabelSet:
    """Normalize a label allowance: the explicit wildcard, or an exact label set.

    The wildcard is trusted grant data, never a default. Labels are opaque exact
    strings; no hierarchy is inferred (assembly plan Step 1)."""
    if values == WILDCARD:
        return WILDCARD
    if isinstance(values, str):
        raise ValueError("a label set is the wildcard or a collection of labels")
    result = frozenset(values)
    if any(not isinstance(v, str) or not v for v in result):
        raise ValueError("labels are non-empty strings")
    return result


def admits(allowance: LabelSet, required: Iterable[str]) -> bool:
    """Every required label must be allowed (conjunction, not overlap)."""
    if allowance == WILDCARD:
        return True
    return all(label in allowance for label in required)


def _labels_to_json(value: LabelSet) -> str | list[str]:
    return WILDCARD if value == WILDCARD else sorted(value)


def _require_aware(value: datetime | None, name: str) -> None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError(f"{name} must be timezone-aware UTC")


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


@dataclass(frozen=True, slots=True, order=True)
class ResourceKey:
    type: ResourceType
    id: UUID

    def __post_init__(self) -> None:
        object.__setattr__(self, "type", ResourceType(self.type))

    def to_json(self) -> dict[str, str]:
        return {"type": self.type.value, "id": str(self.id)}


@dataclass(frozen=True, slots=True, order=True)
class ScopedId:
    """One broker/account/policy parent of a resource. Broker IDs are never tenant IDs."""

    kind: ScopedKind
    id: UUID

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", ScopedKind(self.kind))

    def to_json(self) -> dict[str, str]:
        return {"kind": self.kind.value, "id": str(self.id)}


@dataclass(frozen=True, slots=True)
class Selector:
    """`all` admits every parent of its kind; `only` admits exactly `ids`.
    `only` with no IDs admits none of that kind."""

    kind: ScopedKind
    mode: SelectorMode
    ids: frozenset[UUID] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", ScopedKind(self.kind))
        object.__setattr__(self, "mode", SelectorMode(self.mode))
        object.__setattr__(self, "ids", frozenset(self.ids))
        if self.mode == SelectorMode.ALL and self.ids:
            raise ValueError("an 'all' selector carries no IDs")

    def admits(self, value: UUID) -> bool:
        return self.mode == SelectorMode.ALL or value in self.ids

    def to_json(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "mode": self.mode.value,
            "ids": sorted(str(i) for i in self.ids),
        }


def unrestricted_selectors() -> tuple[Selector, ...]:
    """Explicit `all` for every parent kind — for trusted provisioning only.

    There is deliberately no implicit default: callers must choose this."""
    return tuple(Selector(kind, SelectorMode.ALL) for kind in ScopedKind)


def _one_selector_per_kind(selectors: Iterable[Selector]) -> tuple[Selector, ...]:
    ordered = tuple(sorted(selectors, key=lambda s: s.kind.value))
    kinds = [s.kind for s in ordered]
    if sorted(kinds) != sorted(ScopedKind):
        raise ValueError("a grant slice needs exactly one selector per parent kind")
    return ordered


@dataclass(frozen=True, slots=True)
class ScopeSlice:
    """One complete current grant: a membership's role AND all of its restrictions.

    A slice is never combined with another (no role from slice A with labels from
    slice B — ADR-0062)."""

    membership_id: UUID
    scope: OwnedScope
    role: PilotRole
    valid_from: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    grant_revision: int
    selectors: tuple[Selector, ...]
    classifications: LabelSet
    source_acl_ids: LabelSet

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", PilotRole(self.role))
        _require_aware(self.valid_from, "valid_from")
        _require_aware(self.expires_at, "expires_at")
        _require_aware(self.revoked_at, "revoked_at")
        if self.grant_revision < 1:
            raise ValueError("grant_revision must be positive")
        if self.expires_at is not None and self.expires_at <= self.valid_from:
            raise ValueError("expires_at must follow valid_from")
        object.__setattr__(self, "selectors", _one_selector_per_kind(self.selectors))
        object.__setattr__(self, "classifications", labels(self.classifications))
        object.__setattr__(self, "source_acl_ids", labels(self.source_acl_ids))

    def current_at(self, at: datetime) -> bool:
        if self.revoked_at is not None and self.revoked_at <= at:
            return False
        if at < self.valid_from:
            return False
        return self.expires_at is None or at < self.expires_at

    def selector(self, kind: ScopedKind) -> Selector:
        return next(s for s in self.selectors if s.kind == kind)

    def to_json(self) -> dict[str, object]:
        return {
            "membership_id": str(self.membership_id),
            "scope": self.scope.to_json(),
            "role": self.role.value,
            "valid_from": self.valid_from.isoformat(),
            "expires_at": _iso(self.expires_at),
            "revoked_at": _iso(self.revoked_at),
            "grant_revision": self.grant_revision,
            "selectors": [s.to_json() for s in self.selectors],
            "classifications": _labels_to_json(self.classifications),
            "source_acl_ids": _labels_to_json(self.source_acl_ids),
        }


@dataclass(frozen=True, slots=True)
class ResourceEnvelope:
    """Security metadata hydrated only from authoritative rows (never request input).

    `classifications` is required and non-empty: an absent classification is a
    missing attribute, not "unrestricted". An empty `source_acl_ids` means the
    trusted resource declares no source ACL."""

    key: ResourceKey
    scope: OwnedScope
    parent_chain: frozenset[ScopedId]
    classifications: frozenset[str]
    source_acl_ids: frozenset[str]
    dependency_keys: frozenset[ResourceKey]
    resource_revision: int
    restriction_revision: int

    def __post_init__(self) -> None:
        for name in ("parent_chain", "classifications", "source_acl_ids", "dependency_keys"):
            object.__setattr__(self, name, frozenset(getattr(self, name)))
        if not self.classifications or any(not c for c in self.classifications):
            raise ValueError("a resource declares at least one classification label")
        if any(not s for s in self.source_acl_ids):
            raise ValueError("source ACL labels are non-empty strings")
        if self.resource_revision < 1 or self.restriction_revision < 1:
            raise ValueError("resource revisions must be positive")
        if self.key in self.dependency_keys:
            raise ValueError("a resource cannot depend on itself")

    def parents(self, kind: ScopedKind) -> tuple[UUID, ...]:
        return tuple(sorted(p.id for p in self.parent_chain if p.kind == kind))


@dataclass(frozen=True, slots=True)
class RequestedScope:
    """Untrusted narrowing input. `knowledge_base_ids=None` adds no filter; an empty
    set admits nothing. Filters only intersect authority, never add it. Business
    valid/known times select history and never participate in authorization."""

    knowledge_base_ids: frozenset[UUID] | None
    selectors: tuple[Selector, ...]
    business_valid_as_of: datetime | None
    business_known_as_of: datetime | None

    def __post_init__(self) -> None:
        if self.knowledge_base_ids is not None:
            object.__setattr__(self, "knowledge_base_ids", frozenset(self.knowledge_base_ids))
        kinds = [s.kind for s in self.selectors]
        if len(kinds) != len(set(kinds)):
            raise ValueError("at most one requested selector per parent kind")
        object.__setattr__(
            self, "selectors", tuple(sorted(self.selectors, key=lambda s: s.kind.value))
        )
        _require_aware(self.business_valid_as_of, "business_valid_as_of")
        _require_aware(self.business_known_as_of, "business_known_as_of")

    def to_json(self) -> dict[str, object]:
        return {
            "knowledge_base_ids": (
                None
                if self.knowledge_base_ids is None
                else sorted(str(i) for i in self.knowledge_base_ids)
            ),
            "selectors": [s.to_json() for s in self.selectors],
            "business_valid_as_of": _iso(self.business_valid_as_of),
            "business_known_as_of": _iso(self.business_known_as_of),
        }


NO_FILTER = RequestedScope(None, (), None, None)


@dataclass(frozen=True, slots=True)
class ActionCeiling:
    """An exact tenant/KB/resource and finite action set; no wildcard resource."""

    scope: OwnedScope
    resource: ResourceKey
    actions: frozenset[Action]

    def __post_init__(self) -> None:
        actions = frozenset(Action(a) for a in self.actions)
        if not actions:
            raise ValueError("a delegation ceiling names at least one action")
        object.__setattr__(self, "actions", actions)

    def to_json(self) -> dict[str, object]:
        return {
            "scope": self.scope.to_json(),
            "resource": self.resource.to_json(),
            "actions": sorted(a.value for a in self.actions),
        }


@dataclass(frozen=True, slots=True)
class Delegation:
    """Server-owned expiring authority ceiling bound to one executor (S0005).

    Authority is the intersection of the ceiling and the acting principal's current
    grants. No onward delegation in v1."""

    id: UUID
    acting_principal_id: UUID
    executor_principal_id: UUID
    issued_by: UUID
    issued_at: datetime
    not_before: datetime
    expires_at: datetime
    revoked_at: datetime | None
    revision: int
    ceilings: tuple[ActionCeiling, ...]
    onward_delegation: Literal[False] = False

    def __post_init__(self) -> None:
        for name in ("issued_at", "not_before", "expires_at", "revoked_at"):
            _require_aware(getattr(self, name), name)
        if self.expires_at <= self.not_before:
            raise ValueError("expires_at must follow not_before")
        if self.revision < 1:
            raise ValueError("revision must be positive")
        if not self.ceilings:
            raise ValueError("a delegation needs at least one ceiling")
        if self.onward_delegation is not False:
            raise ValueError("onward delegation is not supported in v1")
        if self.acting_principal_id == self.executor_principal_id:
            raise ValueError("a principal cannot delegate to itself")
        object.__setattr__(
            self,
            "ceilings",
            tuple(sorted(self.ceilings, key=lambda c: (c.resource.type.value, str(c.resource.id)))),
        )

    def active_at(self, at: datetime) -> bool:
        if self.revoked_at is not None and self.revoked_at <= at:
            return False
        return self.not_before <= at < self.expires_at

    def permits(self, scope: OwnedScope, resource: ResourceKey, action: Action) -> bool:
        return any(
            c.scope == scope and c.resource == resource and action in c.actions
            for c in self.ceilings
        )

    def to_json(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "acting_principal_id": str(self.acting_principal_id),
            "executor_principal_id": str(self.executor_principal_id),
            "issued_by": str(self.issued_by),
            "issued_at": self.issued_at.isoformat(),
            "not_before": self.not_before.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "revoked_at": _iso(self.revoked_at),
            "revision": self.revision,
            "ceilings": [c.to_json() for c in self.ceilings],
            "onward_delegation": False,
        }


@dataclass(frozen=True, slots=True)
class PolicyRelease:
    """Immutable identity of the evaluated Casbin model + policy + contract version.

    `policy_sha256` is the legacy F0001 hash of policy.csv, kept on every decision
    for continuity with existing audit rows."""

    release_id: str
    release_sha256: str
    model_sha256: str
    policy_sha256: str
    contract_version: str


def principal_to_json(principal: Principal) -> dict[str, str]:
    return {
        "id": str(principal.id),
        "kind": principal.kind.value,
        "status": principal.status.value,
        "issuer": principal.issuer,
        "subject": principal.subject,
    }


@dataclass(frozen=True, slots=True)
class AuthorizationContext:
    """Trusted authority for one protected operation. Never a public DTO.

    Acting equals authenticated unless a verified delegation binds both: the
    authenticated principal is the executor and the acting principal is the one
    the delegation names (S0005 AC1/AC4)."""

    authenticated: Principal
    acting: Principal
    delegation: Delegation | None
    authorization_time: datetime
    authority_revision: int
    policy_release: PolicyRelease
    scope_slices: tuple[ScopeSlice, ...]
    requested_scope: RequestedScope
    trace_id: str
    schema_version: int = field(default=SCHEMA_VERSION)

    def __post_init__(self) -> None:
        _require_aware(self.authorization_time, "authorization_time")
        if self.authority_revision < 1:
            raise ValueError("authority_revision must be positive")
        if not self.trace_id:
            raise ValueError("trace_id is required")
        if self.delegation is None:
            if self.acting.id != self.authenticated.id:
                raise ValueError("acting differs from authenticated without a delegation")
        elif (
            self.delegation.executor_principal_id != self.authenticated.id
            or self.delegation.acting_principal_id != self.acting.id
        ):
            raise ValueError("delegation does not bind the authenticated and acting principals")
        object.__setattr__(
            self,
            "scope_slices",
            tuple(sorted(self.scope_slices, key=lambda s: str(s.membership_id))),
        )

    def to_json(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "authenticated": principal_to_json(self.authenticated),
            "acting": principal_to_json(self.acting),
            "delegation": self.delegation.to_json() if self.delegation else None,
            "authorization_time": self.authorization_time.isoformat(),
            "authority_revision": self.authority_revision,
            "policy_release": self.policy_release.release_id,
            "scope_slices": [s.to_json() for s in self.scope_slices],
            "requested_scope": self.requested_scope.to_json(),
            "trace_id": self.trace_id,
        }


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    """Schema `Decision`: the durable, non-secret record of one authorization.

    `grant_revision` is the principal-authority revision (never a fabricated 0).
    Allow requires a resolved scope, current policy, and at least one fully
    matching grant slice; permission allow is not a successful business effect —
    `operation_outcome` distinguishes attempted/succeeded/denied/failed."""

    decision_id: UUID
    occurred_at: datetime
    authenticated_principal_id: UUID
    actor_principal_id: UUID
    actor_kind: PrincipalKind
    executor_principal_id: UUID | None
    delegation_id: UUID | None
    delegation_revision: int | None
    scope: OwnedScope | None
    resource: ResourceKey
    resource_revision: int | None
    restriction_revision: int | None
    action: str
    allowed: bool
    reason_code: ReasonCode
    policy_hash: str
    policy_release: str
    grant_revision: int
    matched_membership_ids: tuple[UUID, ...]
    trace_id: str
    operation_outcome: OperationOutcome

    def __post_init__(self) -> None:
        _require_aware(self.occurred_at, "occurred_at")
        object.__setattr__(self, "reason_code", ReasonCode(self.reason_code))
        object.__setattr__(self, "operation_outcome", OperationOutcome(self.operation_outcome))
        object.__setattr__(
            self, "matched_membership_ids", tuple(sorted(set(self.matched_membership_ids), key=str))
        )
        if self.grant_revision < 1:
            raise ValueError("grant_revision must be positive")
        if self.allowed:
            if (
                self.reason_code != ReasonCode.ALLOWED
                or self.scope is None
                or self.resource_revision is None
                or self.restriction_revision is None
                or not self.matched_membership_ids
                or self.action not in {a.value for a in Action}
            ):
                raise ValueError("an allow needs a resolved scope and a matching grant")
        elif self.reason_code == ReasonCode.ALLOWED or self.operation_outcome not in {
            OperationOutcome.DENIED,
            OperationOutcome.FAILED,
        }:
            raise ValueError("a denial carries a denial reason and a denied/failed outcome")

    def with_outcome(self, outcome: OperationOutcome) -> AuthorizationDecision:
        """Terminal outcome of an allowed decision (succeeded, or failed on rollback)."""
        if not self.allowed:
            raise ValueError("only an allowed decision changes its operation outcome")
        return replace(self, operation_outcome=outcome)

    def to_json(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "decision_id": str(self.decision_id),
            "occurred_at": self.occurred_at.isoformat(),
            "authenticated_principal_id": str(self.authenticated_principal_id),
            "actor_principal_id": str(self.actor_principal_id),
            "actor_kind": self.actor_kind.value,
            "executor_principal_id": (
                str(self.executor_principal_id) if self.executor_principal_id else None
            ),
            "delegation_id": str(self.delegation_id) if self.delegation_id else None,
            "delegation_revision": self.delegation_revision,
            "scope": self.scope.to_json() if self.scope else None,
            "resource": self.resource.to_json(),
            "resource_revision": self.resource_revision,
            "restriction_revision": self.restriction_revision,
            "action": self.action,
            "allowed": self.allowed,
            "reason_code": self.reason_code.value,
            "policy_hash": self.policy_hash,
            "policy_release": self.policy_release,
            "grant_revision": self.grant_revision,
            "matched_membership_ids": [str(i) for i in self.matched_membership_ids],
            "trace_id": self.trace_id,
            "operation_outcome": self.operation_outcome.value,
        }


@dataclass(frozen=True, slots=True)
class AuthenticationEvent:
    """Schema `AuthenticationEvent`: a rejected credential. No principal is resolved
    (`principal_id` is always null) and no token or payload is carried."""

    event_id: UUID
    occurred_at: datetime
    reason_code: AuthenticationReason
    route_template: str
    trace_id: str

    def __post_init__(self) -> None:
        _require_aware(self.occurred_at, "occurred_at")
        object.__setattr__(self, "reason_code", AuthenticationReason(self.reason_code))
        if not self.route_template or not self.trace_id:
            raise ValueError("route_template and trace_id are required")

    def to_json(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
            "event_type": "credential_verification_failed",
            "principal_id": None,
            "reason_code": self.reason_code.value,
            "route_template": self.route_template,
            "trace_id": self.trace_id,
        }


def is_active(principal: Principal) -> bool:
    return principal.status == PrincipalStatus.ACTIVE
