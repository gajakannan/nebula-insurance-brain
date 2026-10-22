"""Instance-local hooks proven by F0004 Step 1a on Docling 2.126.0."""

from __future__ import annotations

from importlib.metadata import version
from typing import Any, Literal

from brain_interpretation.parsed_content import BlockOriginInput, ProducerIdentity
from docling.document_converter import DocumentConverter
from docling_core.types.doc.page import PdfTextCell

Receipt = tuple[Literal["STATED", "OCR"], ProducerIdentity]


class ItemProvenance:
    def __init__(self, converter: DocumentConverter) -> None:
        if version("docling") != "2.126.0":
            raise ValueError("unsupported provenance hook version")
        self.native: dict[tuple[int, str], ProducerIdentity] = {}
        self.ocr: dict[tuple[int, str], ProducerIdentity] = {}
        self.items: dict[str, list[Receipt | None]] = {}
        pipeline: Any = next(iter(converter.initialized_pipelines.values()))
        preprocess = pipeline.preprocessing_model

        class Preprocess:
            def __call__(proxy, conversion: Any, pages: Any) -> Any:
                for page in preprocess(conversion, pages):
                    if page._backend is not None:
                        backend = page._backend
                        producer = ProducerIdentity(
                            f"{type(backend).__module__}.{type(backend).__qualname__}",
                            f"docling:{version('docling')};docling-parse:{version('docling-parse')}",
                            None,
                            None,
                        )
                        for cell in page.cells:
                            if isinstance(cell, PdfTextCell):
                                self.native[(page.page_no, cell.text)] = producer
                    yield page

        pipeline.preprocessing_model = Preprocess()
        automatic = pipeline.ocr_model
        engine = getattr(automatic, "_engine", None) or automatic
        original_ocr = engine.post_process_cells

        def capture_ocr(cells: Any, page: Any, conversion: Any, *args: Any, **kwargs: Any) -> Any:
            engine_class = f"{type(engine).__module__}.{type(engine).__qualname__}"
            # The approved runtime uses RapidOCR. Another engine is unknown,
            # never assigned this engine's package version by resemblance.
            if engine_class == "docling.models.stages.ocr.rapid_ocr_model.RapidOcrModel":
                producer = ProducerIdentity(engine_class, version("rapidocr"), None, None)
                for cell in cells:
                    if cell.from_ocr is True:
                        self.ocr[(page.page_no, cell.text)] = producer
            return original_ocr(cells, page, conversion, *args, **kwargs)

        engine.post_process_cells = capture_ocr
        reader = pipeline.reading_order_model
        original_text = reader._handle_text_element

        def text(element: Any, **kwargs: Any) -> Any:
            item, current_list = original_text(element, **kwargs)
            self._record(item, element)
            return item, current_list

        reader._handle_text_element = text
        original_caption = reader._add_caption_or_footnote

        def caption(element: Any, *args: Any, **kwargs: Any) -> Any:
            item = original_caption(element, *args, **kwargs)
            self._record(item, element)
            return item

        reader._add_caption_or_footnote = caption
        original_merge = reader._merge_elements

        def merge(element: Any, merged: Any, item: Any, height: float) -> Any:
            result = original_merge(element, merged, item, height)
            self._record(item, merged)
            return result

        reader._merge_elements = merge

    def _record(self, item: Any, element: Any) -> None:
        receipts = self.items.setdefault(item.self_ref, [])
        for cell in element.cluster.cells:
            key = (element.page_no, cell.text)
            if isinstance(cell, PdfTextCell) and key in self.native:
                receipts.append(("STATED", self.native[key]))
            elif cell.from_ocr is True and key in self.ocr:
                receipts.append(("OCR", self.ocr[key]))
            else:
                receipts.append(None)

    def project(
        self, document: Any
    ) -> tuple[dict[str, tuple[BlockOriginInput, ...]], tuple[str, ...]]:
        result: dict[str, tuple[BlockOriginInput, ...]] = {}
        unavailable = []
        for item in document.texts:
            receipts = self.items.get(item.self_ref, [])
            observed = {receipt for receipt in receipts if receipt is not None}
            if not receipts or None in receipts or len(observed) != 1:
                unavailable.append(item.self_ref)
                continue
            origin, producer = next(iter(observed))
            regions = []
            for prov in item.prov:
                page = document.pages.get(prov.page_no)
                bbox = None
                if page is not None and page.size.height > 0 and page.size.width > 0:
                    box = prov.bbox.to_top_left_origin(page.size.height)
                    bbox = {"x0": box.l, "y0": box.t, "x1": box.r, "y1": box.b}
                regions.append(
                    {
                        "page": prov.page_no,
                        "bbox": bbox,
                        "char_start": prov.charspan[0],
                        "char_end": prov.charspan[1],
                    }
                )
            if regions:
                anchor: dict[str, Any] = {
                    "kind": "native_text" if origin == "STATED" else "page_region",
                    "regions": regions,
                }
                if origin == "STATED":
                    anchor["native_ref"] = item.self_ref
            else:
                anchor = {"kind": "unresolved", "reason": "converter emitted no text region"}
            result[item.self_ref] = (
                BlockOriginInput(
                    item.self_ref,
                    item.text,
                    origin,
                    producer,
                    anchor,
                    None,
                ),
            )
        return result, tuple(unavailable)
