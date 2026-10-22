from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from importlib.resources import files as package_files
from pathlib import Path
from uuid import uuid4

import pytest
from brain_content.config import LocalObjectStoreConfig
from brain_content.manifest import ArtifactVersionUnsupported, parse_manifest
from brain_content.object_store import LocalFilesystemObjectStore, ObjectNotFoundError
from brain_content.records import ContentBlockV2, ContentLayoutV2, ContentTableV2
from brain_content.store import LocalContentArtifactStore
from brain_content.validation import (
    ArtifactConflict,
    ArtifactIntegrityError,
    ArtifactKey,
    inventory_hash,
    sha256,
    verify_bundle,
)
from brain_content.verified_store import VerifiedBundleStore


def bundle_fixture():
    identifiers = {
        key: str(uuid4())
        for key in ("tenant_id", "knowledge_base_id", "document_id", "version_id", "artifact_id")
    }
    native = {
        "texts": [{"self_ref": "#/texts/0", "text": "A😀B"}],
        "pages": {"1": {"size": {"width": 612, "height": 792}}},
        "tables": [],
    }
    block = {
        "record_type": "block",
        "contract_version": 2,
        "block_id": "#/texts/0",
        "native_ref": "#/texts/0",
        "reading_order": 0,
        "section_path": [],
        "text": "A😀B",
        "text_origin": "STATED",
        "confidence": None,
        "producer": {
            "engine": "synthetic-parser",
            "engine_version": "1",
            "model": None,
            "model_version": None,
        },
        "origin_anchor": {
            "kind": "native_text",
            "native_ref": "#/texts/0",
            "regions": [
                {
                    "page": 1,
                    "bbox": {"x0": 10, "y0": 10, "x1": 100, "y1": 30},
                    "char_start": 0,
                    "char_end": 3,
                }
            ],
        },
    }
    layout = {
        "record_type": "layout",
        "contract_version": 2,
        "page": 1,
        "geometry_state": "available",
        "width": 612,
        "height": 792,
        "rotation_degrees": 0,
        "native_to_canonical": [1, 0, 0, 1, 0, 0],
        "unavailable_reason": None,
    }
    files = {
        "docling-document.json": json.dumps(native).encode(),
        "normalized.md": "A😀B".encode(),
        "blocks.jsonl": json.dumps(block).encode() + b"\n",
        "tables.jsonl": b"",
        "layout.jsonl": json.dumps(layout).encode() + b"\n",
        "source.pdf": b"%PDF-1.4 synthetic development fixture",
    }
    manifest = {
        **identifiers,
        "artifact_contract_version": 2,
        "source_sha256": sha256(files["source.pdf"]),
        "artifact_sha256": "0" * 64,
        "docling_document": {
            "path": "docling-document.json",
            "schema_version": "synthetic-1",
            "sha256": "0" * 64,
        },
        "files": [],
        "execution": {
            "parser_package_version": "synthetic-1",
            "model_artifact_digests": [],
            "configuration_hash": "a" * 64,
            "environment_digest": "synthetic",
            "parser_name": "docling",
            "projection_version": "synthetic-1",
        },
        "extraction_quality": {"status": "complete", "failed_pages": [], "warnings": []},
        "page_count": 1,
        "coordinate_origin": "top_left",
        "offset_encoding": "unicode_code_points",
        "created_at": datetime.now(UTC).isoformat(),
        "source_file": "source.pdf",
        "recipe_sha256": "b" * 64,
        "bundle_hash_algorithm": "sha256-file-inventory-v2",
        "record_contract_version": 2,
        "page_number_base": 1,
        "coordinate_units": "pdf_points",
        "text_normalization_version": "identity-unicode-v1",
    }
    return manifest, files


def seal(manifest, files):
    manifest = copy.deepcopy(manifest)
    manifest["files"] = [
        {"path": path, "sha256": sha256(raw), "size_bytes": len(raw)} for path, raw in files.items()
    ]
    manifest["artifact_sha256"] = inventory_hash(files, manifest["artifact_contract_version"])
    manifest["docling_document"]["sha256"] = sha256(files["docling-document.json"])
    model = parse_manifest(json.dumps(manifest).encode())
    key = ArtifactKey(
        model.artifact_id, model.tenant_id, model.knowledge_base_id, model.artifact_contract_version
    )
    return key, json.dumps(manifest, indent=4).encode(), files


@pytest.fixture
def v2():
    return bundle_fixture()


def test_round_trip_keeps_exact_marker_and_multiple_regions(v2, tmp_path):
    manifest, files = v2
    block = json.loads(files["blocks.jsonl"])
    block["origin_anchor"]["regions"].append(
        {"page": 1, "bbox": None, "char_start": None, "char_end": None}
    )
    files["blocks.jsonl"] = json.dumps(block).encode()
    key, raw, files = seal(manifest, files)
    store = VerifiedBundleStore(
        LocalFilesystemObjectStore(LocalObjectStoreConfig("filesystem", tmp_path, True))
    )
    result = store.publish(key, raw, files)
    assert result.manifest_bytes == raw
    assert len(result.blocks) == 1
    assert len(result.blocks[0].origin_anchor.regions) == 2
    newer = json.loads(raw)
    newer["created_at"] = "2026-10-18T12:00:00Z"
    assert store.publish(key, json.dumps(newer).encode(), files).manifest_bytes == raw
    assert store.load_verified(key).manifest_sha256 == sha256(raw)
    files["normalized.md"] = b"different but internally consistent"
    _, changed_raw, changed = seal(manifest, files)
    with pytest.raises(ArtifactConflict):
        store.publish(key, changed_raw, changed)


@pytest.mark.parametrize("fault", ["hash", "missing", "extra", "source", "aggregate", "owner"])
def test_integrity_failures_are_not_cache_misses(v2, fault):
    manifest, files = v2
    key, raw, files = seal(manifest, files)
    if fault == "hash":
        files["blocks.jsonl"] += b"tamper"
    elif fault == "missing":
        files.pop("normalized.md")
    elif fault == "extra":
        files["undeclared.bin"] = b"x"
    elif fault == "owner":
        key = ArtifactKey(key.artifact_id, uuid4(), key.knowledge_base_id, 2)
    else:
        value = json.loads(raw)
        value["source_sha256" if fault == "source" else "artifact_sha256"] = "0" * 64
        raw = json.dumps(value).encode()
    with pytest.raises(PermissionError if fault == "owner" else ArtifactIntegrityError):
        verify_bundle(key, raw, files)


@pytest.mark.parametrize(
    "fault",
    [
        "unicode",
        "page",
        "bbox",
        "native_ref",
        "duplicate",
        "producer",
        "origin",
        "layout",
        "blank",
        "time",
    ],
)
def test_hashed_but_semantically_invalid_records_are_rejected(v2, fault):
    manifest, files = v2
    block = json.loads(files["blocks.jsonl"])
    if fault == "unicode":
        block["origin_anchor"]["regions"][0]["char_end"] = 4
    elif fault == "page":
        block["origin_anchor"]["regions"][0]["page"] = 2
    elif fault == "bbox":
        block["origin_anchor"]["regions"][0]["bbox"]["x1"] = 613
    elif fault == "native_ref":
        block["native_ref"] = "#/texts/99"
    elif fault == "producer":
        block["producer"]["engine_version"] = ""
    elif fault == "origin":
        block["text_origin"] = "OCR"
    elif fault == "time":
        block["text_origin"] = "TRANSCRIBED"
        block["origin_anchor"] = {
            "kind": "time_span",
            "start_ms": 20,
            "end_ms": 10,
            "speaker": None,
        }
    files["blocks.jsonl"] = json.dumps(block).encode()
    if fault == "duplicate":
        files["blocks.jsonl"] += b"\n" + json.dumps(block).encode()
    if fault == "layout":
        files["layout.jsonl"] = b""
    if fault == "blank":
        files["blocks.jsonl"] += b"\n\n"
    key, raw, files = seal(manifest, files)
    with pytest.raises(ArtifactIntegrityError):
        verify_bundle(key, raw, files)


@pytest.mark.parametrize("fault", ["valid", "bounds", "overlap", "header", "reference", "cycle"])
def test_table_relations_and_merged_cell_coverage(v2, fault):
    manifest, files = v2
    native = json.loads(files["docling-document.json"])
    cell = {
        "cell_id": "cell-0",
        "row_start": 0,
        "col_start": 0,
        "row_span": 2,
        "col_span": 1,
        "text": "A😀B",
        "block_ids": ["#/texts/0"],
    }
    table = {
        "record_type": "table",
        "contract_version": 2,
        "table_id": "t0",
        "native_ref": "#/tables/0",
        "num_rows": 2,
        "num_cols": 1,
        "header_rows": [],
        "continuation_of": None,
        "cells": [cell],
    }
    if fault == "bounds":
        cell["row_span"] = 3
    elif fault == "overlap":
        table["cells"].append({**cell, "cell_id": "cell-1"})
    elif fault == "header":
        table["header_rows"] = [2]
    elif fault == "reference":
        cell["block_ids"] = ["absent"]
    elif fault == "cycle":
        table["continuation_of"] = "t0"
    native["tables"] = [
        {
            "data": {
                "num_rows": 2,
                "num_cols": 1,
                "table_cells": [
                    {
                        "text": c["text"],
                        "start_row_offset_idx": c["row_start"],
                        "end_row_offset_idx": c["row_start"] + c["row_span"],
                        "start_col_offset_idx": c["col_start"],
                        "end_col_offset_idx": c["col_start"] + c["col_span"],
                    }
                    for c in table["cells"]
                ],
            }
        }
    ]
    files["docling-document.json"] = json.dumps(native).encode()
    files["tables.jsonl"] = json.dumps(table).encode()
    key, raw, files = seal(manifest, files)
    if fault == "valid":
        result = verify_bundle(key, raw, files)
        assert result.tables[0].cells[0].row_span == 2
        assert result.tables[0].cells[0].block_ids == [result.blocks[0].block_id]
        return
    with pytest.raises(ArtifactIntegrityError):
        verify_bundle(key, raw, files)


@pytest.mark.parametrize(
    "uri",
    ["https://example.invalid/a.png", "../secret.png", "assets/missing.png", "file:///etc/passwd"],
)
def test_native_resource_closure_prevents_external_or_missing_assets(v2, uri):
    manifest, files = v2
    native = json.loads(files["docling-document.json"])
    native["pictures"] = [{"image": {"uri": uri}}]
    files["docling-document.json"] = json.dumps(native).encode()
    key, raw, files = seal(manifest, files)
    with pytest.raises(ArtifactIntegrityError):
        verify_bundle(key, raw, files)


def test_legacy_no_source_remains_readable_without_fabricated_v2_records(v2):
    manifest, files = v2
    for name in (
        "source_file",
        "recipe_sha256",
        "bundle_hash_algorithm",
        "record_contract_version",
        "page_number_base",
        "coordinate_units",
        "text_normalization_version",
    ):
        manifest.pop(name)
    manifest["execution"].pop("parser_name")
    manifest["execution"].pop("projection_version")
    manifest["artifact_contract_version"] = 1
    files.pop("source.pdf")
    files["blocks.jsonl"] = b'{"block_id":"duplicate"}\n{"block_id":"duplicate"}\n'
    key, raw, files = seal(manifest, files)
    verified = verify_bundle(key, raw, files)
    assert verified.manifest_bytes == raw
    assert not verified.blocks and not verified.tables
    assert "source.pdf" not in verified.files


def test_unknown_version_and_duplicate_json_properties_fail_explicitly(v2):
    key, raw, files = seal(*v2)
    value = json.loads(raw)
    value["artifact_contract_version"] = 99
    with pytest.raises(ArtifactVersionUnsupported):
        verify_bundle(key, json.dumps(value).encode(), files)
    duplicate = raw[:-1] + b', "artifact_contract_version": 2}'
    with pytest.raises(ArtifactIntegrityError):
        verify_bundle(key, duplicate, files)


def test_packaged_runtime_contracts_match_the_authored_product_contracts_exactly():
    root = Path(__file__).resolve().parents[4]
    for name in (
        "content-artifact-manifest.schema.json",
        "content-artifact-manifest-v2.schema.json",
        "content-records-v2.schema.json",
        "document-date-record.schema.json",
        "interpretation-output-manifest.schema.json",
    ):
        assert (
            package_files("brain_content").joinpath("schemas", name).read_bytes()
            == (root / "planning-mds/schemas" / name).read_bytes()
        )


def test_every_record_and_manifest_example_matches_its_runtime_model():
    product = next(p for p in Path(__file__).parents if (p / "planning-mds").is_dir())
    examples = json.loads(
        (
            product / "planning-mds/features/F0004-content-artifact-model/contract-examples.json"
        ).read_text()
    )
    for case in examples["cases"]:
        payload = case["payload"]
        if case["schema"] == "content-artifact-manifest-read.schema.json":

            def validate(p):
                return parse_manifest(json.dumps(p).encode())
        elif case["schema"] == "content-records-v2.schema.json":
            model = {"block": ContentBlockV2, "table": ContentTableV2, "layout": ContentLayoutV2}[
                payload["record_type"]
            ]
            validate = model.model_validate
        else:
            continue
        if case["expected_valid"]:
            validate(payload)
        else:
            with pytest.raises(ValueError):
                validate(payload)


@pytest.mark.asyncio
async def test_async_and_sync_adapters_observe_identical_verified_bytes(v2, tmp_path):
    key, raw, files = seal(*v2)
    objects = LocalFilesystemObjectStore(LocalObjectStoreConfig("filesystem", tmp_path, True))
    sync = VerifiedBundleStore(objects)
    asynchronous = LocalContentArtifactStore(objects)
    sync.publish(key, raw, files)
    result = await asynchronous.load_verified(key)
    assert result == sync.load_verified(key)
    objects.delete(f"{key.prefix}/normalized.md")
    with pytest.raises(ArtifactIntegrityError):
        await asynchronous.load_verified(key)
    with pytest.raises(ObjectNotFoundError):
        sync.load_verified(ArtifactKey(key.artifact_id, uuid4(), key.knowledge_base_id, 2))


def test_undeclared_objects_and_symlinks_never_form_a_verified_bundle(v2, tmp_path):
    key, raw, files = seal(*v2)
    objects = LocalFilesystemObjectStore(LocalObjectStoreConfig("filesystem", tmp_path, True))
    store = VerifiedBundleStore(objects)
    store.publish(key, raw, files)
    objects.create_exclusive(f"{key.prefix}/undeclared.bin", b"extra")
    with pytest.raises(ArtifactIntegrityError):
        store.load_verified(key)
    objects.delete(f"{key.prefix}/undeclared.bin")
    objects.delete(f"{key.prefix}/normalized.md")
    (tmp_path / key.prefix / "normalized.md").symlink_to(tmp_path / key.prefix / "source.pdf")
    with pytest.raises(ArtifactIntegrityError):
        store.load_verified(key)


def test_unavailable_geometry_is_explicit_and_never_zero_height(v2):
    manifest, files = v2
    block = json.loads(files["blocks.jsonl"])
    block["origin_anchor"]["regions"][0]["bbox"] = None
    files["blocks.jsonl"] = json.dumps(block).encode()
    layout = json.loads(files["layout.jsonl"])
    layout.update(
        geometry_state="unavailable",
        width=None,
        height=None,
        rotation_degrees=None,
        native_to_canonical=None,
        unavailable_reason="no observed transform",
    )
    files["layout.jsonl"] = json.dumps(layout).encode()
    key, raw, files = seal(manifest, files)
    assert verify_bundle(key, raw, files).layout[0].height is None
    layout["height"] = 0
    files["layout.jsonl"] = json.dumps(layout).encode()
    key, raw, files = seal(manifest, files)
    with pytest.raises(ArtifactIntegrityError):
        verify_bundle(key, raw, files)
