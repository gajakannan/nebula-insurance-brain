from __future__ import annotations

from pathlib import Path

from brain_interpretation.parsed_content import ParseResult, ParseStatus
from docling.datamodel.base_models import ConversionStatus
from docling.document_converter import DocumentConverter
from docling_core.types.doc.document import DoclingDocument
from pypdf import PdfReader

_STATUS_MAP: dict[ConversionStatus, ParseStatus] = {
    ConversionStatus.SUCCESS: "complete",
    ConversionStatus.PARTIAL_SUCCESS: "partial",
    ConversionStatus.FAILURE: "failed",
}


class DoclingAdapter:
    """Wraps Docling's `DocumentConverter` for the parse-once step (ADR-0003, F0001-S0003).

    `conversion_calls` is always exactly 1 per `parse()` invocation — this adapter is
    the only place `neuron/` calls Docling; `interpret()` never does (asserted by the
    caller, F0001-S0003 acceptance criterion 2). `ocr_page_count` counts pages that
    have no native, extractable text layer — Docling's default pipeline OCRs those
    pages automatically; this reports the count the caller declares as `ocr_calls`
    rather than a truncated or estimated one.
    """

    def __init__(self) -> None:
        self._converter = DocumentConverter()

    def parse(self, source_path: Path) -> ParseResult[DoclingDocument]:
        ocr_page_count = self._count_pages_needing_ocr(source_path)
        result = self._converter.convert(str(source_path), raises_on_error=False)

        failed_pages = sorted({e.page_no for e in result.errors if e.page_no is not None})
        warnings = [f"{e.component_type}/{e.category}: {e.error_message}" for e in result.errors]
        status = _STATUS_MAP.get(result.status, "failed")

        return ParseResult(
            document=result.document,
            page_count=result.document.num_pages(),
            failed_pages=failed_pages,
            ocr_page_count=ocr_page_count,
            status=status,
            warnings=warnings,
        )

    @staticmethod
    def _count_pages_needing_ocr(source_path: Path) -> int:
        reader = PdfReader(str(source_path))
        return sum(1 for page in reader.pages if not page.extract_text().strip())
