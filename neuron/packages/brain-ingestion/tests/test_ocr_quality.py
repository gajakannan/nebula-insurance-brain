"""F0005-S0001-AC2: the published bundle records the OCR page count and engine.

Real Docling/RapidOCR conversions on the default (v1) writer path. The count is
the pages on which the OCR engine produced text, observed during conversion; the
engine identity is read from the running engine and its pinned assets, never
guessed (ADR-0073 amendment, 2026-10-27).
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from brain_content.manifest import ExtractionQuality, OcrQuality, parse_manifest
from brain_ingestion import item_provenance
from brain_ingestion.bundle_writer import build_bundle
from brain_ingestion.conversion_process import _encode_parse, decode_parse
from brain_ingestion.docling_adapter import DoclingAdapter
from brain_interpretation.parsed_content import OcrObservation, ParseResult, ProducerIdentity
from pydantic import ValidationError

RAPID_OCR = "docling.models.stages.ocr.rapid_ocr_model.RapidOcrModel"


def _manifest(parsed: ParseResult) -> dict:
    manifest, _files = build_bundle(
        parsed,
        tenant_id=uuid4(),
        knowledge_base_id=uuid4(),
        document_id=uuid4(),
        version_id=uuid4(),
        artifact_id=uuid4(),
        source_sha256="a" * 64,
        configuration_hash="b" * 64,
    )
    # The bytes the store publishes validate against the v1 contract and read back intact.
    reread = parse_manifest(manifest.model_dump_json().encode())
    assert reread.extraction_quality == manifest.extraction_quality
    return reread.extraction_quality.model_dump(mode="json")


def test_scanned_v1_bundle_records_observed_ocr_pages_and_pinned_engine(
    scanned_gl_pdf: Path,
) -> None:
    pins = item_provenance.ocr_asset_pins()
    parsed = DoclingAdapter().parse(scanned_gl_pdf)

    assert parsed.ocr is not None
    assert parsed.ocr.pages == (1,)
    assert parsed.ocr.engine is not None
    assert parsed.ocr.engine.engine == RAPID_OCR
    # The default writer now records the asset identity too, not only v2.
    assert sorted(parsed.model_artifact_digests) == sorted(pins.values())

    ocr = _manifest(parsed)["ocr"]
    assert ocr["page_count"] == 1
    assert ocr["pages"] == [1]
    assert ocr["engine"]["name"] == RAPID_OCR
    assert ocr["engine"]["version"] == parsed.ocr.engine.engine_version
    assert ocr["engine"]["model_version"].startswith("sha256:")


def test_native_v1_bundle_records_zero_ocr_pages_with_the_configured_engine(
    native_gl_pdf: Path,
) -> None:
    parsed = DoclingAdapter().parse(native_gl_pdf)

    ocr = _manifest(parsed)["ocr"]
    assert ocr["page_count"] == 0
    assert ocr["pages"] == []
    assert ocr["engine"]["name"] == RAPID_OCR


def test_unpinned_assets_record_ocr_pages_but_no_engine_identity(
    monkeypatch: pytest.MonkeyPatch, scanned_gl_pdf: Path
) -> None:
    monkeypatch.setattr(item_provenance, "resolve_ocr_assets", lambda engine: None)
    parsed = DoclingAdapter().parse(scanned_gl_pdf)

    assert parsed.model_artifact_digests == ()
    ocr = _manifest(parsed)["ocr"]
    assert ocr["page_count"] == 1
    assert ocr["engine"] is None


def test_observer_counts_each_converted_source_separately(
    native_gl_pdf: Path, scanned_gl_pdf: Path
) -> None:
    adapter = DoclingAdapter()
    assert adapter.parse(scanned_gl_pdf).ocr.pages == (1,)
    assert adapter.parse(native_gl_pdf).ocr.pages == ()


def test_ocr_observation_survives_the_conversion_child_handoff() -> None:
    engine = ProducerIdentity(RAPID_OCR, "3.9.2", "rapidocr:det=a", "sha256:" + "c" * 64)
    for ocr in (None, OcrObservation((1, 3), engine), OcrObservation((2,), None)):
        parsed = ParseResult(
            document=None,
            page_count=3,
            failed_pages=[],
            ocr_page_count=2,
            status="complete",
            warnings=[],
            ocr=ocr,
        )
        assert decode_parse(None, _encode_parse(parsed)).ocr == ocr


def test_historical_quality_without_ocr_stays_valid() -> None:
    legacy = ExtractionQuality.model_validate(
        {"status": "complete", "failed_pages": [], "warnings": []}
    )
    assert legacy.ocr is None


@pytest.mark.parametrize(
    "value",
    [
        {"page_count": 2, "pages": [1], "engine": None},
        {"page_count": 2, "pages": [2, 1], "engine": None},
        {"page_count": 1, "pages": [0], "engine": None},
        {"page_count": 1, "pages": [1], "engine": {"name": "x", "version": "1"}},
    ],
)
def test_inconsistent_ocr_quality_is_rejected(value: dict) -> None:
    with pytest.raises(ValidationError):
        OcrQuality.model_validate(value)


def test_a_moved_rapidocr_loader_degrades_to_an_unidentified_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins

    real_import = builtins.__import__

    def moved(name: str, *args: object, **kwargs: object) -> object:
        if name == "rapidocr.inference_engine.pytorch.networks":
            raise ImportError("moved upstream")
        return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(builtins, "__import__", moved)
    item_provenance.install_ocr_asset_capture()  # does not raise


def test_without_asset_tags_the_engine_is_recorded_as_unidentified(
    monkeypatch: pytest.MonkeyPatch, scanned_gl_pdf: Path
) -> None:
    # Delta review D-5: what a moved RapidOCR loader degrades to, end to end.
    monkeypatch.setattr(item_provenance, "resolve_ocr_assets", lambda engine: None)
    parsed = DoclingAdapter().parse(scanned_gl_pdf)
    assert parsed.ocr is not None and parsed.ocr.engine is None
    assert _manifest(parsed)["ocr"]["engine"] is None
