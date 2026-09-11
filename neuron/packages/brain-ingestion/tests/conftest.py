from __future__ import annotations

from pathlib import Path

import pytest

NEURON_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def native_gl_pdf() -> Path:
    return NEURON_ROOT / "fixtures" / "gl-policy-declarations.pdf"


@pytest.fixture(scope="session")
def scanned_gl_pdf() -> Path:
    return NEURON_ROOT / "fixtures" / "gl-policy-declarations-scanned.pdf"
