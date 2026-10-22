"""Strict JSON decoding and validation against the product's authored contracts."""

from __future__ import annotations

import json
import math
from datetime import datetime
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any
from uuid import UUID

from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]


def wire_value(value: Any) -> Any:
    """Serialize Python-native identifiers without coercing input scalar types."""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: wire_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [wire_value(item) for item in value]
    return value


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON property")
        result[key] = value
    return result


def _invalid_number(value: str) -> None:
    raise ValueError("non-finite JSON number")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("non-finite JSON number")
    return number


def decode_json(raw: bytes | str) -> Any:
    return json.loads(
        raw,
        object_pairs_hook=_unique_object,
        parse_constant=_invalid_number,
        parse_float=_finite_float,
    )


@lru_cache(maxsize=8)
def schema(name: str) -> dict[str, Any]:
    allowed = {
        "content-artifact-manifest.schema.json",
        "content-artifact-manifest-v2.schema.json",
        "content-records-v2.schema.json",
        "document-date-record.schema.json",
        "interpretation-output-manifest.schema.json",
    }
    if name not in allowed:
        raise ValueError("unknown content contract")
    packaged = files("brain_content").joinpath("schemas", name)
    if packaged.is_file():
        return decode_json(packaged.read_bytes())
    for start in (Path(__file__).resolve().parent, Path.cwd()):
        for root in (start, *start.parents):
            path = root / "planning-mds" / "schemas" / name
            if path.is_file():
                return decode_json(path.read_bytes())
    raise RuntimeError("content contracts are missing from the application deployment")


def validate_contract(name: str, value: Any, definition: str | None = None) -> None:
    contract = schema(name)
    if definition is not None:
        contract = {"$ref": f"#/$defs/{definition}", "$defs": contract["$defs"]}
    validator = Draft202012Validator(contract, format_checker=FormatChecker())
    errors = list(validator.iter_errors(value))
    if errors:
        # Do not place protected values, quotes, paths or schema reprs in errors.
        raise ValueError("CONTENT_CONTRACT_INVALID")
