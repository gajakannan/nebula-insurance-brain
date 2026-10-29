from __future__ import annotations

import gzip
import io
import tarfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from brain_ingestion.docling_adapter import DoclingAdapter
from pypdf import PdfReader, PdfWriter


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


@pytest.mark.parametrize("capture_provenance", [False, True])
@pytest.mark.parametrize("prefix_kind", ["gzip", "zip", "text", "empty"])
def test_non_pdf_magic_is_rejected_before_any_parser(
    tmp_path: Path, capture_provenance: bool, prefix_kind: str
) -> None:
    pdf = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(pdf)
    if prefix_kind == "gzip":
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w") as handle:
            handle.addfile(tarfile.TarInfo("empty.txt"))
        payload = gzip.compress(archive.getvalue()) + b"\n" + pdf.getvalue()
    elif prefix_kind == "zip":
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as handle:
            handle.writestr("empty.txt", b"")
        payload = archive.getvalue() + b"\n" + pdf.getvalue()
    elif prefix_kind == "text":
        payload = b"untrusted prefix\n" + pdf.getvalue()
    else:
        payload = b""
    source = tmp_path / "source.pdf"
    source.write_bytes(payload)
    if payload:
        # These inputs pass the old non-strict PdfReader precheck.
        assert len(PdfReader(source).pages) == 1
    adapter = DoclingAdapter(capture_provenance=capture_provenance)
    with (
        patch("brain_ingestion.docling_adapter.PdfReader", side_effect=AssertionError("reader")),
        patch.object(adapter._converter, "convert", side_effect=AssertionError("conversion")),
        patch.object(
            adapter._converter, "initialize_pipeline", side_effect=AssertionError("pipeline")
        ),
        pytest.raises(ValueError, match="PDF file signature"),
    ):
        adapter.parse(source)


@pytest.mark.parametrize("capture_provenance", [False, True])
def test_pypdf_structure_errors_do_not_fail_a_docling_conversion(
    native_gl_pdf: Path, capture_provenance: bool
) -> None:
    # Code Review L-N1: pypdf's own errors are not ValueErrors; the conversion
    # still publishes, with Docling's page count and an explicit warning.
    from brain_ingestion import docling_adapter
    from pypdf.errors import PdfReadError

    def unreadable(*_args: object, **_kwargs: object) -> None:
        raise PdfReadError("damaged xref")

    with patch.object(docling_adapter, "PdfReader", side_effect=unreadable):
        result = DoclingAdapter(capture_provenance=capture_provenance).parse(native_gl_pdf)

    assert result.status in ("complete", "partial")
    assert result.page_count == 1
    assert "pdf_structure_unreadable" in result.warnings
