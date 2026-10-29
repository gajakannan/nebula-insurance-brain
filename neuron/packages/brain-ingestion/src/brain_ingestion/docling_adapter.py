from __future__ import annotations

from pathlib import Path

from brain_interpretation.parsed_content import ParseResult, ParseStatus
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.document_converter import DocumentConverter
from docling_core.types.doc.document import DoclingDocument
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from brain_ingestion.item_provenance import (
    ItemProvenance,
    OcrObserver,
    install_ocr_asset_capture,
)

# Before any converter in this process loads OCR models (S0005 asset identity).
install_ocr_asset_capture()

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
        self._capture_provenance = capture_provenance
        self._converter, self._ocr = self._new_converter()

    @staticmethod
    def _new_converter() -> tuple[DocumentConverter, OcrObserver]:
        converter = DocumentConverter(allowed_formats=[InputFormat.PDF])
        converter.initialize_pipeline(InputFormat.PDF)
        return converter, OcrObserver(converter)

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
            self._converter, self._ocr = self._new_converter()
            observer = ItemProvenance(self._converter)
        self._ocr.pages.clear()
        result = self._converter.convert(str(source_path), raises_on_error=False)

        failed_pages = sorted({e.page_no for e in result.errors if e.page_no is not None})
        warnings = [f"{e.component_type}/{e.category}: {e.error_message}" for e in result.errors]
        status = _STATUS_MAP.get(result.status, "failed")
        # A page that converts empty is a failed page, not silent success
        # (F0005-S0001 edge cases): it never lets the document read as complete.
        pdf_pages = _pdf_pages(source_path)
        if pdf_pages is None:
            # pypdf cannot read the structure Docling converted: count Docling's
            # pages and say so, rather than failing the document (Code Review L-N1).
            warnings.append("pdf_structure_unreadable")
        page_total = len(pdf_pages) if pdf_pages is not None else result.document.num_pages()
        populated = {
            prov.page_no
            for item in (*result.document.texts, *result.document.tables)
            for prov in item.prov
        }
        empty = [page for page in range(1, page_total + 1) if page not in populated]
        if empty and status != "failed":
            failed_pages = sorted({*failed_pages, *empty})
            warnings += [f"empty_page:{page}" for page in empty]
            status = "partial"
        provenance, unavailable = observer.project(result.document) if observer else ({}, ())
        rotations = (
            {index + 1: page.rotation % 360 for index, page in enumerate(pdf_pages)}
            if observer and pdf_pages is not None
            else {}
        )

        return ParseResult(
            document=result.document,
            page_count=len(rotations) if rotations else result.document.num_pages(),
            failed_pages=failed_pages,
            ocr_page_count=ocr_page_count,
            status=status,
            warnings=warnings,
            projection_version=2 if observer else None,
            provenance=provenance,
            origin_unavailable=unavailable,
            page_rotations=rotations,
            model_artifact_digests=self._ocr.assets,
            ocr=self._ocr.observation(),
        )

    @staticmethod
    def _count_pages_needing_ocr(source_path: Path) -> int:
        try:
            reader = PdfReader(str(source_path))
            pages = list(reader.pages)
        except (ValueError, KeyError, TypeError, OSError, PyPdfError):
            return 0  # no readable text layer to inspect; the OCR observer counts
        count = 0
        for page in pages:
            try:
                text = page.extract_text()
            except (ValueError, KeyError, TypeError, OSError, PyPdfError):
                # A damaged content stream has no usable native text layer. It is
                # Docling's failed/OCR page to report, not a whole-document failure
                # (F0005-S0001-AC4).
                text = ""
            if not text.strip():
                count += 1
        return count


def _pdf_pages(source_path: Path) -> list | None:
    try:
        return list(PdfReader(str(source_path)).pages)
    except (ValueError, KeyError, TypeError, OSError, PyPdfError):
        return None
