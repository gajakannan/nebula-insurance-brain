"""Real pinned Graph stages; recorded model responses, not an inference-quality proof."""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest
from brain_content.config import LocalObjectStoreConfig
from brain_content.object_store import LocalFilesystemObjectStore
from brain_content.store import LocalContentArtifactStore
from brain_extraction.docling_graph_pipeline import DoclingGraphPipelineAdapter
from brain_ingestion.bundle_writer import build_bundle
from brain_ingestion.docling_adapter import DoclingAdapter
from brain_interpretation.parsed_content import ParseResult
from docling.document_converter import DocumentConverter
from docling_core.types.doc import DocItemLabel, DoclingDocument
from docling_graph.exceptions import PipelineError
from docling_graph.pipeline.context import PipelineContext
from docling_graph.pipeline.stages import ExtractionStage
from pydantic import BaseModel


class Limit(BaseModel):
    each_occurrence_limit: str


class Insured(BaseModel):
    named_insured: str


class RecordedClient:
    model = "recorded-response-no-live-model"

    def __init__(
        self, value: dict[str, Any], before_call: Callable[[], None] = lambda: None
    ) -> None:
        self.value = value
        self.calls = 0
        self.before_call = before_call

    def get_json_response(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.before_call()
        self.calls += 1
        return self.value

    def get_json_response_stream(self, *args: Any, **kwargs: Any) -> Iterator[dict[str, Any]]:
        yield self.get_json_response(*args, **kwargs)


def native_document() -> DoclingDocument:
    document = DoclingDocument(name="synthetic-checkpoint")
    document.add_text(
        label=DocItemLabel.TEXT,
        text="Each Occurrence Limit: $1,000,000. Named Insured: Meridian.",
    )
    return document


def pipeline(client: RecordedClient) -> DoclingGraphPipelineAdapter:
    return DoclingGraphPipelineAdapter(llm_client=client, model_id=client.model)


@pytest.mark.parametrize("fail_extraction", [False, True])
def test_bundle_is_published_before_extraction_and_survives_failure(
    tmp_path: Path,
    fail_extraction: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Exercise the real manifest-last filesystem store without testing its thread
    # executor. This sandbox cannot deliver asyncio's socket-based thread wakeup.
    # This check proves publication ordering, not worker crash/restart durability.
    async def inline_io(function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        return function(*args, **kwargs)

    monkeypatch.setattr(asyncio, "to_thread", inline_io)
    source = tmp_path / "policy.md"
    source.write_text("synthetic source")
    artifact_id = uuid4()
    store = LocalContentArtifactStore(
        LocalFilesystemObjectStore(
            LocalObjectStoreConfig(provider="filesystem", root=tmp_path / "store", immutable=True)
        )
    )
    parsed = ParseResult(native_document(), 0, [2], 0, "partial", ["synthetic failed page"])
    converted = []

    def convert(path: Path) -> ParseResult[DoclingDocument]:
        converted.append(path)
        return parsed

    def publish(result: ParseResult[DoclingDocument]) -> None:
        manifest, files = build_bundle(
            result,
            tenant_id=uuid4(),
            knowledge_base_id=uuid4(),
            document_id=uuid4(),
            version_id=uuid4(),
            artifact_id=artifact_id,
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            configuration_hash="b" * 64,
            source_bytes=source.read_bytes(),
            source_filename=source.name,
        )
        asyncio.run(store.put_bundle(manifest, files))

    def assert_published() -> None:
        manifest = asyncio.run(store.get_manifest(artifact_id))
        assert manifest.extraction_quality.status == "partial"
        assert manifest.extraction_quality.failed_pages == [2]
        assert manifest.extraction_quality.warnings == ["synthetic failed page"]

    client = RecordedClient({"each_occurrence_limit": "$1,000,000"}, assert_published)
    if fail_extraction:

        def fail_after_checkpoint(_stage: ExtractionStage, _context: PipelineContext) -> None:
            assert_published()
            raise TimeoutError("injected extraction timeout")

        with (
            patch.object(ExtractionStage, "execute", fail_after_checkpoint),
            pytest.raises(PipelineError, match="injected extraction timeout"),
        ):
            pipeline(client).run(source=source, template=Limit, converter=convert, publish=publish)
    else:
        result = pipeline(client).run(
            source=source,
            template=Limit,
            converter=convert,
            publish=publish,
        )
        assert result.extracted_models[0].model_dump()["each_occurrence_limit"] == "$1,000,000"
        assert result.parse_result is parsed
        assert "llm_client" not in result.effective_configuration
        assert result.graph["nodes"]
    assert converted == [source]
    assert_published()
    # A new store object reconstructs the artifact after the pipeline has exited.
    reopened = LocalContentArtifactStore(
        LocalFilesystemObjectStore(
            LocalObjectStoreConfig(provider="filesystem", root=tmp_path / "store", immutable=True)
        )
    )
    saved = asyncio.run(reopened.open_file(artifact_id, "docling-document.json"))
    assert DoclingDocument.model_validate_json(saved) == parsed.document


def test_saved_json_reinterpretation_uses_real_graph_without_conversion(tmp_path: Path) -> None:
    source = tmp_path / "docling-document.json"
    source.write_text(native_document().model_dump_json())
    original = source.read_bytes()
    cases: list[tuple[type[BaseModel], dict[str, Any]]] = [
        (Limit, {"each_occurrence_limit": "$1,000,000"}),
        (Insured, {"named_insured": "Meridian"}),
    ]
    for template, values in cases:
        client = RecordedClient(values)
        with patch.object(
            DocumentConverter, "convert", side_effect=AssertionError("reparse")
        ) as conversion:
            result = pipeline(client).run(source=source, template=template)
        assert conversion.call_count == 0
        assert result.parse_result is None
        assert result.extracted_models[0].model_dump() == values
        assert client.calls >= 1
        assert source.read_bytes() == original


def test_publication_failure_prevents_model_calls(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("source")
    client = RecordedClient({"each_occurrence_limit": "$1,000,000"})

    def publish(_result: ParseResult[DoclingDocument]) -> None:
        raise OSError("injected publication failure")

    with pytest.raises(PipelineError, match="injected publication failure"):
        pipeline(client).run(
            source=source,
            template=Limit,
            converter=lambda _: ParseResult(native_document(), 0, [], 0, "complete", []),
            publish=publish,
        )
    assert client.calls == 0


@pytest.mark.parametrize("scanned", [False, True])
def test_native_and_scanned_conversion_then_saved_json_reuse(
    tmp_path: Path,
    scanned: bool,
) -> None:
    """Real PDF conversion/OCR and Graph stages; recorded extraction, no live model."""
    name = "gl-policy-declarations-scanned.pdf" if scanned else "gl-policy-declarations.pdf"
    source = Path(__file__).resolve().parents[2] / "fixtures" / name
    saved = tmp_path / "docling-document.json"
    conversions = []
    converter = DoclingAdapter()

    def convert(path: Path) -> ParseResult[DoclingDocument]:
        conversions.append(path)
        return converter.parse(path)

    def publish(parsed: ParseResult[DoclingDocument]) -> None:
        assert parsed.status == "complete"
        assert parsed.ocr_page_count == int(scanned)
        saved.write_text(parsed.document.model_dump_json())

    first = pipeline(RecordedClient({"each_occurrence_limit": "$1,000,000"})).run(
        source=source,
        template=Limit,
        converter=convert,
        publish=publish,
    )
    assert first.parse_result is not None
    assert conversions == [source]
    original = saved.read_bytes()
    with patch.object(DocumentConverter, "convert", side_effect=AssertionError("reparse")):
        second = pipeline(RecordedClient({"named_insured": "Meridian"})).run(
            source=saved,
            template=Insured,
        )
    assert second.parse_result is None
    assert saved.read_bytes() == original
