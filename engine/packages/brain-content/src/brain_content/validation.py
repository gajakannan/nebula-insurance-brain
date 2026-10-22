"""Shared, versioned byte and record verifier. No parser or application I/O."""

from __future__ import annotations

import base64
import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal
from uuid import UUID

from brain_content.contracts import decode_json
from brain_content.manifest import ArtifactVersionUnsupported, Manifest, parse_manifest
from brain_content.records import (
    ContentBlockV2,
    ContentLayoutV2,
    ContentTableV2,
    FigureAnchor,
    NativeTextAnchor,
    Record,
    TimeSpanAnchor,
)

PAYLOAD_FILES = frozenset(
    {"docling-document.json", "normalized.md", "blocks.jsonl", "tables.jsonl", "layout.jsonl"}
)
ASSET_PATH = re.compile(r"assets/[A-Za-z0-9_-]+\.[A-Za-z0-9]+\Z")


class ArtifactIntegrityError(RuntimeError):
    code = "ARTIFACT_INTEGRITY"


class ArtifactConflict(ArtifactIntegrityError):
    code = "ARTIFACT_CONFLICT"


@dataclass(frozen=True)
class ArtifactKey:
    artifact_id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID
    contract_version: Literal[1, 2]

    def __post_init__(self) -> None:
        if type(self.contract_version) is not int or self.contract_version not in (1, 2):
            raise ArtifactVersionUnsupported("ARTIFACT_VERSION_UNSUPPORTED")

    @property
    def prefix(self) -> str:
        if self.contract_version == 1:
            return f"bundles/{self.artifact_id}"
        if self.contract_version == 2:
            return f"bundles/{self.tenant_id}/{self.knowledge_base_id}/{self.artifact_id}"
        raise ArtifactVersionUnsupported("ARTIFACT_VERSION_UNSUPPORTED")


@dataclass(frozen=True)
class VerifiedBundle:
    key: ArtifactKey
    manifest: Manifest
    manifest_bytes: bytes
    manifest_sha256: str
    files: Mapping[str, bytes]
    blocks: tuple[ContentBlockV2, ...]
    tables: tuple[ContentTableV2, ...]
    layout: tuple[ContentLayoutV2, ...]


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def inventory_hash(files: Mapping[str, bytes], version: int) -> str:
    if version == 1:
        return sha256("".join(sha256(files[path]) for path in sorted(files)).encode())
    if version != 2:
        raise ArtifactVersionUnsupported("ARTIFACT_VERSION_UNSUPPORTED")
    inventory = [
        {"path": path, "sha256": sha256(files[path]), "size_bytes": len(files[path])}
        for path in sorted(files)
    ]
    return sha256(
        json.dumps(inventory, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    )


def valid_path(path: str, version: int) -> bool:
    return (
        path in PAYLOAD_FILES
        or path == "source.pdf"
        or (version == 1 and path == "source")
        or (version == 2 and ASSET_PATH.fullmatch(path) is not None)
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ArtifactIntegrityError(message)


def _reference(native: Any, pointer: str) -> Any:
    _require(pointer.startswith("#/"), "native reference is not local")
    target = native
    try:
        for part in pointer[2:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            target = target[int(part)] if isinstance(target, list) else target[part]
    except (KeyError, IndexError, ValueError, TypeError):
        raise ArtifactIntegrityError("native reference is unresolved") from None
    return target


def _asset_closure(native: Any, files: Mapping[str, bytes], version: int) -> None:
    referenced: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, dict):
            for key, item in value.items():
                if key in ("$ref", "cref") and isinstance(item, str):
                    _reference(native, item)
                if key == "uri" and isinstance(item, str):
                    if item.startswith("data:"):
                        header, separator, data = item.partition(",")
                        _require(bool(separator and data), "empty native embedded resource")
                        if ";base64" in header:
                            try:
                                base64.b64decode(data, validate=True)
                            except ValueError:
                                raise ArtifactIntegrityError("invalid embedded resource") from None
                    else:
                        _require(
                            version == 2 and ASSET_PATH.fullmatch(item) is not None,
                            "unsafe native resource reference",
                        )
                        _require(item in files, "native resource is missing")
                        referenced.add(item)
                visit(item)

    visit(native)
    declared = {path for path in files if path.startswith("assets/")}
    _require(referenced == declared, "native asset inventory mismatch")


def _jsonl[R: Record](raw: bytes, model: type[R]) -> tuple[R, ...]:
    records = []
    try:
        for line in raw.splitlines():
            _require(bool(line.strip()), "empty JSONL record")
            records.append(model.model_validate(decode_json(line)))
    except ValueError:
        raise ArtifactIntegrityError("invalid content record") from None
    return tuple(records)


def _unique(values: list[Any], message: str) -> None:
    _require(len(set(values)) == len(values), message)


def _records(
    manifest: Manifest, native: dict[str, Any], files: Mapping[str, bytes]
) -> tuple[tuple[ContentBlockV2, ...], tuple[ContentTableV2, ...], tuple[ContentLayoutV2, ...]]:
    blocks = _jsonl(files["blocks.jsonl"], ContentBlockV2)
    tables = _jsonl(files["tables.jsonl"], ContentTableV2)
    layout = _jsonl(files["layout.jsonl"], ContentLayoutV2)
    _unique([b.block_id for b in blocks], "duplicate block ID")
    _unique([b.reading_order for b in blocks], "duplicate reading order")
    _unique([t.table_id for t in tables], "duplicate table ID")
    _unique([p.page for p in layout], "duplicate layout page")
    pages = {p.page: p for p in layout}
    _require(set(pages) == set(range(1, manifest.page_count + 1)), "page count mismatch")
    native_pages = native.get("pages", {})
    _require(isinstance(native_pages, dict), "invalid native pages")
    observed_pages = {int(page) for page in native_pages}
    failed_pages = manifest.extraction_quality.failed_pages
    _unique(failed_pages, "duplicate failed page")
    _require(observed_pages | set(failed_pages) == set(pages), "native page count mismatch")
    for page in layout:
        if page.geometry_state == "available":
            size = native_pages.get(str(page.page), {}).get("size", {})
            _require(
                size.get("width") == page.width and size.get("height") == page.height,
                "page dimensions disagree with native content",
            )
            transform = page.native_to_canonical
            assert transform is not None
            _require(
                all(math.isfinite(n) for n in transform)
                and transform[0] * transform[3] - transform[1] * transform[2] != 0,
                "invalid native coordinate transform",
            )
    native_blocks: dict[str, list[ContentBlockV2]] = {}
    timed: list[tuple[int, int, int]] = []
    for block in blocks:
        _reference(native, block.native_ref)
        native_blocks.setdefault(block.native_ref, []).append(block)
        anchor = block.origin_anchor
        if isinstance(anchor, NativeTextAnchor):
            _require(anchor.native_ref == block.native_ref, "anchor native reference mismatch")
        if isinstance(anchor, FigureAnchor):
            _reference(native, anchor.figure_ref)
        if isinstance(anchor, TimeSpanAnchor):
            _require(anchor.start_ms <= anchor.end_ms, "reversed transcript time")
            timed.append((block.reading_order, anchor.start_ms, anchor.end_ms))
        for region in getattr(anchor, "regions", []):
            _require(region.page in pages, "region page is missing")
            if region.char_start is not None:
                _require(
                    region.char_end is not None
                    and 0 <= region.char_start <= region.char_end <= len(block.text),
                    "character range is outside block text",
                )
            if region.bbox is not None:
                page = pages[region.page]
                box = region.bbox
                _require(
                    page.geometry_state == "available"
                    and page.width is not None
                    and page.height is not None
                    and 0 <= box.x0 <= box.x1 <= page.width
                    and 0 <= box.y0 <= box.y1 <= page.height,
                    "region geometry is outside canonical page",
                )
    for pointer, grouped in native_blocks.items():
        source = _reference(native, pointer)
        if any(b.text_origin in ("STATED", "OCR") for b in grouped):
            _require(isinstance(source, dict), "native text item is invalid")
            text = "".join(b.text for b in sorted(grouped, key=lambda b: b.reading_order))
            _require(source.get("text") == text, "block text differs from native text")
    texts = native.get("texts", [])
    _require(isinstance(texts, list), "invalid native text inventory")
    for index, item in enumerate(texts):
        _require(
            isinstance(item, dict)
            and item.get("self_ref") == f"#/texts/{index}"
            and item["self_ref"] in native_blocks,
            "native text is missing its normalized block",
        )
    timed.sort()
    _require(
        all(a[1] <= b[1] and a[2] <= b[2] for a, b in zip(timed, timed[1:], strict=False)),
        "non-monotonic transcript time",
    )
    block_ids = {b.block_id for b in blocks}
    by_table = {t.table_id: t for t in tables}
    native_tables = native.get("tables", [])
    _require(isinstance(native_tables, list), "invalid native table inventory")
    _unique([table.native_ref for table in tables], "duplicate native table projection")
    _require(
        {table.native_ref for table in tables}
        == {f"#/tables/{index}" for index in range(len(native_tables))},
        "native table is missing its normalized record",
    )
    for table in tables:
        source = _reference(native, table.native_ref)
        _require(isinstance(source, dict), "invalid native table reference")
        data = source.get("data", {})
        native_cells = data.get("table_cells", [])
        _require(
            data.get("num_rows") == table.num_rows
            and data.get("num_cols") == table.num_cols
            and len(native_cells) == len(table.cells),
            "normalized table differs from native structure",
        )
        _require(all(0 <= row < table.num_rows for row in table.header_rows), "invalid header row")
        _unique(table.header_rows, "duplicate header row")
        _unique([c.cell_id for c in table.cells], "duplicate cell ID")
        occupied: set[tuple[int, int]] = set()
        for ordinal, cell in enumerate(table.cells):
            original = native_cells[ordinal]
            _require(
                original.get("text") == cell.text
                and original.get("start_row_offset_idx") == cell.row_start
                and original.get("end_row_offset_idx") == cell.row_start + cell.row_span
                and original.get("start_col_offset_idx") == cell.col_start
                and original.get("end_col_offset_idx") == cell.col_start + cell.col_span,
                "normalized table cell differs from native content",
            )
            _require(
                cell.row_start + cell.row_span <= table.num_rows
                and cell.col_start + cell.col_span <= table.num_cols,
                "table cell is out of bounds",
            )
            covered = {
                (row, col)
                for row in range(cell.row_start, cell.row_start + cell.row_span)
                for col in range(cell.col_start, cell.col_start + cell.col_span)
            }
            _require(not occupied & covered, "table cells overlap")
            occupied.update(covered)
            _require(set(cell.block_ids) <= block_ids, "table references an absent block")
            _unique(cell.block_ids, "duplicate cell block reference")
        seen = {table.table_id}
        continuation = table.continuation_of
        while continuation is not None:
            _require(continuation in by_table and continuation not in seen, "invalid continuation")
            seen.add(continuation)
            continuation = by_table[continuation].continuation_of
    return blocks, tables, layout


def verify_bundle(
    key: ArtifactKey, manifest_bytes: bytes, files: Mapping[str, bytes]
) -> VerifiedBundle:
    try:
        manifest = parse_manifest(manifest_bytes)
    except ArtifactVersionUnsupported:
        raise
    except ValueError:
        raise ArtifactIntegrityError("invalid manifest") from None
    if (manifest.tenant_id, manifest.knowledge_base_id) != (key.tenant_id, key.knowledge_base_id):
        raise PermissionError("artifact scope mismatch")
    _require(
        manifest.artifact_id == key.artifact_id
        and manifest.artifact_contract_version == key.contract_version,
        "artifact identity mismatch",
    )
    expected = {entry.path: entry for entry in manifest.files}
    _require(len(expected) == len(manifest.files), "duplicate bundle path")
    _require(set(expected) == set(files), "bundle file inventory mismatch")
    _require(set(files) >= PAYLOAD_FILES, "native bundle is incomplete")
    for path, entry in expected.items():
        _require(valid_path(path, key.contract_version), "invalid bundle filename")
        _require(
            len(files[path]) == entry.size_bytes and sha256(files[path]) == entry.sha256,
            "bundle file hash mismatch",
        )
    _require(
        inventory_hash(files, key.contract_version) == manifest.artifact_sha256,
        "bundle hash mismatch",
    )
    reference = manifest.docling_document
    _require(
        reference.path == "docling-document.json"
        and expected[reference.path].sha256 == reference.sha256,
        "native document reference mismatch",
    )
    sources = [path for path in files if path in ("source", "source.pdf")]
    _require(len(sources) <= 1, "multiple retained sources")
    if key.contract_version == 2:
        _require(sources == ["source.pdf"], "retained source is missing")
        _require(bool(files["source.pdf"]) and manifest.page_count > 0, "empty source conversion")
    if sources:
        _require(
            sha256(files[sources[0]]) == manifest.source_sha256, "retained source hash mismatch"
        )
    try:
        native = decode_json(files[reference.path])
        _require(isinstance(native, dict), "invalid native document")
        _asset_closure(native, files, key.contract_version)
        if key.contract_version == 2:
            quality = manifest.extraction_quality
            _require(
                (quality.status == "complete" and not quality.failed_pages)
                or (quality.status == "partial" and bool(quality.failed_pages or quality.warnings)),
                "parse quality lacks diagnostics",
            )
            records = _records(manifest, native, files)
        else:
            records = ((), (), ())
    except (ValueError, TypeError, KeyError, AttributeError, IndexError):
        raise ArtifactIntegrityError("invalid native content or record") from None
    return VerifiedBundle(
        key,
        manifest,
        manifest_bytes,
        sha256(manifest_bytes),
        MappingProxyType(dict(files)),
        *records,
    )
