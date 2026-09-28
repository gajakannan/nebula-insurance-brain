from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import casbin
from brain_domain.authx import CONTRACT_VERSION, PolicyRelease, ResourceKey
from brain_domain.tenancy import OwnedScope


@dataclass
class _Sub:
    role: str
    knowledge_base_id: str


@dataclass
class _Obj:
    type: str
    knowledge_base_id: str


def _length_prefixed(*parts: bytes) -> bytes:
    """Unambiguous concatenation: 8-byte big-endian length before every part."""
    return b"".join(len(part).to_bytes(8, "big") + part for part in parts)


def compute_policy_release(
    model_bytes: bytes, policy_bytes: bytes, contract_version: str = CONTRACT_VERSION
) -> PolicyRelease:
    """Immutable release identity over exact model bytes, policy bytes and the
    kernel-contract version (assembly plan: "Policy release")."""
    release_sha256 = hashlib.sha256(
        _length_prefixed(model_bytes, policy_bytes, contract_version.encode("utf-8"))
    ).hexdigest()
    return PolicyRelease(
        release_id=f"sha256:{release_sha256}",
        release_sha256=release_sha256,
        model_sha256=hashlib.sha256(model_bytes).hexdigest(),
        policy_sha256=hashlib.sha256(policy_bytes).hexdigest(),
        contract_version=contract_version,
    )


class CasbinAuthorizationAdapter:
    """Loads `planning-mds/security/policies/{model.conf,policy.csv}` and evaluates
    the ABAC matcher `r.sub.role == p.sub && r.obj.type == p.obj && r.act == p.act &&
    eval(p.cond)`. The pilot rows are unchanged by F0002; every other restriction
    (parent, classification, source, dependency, delegation) is a typed conjunct in
    `brain_security.evaluation`, never a Casbin expression.

    `policy_hash` = sha256 of the loaded `policy.csv` bytes (the F0001 audit field);
    `release` = the immutable model+policy+contract identity recorded on every
    F0002 decision."""

    def __init__(self, model_path: str | Path, policy_path: str | Path) -> None:
        model_path, policy_path = Path(model_path), Path(policy_path)
        model_bytes, policy_bytes = model_path.read_bytes(), policy_path.read_bytes()
        self._enforcer = casbin.Enforcer(str(model_path), str(policy_path))
        self._release = compute_policy_release(model_bytes, policy_bytes)

    def enforce(
        self,
        role: str,
        sub_knowledge_base_id: str,
        resource_type: str,
        obj_knowledge_base_id: str,
        action: str,
    ) -> bool:
        sub = _Sub(role=role, knowledge_base_id=sub_knowledge_base_id)
        obj = _Obj(type=resource_type, knowledge_base_id=obj_knowledge_base_id)
        return bool(self._enforcer.enforce(sub, obj, action))

    def permits(
        self,
        role: str,
        grant_scope: OwnedScope,
        resource_scope: OwnedScope,
        resource: ResourceKey,
        action: str,
    ) -> bool:
        """`brain_security.evaluation.PolicyEvaluator`. The grant's KB is the subject
        and the resource's KB the object, so the policy condition still compares two
        independently sourced values rather than a value with itself."""
        return self.enforce(
            role,
            str(grant_scope.knowledge_base_id),
            resource.type.value,
            str(resource_scope.knowledge_base_id),
            action,
        )

    @property
    def policy_hash(self) -> str:
        return self._release.policy_sha256

    @property
    def release(self) -> PolicyRelease:
        return self._release
