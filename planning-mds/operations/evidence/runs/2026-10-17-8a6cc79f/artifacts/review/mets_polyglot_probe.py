"""Bounded security probe: no large archive, model download, or conversion."""
import gzip
import io
import sys
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import patch

import filetype
from docling.datamodel.document import _DocumentConversionInput
from docling.document_converter import DocumentConverter
from pypdf import PdfReader, PdfWriter

from brain_ingestion.docling_adapter import DoclingAdapter

archive = io.BytesIO()
with tarfile.open(fileobj=archive, mode="w") as handle:
    entry = tarfile.TarInfo("empty.txt")
    handle.addfile(entry)
pdf = io.BytesIO()
writer = PdfWriter()
writer.add_blank_page(width=100, height=100)
writer.write(pdf)
payload = gzip.compress(archive.getvalue()) + b"\n" + pdf.getvalue()

class ReachedMetsDetector(Exception):
    pass

def intercepted_detector(obj):
    print("REACHED_METS_DETECTION_BEFORE_PDF_ALLOWLIST", flush=True)
    raise ReachedMetsDetector()

with tempfile.TemporaryDirectory() as directory:
    source = Path(directory) / "source.pdf"
    source.write_bytes(payload)
    print("source bytes", len(payload), "mime", filetype.guess_mime(str(source)))
    print("PdfReader accepted pages", len(PdfReader(source).pages))
    _DocumentConversionInput._detect_mets_gbs = staticmethod(intercepted_detector)
    if "--expect-rejection" in sys.argv:
        for capture in (False, True):
            adapter = DoclingAdapter(capture_provenance=capture)
            with (
                patch.object(DoclingAdapter, "_count_pages_needing_ocr", side_effect=AssertionError("PDF parser must not run")) as preparse,
                patch.object(DocumentConverter, "initialize_pipeline", side_effect=AssertionError("pipeline must not initialize")) as initialize,
                patch.object(DocumentConverter, "convert", side_effect=AssertionError("converter must not run")) as convert,
            ):
                try:
                    adapter.parse(source)
                except ValueError as error:
                    assert "PDF file signature" in str(error)
                else:
                    raise AssertionError("Polyglot must be rejected")
                assert preparse.call_count == initialize.call_count == convert.call_count == 0
                print("REJECTED BEFORE PARSERS", "capture_provenance", capture, "calls", 0)
        print("CONFIRMED: fixed adapter rejects polyglot in both modes before any parser/detection")
    else:
        try:
            DoclingAdapter().parse(source)
        except ReachedMetsDetector:
            print("CONFIRMED: ordinary adapter parse reaches archive detector")
        else:
            raise AssertionError("Expected bounded detector interception")
