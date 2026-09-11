from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

import tiktoken
from brain_content.store import ContentArtifactStore
from brain_interpretation.counters import CounterAccumulator
from brain_interpretation.result import (
    BoundingBox,
    CandidateAssertion,
    EvidenceBinding,
    InterpretationBasis,
    InterpretationResult,
    RunConfiguration,
)
from docling_core.types.doc.base import BoundingBox as DoclingBoundingBox
from docling_core.types.doc.base import CoordOrigin
from docling_core.types.doc.document import DoclingDocument, ProvenanceItem, TextItem
from openai import OpenAI
from pydantic import BaseModel

from brain_extraction.context_guard import ContextGuard
from brain_extraction.profiles import ExtractionProfile

Block = tuple[str, TextItem, ProvenanceItem]

# --- Finding recorded for ADR-0040 (F0001-S0003) ---------------------------------
# The `docling-graph` PyPI package (1.9.1) was evaluated as the extraction engine per
# ADR-0001/SOLUTION-PATTERNS. Its public `run_pipeline()` API always reconverts the
# source document itself (`docling_graph.core.extractors.document_processor
# .DocumentProcessor.convert_to_docling_doc` calls `DocumentConverter.convert(source)`
# unconditionally) and provides no path to inject an already-parsed `DoclingDocument`.
# Its internal converter also only registers `InputFormat.PDF`/`InputFormat.IMAGE`, not
# `InputFormat.JSON_DOCLING`, so even a serialized-DoclingDocument-as-source workaround
# is unavailable. This conflicts with ADR-0003 (parse once) and this story's own
# acceptance criterion 2 (zero conversion/OCR calls on reinterpretation) — confirmed by
# a live run against this proof's fixture on 2026-09-09.
#
# Decision: this adapter calls the OpenAI-compatible endpoint directly (the same
# backend contract ADR-0001/ADR-0055 already specify — vLLM serving
# microsoft/Phi-4-mini-instruct), operating on the DoclingDocument reconstructed from
# the persisted `docling-document.json` bytes (zero Docling calls), with vLLM's native
# guided/structured JSON output (`response_format: json_schema`, strict) enforcing the
# extraction template schema — a stronger no-truncated-output guarantee than parsing
# free-form completions. `docling-graph` is not installed as a `neuron/` runtime
# dependency of this module. Evidence grounding here is verbatim substring matching
# against the same `doc.texts` blocks `brain_ingestion.bundle_writer` enumerates,
# giving `char_start`/`char_end` in the *same* coordinate space as `blocks.jsonl`
# (`docling-graph`'s own chunk-relative doclang offsets do not share that space).
# -----------------------------------------------------------------------------


def _strict_json_schema(template: type[BaseModel]) -> dict:
    """Pydantic's `model_json_schema()` omits `required`/`additionalProperties`, which
    OpenAI/vLLM's `strict: true` structured-output mode needs on *every* property to
    reliably constrain generation. Without them, a live run against this proof's
    fixture (2026-09-09) produced a materially worse, non-deterministic extraction:
    the model returned `null` for a present field and fabricated a run-on composite
    string for another rather than the single verbatim value. Adding both restored
    correct, deterministic extraction — recorded for ADR-0040."""
    schema = template.model_json_schema()
    schema["required"] = list(schema.get("properties", {}).keys())
    schema["additionalProperties"] = False
    return schema


def _to_top_left_bbox(bbox: DoclingBoundingBox | None, page_height: float) -> BoundingBox | None:
    if bbox is None:
        return None
    if bbox.coord_origin == CoordOrigin.BOTTOMLEFT:
        y0, y1 = page_height - bbox.t, page_height - bbox.b
    else:
        y0, y1 = bbox.t, bbox.b
    return BoundingBox(page=0, x0=bbox.l, y0=y0, x1=bbox.r, y1=y1)


class DoclingGraphAdapter:
    """Interprets a persisted content artifact against an extraction profile via the
    OpenAI-compatible backend (F0001-S0003). See the module docstring above for why
    this does not use the `docling-graph` package."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model_id: str,
        context_limit: int = 4096,
        max_output_tokens: int = 512,
    ) -> None:
        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._base_url = base_url
        self._model_id = model_id
        self._context_limit = context_limit
        self._max_output_tokens = max_output_tokens
        self._guard = ContextGuard(context_limit, reserve_for_output=max_output_tokens)
        self._encoding = tiktoken.get_encoding("cl100k_base")

    async def interpret(
        self, *, store: ContentArtifactStore, artifact_id: UUID, profile: ExtractionProfile
    ) -> InterpretationResult:
        counters = CounterAccumulator()
        run_id = uuid4()

        docling_document_bytes = await store.open_file(artifact_id, "docling-document.json")
        doc = DoclingDocument.model_validate_json(docling_document_bytes)
        page_heights = {page_no: item.size.height for page_no, item in doc.pages.items()}

        blocks: list[Block] = [
            (f"text-{i}", text_item, prov)
            for i, text_item in enumerate(doc.texts)
            for prov in text_item.prov
        ]
        document_text = "\n".join(text_item.text for _bid, text_item, _prov in blocks)

        schema = _strict_json_schema(profile.template)
        schema_hash = hashlib.sha256(json.dumps(schema, sort_keys=True).encode("utf-8")).hexdigest()
        prompt = (
            "Extract the requested fields as strict JSON matching the schema. "
            "Use null for any field not present. Copy values verbatim from the source "
            f"text; never paraphrase.\n\n--- SOURCE ---\n{document_text}\n--- END SOURCE ---"
        )
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        prompt_tokens_estimate = len(self._encoding.encode(prompt))

        run_configuration = RunConfiguration(
            backend="openai_compatible",
            model_id=self._model_id,
            model_revision=None,
            endpoint_hash=hashlib.sha256(self._base_url.encode("utf-8")).hexdigest(),
            prompt_hash=prompt_hash,
            schema_hash=schema_hash,
            context_limit=self._context_limit,
            profile_id=profile.profile_id,
            profile_version=profile.profile_version,
        )

        try:
            self._guard.check(prompt_tokens_estimate)
        except Exception as exc:  # ContextLimitExceeded — no truncated output accepted
            return InterpretationResult(
                run_id=run_id,
                artifact_id=artifact_id,
                status="failed",
                entities=[],
                assertions=[],
                relationships=[],
                quality_signals={},
                warnings=[str(exc)],
                failed_chunks=["full_document"],
                run_configuration=run_configuration,
                counters=counters.freeze(),
                provenance_ledger_ref=None,
                created_at=datetime.now(UTC),
            )

        response = self._client.chat.completions.create(
            model=self._model_id,
            messages=[{"role": "user", "content": prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": profile.template.__name__,
                    "schema": schema,
                    "strict": True,
                },
            },
            max_tokens=self._max_output_tokens,
            # Deterministic extraction: the harness must be repeatable (F0001-S0003
            # non-functional expectation), and model_confidence is explicitly not
            # calibrated (business rule 3) — temperature=0 removes one axis of
            # non-reproducibility without claiming to fix the other.
            temperature=0,
        )
        usage = response.usage
        counters.record_model_call(
            prompt_tokens=usage.prompt_tokens if usage else prompt_tokens_estimate,
            completion_tokens=usage.completion_tokens if usage else 0,
        )

        content = response.choices[0].message.content
        assertions: list[CandidateAssertion] = []
        warnings: list[str] = []
        failed_chunks: list[str] = []
        extracted: BaseModel | None = None
        if content is None:
            warnings.append("schema validation failed: empty completion content")
            failed_chunks.append("full_document")
        else:
            try:
                extracted = profile.template.model_validate_json(content)
            except Exception as exc:  # schema-invalid output — record and stay partial
                warnings.append(f"schema validation failed: {exc}")
                failed_chunks.append("full_document")

        if extracted is not None:
            for field_name, value in extracted.model_dump().items():
                assertions.append(
                    self._bind_field(field_name, value, blocks, page_heights, artifact_id)
                )

        status: Literal["complete", "failed"] = "complete" if extracted is not None else "failed"
        return InterpretationResult(
            run_id=run_id,
            artifact_id=artifact_id,
            status=status,
            entities=[],
            assertions=assertions,
            relationships=[],
            quality_signals={},
            warnings=warnings,
            failed_chunks=failed_chunks,
            run_configuration=run_configuration,
            counters=counters.freeze(),
            provenance_ledger_ref=None,
            created_at=datetime.now(UTC),
        )

    def _bind_field(
        self,
        field_name: str,
        value: object,
        blocks: list[Block],
        page_heights: dict[int, float],
        artifact_id: UUID,
    ) -> CandidateAssertion:
        evidence: list[EvidenceBinding] = []
        interpretation_basis: InterpretationBasis = "AMBIGUOUS"

        if isinstance(value, str) and value:
            for block_id, text_item, prov in blocks:
                offset = text_item.text.find(value)
                if offset == -1:
                    continue
                bbox = _to_top_left_bbox(prov.bbox, page_heights.get(prov.page_no, 0.0))
                if bbox is not None:
                    bbox = bbox.model_copy(update={"page": prov.page_no})
                evidence.append(
                    EvidenceBinding(
                        artifact_id=artifact_id,
                        block_id=block_id,
                        page=prov.page_no,
                        bbox=bbox,
                        char_start=offset,
                        char_end=offset + len(value),
                        precision="span",
                    )
                )
                interpretation_basis = "EXPLICIT"
                break  # first verbatim match; a value repeated verbatim elsewhere is not re-bound

        if not evidence:
            evidence.append(
                EvidenceBinding(
                    artifact_id=artifact_id,
                    block_id=None,
                    page=None,
                    bbox=None,
                    char_start=None,
                    char_end=None,
                    precision="unresolved",
                )
            )

        return CandidateAssertion(
            id=uuid4(),
            subject_type="Policy",
            slot_type=field_name,
            value={"value": value},
            evidence=evidence,
            model_confidence=None,
            interpretation_basis=interpretation_basis,
        )
