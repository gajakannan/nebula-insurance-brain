"""Real pinned Graph consumers over retained v1/v2 bytes, recorded responses."""

from __future__ import annotations

import json
import runpy
from pathlib import Path
from threading import BoundedSemaphore, Event
from unittest.mock import patch
from uuid import uuid4

import httpx
import pytest
from brain_content.checkpoints import CheckpointStore
from brain_content.manifest import ParserExecutionV2
from brain_content.outputs import RunManifestV2
from brain_content.validation import ArtifactKey
from brain_extraction.graph_evidence import ground_value
from brain_extraction.graph_interpretation import GraphInterpretationService
from brain_extraction.profiles import load_profile
from brain_extraction.vllm_graph_client import VllmGraphClient
from brain_ingestion.content_projection import build_bundle_v2
from brain_ingestion.docling_adapter import DoclingAdapter
from brain_interpretation.parsed_content import BlockOriginInput, ParseResult, ProducerIdentity
from brain_review.evidence import evidence_binding_to_locator
from docling.document_converter import DocumentConverter
from docling_core.types.doc import DoclingDocument
from rapidocr import RapidOCR


@pytest.mark.parametrize("content_version", [1, 2])
def test_two_profiles_and_restart_use_saved_native_without_parser_or_ocr(tmp_path, content_version):
    helpers = runpy.run_path(str(Path(__file__).parent / "test_document_delivery.py"))
    store, manifest, files = helpers["bundle"](tmp_path)
    if content_version == 2:
        native = helpers["document"]()
        text = native.texts[0].text
        proven = BlockOriginInput(
            native_ref="#/texts/0",
            text=text,
            text_origin="STATED",
            producer=ProducerIdentity("controlled-native-fixture", "1", None, None),
            origin_anchor={
                "kind": "native_text",
                "native_ref": "#/texts/0",
                "regions": [
                    {
                        "page": 1,
                        "bbox": {"x0": 10, "y0": 10, "x1": 500, "y1": 80},
                        "char_start": 0,
                        "char_end": len(text),
                    }
                ],
            },
            confidence=None,
        )
        parsed = ParseResult(native, 1, [], 0, "complete", [], page_rotations={1: 0})
        manifest, files = build_bundle_v2(
            parsed,
            tenant_id=manifest.tenant_id,
            knowledge_base_id=manifest.knowledge_base_id,
            document_id=manifest.document_id,
            version_id=manifest.version_id,
            artifact_id=manifest.artifact_id,
            source_bytes=files["source.pdf"],
            recipe_sha256="b" * 64,
            execution=ParserExecutionV2(
                parser_package_version="controlled",
                parser_name="docling",
                projection_version="content-projection-v2.0",
                configuration_hash="b" * 64,
                environment_digest="controlled-fixture",
                model_artifact_digests=[],
            ),
            provenance={"#/texts/0": (proven,)},
            retained_assets={},
        )
    key = ArtifactKey(
        manifest.artifact_id, manifest.tenant_id, manifest.knowledge_base_id, content_version
    )
    store.verified.publish(key, manifest.model_dump_json().encode(), files)
    original = store.load_verified(key)
    calls = []
    cases = [
        ("gl-limits-a", {"each_occurrence_limit": "$1,000,000", "general_aggregate_limit": None}),
        (
            "gl-limits-b",
            {"named_insured": None, "policy_period_start": "2026-01-01", "policy_period_end": None},
        ),
    ]
    with (
        patch.object(DoclingAdapter, "parse", side_effect=AssertionError("parser forbidden")),
        patch.object(
            DocumentConverter, "convert", side_effect=AssertionError("converter forbidden")
        ),
        patch.object(
            DocumentConverter,
            "convert_all",
            side_effect=AssertionError("batch converter forbidden"),
        ),
        patch.object(RapidOCR, "__call__", side_effect=AssertionError("OCR forbidden")),
    ):
        for profile_id, values in cases:

            def response(request, values=values):
                calls.append(request)
                return httpx.Response(
                    200,
                    json={
                        "id": "recorded",
                        "object": "chat.completion",
                        "created": 1,
                        "model": "fixture",
                        "choices": [
                            {
                                "index": 0,
                                "finish_reason": "stop",
                                "message": {
                                    "role": "assistant",
                                    "content": json.dumps(values),
                                },
                            }
                        ],
                        "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
                    },
                )

            client = VllmGraphClient(
                base_url="http://127.0.0.1:8000/v1",
                api_key="synthetic",
                model_id="fixture",
                model_revision="a" * 40,
                token_counter=lambda *_: 200,
                slots=BoundedSemaphore(1),
                cancelled=Event(),
                http_client=httpx.Client(transport=httpx.MockTransport(response)),
            )
            run_id = uuid4()
            try:
                reopened = CheckpointStore(store.objects)
                service = GraphInterpretationService(reopened, lambda *_: None)
                args = dict(
                    tenant_id=key.tenant_id,
                    knowledge_base_id=key.knowledge_base_id,
                    artifact_id=key.artifact_id,
                    artifact_key=key,
                    run_id=run_id,
                    profile=load_profile(profile_id),
                    client=client,
                    output_contract_version=2,
                )
                result = service.interpret(**args)
                # The actual pinned direct-mode ledger omits native refs. This
                # existing Graph limitation stays explicit in both versions.
                assert result.status == "partial" and result.assertions
                assert result.warnings == ["unresolved_property_evidence"]
                assert result.assertions[0].evidence[0].precision == "unresolved"
                assert result.assertions[0].evidence[0].bbox is None
                # A controlled native-reference ledger separately proves that
                # retained geometry still yields the accepted BoxSelector.
                doc = DoclingDocument.model_validate_json(original.files["docling-document.json"])
                evidence = ground_value(
                    doc,
                    {"version": 2, "chunks": {"0": {"doc_item_refs": ["#/texts/0"]}}},
                    key.artifact_id,
                    next(value for value in values.values() if value is not None),
                )[0]
                assert evidence.precision == "span" and evidence.bbox is not None
                locator = evidence_binding_to_locator(**evidence.model_dump())
                assert locator.precision == "exact-span"
                assert locator.selector[0]["type"] == "nebula:BoxSelector"
                before = len(calls)
                assert service.interpret(**args) == result
                assert len(calls) == before
                outputs = reopened.load_run_bundle(
                    tenant_id=key.tenant_id,
                    knowledge_base_id=key.knowledge_base_id,
                    artifact_id=key.artifact_id,
                    artifact_key=key,
                    run_id=run_id,
                )
                assert isinstance(outputs.manifest, RunManifestV2)
                assert outputs.manifest.document_date_selection_id is None
                assert outputs.manifest.pipeline.name == "docling-graph"
            finally:
                client.close()
    assert len(calls) >= 2
    final = CheckpointStore(store.objects).load_verified(key)
    assert final.manifest_bytes == original.manifest_bytes
    assert dict(final.files) == dict(original.files)
