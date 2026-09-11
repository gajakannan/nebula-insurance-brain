from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import UTC, datetime
from importlib.metadata import version as pkg_version
from pathlib import Path
from uuid import UUID

from brain_content.manifest import (
    ArtifactFile,
    ArtifactManifest,
    DoclingDocumentRef,
    ExecutionRecord,
    ExtractionQuality,
)
from docling_core.types.doc.base import BoundingBox, CoordOrigin

from brain_ingestion.docling_adapter import ParseResult


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _to_top_left_bbox(bbox: BoundingBox, page_height: float) -> dict[str, float]:
    """Docling's native `BoundingBox` may be `BOTTOMLEFT`-origin; the artifact contract
    declares `coordinate_origin: top_left` (F0001-S0003 manifest field), so every
    bounding box is normalized here, once, at write time. The caller attaches `page`
    from the enclosing `ProvenanceItem` — `BoundingBox` itself carries no page number."""
    if bbox.coord_origin == CoordOrigin.BOTTOMLEFT:
        y0 = page_height - bbox.t
        y1 = page_height - bbox.b
    else:
        y0, y1 = bbox.t, bbox.b
    return {"x0": bbox.l, "y0": y0, "x1": bbox.r, "y1": y1}


def _environment_digest() -> str:
    payload = (
        f"python={sys.version.split()[0]};"
        f"platform={platform.platform()};"
        f"docling={pkg_version('docling')}"
    )
    return _sha256(payload.encode("utf-8"))


def build_bundle(
    parse_result: ParseResult,
    *,
    tenant_id: UUID,
    knowledge_base_id: UUID,
    document_id: UUID,
    version_id: UUID,
    artifact_id: UUID,
    source_sha256: str,
    configuration_hash: str,
    source_bytes: bytes | None = None,
    source_filename: str | None = None,
) -> tuple[ArtifactManifest, dict[str, bytes]]:
    """Turn a `ParseResult` into the six-file bundle + manifest (F0001-S0003
    acceptance criterion 1). `manifest.json` itself is not included in the returned
    file map — `ContentArtifactStore.put_bundle` writes it last as the completion
    marker (ADR-0059).

    `source_bytes`/`source_filename` retain the original source alongside the six
    derived files, as `source{ext}` — ADR-0059's stated purpose ("Nebula must retain
    original source bytes") that F0001-S0004's Review Panel depends on to render the
    page a reviewer is correcting. Optional and additive: omitting it reproduces
    F0001-S0003's original six-file bundle unchanged."""
    doc = parse_result.document
    page_heights = {page_no: item.size.height for page_no, item in doc.pages.items()}

    docling_document_bytes = doc.model_dump_json(indent=2).encode("utf-8")
    normalized_md_bytes = doc.export_to_markdown().encode("utf-8")

    blocks: list[dict] = []
    for index, text_item in enumerate(doc.texts):
        for prov in text_item.prov:
            page_height = page_heights.get(prov.page_no, 0.0)
            bbox = _to_top_left_bbox(prov.bbox, page_height)
            bbox["page"] = prov.page_no
            blocks.append(
                {
                    "block_id": f"text-{index}",
                    "page": prov.page_no,
                    "text": text_item.text,
                    "bbox": bbox,
                    "char_start": prov.charspan[0],
                    "char_end": prov.charspan[1],
                }
            )
    blocks_jsonl_bytes = (
        "\n".join(json.dumps(b) for b in blocks) + ("\n" if blocks else "")
    ).encode("utf-8")

    tables: list[dict] = []
    for index, table_item in enumerate(doc.tables):
        for prov in table_item.prov:
            tables.append(
                {
                    "table_id": f"table-{index}",
                    "page": prov.page_no,
                    "num_rows": table_item.data.num_rows if table_item.data else None,
                    "num_cols": table_item.data.num_cols if table_item.data else None,
                }
            )
    tables_jsonl_bytes = (
        "\n".join(json.dumps(t) for t in tables) + ("\n" if tables else "")
    ).encode("utf-8")

    layout = [
        {"page": page_no, "width": item.size.width, "height": item.size.height}
        for page_no, item in sorted(doc.pages.items())
    ]
    layout_jsonl_bytes = ("\n".join(json.dumps(entry) for entry in layout) + "\n").encode("utf-8")

    files = {
        "docling-document.json": docling_document_bytes,
        "normalized.md": normalized_md_bytes,
        "blocks.jsonl": blocks_jsonl_bytes,
        "tables.jsonl": tables_jsonl_bytes,
        "layout.jsonl": layout_jsonl_bytes,
    }
    if source_bytes is not None:
        suffix = Path(source_filename).suffix if source_filename else ""
        files[f"source{suffix}"] = source_bytes
    artifact_files = [
        ArtifactFile(path=path, sha256=_sha256(data), size_bytes=len(data))
        for path, data in sorted(files.items())
    ]
    artifact_sha256 = _sha256(
        "".join(f.sha256 for f in sorted(artifact_files, key=lambda f: f.path)).encode("ascii")
    )

    manifest = ArtifactManifest(
        artifact_contract_version=1,
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
        document_id=document_id,
        version_id=version_id,
        artifact_id=artifact_id,
        source_sha256=source_sha256,
        artifact_sha256=artifact_sha256,
        docling_document=DoclingDocumentRef(
            path="docling-document.json",
            schema_version=doc.version,
            sha256=_sha256(docling_document_bytes),
        ),
        files=artifact_files,
        execution=ExecutionRecord(
            parser_package_version=f"docling=={pkg_version('docling')}",
            model_artifact_digests=[],
            configuration_hash=configuration_hash,
            environment_digest=_environment_digest(),
        ),
        extraction_quality=ExtractionQuality(
            status=parse_result.status,
            failed_pages=parse_result.failed_pages,
            warnings=parse_result.warnings,
        ),
        page_count=parse_result.page_count,
        created_at=datetime.now(UTC),
    )
    return manifest, files
