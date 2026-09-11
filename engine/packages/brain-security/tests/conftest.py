from __future__ import annotations

from pathlib import Path

import pytest

# repo root: tests -> brain-security -> packages -> engine -> nebula-insurance-brain
REPO_ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture
def model_path() -> Path:
    return REPO_ROOT / "planning-mds" / "security" / "policies" / "model.conf"


@pytest.fixture
def policy_path() -> Path:
    return REPO_ROOT / "planning-mds" / "security" / "policies" / "policy.csv"
