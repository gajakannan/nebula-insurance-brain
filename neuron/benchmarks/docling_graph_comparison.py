"""Synthetic development comparison; all model responses are recorded.

This runs actual baseline/Graph code to compare orchestration and evidence mapping.
It does not measure model accuracy, provider tokens/cost, or inference latency.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import tempfile
import time
from importlib.metadata import version
from pathlib import Path
from threading import BoundedSemaphore
from typing import Any, Literal
from unittest.mock import patch
from uuid import UUID, uuid4

import httpx
import tiktoken
from brain_content.checkpoints import CheckpointStore
from brain_content.config import LocalObjectStoreConfig
from brain_content.manifest import ArtifactManifest
from brain_content.object_store import LocalFilesystemObjectStore
from brain_extraction.graph_interpretation import GraphInterpretationService
from brain_extraction.openai_compatible_adapter import OpenAICompatibleExtractionAdapter
from brain_extraction.profiles import load_profile
from brain_extraction.vllm_graph_client import InferenceLimits, VllmGraphClient
from brain_ingestion.bundle_writer import build_bundle
from brain_interpretation.parsed_content import ParseResult
from brain_interpretation.result import InterpretationResult
from docling.document_converter import DocumentConverter
from docling_core.types.doc import DocItemLabel, DoclingDocument
from docling_core.types.doc.base import BoundingBox, CoordOrigin, Size
from docling_core.types.doc.document import ProvenanceItem

VALUE = "$1,000,000"


def fixture(kind: str) -> tuple[DoclingDocument, list[tuple[int, int, int]]]:
    doc = DoclingDocument(name=f"synthetic-{kind}")
    for page in (1, 2):
        doc.add_page(page_no=page, size=Size(width=600, height=800))
    source = f"Each Occurrence Limit: {VALUE}."
    start, end = source.index(VALUE), source.index(VALUE) + len(VALUE)
    box = BoundingBox(l=20, t=20, r=500, b=60, coord_origin=CoordOrigin.TOPLEFT)
    item = doc.add_text(
        label=DocItemLabel.TEXT,
        text=source,
        prov=ProvenanceItem(page_no=1, charspan=(0, len(source)), bbox=box),
    )
    expected = [(1, start, end)]
    if kind == "multi-region":
        split = start + 4
        item.prov = [
            ProvenanceItem(page_no=1, charspan=(0, split), bbox=box),
            ProvenanceItem(page_no=2, charspan=(split, len(source)), bbox=box),
        ]
        expected = [(1, start, split), (2, split, end)]
    elif kind == "ambiguous":
        doc.add_text(
            label=DocItemLabel.TEXT,
            text=source,
            prov=ProvenanceItem(page_no=2, charspan=(0, len(source)), bbox=box),
        )
        expected = []  # Repeated amount must remain unresolved, not select the first hit.
    elif kind != "unique":
        raise ValueError("unknown synthetic case")
    # Force actual chunking without repeating the target amount.
    for number in range(8):
        filler = f"Synthetic clause {number}. " + "Coverage wording for chunk sizing. " * 10
        doc.add_text(
            label=DocItemLabel.TEXT,
            text=filler,
            prov=ProvenanceItem(page_no=2, charspan=(0, len(filler)), bbox=box),
        )
    return doc, expected


class BundleReader:
    """Read-only baseline protocol adapter over already verified bundle bytes."""

    def __init__(self, manifest: ArtifactManifest, files: dict[str, bytes]) -> None:
        self.manifest, self.files = manifest, files

    async def get_manifest(self, artifact_id: UUID) -> ArtifactManifest:
        assert artifact_id == self.manifest.artifact_id
        return self.manifest

    async def open_file(self, artifact_id: UUID, path: str) -> bytes:
        assert artifact_id == self.manifest.artifact_id
        return self.files[path]

    async def put_bundle(self, manifest: ArtifactManifest, files: Any) -> ArtifactManifest:
        raise PermissionError("comparison input is read-only")


class RecordedTransport:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def respond(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        name = body["response_format"]["json_schema"]["name"]
        self.calls.append(name)
        values = {"each_occurrence_limit": VALUE, "general_aggregate_limit": None}
        payload: dict[str, Any]
        if name == "dense_skeleton":
            payload = {"nodes": [{"i": 0, "path": "", "ids": {}, "p": None}]}
        elif name == "dense_fill":
            payload = {"items": [values]}
        elif name in ("GLLimitsA", "extraction_result", "direct_extraction"):
            payload = values
        else:
            raise AssertionError(f"unexpected model phase: {name}")
        content = json.dumps(payload)
        prompt = len(
            self.encoding.encode(
                json.dumps(body["messages"])
                + json.dumps(body["response_format"]["json_schema"]["schema"])
            )
        )
        completion = len(self.encoding.encode(content))
        return httpx.Response(
            200,
            json={
                "id": "recorded",
                "object": "chat.completion",
                "created": 1,
                "model": "synthetic-recorded",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": content},
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt,
                    "completion_tokens": completion,
                    "total_tokens": prompt + completion,
                },
            },
        )

    def http_client(self) -> httpx.Client:
        return httpx.Client(transport=httpx.MockTransport(self.respond))


def score(result: InterpretationResult, expected: list[tuple[int, int, int]]) -> dict[str, Any]:
    fields: dict[str, list[Any]] = {}
    for assertion in result.assertions:
        fields.setdefault(assertion.slot_type, []).append(assertion.value.get("value"))
    amount = [a for a in result.assertions if a.slot_type == "each_occurrence_limit"]
    evidence_ok = False
    if len(amount) == 1:
        bindings = amount[0].evidence
        if expected:
            evidence_ok = all(e.precision == "span" and e.block_id == "text-0" for e in bindings)
            evidence_ok = evidence_ok and sorted(
                (e.page, e.char_start, e.char_end) for e in bindings
            ) == sorted(expected)
        else:
            evidence_ok = len(bindings) == 1 and bindings[0].precision == "unresolved"
    return {
        "schema_valid": result.status != "failed" and not result.failed_chunks,
        "amount_exact": fields.get("each_occurrence_limit") == [VALUE],
        # The baseline emits a null assertion; Graph omits an abstained field.
        "absent_field_abstained": fields.get("general_aggregate_limit", []) in ([], [None]),
        "evidence_matches_expected": evidence_ok,
        "review_candidates": sum(
            a.model_confidence is None
            or a.model_confidence < 0.5
            or any(e.precision == "unresolved" for e in a.evidence)
            for a in result.assertions
        ),
    }


def run_comparison(root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(messages: list[dict[str, str]], schema: str) -> int:
        return len(encoding.encode(json.dumps(messages) + schema))

    objects = LocalFilesystemObjectStore(LocalObjectStoreConfig("filesystem", root, True))
    store = CheckpointStore(objects)
    profile = load_profile("gl-limits-a")
    for kind in ("unique", "ambiguous", "multi-region"):
        doc, expected = fixture(kind)
        source = doc.model_dump_json().encode()
        manifest, files = build_bundle(
            ParseResult(doc, 2, [], 0, "complete", []),
            tenant_id=uuid4(),
            knowledge_base_id=uuid4(),
            document_id=uuid4(),
            version_id=uuid4(),
            artifact_id=uuid4(),
            source_sha256=hashlib.sha256(source).hexdigest(),
            configuration_hash="b" * 64,
            source_bytes=source,
            source_filename="source.json",
        )
        store.publish(manifest, files)
        native_hash = hashlib.sha256(files["docling-document.json"]).hexdigest()
        for mode in ("baseline", "direct", "dense"):
            recorded = RecordedTransport()
            started = time.perf_counter()
            chunk_count = None
            # Verify actual absence of conversion, not self-reported result counters.
            with patch.object(DocumentConverter, "convert", side_effect=AssertionError("reparse")):
                if mode == "baseline":
                    baseline = OpenAICompatibleExtractionAdapter(
                        base_url="http://recorded.invalid/v1",
                        api_key="synthetic",
                        model_id="synthetic-recorded",
                        context_limit=16384,
                        http_client=recorded.http_client(),
                    )
                    try:
                        result = asyncio.run(
                            baseline.interpret(
                                store=BundleReader(manifest, files),
                                artifact_id=manifest.artifact_id,
                                profile=profile,
                            )
                        )
                    finally:
                        baseline.close()
                else:
                    client = VllmGraphClient(
                        base_url="http://recorded.invalid/v1",
                        api_key="synthetic",
                        model_id="synthetic-recorded",
                        model_revision="a" * 40,
                        token_counter=count_tokens,
                        slots=BoundedSemaphore(1),
                        limits=InferenceLimits(context_tokens=16384, total_reserved_tokens=131072),
                        http_client=recorded.http_client(),
                    )

                    def authorize(
                        tenant: UUID,
                        kb: UUID,
                        artifact: UUID,
                        action: str,
                        bound: ArtifactManifest = manifest,
                    ) -> None:
                        assert (tenant, kb, artifact, action) == (
                            bound.tenant_id,
                            bound.knowledge_base_id,
                            bound.artifact_id,
                            "interpret",
                        )

                    contract: Literal["direct", "dense"] = "dense" if mode == "dense" else "direct"
                    try:
                        result = GraphInterpretationService(store, authorize).interpret(
                            tenant_id=manifest.tenant_id,
                            knowledge_base_id=manifest.knowledge_base_id,
                            artifact_id=manifest.artifact_id,
                            run_id=uuid4(),
                            profile=profile,
                            client=client,
                            extraction_contract=contract,
                            chunk_max_tokens=96,
                        )
                    finally:
                        client.close()
                    outputs = store.load_run(
                        tenant_id=manifest.tenant_id,
                        knowledge_base_id=manifest.knowledge_base_id,
                        artifact_id=manifest.artifact_id,
                        run_id=result.run_id,
                    )
                    ledger = json.loads(outputs["provenance.json"])
                    chunk_count = len(ledger.get("chunks", {})) if ledger else 0
            _, after = store.load(
                manifest.artifact_id, manifest.tenant_id, manifest.knowledge_base_id
            )
            assert hashlib.sha256(after["docling-document.json"]).hexdigest() == native_hash
            rows.append(
                {
                    "case": kind,
                    "engine": mode,
                    "status": result.status,
                    "checks": score(result, expected),
                    "model_phases": recorded.calls,
                    "model_calls": len(recorded.calls),
                    "chunk_count": chunk_count,
                    "estimated_prompt_tokens": result.counters.prompt_tokens,
                    "estimated_completion_tokens": result.counters.completion_tokens,
                    "local_elapsed_seconds": round(time.perf_counter() - started, 4),
                    "native_sha256": native_hash,
                    "conversion_calls": 0,
                }
            )
    report = {
        "scope": "synthetic development proof; recorded responses; not release acceptance",
        "model": "none — HTTP MockTransport only",
        "token_count_source": "cl100k_base estimate; not serving-tokenizer or provider usage",
        "latency_scope": "local pipeline time; no model inference latency",
        "fixture_version": 1,
        "configuration": {
            "context_tokens": 16384,
            "chunk_max_tokens": 96,
            "output_tokens": 512,
            "parallel_workers": 1,
            "evidence_mapper_version": 2,
        },
        "package_versions": {
            name: version(name) for name in ("docling", "docling-graph", "docling-core")
        },
        "profile_schema_sha256": profile.schema_sha256,
        "rows": rows,
    }
    report["development_checks_passed"] = all(
        row["checks"]["schema_valid"]
        and row["checks"]["amount_exact"]
        and row["checks"]["absent_field_abstained"]
        and row["conversion_calls"] == 0
        and (
            row["engine"] != "dense"
            or (
                row["checks"]["evidence_matches_expected"]
                and row["chunk_count"] > 1
                and row["model_phases"] == ["dense_skeleton", "dense_fill"]
            )
        )
        for row in rows
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a new report path")
    with tempfile.TemporaryDirectory(prefix="nebula-dev-comparison-") as temporary:
        report = run_comparison(Path(temporary))
    # The report contains synthetic case labels, metrics and hashes, not source payloads.
    with args.output.open("x") as target:
        json.dump(report, target, indent=2)
        target.write("\n")
    print(f"Wrote {len(report['rows'])} synthetic comparisons to {args.output}")
    if not report["development_checks_passed"]:
        raise SystemExit("synthetic development checks failed; see report")


if __name__ == "__main__":
    main()
