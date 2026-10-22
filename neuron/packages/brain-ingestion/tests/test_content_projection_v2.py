from __future__ import annotations

import runpy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from brain_content.manifest import ParserExecutionV2
from brain_content.validation import ArtifactKey, verify_bundle
from brain_ingestion.content_projection import OriginUnavailable, build_bundle_v2
from brain_ingestion.docling_adapter import DoclingAdapter
from brain_ingestion.item_provenance import ItemProvenance
from brain_interpretation.parsed_content import BlockOriginInput, ParseResult, ProducerIdentity
from docling_core.types.doc import DoclingDocument, Size, TableCell, TableData


@pytest.fixture(scope="module")
def observed_documents(tmp_path_factory):
    helper = runpy.run_path(str(Path(__file__).parent / "spikes/test_item_provenance.py"))
    fixtures = helper["create_fixtures"](tmp_path_factory.mktemp("v2-fixtures"))
    return {
        name: (DoclingAdapter(capture_provenance=True).parse(path), path.read_bytes())
        for name, path in fixtures.items()
    }


def build(parsed, source, **overrides):
    values = {
        "tenant_id": uuid4(),
        "knowledge_base_id": uuid4(),
        "document_id": uuid4(),
        "version_id": uuid4(),
        "artifact_id": uuid4(),
        "source_bytes": source,
        "recipe_sha256": "a" * 64,
        "execution": ParserExecutionV2(
            parser_package_version="2.126.0",
            parser_name="docling",
            projection_version="content-projection-v2.0",
            configuration_hash="b" * 64,
            environment_digest="synthetic-development",
            model_artifact_digests=[],
        ),
        "provenance": parsed.provenance,
        "retained_assets": {},
        **overrides,
    }
    return build_bundle_v2(parsed, **values)


def test_empty_conversion_never_becomes_complete_content():
    document = DoclingDocument(name="empty-conversion")
    document.add_page(page_no=1, size=Size(width=612, height=792))
    parsed = ParseResult(document, 1, [], 0, "complete", [])
    with pytest.raises(ValueError, match="CONTENT_CONTRACT_INVALID"):
        build(parsed, b"%PDF-1.4 empty synthetic fixture")


@pytest.mark.parametrize(
    "fixture,expected",
    [
        ("native", {"STATED"}),
        ("scanned", {"OCR"}),
        ("mixed", {"STATED", "OCR"}),
    ],
)
def test_actual_converter_to_v2_bundle_preserves_observed_origins(
    observed_documents, fixture, expected
):
    parsed, source = observed_documents[fixture]
    assert not parsed.origin_unavailable
    manifest, files = build(parsed, source)
    key = ArtifactKey(manifest.artifact_id, manifest.tenant_id, manifest.knowledge_base_id, 2)
    verified = verify_bundle(key, manifest.model_dump_json().encode(), files)
    assert {block.text_origin for block in verified.blocks} == expected
    assert len({block.block_id for block in verified.blocks}) == len(parsed.document.texts)
    assert all(block.producer.engine and block.producer.engine_version for block in verified.blocks)
    assert files["source.pdf"] == source
    assert manifest.artifact_contract_version == 2
    assert "document_date" not in manifest.model_dump()


def test_missing_origin_requests_document_fallback_without_fabricating_stated(observed_documents):
    parsed, source = observed_documents["native"]
    provenance = dict(parsed.provenance)
    missing = next(iter(provenance))
    provenance.pop(missing)
    with pytest.raises(OriginUnavailable) as caught:
        build(parsed, source, provenance=provenance)
    assert missing in caught.value.references


def test_missing_producer_fails_instead_of_using_unknown_origin_fallback(observed_documents):
    parsed, source = observed_documents["native"]
    provenance = dict(parsed.provenance)
    ref = next(iter(provenance))
    original = provenance[ref][0]
    provenance[ref] = (replace(original, producer=ProducerIdentity("", "", None, None)),)
    with pytest.raises(ValueError) as caught:
        build(parsed, source, provenance=provenance)
    assert not isinstance(caught.value, OriginUnavailable)


def test_failed_parse_and_asset_payload_override_never_publish(observed_documents):
    parsed, source = observed_documents["native"]
    with pytest.raises(ValueError):
        build(replace(parsed, status="failed"), source)
    with pytest.raises(ValueError):
        build(parsed, source, retained_assets={"source.pdf": b"replacement"})


def test_missing_rotation_retains_coarse_geometry_without_zero_height(observed_documents):
    parsed, source = observed_documents["native"]
    manifest, files = build(replace(parsed, page_rotations={}), source)
    key = ArtifactKey(manifest.artifact_id, manifest.tenant_id, manifest.knowledge_base_id, 2)
    bundle = verify_bundle(key, manifest.model_dump_json().encode(), files)
    assert bundle.layout[0].geometry_state == "unavailable"
    assert bundle.layout[0].height is None
    assert all(
        region.bbox is None for block in bundle.blocks for region in block.origin_anchor.regions
    )


def test_merged_header_and_repeated_amounts_keep_distinct_cell_and_block_ids():
    document = DoclingDocument(name="synthetic-controlled-table")
    document.add_page(page_no=1, size=Size(width=612, height=792))
    data = TableData(
        num_rows=2,
        num_cols=2,
        table_cells=[
            TableCell(
                text="LIMITS",
                start_row_offset_idx=0,
                end_row_offset_idx=1,
                start_col_offset_idx=0,
                end_col_offset_idx=2,
                col_span=2,
                column_header=True,
            ),
            TableCell(
                text="$100",
                start_row_offset_idx=1,
                end_row_offset_idx=2,
                start_col_offset_idx=0,
                end_col_offset_idx=1,
            ),
            TableCell(
                text="$100",
                start_row_offset_idx=1,
                end_row_offset_idx=2,
                start_col_offset_idx=1,
                end_col_offset_idx=2,
            ),
        ],
    )
    table = document.add_table(data=data)
    provenance = {}
    for ordinal, cell in enumerate(data.table_cells):
        ref = f"{table.self_ref}/data/table_cells/{ordinal}"
        provenance[ref] = (
            BlockOriginInput(
                ref,
                cell.text,
                "STATED",
                ProducerIdentity("controlled-fixture", "1", None, None),
                {"kind": "unresolved", "reason": "synthetic contract fixture"},
                None,
            ),
        )
    parsed = ParseResult(
        document,
        1,
        [],
        0,
        "complete",
        [],
        projection_version=2,
        provenance=provenance,
        page_rotations={1: 0},
    )
    manifest, files = build(parsed, b"%PDF synthetic table fixture")
    key = ArtifactKey(manifest.artifact_id, manifest.tenant_id, manifest.knowledge_base_id, 2)
    bundle = verify_bundle(key, manifest.model_dump_json().encode(), files)
    stored = bundle.tables[0]
    assert stored.header_rows == [0]
    assert stored.cells[0].col_span == 2
    assert stored.cells[1].text == stored.cells[2].text == "$100"
    assert stored.cells[1].cell_id != stored.cells[2].cell_id
    assert stored.cells[1].block_ids != stored.cells[2].block_ids
    assert stored.continuation_of is None


def test_false_ocr_flag_without_positive_backend_receipt_is_unavailable():
    observer = ItemProvenance.__new__(ItemProvenance)
    observer.native, observer.ocr, observer.items = {}, {}, {}
    item = SimpleNamespace(self_ref="#/texts/0", text="unattributed", prov=[])
    cell = SimpleNamespace(text=item.text, from_ocr=False)
    element = SimpleNamespace(page_no=1, cluster=SimpleNamespace(cells=[cell]))
    observer._record(item, element)
    provenance, unavailable = observer.project(SimpleNamespace(texts=[item]))
    assert provenance == {}
    assert unavailable == (item.self_ref,)
