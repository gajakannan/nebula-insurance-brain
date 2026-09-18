from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ParseStatus = Literal["complete", "partial", "failed"]


@dataclass(frozen=True, slots=True)
class ParseResult[DocumentT]:
    """Conversion checkpoint shared by pipeline and bundle adapters.

    The document type is supplied by the adapter; this contract does not import
    a converter or couple the interpretation package to a concrete parser.
    """

    document: DocumentT
    page_count: int
    failed_pages: list[int]
    ocr_page_count: int
    status: ParseStatus
    warnings: list[str]
