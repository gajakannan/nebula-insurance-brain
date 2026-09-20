"""Conservative value grounding through Graph's native-item reference ledger.

Node identity anchors and chunk-relative offsets are never property selectors.
Each property is independently located in immutable Docling items. Repeated or
normalized values without a unique verbatim location remain unresolved.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from brain_interpretation.result import BoundingBox, EvidenceBinding
from docling_core.types.doc import DoclingDocument
from docling_core.types.doc.base import CoordOrigin


def ground_value(
    document: DoclingDocument, ledger: dict[str, Any] | None, artifact_id: UUID, value: Any
) -> list[EvidenceBinding]:
    unresolved = [EvidenceBinding(artifact_id=artifact_id, precision="unresolved")]
    if not isinstance(value, str) or not value.strip() or not ledger or ledger.get("version") != 2:
        return unresolved
    refs = {
        ref for chunk in ledger.get("chunks", {}).values() for ref in chunk.get("doc_item_refs", [])
    }
    hits: list[list[EvidenceBinding]] = []
    for index, item in enumerate(document.texts):
        if item.self_ref not in refs:
            continue
        start = item.text.find(value)
        while start >= 0:
            end = start + len(value)
            bindings = []
            for prov in item.prov:
                if not prov.charspan[0] <= start < end <= prov.charspan[1]:
                    continue
                page = document.pages.get(prov.page_no)
                if page is None:
                    continue
                box = prov.bbox.to_top_left_origin(page.size.height)
                bindings.append(
                    EvidenceBinding(
                        artifact_id=artifact_id,
                        block_id=f"text-{index}",
                        page=prov.page_no,
                        bbox=BoundingBox(page=prov.page_no, x0=box.l, y0=box.t, x1=box.r, y1=box.b),
                        char_start=start,
                        char_end=end,
                        precision="span",
                    )
                )
            # An unlocatable second occurrence still makes the value ambiguous.
            hits.append(bindings)
            start = item.text.find(value, start + 1)
    for index, table in enumerate(document.tables):
        if table.self_ref not in refs:
            continue
        for cell in table.data.table_cells:
            if cell.text != value:
                continue
            # An unlocated cell still counts as an occurrence; ambiguity must not
            # disappear just because one matching cell lacks usable geometry.
            bindings = []
            if len(table.prov) == 1 and cell.bbox is not None:
                prov = table.prov[0]
                page = document.pages.get(prov.page_no)
                if page is not None:
                    box = cell.bbox.to_top_left_origin(page.size.height)
                    if box.coord_origin == CoordOrigin.TOPLEFT:
                        bindings.append(
                            EvidenceBinding(
                                artifact_id=artifact_id,
                                block_id=f"table-{index}",
                                page=prov.page_no,
                                bbox=BoundingBox(
                                    page=prov.page_no, x0=box.l, y0=box.t, x1=box.r, y1=box.b
                                ),
                                precision="table_cell",
                            )
                        )
            hits.append(bindings)
    return hits[0] if len(hits) == 1 and hits[0] else unresolved
