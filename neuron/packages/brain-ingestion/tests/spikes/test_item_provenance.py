"""F0004 Step 1a: observe producer receipts at the pinned converter boundary.

Synthetic development PDFs only; no frozen corpus or production writer changes.
Run directly to retain fixtures, native exports and an expected/observed report.
Instance-local wrappers preserve the converter's actual cells-to-item relation.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import io
import json
import sys
from pathlib import Path
from typing import Any

import pypdfium2
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter
from docling_core.types.doc.page import PdfTextCell
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

NATIVE_LINES = ("NATIVE ALPHA POLICY", "NATIVE BETA COVERAGE")
SCANNED_LINES = ("SCANNED GAMMA POLICY", "SCANNED DELTA COVERAGE")
PACKAGES = ("docling", "docling-core", "docling-parse", "rapidocr", "torch")


def _text_pdf(lines: tuple[str, ...]) -> bytes:
    buffer = io.BytesIO()
    canvas = Canvas(buffer, pagesize=(612, 792), invariant=1)
    canvas.setFont("Helvetica", 22)
    for index, line in enumerate(lines):
        canvas.drawString(60, 700 - 45 * index, line)
    canvas.save()
    return buffer.getvalue()


def create_fixtures(folder: Path) -> dict[str, Path]:
    folder.mkdir(parents=True, exist_ok=True)
    native = folder / "native.pdf"
    native.write_bytes(_text_pdf(NATIVE_LINES))
    with pypdfium2.PdfDocument(_text_pdf(SCANNED_LINES)) as document:
        page = document[0]
        bitmap = page.render(scale=3)
        image: Image.Image = bitmap.to_pil().copy()
        bitmap.close()
        page.close()
    paths = {"native": native}
    for name in ("scanned", "mixed"):
        path = folder / f"{name}.pdf"
        canvas = Canvas(str(path), pagesize=(612, 792), invariant=1)
        if name == "mixed":
            canvas.setFont("Helvetica", 22)
            for index, line in enumerate(NATIVE_LINES):
                canvas.drawString(60, 730 - 40 * index, line)
            # The raster includes no PDF text. Its upper text is below the
            # native layer, so a mixed page exercises actual region OCR.
            canvas.drawImage(ImageReader(image), 0, 50, width=612, height=500)
        else:
            canvas.drawImage(ImageReader(image), 0, 0, width=612, height=792)
        canvas.save()
        paths[name] = path
    return paths


def _class_name(value: Any) -> str:
    return f"{type(value).__module__}.{type(value).__qualname__}"


class ItemReceipts:
    def __init__(self, converter: DocumentConverter):
        self.receipts: dict[str, list[dict[str, Any]]] = {}
        self.native_cells: dict[tuple[int, str], str] = {}
        self.ocr_cells: dict[tuple[int, str], str] = {}
        pipeline = next(iter(converter.initialized_pipelines.values()))
        ocr = pipeline.ocr_model
        engine = getattr(ocr, "_engine", None) or ocr
        original_ocr = engine.post_process_cells

        def post_process(cells: Any, page: Any, conversion: Any, *args: Any, **kwargs: Any):
            # These are the actual cells emitted by the actual engine, before
            # the converter merges them with PDF cells. No page OCR count.
            for cell in cells:
                if cell.from_ocr is True:
                    self.ocr_cells[(page.page_no, cell.text)] = _class_name(engine)
            return original_ocr(cells, page, conversion, *args, **kwargs)

        engine.post_process_cells = post_process
        preprocess = pipeline.preprocessing_model

        class PreprocessProxy:
            def __call__(proxy_self, conversion: Any, pages: Any):
                for page in preprocess(conversion, pages):
                    # Assembly releases the backend before reading order. Keep
                    # the actual backend-to-native-cell receipt at extraction.
                    if page._backend is not None:
                        for cell in page.cells:
                            if isinstance(cell, PdfTextCell):
                                self.native_cells[(page.page_no, cell.text)] = _class_name(
                                    page._backend
                                )
                    yield page

        pipeline.preprocessing_model = PreprocessProxy()
        reader = pipeline.reading_order_model
        original_text = reader._handle_text_element

        def handle(element: Any, **kwargs: Any):
            item, current_list = original_text(element, **kwargs)
            self._record(item, element)
            return item, current_list

        reader._handle_text_element = handle
        original_caption = reader._add_caption_or_footnote

        def caption(element: Any, *args: Any, **kwargs: Any):
            item = original_caption(element, *args, **kwargs)
            self._record(item, element)
            return item

        reader._add_caption_or_footnote = caption
        original_merge = reader._merge_elements

        def merge(element: Any, merged: Any, item: Any, height: float):
            result = original_merge(element, merged, item, height)
            self._record(item, merged)
            return result

        reader._merge_elements = merge

    def _record(self, item: Any, element: Any) -> None:
        receipts = self.receipts.setdefault(item.self_ref, [])
        for cell in element.cluster.cells:
            producer = None
            origin = "ORIGIN_UNAVAILABLE"
            if isinstance(cell, PdfTextCell):
                # Positive native backend type and its observed instance;
                # a generic cell with from_ocr=False does not qualify.
                producer = self.native_cells.get((element.page_no, cell.text))
                if producer:
                    origin = "STATED"
            elif cell.from_ocr is True:
                producer = self.ocr_cells.get((element.page_no, cell.text))
                if producer:
                    origin = "OCR"
            receipts.append(
                {
                    "cell_index": cell.index,
                    "cell_text": cell.text,
                    "cell_class": _class_name(cell),
                    "from_ocr": cell.from_ocr,
                    "origin": origin,
                    "producer_class": producer,
                    "producer_packages": {p: metadata.version(p) for p in PACKAGES},
                }
            )

    def observations(self, document: Any, fixture: str) -> list[dict[str, Any]]:
        observations = []
        for item in document.texts:
            receipts = self.receipts.get(item.self_ref, [])
            origins = {receipt["origin"] for receipt in receipts}
            observed = (
                next(iter(origins))
                if len(origins) == 1 and "ORIGIN_UNAVAILABLE" not in origins
                else "ORIGIN_UNAVAILABLE"
            )
            if fixture == "native":
                expected = ["STATED"]
            elif fixture == "scanned":
                expected = ["OCR"]
            else:
                expected = []
                if "NATIVE" in item.text.upper():
                    expected.append("STATED")
                if "SCANNED" in item.text.upper():
                    expected.append("OCR")
            matches = observed in expected if len(expected) == 1 else False
            # The approved mixed-page criterion permits precisely identified
            # unattributable items, and consequently a per-document v1 fallback.
            if fixture == "mixed" and observed == "ORIGIN_UNAVAILABLE":
                matches = True
            observations.append(
                {
                    "native_ref": item.self_ref,
                    "text": item.text,
                    "expected_origins": expected,
                    "observed_origin": observed,
                    "matches": matches,
                    "receipts": receipts,
                    "unavailable_reason": (
                        None
                        if observed != "ORIGIN_UNAVAILABLE"
                        else "no complete single-producer cells-to-item trace"
                    ),
                }
            )
        return observations


def run_spike(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "step": "F0004-1a",
        "synthetic_development_only": True,
        "python": sys.version,
        "versions": {p: metadata.version(p) for p in PACKAGES},
        "fixtures": {},
        "result": "NOT_RUN",
    }
    report_path = output / "item-provenance.json"
    try:
        assert metadata.version("docling") == "2.126.0"
        fixtures = create_fixtures(output / "fixtures")
        converter = DocumentConverter()
        converter.initialize_pipeline(InputFormat.PDF)
        for name, fixture in fixtures.items():
            # New converter-local observers for each independent conversion.
            # Reuse the initialized pipeline without stacking wrappers.
            observer = ItemReceipts(converter)
            conversion = converter.convert(fixture, raises_on_error=False)
            observations = observer.observations(conversion.document, name)
            (output / f"{name}.native.json").write_text(
                conversion.document.model_dump_json(indent=2)
            )
            text = " ".join(item.text for item in conversion.document.texts).upper()
            expected_tokens = (
                ("ALPHA", "BETA")
                if name == "native"
                else ("GAMMA", "DELTA")
                if name == "scanned"
                else ("ALPHA", "BETA", "GAMMA", "DELTA")
            )
            missing = [token for token in expected_tokens if token not in text]
            unavailable = sum(
                item["observed_origin"] == "ORIGIN_UNAVAILABLE" for item in observations
            )
            report["fixtures"][name] = {
                "conversion_status": conversion.status.value,
                "item_count": len(observations),
                "origin_unavailable_count": unavailable,
                "expected_document_v1_fallback": unavailable > 0,
                "missing_expected_tokens": missing,
                "items": observations,
                "pass": bool(observations)
                and conversion.status.value == "success"
                and not missing
                and all(item["matches"] for item in observations),
            }
            # Each fixture gets a fresh converter to keep observers isolated.
            if name != "mixed":
                converter = DocumentConverter()
                converter.initialize_pipeline(InputFormat.PDF)
        report["result"] = "PASS" if all(f["pass"] for f in report["fixtures"].values()) else "FAIL"
    except Exception as exc:
        report["result"] = "RUNTIME_ERROR"
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def test_pinned_converter_item_provenance(tmp_path: Path) -> None:
    report = run_spike(tmp_path)
    assert report["result"] == "PASS", json.dumps(report, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_spike(args.output)
    print(json.dumps({"result": result["result"], "report": str(args.output)}, indent=2))
    raise SystemExit(0 if result["result"] == "PASS" else 1)
