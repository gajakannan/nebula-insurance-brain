from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _find_upward(start: Path, relative: str) -> str:
    for candidate_dir in (start, *start.parents):
        candidate = candidate_dir / relative
        if candidate.is_file():
            return str(candidate)
    raise FileNotFoundError(f"{relative} not found by walking up from {start}")


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    oidc_issuer: str
    oidc_audience: str
    casbin_model_path: str
    casbin_policy_path: str

    @classmethod
    def from_env(cls) -> Settings:
        repo_search_root = Path.cwd()
        model_path = os.environ.get("BRAIN_CASBIN_MODEL_PATH") or _find_upward(
            repo_search_root, "planning-mds/security/policies/model.conf"
        )
        policy_path = os.environ.get("BRAIN_CASBIN_POLICY_PATH") or _find_upward(
            repo_search_root, "planning-mds/security/policies/policy.csv"
        )
        return cls(
            database_url=os.environ.get(
                "BRAIN_DATABASE_URL", "postgresql+asyncpg://brain:brain@localhost:5432/brain"
            ),
            oidc_issuer=os.environ.get(
                "BRAIN_OIDC_ISSUER", "http://localhost:9010/application/o/brain/"
            ),
            oidc_audience=os.environ.get("BRAIN_OIDC_AUDIENCE", "brain"),
            casbin_model_path=model_path,
            casbin_policy_path=policy_path,
        )
