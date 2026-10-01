"""F0002 schema/implementation equivalence for the AuthX kernel v1 carriers.

Two directions: (1) carriers the implementation produces serialize to payloads the
schema accepts; (2) the authored contract examples round-trip through the domain
types, and every authored *invalid* shape is also refused by the domain types (so a
malformed carrier cannot be constructed in-process either). Structural validity
confers no authority — trust is established only by the repositories.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from brain_domain.authx import (
    ActionCeiling,
    AuthenticationEvent,
    AuthorizationContext,
    AuthorizationDecision,
    Delegation,
    OperationOutcome,
    PolicyRelease,
    ReasonCode,
    RequestedScope,
    ResourceKey,
    ResourceType,
    ScopeSlice,
    Selector,
    unrestricted_selectors,
)
from brain_domain.principal import Principal, PrincipalKind, PrincipalStatus
from brain_domain.tenancy import OwnedScope, OwnershipConflict, TenancyIdentity
from jsonschema import Draft202012Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA = json.loads((REPO_ROOT / "planning-mds/schemas/authx-kernel.schema.json").read_text())
EXAMPLES = json.loads(
    (
        REPO_ROOT
        / "planning-mds/features/archive/F0002-tenancy-aware-domain-kernel-and-principal-contracts"
        / "contract-examples.json"
    ).read_text()
)
NOW = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)


def validator(definition: str) -> Draft202012Validator:
    return Draft202012Validator(
        {"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": f"#/$defs/{definition}"},
        format_checker=FormatChecker(),
    )


def assert_valid(definition: str, payload: dict[str, Any]) -> None:
    errors = [e.message for e in validator(definition).iter_errors(payload)]
    assert not errors, errors


# --- JSON -> domain (the only parse path is for contract proof; production never
# --- deserializes an AuthorizationContext from a client or model) ------------------


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def _scope(data: dict[str, str]) -> OwnedScope:
    return OwnedScope(
        UUID(data["tenant_id"]), UUID(data["workspace_id"]), UUID(data["knowledge_base_id"])
    )


def _principal(data: dict[str, str]) -> Principal:
    return Principal(
        UUID(data["id"]),
        PrincipalKind(data["kind"]),
        data["issuer"],
        data["subject"],
        PrincipalStatus(data["status"]),
    )


def _selector(data: dict[str, Any]) -> Selector:
    return Selector(data["kind"], data["mode"], frozenset(UUID(i) for i in data["ids"]))


def _labels(value: Any) -> Any:
    return value if value == "*" else frozenset(value)


def parse_slice(data: dict[str, Any]) -> ScopeSlice:
    return ScopeSlice(
        membership_id=UUID(data["membership_id"]),
        scope=_scope(data["scope"]),
        role=data["role"],
        valid_from=_dt(data["valid_from"]),  # type: ignore[arg-type]
        expires_at=_dt(data["expires_at"]),
        revoked_at=_dt(data["revoked_at"]),
        grant_revision=data["grant_revision"],
        selectors=tuple(_selector(s) for s in data["selectors"]),
        classifications=_labels(data["classifications"]),
        source_acl_ids=_labels(data["source_acl_ids"]),
    )


def parse_delegation(data: dict[str, Any]) -> Delegation:
    return Delegation(
        id=UUID(data["id"]),
        acting_principal_id=UUID(data["acting_principal_id"]),
        executor_principal_id=UUID(data["executor_principal_id"]),
        issued_by=UUID(data["issued_by"]),
        issued_at=_dt(data["issued_at"]),  # type: ignore[arg-type]
        not_before=_dt(data["not_before"]),  # type: ignore[arg-type]
        expires_at=_dt(data["expires_at"]),  # type: ignore[arg-type]
        revoked_at=_dt(data["revoked_at"]),
        revision=data["revision"],
        ceilings=tuple(
            ActionCeiling(
                _scope(c["scope"]),
                ResourceKey(c["resource"]["type"], UUID(c["resource"]["id"])),
                frozenset(c["actions"]),
            )
            for c in data["ceilings"]
        ),
        onward_delegation=data["onward_delegation"],
    )


def parse_context(data: dict[str, Any]) -> AuthorizationContext:
    requested = data["requested_scope"]
    kb_ids = requested["knowledge_base_ids"]
    return AuthorizationContext(
        authenticated=_principal(data["authenticated"]),
        acting=_principal(data["acting"]),
        delegation=parse_delegation(data["delegation"]) if data["delegation"] else None,
        authorization_time=_dt(data["authorization_time"]),  # type: ignore[arg-type]
        authority_revision=data["authority_revision"],
        policy_release=PolicyRelease(data["policy_release"], "0" * 64, "0" * 64, "0" * 64, "v1"),
        scope_slices=tuple(parse_slice(s) for s in data["scope_slices"]),
        requested_scope=RequestedScope(
            None if kb_ids is None else frozenset(UUID(k) for k in kb_ids),
            tuple(_selector(s) for s in requested["selectors"]),
            _dt(requested["business_valid_as_of"]),
            _dt(requested["business_known_as_of"]),
        ),
        trace_id=data["trace_id"],
    )


def parse_decision(data: dict[str, Any]) -> AuthorizationDecision:
    return AuthorizationDecision(
        decision_id=UUID(data["decision_id"]),
        occurred_at=_dt(data["occurred_at"]),  # type: ignore[arg-type]
        authenticated_principal_id=UUID(data["authenticated_principal_id"]),
        actor_principal_id=UUID(data["actor_principal_id"]),
        actor_kind=PrincipalKind(data["actor_kind"]),
        executor_principal_id=UUID(data["executor_principal_id"])
        if data["executor_principal_id"]
        else None,
        delegation_id=UUID(data["delegation_id"]) if data["delegation_id"] else None,
        delegation_revision=data["delegation_revision"],
        scope=_scope(data["scope"]) if data["scope"] else None,
        resource=ResourceKey(data["resource"]["type"], UUID(data["resource"]["id"])),
        resource_revision=data["resource_revision"],
        restriction_revision=data["restriction_revision"],
        action=data["action"],
        allowed=data["allowed"],
        reason_code=data["reason_code"],
        policy_hash=data["policy_hash"],
        policy_release=data["policy_release"],
        grant_revision=data["grant_revision"],
        matched_membership_ids=tuple(UUID(i) for i in data["matched_membership_ids"]),
        trace_id=data["trace_id"],
        operation_outcome=data["operation_outcome"],
    )


def parse_identity(data: dict[str, Any]) -> TenancyIdentity:
    return TenancyIdentity(
        tenant_id=UUID(data["tenant_id"]),
        entity_id=UUID(data["entity_id"]),
        kb_scopes=tuple(_scope(s) for s in data["kb_scopes"]),
        created_at=_dt(data["created_at"]),  # type: ignore[arg-type]
        created_by=UUID(data["created_by"]),
    )


def parse_authentication(data: dict[str, Any]) -> AuthenticationEvent:
    if data["principal_id"] is not None or data["event_type"] != "credential_verification_failed":
        raise ValueError("an authentication event never resolves a principal")
    return AuthenticationEvent(
        event_id=UUID(data["event_id"]),
        occurred_at=_dt(data["occurred_at"]),  # type: ignore[arg-type]
        reason_code=data["reason_code"],
        route_template=data["route_template"],
        trace_id=data["trace_id"],
    )


PARSERS = {
    "AuthorizationContext": parse_context,
    "Delegation": parse_delegation,
    "Decision": parse_decision,
    "TenancyIdentity": parse_identity,
    "AuthenticationEvent": parse_authentication,
}


def _normalize(payload: Any) -> Any:
    """Canonical comparison: collection order carries no authorization meaning."""
    if isinstance(payload, dict):
        return {k: _normalize(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return sorted((_normalize(v) for v in payload), key=json.dumps)
    if isinstance(payload, str) and payload.endswith("Z") and "T" in payload:
        return _dt(payload).isoformat()  # type: ignore[union-attr]
    return payload


def _parse_or_reject(definition: str, payload: dict[str, Any]) -> Any:
    unknown = set(payload) - set(SCHEMA["$defs"][definition]["properties"])
    if unknown:
        raise ValueError(f"closed carrier rejects {sorted(unknown)}")
    return PARSERS[definition](payload)


def test_schema_itself_is_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize("case", EXAMPLES["cases"], ids=lambda c: c["id"])
def test_authored_examples_match_schema_and_implementation(case: dict[str, Any]) -> None:
    definition, payload = case["schema_definition"], case["payload"]
    schema_ok = not list(validator(definition).iter_errors(payload))
    assert schema_ok == case["expected_schema_valid"]
    if case["expected_schema_valid"]:
        carrier = _parse_or_reject(definition, payload)
        assert _normalize(carrier.to_json()) == _normalize(payload)
    else:
        with pytest.raises((ValueError, KeyError, TypeError, OwnershipConflict)):
            _parse_or_reject(definition, payload)


def _principal_fixture(kind: PrincipalKind = PrincipalKind.USER) -> Principal:
    return Principal(uuid4(), kind, "https://issuer", uuid4().hex, PrincipalStatus.ACTIVE)


def test_produced_carriers_validate_against_the_schema() -> None:
    owned = OwnedScope(uuid4(), uuid4(), uuid4())
    user, agent = _principal_fixture(), _principal_fixture(PrincipalKind.AGENT)
    resource = ResourceKey(ResourceType.CONTENT_ARTIFACT, uuid4())
    delegation = Delegation(
        id=uuid4(),
        acting_principal_id=user.id,
        executor_principal_id=agent.id,
        issued_by=uuid4(),
        issued_at=NOW,
        not_before=NOW,
        expires_at=NOW + timedelta(hours=1),
        revoked_at=None,
        revision=1,
        ceilings=(ActionCeiling(owned, resource, frozenset({"read"})),),
    )
    slice_ = ScopeSlice(
        membership_id=uuid4(),
        scope=owned,
        role="TenantMember",
        valid_from=NOW,
        expires_at=None,
        revoked_at=None,
        grant_revision=2,
        selectors=unrestricted_selectors(),
        classifications=frozenset({"internal"}),
        source_acl_ids="*",
    )
    release = PolicyRelease("sha256:" + "a" * 64, "a" * 64, "b" * 64, "c" * 64, "authx-kernel:v1")
    context = AuthorizationContext(
        authenticated=agent,
        acting=user,
        delegation=delegation,
        authorization_time=NOW,
        authority_revision=3,
        policy_release=release,
        scope_slices=(slice_,),
        requested_scope=RequestedScope(frozenset({owned.knowledge_base_id}), (), NOW, None),
        trace_id="trace",
    )
    assert_valid("AuthorizationContext", context.to_json())
    assert_valid("Delegation", delegation.to_json())
    common = dict(
        decision_id=uuid4(),
        occurred_at=NOW,
        authenticated_principal_id=agent.id,
        actor_principal_id=user.id,
        actor_kind=PrincipalKind.USER,
        executor_principal_id=agent.id,
        delegation_id=delegation.id,
        delegation_revision=1,
        resource=resource,
        action="read",
        policy_hash="c" * 64,
        policy_release=release.release_id,
        grant_revision=3,
        trace_id="t",
    )
    allowed = AuthorizationDecision(
        **common,
        scope=owned,
        resource_revision=1,
        restriction_revision=1,
        allowed=True,
        reason_code=ReasonCode.ALLOWED,
        matched_membership_ids=(slice_.membership_id,),
        operation_outcome=OperationOutcome.SUCCEEDED,
    )
    denied = AuthorizationDecision(
        **common,
        scope=None,
        resource_revision=None,
        restriction_revision=None,
        allowed=False,
        reason_code=ReasonCode.MISSING_ATTRIBUTES,
        matched_membership_ids=(),
        operation_outcome=OperationOutcome.DENIED,
    )
    for decision in (allowed, denied, allowed.with_outcome(OperationOutcome.FAILED)):
        assert_valid("Decision", decision.to_json())
    identity = TenancyIdentity(owned.tenant_id, uuid4(), (owned,), NOW, uuid4())
    assert_valid("TenancyIdentity", identity.to_json())
    event = AuthenticationEvent(uuid4(), NOW, "expired", "/content/{artifact_id}", "t")
    assert_valid("AuthenticationEvent", event.to_json())


def test_domain_refuses_semantically_invalid_carriers() -> None:
    owned = OwnedScope(uuid4(), uuid4(), uuid4())
    user = _principal_fixture()
    with pytest.raises(OwnershipConflict):  # an association cannot cross tenants
        TenancyIdentity(uuid4(), uuid4(), (owned,), NOW, uuid4())
    with pytest.raises(ValueError):  # acting differs from authenticated, no delegation
        AuthorizationContext(
            authenticated=user,
            acting=_principal_fixture(),
            delegation=None,
            authorization_time=NOW,
            authority_revision=1,
            policy_release=PolicyRelease("r", "0" * 64, "0" * 64, "0" * 64, "v1"),
            scope_slices=(),
            requested_scope=RequestedScope(None, (), None, None),
            trace_id="t",
        )
    with pytest.raises(ValueError):  # naive datetimes are never accepted
        AuthenticationEvent(uuid4(), datetime(2026, 1, 1), "expired", "/x", "t")  # noqa: DTZ001
    with pytest.raises(ValueError):  # a grant slice needs one selector per parent kind
        ScopeSlice(
            membership_id=uuid4(),
            scope=owned,
            role="TenantMember",
            valid_from=NOW,
            expires_at=None,
            revoked_at=None,
            grant_revision=1,
            selectors=(),
            classifications="*",
            source_acl_ids="*",
        )
    with pytest.raises(ValueError):  # unapproved pilot role
        ScopeSlice(
            membership_id=uuid4(),
            scope=owned,
            role="Administrator",
            valid_from=NOW,
            expires_at=None,
            revoked_at=None,
            grant_revision=1,
            selectors=unrestricted_selectors(),
            classifications="*",
            source_acl_ids="*",
        )
