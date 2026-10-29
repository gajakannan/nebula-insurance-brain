"""Shared opt-in live qualification support for F0005 (not collected as tests).

Every live suite requires BRAIN_RUN_LIVE_QUALIFICATION=1, the dedicated Brain
vLLM server recorded in the host guard, its credential through the local secret
mechanism, and BRAIN_TEST_POSTGRES_URL for isolated schemas.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "neuron/fixtures/qualification"


def _load(name: str, path: Path) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


qualification = _load("f0005_qualification", ROOT / "neuron/benchmarks/f0005_qualification.py")
fault_proxy = _load("f0005_fault_proxy", ROOT / "neuron/tests/support/fault_proxy.py")


def require_live() -> tuple[str, object]:
    if os.environ.get("BRAIN_RUN_LIVE_QUALIFICATION") != "1":
        pytest.skip("set BRAIN_RUN_LIVE_QUALIFICATION=1 for live F0005 qualification")
    url = os.environ.get("BRAIN_TEST_POSTGRES_URL")
    if not url or "BRAIN_INFERENCE_API_KEY" not in os.environ:
        pytest.fail("live qualification requires BRAIN_TEST_POSTGRES_URL and the Brain credential")
    return url, qualification.LiveSettings.from_environment()


def corpus_documents() -> list[dict]:
    import yaml

    return yaml.safe_load((CORPUS / "corpus.yaml").read_text())["documents"]


def upstream(settings: object) -> str:
    return settings.provider_url.rsplit("/v1", 1)[0]  # type: ignore[attr-defined]
