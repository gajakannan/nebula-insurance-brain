"""Physical recipe identity, independent of the extraction profile."""

from __future__ import annotations

import hashlib
import json
from importlib.metadata import version
from typing import Literal

from brain_ingestion.content_projection import PROJECTION_VERSION


def physical_recipe(contract_version: Literal[1, 2]) -> str:
    values: dict[str, object]
    if contract_version == 1:
        # Preserve the exact existing recipe serialization and legacy identities.
        values = {"adapter": "docling-default-pdf-v1", "docling": version("docling")}
    else:
        values = {
            "adapter": "docling-item-provenance-pdf-v2",
            "projection": PROJECTION_VERSION,
            "packages": {
                name: version(name)
                for name in ("docling", "docling-core", "docling-parse", "rapidocr", "pypdf")
            },
        }
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()
