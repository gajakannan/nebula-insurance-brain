from __future__ import annotations

import pytest
from brain_assertions.normalization import (
    locate_quote,
    match_positions,
    normalize,
    normalize_name,
    normalize_with_mapping,
)


@pytest.mark.parametrize(
    ("source", "quote"),
    [
        ("Café", "Cafe\u0301"),
        ("Straße", "STRASSE"),
        ("Cedar\t Roofing\nCo.", "cedar roofing co."),
        ("a $ 500,000 limit", "A $500,000 LIMIT"),
        ("indemni-\nfication", "indemnification"),
        ("indemni\u2010\r\nfication", "indemnification"),
        ("\u1100\u1161", "가"),
    ],
)
def test_normalization_matches_without_changing_originals(source, quote):
    normalized = normalize_with_mapping(source)
    assert normalized.text == normalize(quote)
    assert len(normalized.text) == len(normalized.ranges)
    location = locate_quote(source, quote, {"block_id": "b", "native_ref": "#/paragraphs/1"})
    assert location.precision == "span"
    assert location.selector["char_start"] == 0
    assert location.selector["char_end"] == len(source)


@pytest.mark.parametrize(
    ("source", "quote"),
    [
        ("$500,000", "$5,000,000"),
        ("500.00", "50000"),
        ("USD 5", "EUR 5"),
        ("part-\n2", "part2"),
        ("pre-existing", "preexisting"),
    ],
)
def test_normalization_preserves_numbers_symbols_and_non_line_hyphens(source, quote):
    assert locate_quote(source, quote, {"block_id": "b"}) is None


def test_original_ranges_are_not_model_offsets():
    source = "Limit: $ \t500,000 only"
    location = locate_quote(
        source, "$500,000", {"block_id": "b", "native_ref": "p:2", "char_start": 20}
    )
    assert location.precision == "span"
    assert location.selector["char_start"] == 27
    assert location.selector["char_end"] == 37


def test_repetition_and_multiregion_never_fabricate_unique_span():
    location = locate_quote(
        "$5 then $5", "$5", {"block_id": "b", "native_ref": "pdf:1", "char_start": 4, "char_end": 9}
    )
    assert location.precision == "block"
    assert "char_start" not in location.selector
    regions = [{"page": 1, "bbox": {"x0": 1}}, {"page": 2, "bbox": {"x0": 2}}]
    location = locate_quote(
        "continued claim", "continued claim", {"native_ref": "pdf:1", "regions": regions}
    )
    assert location.precision == "block"
    assert location.selector["regions"] == regions
    assert "bbox" not in location.selector


def test_verified_cell_identity_survives_equal_text_without_guessing_cells():
    for selector in (
        {"cell_id": "c7", "sheet": "GL", "row": 4, "column": 2},
        {"cell_id": "r3c2", "row": 3, "column": 2, "kind": "csv"},
    ):
        location = locate_quote("5 5", "5", selector)
        assert location.precision == "table_cell"
        assert location.selector == selector


def test_partial_casefold_and_combining_clusters_coarsen_honestly():
    assert locate_quote("ß", "s", {"block_id": "b"}).precision == "block"
    source = "a\u0315\u0300"
    assert locate_quote(source, "à", {"block_id": "b"}).precision == "block"
    assert normalize_name("  CAFÉ\t LTD  ") == "café ltd"
    assert normalize_name("A-\nB") == "a- b"


@pytest.mark.parametrize(
    ("selector", "precision"),
    [
        ({"page": 2, "precision": "page"}, "page"),
        ({"document_version_id": "v", "precision": "document"}, "document"),
        ({"kind": "unresolved", "reason": "no-coordinate"}, "unresolved"),
        ({}, "unresolved"),
    ],
)
def test_coarse_and_unresolved_locations_stay_honest(selector, precision):
    assert locate_quote("claim", "claim", selector).precision == precision
    assert match_positions("aaaa", "aa") == ((0, 2), (1, 3), (2, 4))
    assert match_positions("claim", "") == ()
