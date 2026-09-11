from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from brain_ingestion.bundle_writer import build_bundle
from brain_ingestion.docling_adapter import DoclingAdapter


def test_source_bytes_are_retained_as_a_seventh_file_when_provided(native_gl_pdf: Path) -> None:
    parse_result = DoclingAdapter().parse(native_gl_pdf)
    source_bytes = native_gl_pdf.read_bytes()

    manifest, files = build_bundle(
        parse_result,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        document_id=uuid4(),
        version_id=uuid4(),
        artifact_id=uuid4(),
        source_sha256="a" * 64,
        configuration_hash="b" * 64,
        source_bytes=source_bytes,
        source_filename=native_gl_pdf.name,
    )

    assert files["source.pdf"] == source_bytes
    assert any(f.path == "source.pdf" for f in manifest.files)


def test_omitting_source_bytes_reproduces_the_original_six_file_bundle(native_gl_pdf: Path) -> None:
    parse_result = DoclingAdapter().parse(native_gl_pdf)

    _manifest, files = build_bundle(
        parse_result,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        document_id=uuid4(),
        version_id=uuid4(),
        artifact_id=uuid4(),
        source_sha256="a" * 64,
        configuration_hash="b" * 64,
    )

    assert "source.pdf" not in files
    assert set(files.keys()) == {
        "docling-document.json",
        "normalized.md",
        "blocks.jsonl",
        "tables.jsonl",
        "layout.jsonl",
    }
