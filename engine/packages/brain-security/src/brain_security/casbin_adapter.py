from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import casbin


@dataclass
class _Sub:
    role: str
    knowledge_base_id: str


@dataclass
class _Obj:
    type: str
    knowledge_base_id: str


class CasbinAuthorizationAdapter:
    """Loads `planning-mds/security/policies/{model.conf,policy.csv}` and evaluates
    the ABAC matcher `r.sub.role == p.sub && r.obj.type == p.obj && r.act == p.act &&
    eval(p.cond)`. `policy_hash` = sha256 of the loaded `policy.csv` bytes, recorded
    on every decision."""

    def __init__(self, model_path: str | Path, policy_path: str | Path) -> None:
        policy_path = Path(policy_path)
        self._enforcer = casbin.Enforcer(str(model_path), str(policy_path))
        self._policy_hash = hashlib.sha256(policy_path.read_bytes()).hexdigest()

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

    @property
    def policy_hash(self) -> str:
        return self._policy_hash
