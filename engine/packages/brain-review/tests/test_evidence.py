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
