"""F0005-S0005: exact OCR asset identity, read from the engine that actually ran.

Real Docling/RapidOCR conversion of a scanned qualification document. An
unresolvable asset, or one whose digest differs from the preflight pin, records
no OCR producer: OCR items become ORIGIN_UNAVAILABLE (per-document v1 fallback)
and no guessed identity is written.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from brain_ingestion import item_provenance
from brain_ingestion.docling_adapter import DoclingAdapter

ROOT = Path(__file__).resolve().parents[4]
SCANNED = ROOT / "neuron/fixtures/qualification/documents/gl-q-009.pdf"


@pytest.fixture(scope="module")
def pins() -> dict[str, str]:
    pins = item_provenance.ocr_asset_pins()
    assert set(pins) == {"det", "cls", "rec"}
    return pins


def test_pins_match_the_installed_asset_files(pins):
    import rapidocr

    models = Path(rapidocr.__file__).parent / "models"
    for identity in pins.values():
        name, rest = identity.split("@", 1)
        digest = rest.rsplit(":sha256:", 1)[1]
        assert hashlib.sha256((models / name).read_bytes()).hexdigest() == digest


def test_scanned_items_record_ocr_origin_with_exact_asset_identity(pins):
    parsed = DoclingAdapter(capture_provenance=True).parse(SCANNED)
    assert parsed.origin_unavailable == ()
    assert sorted(parsed.model_artifact_digests) == sorted(pins.values())
    origins = [origin for items in parsed.provenance.values() for origin in items]
    assert origins and {origin.text_origin for origin in origins} == {"OCR"}
    producers = {origin.producer for origin in origins}
    assert len(producers) == 1
    producer = producers.pop()
    assert producer.engine == "docling.models.stages.ocr.rapid_ocr_model.RapidOcrModel"
    assert producer.model and producer.model_version
    composite = "\n".join(pins[task] for task in sorted(pins))
    assert producer.model_version == "sha256:" + hashlib.sha256(composite.encode()).hexdigest()
    assert producer.model == "rapidocr:" + ",".join(
        f"{task}={pins[task].split('@')[0]}" for task in sorted(pins)
    )


@pytest.mark.parametrize("failure", ["altered_digest", "unresolvable_asset"])
def test_unpinned_or_unknown_assets_block_v2_identity(monkeypatch, pins, failure):
    if failure == "altered_digest":
        altered = {**pins, "rec": pins["rec"][:-8] + "00000000"}
        monkeypatch.setattr(item_provenance, "ocr_asset_pins", lambda: altered)
    else:
        monkeypatch.setattr(item_provenance, "resolve_ocr_assets", lambda engine: None)
    parsed = DoclingAdapter(capture_provenance=True).parse(SCANNED)
    assert parsed.model_artifact_digests == ()
    assert parsed.origin_unavailable  # OCR items cannot be attributed
    for items in parsed.provenance.values():
        assert all(origin.text_origin != "OCR" for origin in items)
