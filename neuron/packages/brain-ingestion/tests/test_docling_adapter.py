from __future__ import annotations

from pathlib import Path

from brain_ingestion.docling_adapter import DoclingAdapter


def test_native_pdf_parses_with_no_pages_needing_ocr(native_gl_pdf: Path) -> None:
    result = DoclingAdapter().parse(native_gl_pdf)

    assert result.status == "complete"
    assert result.page_count == 1
    assert result.ocr_page_count == 0
    assert result.failed_pages == []
    assert result.document.texts, "expected at least one text item from the declarations page"


def test_scanned_pdf_requires_ocr_on_every_page(scanned_gl_pdf: Path) -> None:
    result = DoclingAdapter().parse(scanned_gl_pdf)

    assert result.page_count == 1
    assert result.ocr_page_count == 1


def test_native_pdf_text_contains_the_each_occurrence_limit(native_gl_pdf: Path) -> None:
    result = DoclingAdapter().parse(native_gl_pdf)

    full_text = " ".join(t.text for t in result.document.texts)
    assert "1,000,000" in full_text
