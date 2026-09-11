from __future__ import annotations

from typing import Literal
from uuid import UUID

from brain_domain.review import EvidenceLocator, EvidenceLocatorPrecision

# F0001-S0003's interpretation-time precision vocabulary (span/table_cell/block/page/
# document/unresolved — section 108.2) maps onto ADR-0058's review-time vocabulary
# (exact-span/table-cell/block/page/document/unresolved) one-to-one but under different
# spellings; see brain_domain.review's module docstring for why the two are not unified.
InterpretationPrecision = Literal["span", "table_cell", "block", "page", "document", "unresolved"]

_PRECISION_MAP: dict[InterpretationPrecision, EvidenceLocatorPrecision] = {
    "span": "exact-span",
    "table_cell": "table-cell",
    "block": "block",
    "page": "page",
    "document": "document",
    "unresolved": "unresolved",
}


def evidence_binding_to_locator(
    *,
    artifact_id: UUID,
    precision: InterpretationPrecision,
    block_id: str | None = None,
    page: int | None = None,
    bbox: dict | None = None,
    char_start: int | None = None,
    char_end: int | None = None,
    unresolved_reason: str | None = None,
) -> EvidenceLocator:
    """Bridges an interpretation-run `EvidenceBinding` (`neuron/brain_interpretation`)
    into the review layer's `EvidenceLocator` (ADR-0058), the boundary where a
    candidate assertion becomes something a reviewer can be shown. Takes plain values
    rather than `neuron`'s Pydantic model — `engine/` never imports from `neuron/`
    (clean architecture: canonical/review data crosses that boundary through this kind
    of explicit mapping, not a shared type)."""
    selector: tuple[dict, ...] = ()
    if precision != "unresolved" and (bbox is not None or page is not None):
        box_selector: dict = {"type": "nebula:BoxSelector"}
        if page is not None:
            box_selector["page"] = page
        if bbox is not None:
            box_selector.update({k: bbox[k] for k in ("x0", "y0", "x1", "y1") if k in bbox})
        if char_start is not None:
            box_selector["char_start"] = char_start
        if char_end is not None:
            box_selector["char_end"] = char_end
        selector = (box_selector,)

    return EvidenceLocator(
        source=str(artifact_id),
        precision=_PRECISION_MAP[precision],
        part=block_id,
        unresolved_reason=unresolved_reason,
        selector=selector,
    )
