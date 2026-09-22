"""Translate and publish a Graph attempt without giving Graph canonical authority."""

from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any, Literal
from uuid import UUID, uuid5

from brain_content.checkpoints import CheckpointStore
from brain_interpretation.result import (
    CandidateAssertion,
    Counters,
    InterpretationResult,
    RunConfiguration,
)
from docling_core.types.doc import DoclingDocument

from brain_extraction.docling_graph_pipeline import DoclingGraphPipelineAdapter
from brain_extraction.graph_evidence import ground_value
from brain_extraction.profiles import ExtractionProfile
from brain_extraction.vllm_graph_client import VllmGraphClient


def _json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()


class GraphInterpretationService:
    def __init__(
        self, store: CheckpointStore, authorize: Callable[[UUID, UUID, UUID, str], None]
    ) -> None:
        self.store = store
        self.authorize = authorize

    def interpret(
        self,
        *,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        artifact_id: UUID,
        run_id: UUID,
        profile: ExtractionProfile,
        client: VllmGraphClient,
        extraction_contract: Literal["direct", "dense"] = "direct",
        chunk_max_tokens: int = 512,
        selected_refs: tuple[str, ...] = (),
        publish: Callable[[Callable[[], str]], str] | None = None,
    ) -> InterpretationResult:
        # Targeted interpretation cannot quietly become a whole-document request.
        # The pinned upstream pipeline does not expose a tested ref-preserving slice.
        if selected_refs:
            raise NotImplementedError("targeted native-item interpretation is not qualified")
        self.authorize(tenant_id, knowledge_base_id, artifact_id, "interpret")
        manifest, files = self.store.load(artifact_id, tenant_id, knowledge_base_id)
        document = DoclingDocument.model_validate_json(files[manifest.docling_document.path])
        result_ref = f"runs/{tenant_id}/{knowledge_base_id}/{run_id}/manifest.json"
        if self.store.objects.exists(result_ref):
            prior = self.store.load_run(
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                artifact_id=artifact_id,
                run_id=run_id,
            )
            previous = InterpretationResult.model_validate_json(prior["result.json"])
            prior_metadata = json.loads(prior["metadata.json"])
            if prior_metadata.get("requested_configuration") != {
                "extraction_contract": extraction_contract,
                "chunk_max_tokens": chunk_max_tokens,
                "model_id": client.model,
                "model_revision": client.diagnostics()["model_revision"],
                "limits": client.diagnostics()["limits"],
            }:
                raise ValueError("run identity belongs to a different configuration")
            if (
                previous.run_configuration.profile_id,
                previous.run_configuration.profile_version,
                previous.run_configuration.schema_hash,
            ) != (
                profile.profile_id,
                profile.profile_version,
                hashlib.sha256(
                    json.dumps(profile.template.model_json_schema(), sort_keys=True).encode()
                ).hexdigest(),
            ):
                raise ValueError("run identity belongs to a different profile")
            return previous
        output = None
        warnings = []
        try:
            with tempfile.TemporaryDirectory(prefix="nebula-interpret-") as temporary:
                source = Path(temporary) / "docling-document.json"
                source.write_bytes(files[manifest.docling_document.path])
                output = DoclingGraphPipelineAdapter(llm_client=client, model_id=client.model).run(
                    source=source,
                    template=profile.template,
                    extraction_contract=extraction_contract,
                    chunk_max_tokens=chunk_max_tokens,
                )
        except Exception as exc:
            # Provider and pipeline exceptions can contain source text. Keep only
            # a type-level failure code in the durable result's ordinary warnings.
            warnings.append(f"pipeline_failure:{type(exc).__name__}")
        diagnostics = client.diagnostics()
        calls = diagnostics["calls"]
        assertions = []
        if output is not None:
            for index, model in enumerate(output.extracted_models):
                for field, value in model.model_dump(mode="json").items():
                    if value is None:
                        continue
                    evidence = ground_value(document, output.provenance, artifact_id, value)
                    assertions.append(
                        CandidateAssertion(
                            id=uuid5(run_id, f"{index}:{field}"),
                            subject_type="Policy",
                            slot_type=field,
                            value={"value": value},
                            evidence=evidence,
                            model_confidence=None,
                            interpretation_basis="AMBIGUOUS"
                            if evidence[0].precision == "unresolved"
                            else "EXPLICIT",
                        )
                    )
        unresolved = sum(any(e.precision == "unresolved" for e in a.evidence) for a in assertions)
        if output is not None and not output.extracted_models:
            warnings.append("empty_extraction")
        if unresolved:
            warnings.append("unresolved_property_evidence")
        if manifest.extraction_quality.status != "complete":
            warnings.append("partial_source_conversion")
        if any(call["outcome"] != "complete" for call in calls):
            warnings.append("model_call_failures")
        result = InterpretationResult(
            run_id=run_id,
            artifact_id=artifact_id,
            status="failed" if output is None else ("partial" if warnings else "complete"),
            entities=[],
            assertions=assertions,
            relationships=[],
            quality_signals={"unresolved_property_count": float(unresolved)},
            warnings=warnings,
            failed_chunks=["document"] if output is None else [],
            run_configuration=RunConfiguration(
                backend="openai_compatible",
                model_id=client.model,
                model_revision=diagnostics["model_revision"],
                endpoint_hash=diagnostics["endpoint_hash"],
                prompt_hash=hashlib.sha256(_json([c["prompt_hash"] for c in calls])).hexdigest(),
                schema_hash=hashlib.sha256(
                    json.dumps(profile.template.model_json_schema(), sort_keys=True).encode()
                ).hexdigest(),
                context_limit=diagnostics["limits"]["context_tokens"],
                profile_id=profile.profile_id,
                profile_version=profile.profile_version,
            ),
            counters=Counters(
                model_calls=len(calls),
                prompt_tokens=sum(c["prompt_tokens"] or 0 for c in calls),
                completion_tokens=sum(c["completion_tokens"] or 0 for c in calls),
            ),
            provenance_ledger_ref=f"runs/{tenant_id}/{knowledge_base_id}/{run_id}/provenance.json",
            created_at=datetime.now(UTC),
        )
        metadata = {
            "contract_version": 1,
            "engine": "docling-graph",
            "diagnostics": diagnostics,
            "artifact_sha256": manifest.artifact_sha256,
            "profile_id": profile.profile_id,
            "profile_version": profile.profile_version,
            "schema_sha256": result.run_configuration.schema_hash,
            "selected_refs": [],
            "requested_configuration": {
                "extraction_contract": extraction_contract,
                "chunk_max_tokens": chunk_max_tokens,
                "model_id": client.model,
                "model_revision": diagnostics["model_revision"],
                "limits": diagnostics["limits"],
            },
            "evidence_mapper_version": 2,
            "pipeline_config": output.effective_configuration if output else None,
            "package_versions": {
                name: version(name) for name in ("docling", "docling-core", "docling-graph")
            },
        }
        outputs = {
            "result.json": result.model_dump_json().encode(),
            "provenance.json": _json(output.provenance if output else None),
            "graph.json": _json(output.graph if output else None),
            "metadata.json": _json(metadata),
        }
        self.authorize(tenant_id, knowledge_base_id, artifact_id, "interpret")

        def save() -> str:
            return self.store.publish_run(
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                artifact_id=artifact_id,
                run_id=run_id,
                files=outputs,
            )

        if publish is None:
            save()
        else:
            publish(save)
        return result
