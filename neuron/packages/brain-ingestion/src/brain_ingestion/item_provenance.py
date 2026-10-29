"""Instance-local hooks proven by F0004 Step 1a on Docling 2.126.0."""

from __future__ import annotations

import hashlib
import json
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal

from brain_interpretation.parsed_content import BlockOriginInput, OcrObservation, ProducerIdentity
from docling.document_converter import DocumentConverter
from docling_core.types.doc.page import PdfTextCell

Receipt = tuple[Literal["STATED", "OCR"], ProducerIdentity]
_OCR_TASKS = (
    ("det", "text_det", "use_det"),
    ("cls", "text_cls", "use_cls"),
    ("rec", "text_rec", "use_rec"),
)


def install_ocr_asset_capture() -> None:
    """Tag each RapidOCR torch predictor with the model file it was loaded from.

    RapidOCR resolves, verifies and loads the file, then discards the path. The
    tag lets provenance read the identity from the engine instance that actually
    runs, rather than from defaults or documentation. Installed once per process
    before any converter initializes its OCR engine; it changes no behavior.
    """
    try:
        from rapidocr.inference_engine.pytorch.networks import main as torch_networks

        loader = torch_networks.ModelLoader
        build = loader._build_and_load_model
    except (ImportError, AttributeError):
        # An upstream layout change must not break conversion at import. With no
        # tags, assets are unresolvable: the bundle records the OCR engine as
        # unidentified and items as ORIGIN_UNAVAILABLE, never a guess (Architect
        # G3). Revalidate this hook on every RapidOCR/Docling upgrade.
        return
    if getattr(loader, "_nebula_asset_capture", False):
        return

    def tagged(self: Any, arch_config: Any, model_path: Path) -> Any:
        model = build(self, arch_config, model_path)
        model._nebula_asset_path = Path(model_path)
        return model

    setattr(loader, "_build_and_load_model", tagged)  # noqa: B010 - see docstring
    setattr(loader, "_nebula_asset_capture", True)  # noqa: B010


def ocr_asset_pins() -> dict[str, str]:
    """Digests recorded at preflight for the pinned RapidOCR runtime."""
    data = json.loads(files("brain_ingestion").joinpath("ocr_asset_pins.json").read_text())
    if data.get("rapidocr") != version("rapidocr"):
        return {}
    return dict(data["assets"])


def resolve_ocr_assets(engine: Any) -> dict[str, str] | None:
    """Identity of each OCR model file loaded by this engine, or None if unknowable."""
    reader = getattr(engine, "reader", None)
    if reader is None:
        return None
    assets: dict[str, str] = {}
    for task, attribute, enabled in _OCR_TASKS:
        if not getattr(reader, enabled, True):
            continue
        predictor = getattr(
            getattr(getattr(reader, attribute, None), "session", None), "predictor", None
        )
        path = getattr(predictor, "_nebula_asset_path", None)
        if not isinstance(path, Path) or not path.is_file():
            return None
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assets[task] = f"{path.name}@rapidocr=={version('rapidocr')}:sha256:{digest}"
    return assets or None


_RAPID_OCR = "docling.models.stages.ocr.rapid_ocr_model.RapidOcrModel"


def ocr_stage(converter: DocumentConverter) -> Any:
    """The OCR engine instance of the converter's initialized PDF pipeline, if any."""
    pipeline: Any = next(iter(converter.initialized_pipelines.values()))
    automatic = getattr(pipeline, "ocr_model", None)
    return getattr(automatic, "_engine", None) or automatic


def identify_ocr_engine(engine: Any) -> tuple[ProducerIdentity | None, tuple[str, ...]]:
    """Producer identity and pinned asset digests of the running OCR engine.

    Hashes the files at conversion time. An unresolvable asset, one that differs
    from the preflight pin, or an engine other than the approved RapidOCR is
    unknown: no identity is returned, so items become ORIGIN_UNAVAILABLE and the
    bundle records the engine as unidentified rather than guessed.
    """
    if engine is None or f"{type(engine).__module__}.{type(engine).__qualname__}" != _RAPID_OCR:
        return None, ()
    assets = resolve_ocr_assets(engine)
    if assets is None or assets != ocr_asset_pins():
        return None, ()
    pinned = tuple(assets[task] for task in sorted(assets))
    identity = ProducerIdentity(
        _RAPID_OCR,
        version("rapidocr"),
        "rapidocr:" + ",".join(f"{task}={assets[task].split('@')[0]}" for task in sorted(assets)),
        "sha256:" + hashlib.sha256("\n".join(pinned).encode()).hexdigest(),
    )
    return identity, pinned


class OcrObserver:
    """Observes which pages the OCR engine produced text on (F0005-S0001-AC2).

    Runs on every conversion, v1 or v2, so the bundle records the OCR page count
    and engine from what happened rather than an estimate from the text layer.
    """

    def __init__(self, converter: DocumentConverter) -> None:
        self.pages: set[int] = set()
        engine = ocr_stage(converter)
        self.engine, self.assets = identify_ocr_engine(engine)
        if engine is None:
            return
        original = engine.post_process_cells

        def observe(cells: Any, page: Any, *args: Any, **kwargs: Any) -> Any:
            if any(getattr(cell, "from_ocr", False) is True for cell in cells):
                self.pages.add(page.page_no)
            return original(cells, page, *args, **kwargs)

        engine.post_process_cells = observe

    def observation(self) -> OcrObservation:
        return OcrObservation(pages=tuple(sorted(self.pages)), engine=self.engine)


class ItemProvenance:
    def __init__(self, converter: DocumentConverter) -> None:
        if version("docling") != "2.126.0":
            raise ValueError("unsupported provenance hook version")
        self.native: dict[tuple[int, str], ProducerIdentity] = {}
        self.ocr: dict[tuple[int, str], ProducerIdentity] = {}
        self.items: dict[str, list[Receipt | None]] = {}
        self.ocr_assets: tuple[str, ...] = ()
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
        engine = ocr_stage(converter)
        original_ocr = engine.post_process_cells
        # Unidentified engine/assets record no OCR producer, so its items become
        # ORIGIN_UNAVAILABLE and the per-document v1 fallback applies.
        ocr_producer, self.ocr_assets = identify_ocr_engine(engine)

        def capture_ocr(cells: Any, page: Any, conversion: Any, *args: Any, **kwargs: Any) -> Any:
            # The approved runtime uses RapidOCR with pinned assets. Another engine
            # or an unpinned asset is unknown, never assigned an identity by resemblance.
            if ocr_producer is not None:
                for cell in cells:
                    if cell.from_ocr is True:
                        self.ocr[(page.page_no, cell.text)] = ocr_producer
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
