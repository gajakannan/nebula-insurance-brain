from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from brain_ingestion.bundle_writer import build_bundle
from brain_ingestion.docling_adapter import DoclingAdapter


def _build(native_gl_pdf: Path):
    parse_result = DoclingAdapter().parse(native_gl_pdf)
    return build_bundle(
        parse_result,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        document_id=uuid4(),
        version_id=uuid4(),
        artifact_id=uuid4(),
        source_sha256="a" * 64,
        configuration_hash="b" * 64,
    )


def test_bundle_contains_all_six_declared_files(native_gl_pdf: Path) -> None:
    manifest, files = _build(native_gl_pdf)

    assert set(files.keys()) == {
        "docling-document.json",
        "normalized.md",
        "blocks.jsonl",
        "tables.jsonl",
        "layout.jsonl",
    }
    assert {f.path for f in manifest.files} == set(files.keys()) | {"docling-document.json"}


def test_manifest_records_a_sha256_per_file(native_gl_pdf: Path) -> None:
    manifest, files = _build(native_gl_pdf)

    for artifact_file in manifest.files:
        import hashlib

        expected = hashlib.sha256(files[artifact_file.path]).hexdigest()
        assert artifact_file.sha256 == expected
        assert artifact_file.size_bytes == len(files[artifact_file.path])


def test_manifest_quality_and_page_count(native_gl_pdf: Path) -> None:
    manifest, _files = _build(native_gl_pdf)

    assert manifest.extraction_quality.status == "complete"
    assert manifest.extraction_quality.failed_pages == []
    assert manifest.page_count == 1
    assert manifest.coordinate_origin == "top_left"


def test_blocks_jsonl_bboxes_are_top_left_origin_and_in_page_bounds(native_gl_pdf: Path) -> None:
    _manifest, files = _build(native_gl_pdf)

    lines = [json.loads(line) for line in files["blocks.jsonl"].decode("utf-8").splitlines()]
    assert lines, "expected at least one block"
    for block in lines:
        bbox = block["bbox"]
        # Page is US Letter (792pt tall); top-left-origin y values must sit within that band,
        # and — the actual normalization check — the smaller y (y0, the top edge) must be
        # above the larger y (y1, the bottom edge) once flipped from Docling's BOTTOMLEFT.
        assert 0 <= bbox["y0"] <= 792
        assert 0 <= bbox["y1"] <= 792
        assert bbox["y0"] < bbox["y1"]


def test_execution_record_names_the_installed_docling_version(native_gl_pdf: Path) -> None:
    manifest, _files = _build(native_gl_pdf)

    assert manifest.execution.parser_package_version.startswith("docling==")


def test_docling_document_ref_sha256_matches_the_file(native_gl_pdf: Path) -> None:
    manifest, files = _build(native_gl_pdf)

    import hashlib

    expected = hashlib.sha256(files["docling-document.json"]).hexdigest()
    assert manifest.docling_document.sha256 == expected
