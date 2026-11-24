"""Materialize bounded synthetic raw JSON recipes for the shared case inventory."""

from __future__ import annotations

from typing import Any


def raw_for_case(case: dict[str, Any]) -> str:
    if case.get("kind") != "raw-json":
        raise ValueError("Raw fixture requested for a non-raw case")
    if ("raw" in case) == ("raw_repeat" in case):
        raise ValueError("Raw case requires exactly one raw representation")
    if "raw" in case:
        if not isinstance(case["raw"], str):
            raise ValueError("Raw fixture must be a string")
        return case["raw"]
    recipe = case["raw_repeat"]
    if (
        not isinstance(recipe, dict)
        or set(recipe) != {"prefix", "character", "count", "suffix"}
        or not isinstance(recipe["prefix"], str)
        or not isinstance(recipe["suffix"], str)
        or recipe["character"] not in ("x", "[", "]", "{", "}")
        or type(recipe["count"]) is not int
        or not 0 <= recipe["count"] <= 16_777_217
    ):
        raise ValueError("Malformed bounded raw fixture recipe")
    return recipe["prefix"] + recipe["character"] * recipe["count"] + recipe["suffix"]
