"""V2 projection over native hierarchy and observed per-item producer receipts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from brain_content.manifest import (
    ArtifactFile,
    ArtifactManifestV2,
    DoclingDocumentRef,
    ExtractionQuality,
    ParserExecutionV2,
)
from brain_content.records import ContentBlockV2, ContentLayoutV2, ContentTableV2
from brain_content.validation import ArtifactKey, inventory_hash, sha256, verify_bundle
from brain_interpretation.parsed_content import BlockOriginInput, ParseResult
from docling_core.types.doc.document import DoclingDocument

PROJECTION_VERSION = "content-projection-v2.0"


class OriginUnavailable(ValueError):
    code = "ORIGIN_UNAVAILABLE"

    def __init__(self, references: tuple[str, ...]):
        super().__init__(self.code)
        self.references = references


def _resolve(native: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError("CONTENT_CONTRACT_INVALID")
    value: Any = native
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    if not isinstance(value, dict):
        raise ValueError("CONTENT_CONTRACT_INVALID")
    return value


def _jsonl(records: list[Any]) -> bytes:
    return b"".join(record.model_dump_json().encode() + b"\n" for record in records)


def build_bundle_v2(
    parsed: ParseResult[DoclingDocument],
    *,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    document_id: UUID,
    version_id: UUID,
    artifact_id: UUID,
    source_bytes: bytes,
    recipe_sha256: str,
    execution: ParserExecutionV2,
    provenance: Mapping[str, tuple[BlockOriginInput, ...]],
    retained_assets: Mapping[str, bytes],
) -> tuple[ArtifactManifestV2, dict[str, bytes]]:
    if parsed.status == "failed" or not source_bytes or parsed.page_count < 1:
        raise ValueError("CONTENT_CONTRACT_INVALID")
    if parsed.origin_unavailable:
        raise OriginUnavailable(parsed.origin_unavailable)
    native_bytes = parsed.document.model_dump_json(indent=2, by_alias=True).encode()
    native = json.loads(native_bytes)
    blocks: list[ContentBlockV2] = []
    tables: list[ContentTableV2] = []
    layout: list[ContentLayoutV2] = []
    seen: set[str] = set()
    unavailable: list[str] = []

    def add_blocks(ref: str, item: dict[str, Any], section_path: list[str]) -> list[str]:
        origins = provenance.get(ref)
        if not origins:
            unavailable.append(ref)
            return []
        if any(origin.native_ref != ref for origin in origins):
            raise ValueError("CONTENT_CONTRACT_INVALID")
        if "".join(origin.text for origin in origins) != item["text"]:
            raise ValueError("CONTENT_CONTRACT_INVALID")
        ids = []
        for index, origin in enumerate(origins):
            block_id = ref if len(origins) == 1 else f"{ref}:{origin.text_origin}:{index}"
            block = ContentBlockV2.model_validate(
                {
                    "record_type": "block",
                    "contract_version": 2,
                    "block_id": block_id,
                    "native_ref": ref,
                    "reading_order": len(blocks),
                    "section_path": section_path,
                    "text": origin.text,
                    "text_origin": origin.text_origin,
                    "producer": asdict(origin.producer),
                    "origin_anchor": origin.origin_anchor,
                    "confidence": origin.confidence,
                }
            )
            blocks.append(block)
            ids.append(block_id)
        return ids

    def walk(ref: str, path: list[str]) -> None:
        if ref in seen:
            raise ValueError("CONTENT_CONTRACT_INVALID")
        seen.add(ref)
        item = _resolve(native, ref)
        if ref.startswith("#/texts/"):
            add_blocks(ref, item, path)
        if ref.startswith("#/tables/"):
            data = item["data"]
            cells = []
            headers: set[int] = set()
            for ordinal, cell in enumerate(data["table_cells"]):
                cell_ref = f"{ref}/data/table_cells/{ordinal}"
                ids = add_blocks(cell_ref, cell, [*path, ref]) if cell["text"] else []
                if cell.get("column_header"):
                    headers.update(range(cell["start_row_offset_idx"], cell["end_row_offset_idx"]))
                cells.append(
                    {
                        "cell_id": f"{ref}:cell:{ordinal}",
                        "row_start": cell["start_row_offset_idx"],
                        "col_start": cell["start_col_offset_idx"],
                        "row_span": cell["end_row_offset_idx"] - cell["start_row_offset_idx"],
                        "col_span": cell["end_col_offset_idx"] - cell["start_col_offset_idx"],
                        "text": cell["text"],
                        "block_ids": ids,
                    }
                )
            tables.append(
                ContentTableV2.model_validate(
                    {
                        "record_type": "table",
                        "contract_version": 2,
                        "table_id": ref,
                        "native_ref": ref,
                        "num_rows": data["num_rows"],
                        "num_cols": data["num_cols"],
                        "header_rows": sorted(headers),
                        "continuation_of": item.get("continuation_of"),
                        "cells": cells,
                    }
                )
            )
        child_path = (
            [*path, ref]
            if ref.startswith("#/groups/") or item.get("label") == "section_header"
            else path
        )
        for child in item.get("children", []):
            walk(child["$ref"], child_path)

    # The actual document forest determines order and ancestry. Never append
    # unvisited texts by array position: an incomplete hierarchy is a failure.
    for root in ("body", "furniture"):
        if root in native:
            walk(f"#/{root}", [])
    for index in range(len(native.get("texts", []))):
        if f"#/texts/{index}" not in seen:
            raise ValueError("CONTENT_CONTRACT_INVALID")
    if unavailable:
        raise OriginUnavailable(tuple(unavailable))
    if not blocks and not tables:
        raise ValueError("CONTENT_CONTRACT_INVALID")
    for number in range(1, parsed.page_count + 1):
        page = parsed.document.pages.get(number)
        rotation = parsed.page_rotations.get(number)
        available = page is not None and rotation in (0, 90, 180, 270)
        width = page.size.width if page is not None else None
        height = page.size.height if page is not None else None
        available = (
            available and width is not None and height is not None and width > 0 and height > 0
        )
        layout.append(
            ContentLayoutV2.model_validate(
                {
                    "record_type": "layout",
                    "contract_version": 2,
                    "page": number,
                    "geometry_state": "available" if available else "unavailable",
                    "width": width if available else None,
                    "height": height if available else None,
                    "rotation_degrees": rotation if available else None,
                    "native_to_canonical": [1, 0, 0, -1, 0, height] if available else None,
                    "unavailable_reason": None
                    if available
                    else "native page geometry is unavailable",
                }
            )
        )
    if any(page.geometry_state == "unavailable" for page in layout):
        unavailable_pages = {p.page for p in layout if p.geometry_state == "unavailable"}
        adjusted = []
        for block in blocks:
            wire = block.model_dump(mode="json")
            for region in wire["origin_anchor"].get("regions", []):
                if region["page"] in unavailable_pages:
                    region["bbox"] = None
            adjusted.append(ContentBlockV2.model_validate(wire))
        blocks = adjusted
    files = {
        "docling-document.json": native_bytes,
        "normalized.md": parsed.document.export_to_markdown().encode(),
        "blocks.jsonl": _jsonl(blocks),
        "tables.jsonl": _jsonl(tables),
        "layout.jsonl": _jsonl(layout),
        "source.pdf": source_bytes,
        **retained_assets,
    }
    # Assets cannot replace any required parse payload, including the source.
    if set(retained_assets) & {
        "docling-document.json",
        "normalized.md",
        "blocks.jsonl",
        "tables.jsonl",
        "layout.jsonl",
        "source.pdf",
        "manifest.json",
    }:
        raise ValueError("CONTENT_CONTRACT_INVALID")
    manifest = ArtifactManifestV2(
        artifact_contract_version=2,
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
        document_id=document_id,
        version_id=version_id,
        artifact_id=artifact_id,
        source_sha256=sha256(source_bytes),
        artifact_sha256=inventory_hash(files, 2),
        docling_document=DoclingDocumentRef(
            path="docling-document.json",
            schema_version=parsed.document.version,
            sha256=sha256(native_bytes),
        ),
        files=[
            ArtifactFile(path=p, sha256=sha256(b), size_bytes=len(b))
            for p, b in sorted(files.items())
        ],
        execution=execution,
        extraction_quality=ExtractionQuality(
            status=parsed.status, failed_pages=parsed.failed_pages, warnings=parsed.warnings
        ),
        page_count=parsed.page_count,
        coordinate_origin="top_left",
        offset_encoding="unicode_code_points",
        created_at=datetime.now(UTC),
        source_file="source.pdf",
        recipe_sha256=recipe_sha256,
        bundle_hash_algorithm="sha256-file-inventory-v2",
        record_contract_version=2,
        page_number_base=1,
        coordinate_units="pdf_points",
        text_normalization_version="identity-unicode-v1",
    )
    verify_bundle(
        ArtifactKey(artifact_id, tenant_id, knowledge_base_id, 2),
        manifest.model_dump_json().encode(),
        files,
    )
    return manifest, files
