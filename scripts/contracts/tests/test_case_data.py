"""Malformed recipe metadata must fail the inventory, even for negative cases."""

import pytest

from scripts.contracts.case_data import raw_for_case


def test_raw_recipe_is_exact_and_bounded():
    case = {
        "kind": "raw-json",
        "raw_repeat": {"prefix": '"', "character": "x", "count": 3, "suffix": '"'},
    }
    assert raw_for_case(case) == '"xxx"'
    assert raw_for_case({"kind": "raw-json", "raw": "null"}) == "null"
    for change in (
        {"count": -1},
        {"count": True},
        {"count": 16777218},
        {"character": "xx"},
        {"extra": 1},
    ):
        invalid = {**case, "raw_repeat": {**case["raw_repeat"], **change}}
        with pytest.raises(ValueError):
            raw_for_case(invalid)
    for invalid in (
        {**case, "raw": "null"},
        {"kind": "instance"},
        {"kind": "raw-json"},
    ):
        with pytest.raises(ValueError):
            raw_for_case(invalid)
