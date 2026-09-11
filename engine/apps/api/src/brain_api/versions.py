from __future__ import annotations

from importlib.metadata import version

# Dependency-matrix pins (docker/DEPENDENCY-MATRIX.md, authored at F0001-S0002) are the
# single source of truth for cross-workspace pins. sqlalchemy is a real dependency of this
# app, so its version is introspected live. docling belongs to neuron/ (Docling is an AI
# runtime dependency per SOLUTION-PATTERNS.md's Clean Architecture Pattern) and is not
# installed here; its pin is declared below and must equal neuron/uv.lock's resolved
# version once S0002 lands the matrix.
DOCLING_PINNED_VERSION = "2.126.0"


def collect_versions() -> dict[str, str]:
    """Return the pinned/introspected versions reported by GET /health."""
    return {
        "fastapi": version("fastapi"),
        "sqlalchemy": version("sqlalchemy"),
        "docling": DOCLING_PINNED_VERSION,
    }
