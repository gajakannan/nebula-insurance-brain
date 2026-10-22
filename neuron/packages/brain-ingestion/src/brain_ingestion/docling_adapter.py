from __future__ import annotations

from pathlib import Path

from brain_interpretation.parsed_content import ParseResult, ParseStatus
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.document_converter import DocumentConverter
from docling_core.types.doc.document import DoclingDocument
from pypdf import PdfReader

from brain_ingestion.item_provenance import ItemProvenance

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

    def __init__(self, *, capture_provenance: bool = False) -> None:
        self._converter = DocumentConverter(allowed_formats=[InputFormat.PDF])
        self._capture_provenance = capture_provenance

    def parse(self, source_path: Path) -> ParseResult[DoclingDocument]:
        # WHY: Docling detects archives before applying allowed_formats, and
        # PdfReader accepts prefixed PDF polyglots. Reject other magic before
        # either parser sees untrusted bytes (SEC-H1).
        with source_path.open("rb") as source:
            if source.read(5) != b"%PDF-":
                raise ValueError("Source must begin with a PDF file signature")
        ocr_page_count = self._count_pages_needing_ocr(source_path)
        observer = None
        if self._capture_provenance:
            # A fresh converter prevents hooks/receipts leaking between sources.
            self._converter = DocumentConverter(allowed_formats=[InputFormat.PDF])
            self._converter.initialize_pipeline(InputFormat.PDF)
            observer = ItemProvenance(self._converter)
        result = self._converter.convert(str(source_path), raises_on_error=False)

        failed_pages = sorted({e.page_no for e in result.errors if e.page_no is not None})
        warnings = [f"{e.component_type}/{e.category}: {e.error_message}" for e in result.errors]
        status = _STATUS_MAP.get(result.status, "failed")
        provenance, unavailable = observer.project(result.document) if observer else ({}, ())
        rotations = (
            {
                index + 1: page.rotation % 360
                for index, page in enumerate(PdfReader(str(source_path)).pages)
            }
            if observer
            else {}
        )

        return ParseResult(
            document=result.document,
            page_count=len(rotations) if observer else result.document.num_pages(),
            failed_pages=failed_pages,
            ocr_page_count=ocr_page_count,
            status=status,
            warnings=warnings,
            projection_version=2 if observer else None,
            provenance=provenance,
            origin_unavailable=unavailable,
            page_rotations=rotations,
        )

    @staticmethod
    def _count_pages_needing_ocr(source_path: Path) -> int:
        reader = PdfReader(str(source_path))
        return sum(1 for page in reader.pages if not page.extract_text().strip())
