from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any, Literal

# Docling-Graph imports LiteLLM. A self-hosted extraction worker must not fetch
# a remote price catalogue merely by importing its document pipeline.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

from brain_interpretation.parsed_content import ParseResult  # noqa: E402
from docling_core.types.doc.document import DoclingDocument  # noqa: E402
from docling_graph import PipelineConfig  # noqa: E402
from docling_graph.pipeline.context import PipelineContext  # noqa: E402
from docling_graph.pipeline.orchestrator import PipelineOrchestrator  # noqa: E402
from docling_graph.pipeline.stages import (  # noqa: E402
    ExtractionStage,
    PipelineStage,
)
from docling_graph.protocols import LLMClientProtocol  # noqa: E402
from pydantic import BaseModel  # noqa: E402

DOCLING_GRAPH_VERSION = "1.9.1"
DOCLING_GRAPH_WHEEL_SHA256 = "04538ef0f35517f22c77641eb7dca5a35ee8d54d6e818b0341e479dc4280a62f"

Converter = Callable[[Path], ParseResult[DoclingDocument]]
Publisher = Callable[[ParseResult[DoclingDocument]], None]


class ConversionCheckpointError(RuntimeError):
    """Conversion cannot advance into extraction without a published bundle."""


class _ConversionCheckpoint(PipelineStage):
    """Compose a durable boundary into the pinned Graph stage interface.

    Graph owns stage ordering. The supplied converter and publisher preserve
    Nebula's existing native-document and parse-quality contract. No global
    converter monkey patch or private upstream extraction method is used.
    """

    def __init__(self, converter: Converter | None, publish: Publisher | None) -> None:
        self._converter = converter
        self._publish = publish
        self.result: ParseResult[DoclingDocument] | None = None

    def name(self) -> str:
        return "Nebula conversion checkpoint"

    def execute(self, context: PipelineContext) -> PipelineContext:
        metadata = context.input_metadata or {}
        if metadata.get("input_type") == "docling_document":
            # InputNormalizationStage has already loaded the saved native JSON.
            return context
        if self._converter is None or self._publish is None:
            raise ConversionCheckpointError("raw input requires conversion and publication")
        if not isinstance(context.normalized_source, Path):
            raise ConversionCheckpointError("conversion requires a normalized local file")
        result = self._converter(context.normalized_source)
        if result.status == "failed":
            raise ConversionCheckpointError("physical conversion failed")
        self.result = result
        self._publish(result)
        # This is the same stage handoff used by upstream's JSON input handler.
        # ExtractionStage.extract_from_document() performs no conversion.
        context.docling_document = result.document
        context.input_metadata = {**metadata, "input_type": "docling_document"}
        return context


@dataclass(frozen=True, slots=True)
class GraphPipelineOutput:
    """Run outputs, separate from the immutable conversion bundle."""

    extracted_models: tuple[BaseModel, ...]
    provenance: dict[str, Any] | None
    effective_configuration: dict[str, Any]
    graph: dict[str, Any]
    parse_result: ParseResult[DoclingDocument] | None
    package_versions: dict[str, str]
    schema_sha256: str
    input_sha256: str


class DoclingGraphPipelineAdapter:
    """Candidate pipeline; activation still requires ADR-0060 live proof.

    Run this blocking operation in a worker. Source paths must be materialized
    by the authorized application service; URLs, raw text, and user-controlled
    template import strings are deliberately not part of this boundary.
    """

    def __init__(self, *, llm_client: LLMClientProtocol, model_id: str) -> None:
        if version("docling-graph") != DOCLING_GRAPH_VERSION:
            raise RuntimeError("Docling-Graph version differs from the tested integration pin")
        self._client = llm_client
        self._model_id = model_id

    def run(
        self,
        *,
        source: Path,
        template: type[BaseModel],
        converter: Converter | None = None,
        publish: Publisher | None = None,
        extraction_contract: Literal["direct", "dense"] = "direct",
        chunk_max_tokens: int = 512,
        conversion_only: bool = False,
    ) -> GraphPipelineOutput:
        if not isinstance(source, Path) or not source.is_file():
            raise ValueError("source must be a materialized local file")
        if not isinstance(template, type) or not issubclass(template, BaseModel):
            raise ValueError("template must be a trusted Pydantic model class")
        if chunk_max_tokens <= 0:
            raise ValueError("chunk_max_tokens must be positive")
        input_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
        config = PipelineConfig(
            source=str(source),
            template=template,
            backend="llm",
            inference="local",
            model_override=self._model_id,
            provider_override="vllm",
            llm_client=self._client,
            extraction_contract=extraction_contract,
            use_chunking=extraction_contract == "dense",
            chunk_max_tokens=chunk_max_tokens,
            parallel_workers=1,
            gleaning_enabled=False,
            llm_input_format="markdown",
            dump_to_disk=False,
            debug=False,
            gc_collect=False,
            provenance="detailed",
        )
        checkpoint = _ConversionCheckpoint(converter, publish)
        pipeline = PipelineOrchestrator(config, mode="api")
        extraction_positions = [
            i for i, stage in enumerate(pipeline.stages) if isinstance(stage, ExtractionStage)
        ]
        if len(extraction_positions) != 1:
            raise RuntimeError("upstream stage layout differs from the tested integration")
        pipeline.stages.insert(extraction_positions[0], checkpoint)
        if conversion_only:
            pipeline.stages = pipeline.stages[: extraction_positions[0] + 1]
        context = pipeline.run()
        graph = context.knowledge_graph
        return GraphPipelineOutput(
            extracted_models=tuple(context.extracted_models or ()),
            provenance=(context.provenance.model_dump(mode="json") if context.provenance else None),
            effective_configuration=config.to_metadata_config_dict(
                resolved_model=self._model_id, resolved_provider="vllm"
            ),
            graph={
                "nodes": [{"id": node_id, **data} for node_id, data in graph.nodes(data=True)]
                if graph is not None
                else [],
                "edges": [
                    {"source": source_id, "target": target_id, **data}
                    for source_id, target_id, data in graph.edges(data=True)
                ]
                if graph is not None
                else [],
            },
            parse_result=checkpoint.result,
            package_versions={
                name: version(name) for name in ("docling", "docling-core", "docling-graph")
            },
            schema_sha256=hashlib.sha256(
                json.dumps(template.model_json_schema(), sort_keys=True).encode()
            ).hexdigest(),
            input_sha256=input_sha256,
        )
