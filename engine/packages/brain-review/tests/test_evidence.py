from __future__ import annotations

from uuid import uuid4

from brain_review.evidence import evidence_binding_to_locator


def test_span_precision_maps_to_exact_span_with_box_selector() -> None:
    artifact_id = uuid4()

    locator = evidence_binding_to_locator(
        artifact_id=artifact_id,
        precision="span",
        block_id="text-2",
        page=1,
        bbox={"x0": 1.0, "y0": 2.0, "x1": 3.0, "y1": 4.0},
        char_start=10,
        char_end=20,
    )

    assert locator.source == str(artifact_id)
    assert locator.precision == "exact-span"
    assert locator.part == "text-2"
    assert len(locator.selector) == 1
    assert locator.selector[0]["type"] == "nebula:BoxSelector"
    assert locator.selector[0]["page"] == 1
    assert locator.selector[0]["char_start"] == 10


def test_table_cell_maps_to_hyphenated_table_cell() -> None:
    locator = evidence_binding_to_locator(artifact_id=uuid4(), precision="table_cell", page=1)

    assert locator.precision == "table-cell"


def test_unresolved_precision_carries_no_selector() -> None:
    locator = evidence_binding_to_locator(
        artifact_id=uuid4(), precision="unresolved", unresolved_reason="no text layer"
    )

    assert locator.precision == "unresolved"
    assert locator.selector == ()
    assert locator.unresolved_reason == "no text layer"


def test_page_precision_without_bbox_still_carries_a_selector() -> None:
    locator = evidence_binding_to_locator(artifact_id=uuid4(), precision="page", page=3)

    assert locator.precision == "page"
    assert locator.selector[0]["page"] == 3
    assert "x0" not in locator.selector[0]


def test_combined_regions_preserve_every_selector() -> None:
    from brain_review.evidence import combine_evidence_locators

    artifact = uuid4()
    locators = [
        evidence_binding_to_locator(
            artifact_id=artifact,
            precision="span",
            block_id="text-0",
            page=page,
            char_start=start,
            char_end=end,
        )
        for page, start, end in [(1, 10, 14), (2, 14, 20)]
    ]
    result = combine_evidence_locators(locators)
    assert result.precision == "exact-span" and result.part == "text-0"
    assert [s["page"] for s in result.selector] == [1, 2]
    assert [(s["char_start"], s["char_end"]) for s in result.selector] == [(10, 14), (14, 20)]


def test_combined_mixed_or_unresolved_evidence_never_claims_precision() -> None:
    from brain_review.evidence import combine_evidence_locators

    artifact = uuid4()
    span = evidence_binding_to_locator(
        artifact_id=artifact, precision="span", block_id="text-0", page=1
    )
    for other in [
        evidence_binding_to_locator(artifact_id=artifact, precision="unresolved"),
        evidence_binding_to_locator(
            artifact_id=artifact, precision="span", block_id="text-1", page=1
        ),
        evidence_binding_to_locator(artifact_id=artifact, precision="page", page=1),
    ]:
        result = combine_evidence_locators([span, other])
        assert result.precision == "unresolved" and result.selector == ()
    import pytest

    with pytest.raises(ValueError, match="different artifacts"):
        combine_evidence_locators(
            [span, evidence_binding_to_locator(artifact_id=uuid4(), precision="page", page=1)]
        )
    with pytest.raises(ValueError, match="at least one"):
        combine_evidence_locators([])
