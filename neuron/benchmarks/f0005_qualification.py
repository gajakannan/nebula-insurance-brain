"""F0005 live qualification harness (assembly plan Step 7).

Runs the synthetic qualification corpus through the real worker composition
(supervised conversion, host guard, bounded client, evidence mapper, importer)
against the dedicated local vLLM server, one engine at a time. Each engine uses
its own temporary configuration, PostgreSQL schema (queue namespace) and content
root; all share the fixed host guard for the one provider. The committed
configuration is never edited and no candidate job enters the ordinary queue.

Metrics follow the approved PRD exactly. Expected values come only from the
corpus author's independent expectation files. Reports are immutable: an
existing output path is refused, and a provider failure voids the report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import time
import unicodedata
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from importlib.metadata import version
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4, uuid5

import yaml  # type: ignore[import-untyped]
from brain_content.config import (
    EXTRACTION_PIPELINES,
    load_content_writer_config,
    load_extraction_config,
)
from brain_domain.principal import PrincipalKind
from brain_extraction.profiles import load_profile
from brain_ingestion.conversion_process import SupervisedConverter
from brain_ingestion.document_worker import WorkerStopped
from brain_ingestion.submission import enqueue_document
from brain_ingestion.worker_cli import Composition, compose, processing_worker
from brain_ingestion.worker_guard import HostInferenceGuard
from brain_interpretation.result import InterpretationResult
from brain_jobs.queue import events, jobs
from brain_jobs.queue import metadata as job_metadata
from brain_persistence.base import Base
from brain_persistence.models import Assertion, ReviewItemRow
from brain_testing import fixtures
from docling_core.types.doc import DoclingDocument
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "planning-mds/security/policies"
PROFILES = ("gl-limits-a", "gl-limits-b")
CONTEXT_TOKENS = 4096
PROVIDER_FAILURES = {"model_unavailable", "model_timeout", "model_http_error"}


def normalize(value: str) -> str:
    """PRD normalization: whitespace collapse and Unicode NFC only."""
    return " ".join(unicodedata.normalize("NFC", value).split())


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corpus_identity(corpus: Path) -> dict[str, str]:
    hashes = (corpus / "CORPUS-HASHES.txt").read_text()
    expectation_lines = sorted(line for line in hashes.splitlines() if "  expectations/" in line)
    return {
        "corpus_sha256": sha256_file(corpus / "CORPUS-HASHES.txt"),
        "expectation_set_sha256": hashlib.sha256(
            ("\n".join(expectation_lines) + "\n").encode()
        ).hexdigest(),
    }


def verify_corpus(corpus: Path) -> None:
    for line in (corpus / "CORPUS-HASHES.txt").read_text().splitlines():
        digest, name = line.split("  ", 1)
        if sha256_file(corpus / name) != digest:
            raise SystemExit(f"corpus hash mismatch: {name}")


@dataclass
class Isolated:
    """One engine's queue namespace, schema, content root and temporary config."""

    pipeline: str
    v2_writer_enabled: bool
    engine: Engine
    schema: str
    config_path: Path
    config_sha256: str
    content_root: Path
    tenant: UUID
    knowledge_base: UUID
    actor: UUID
    membership: UUID
    parts: Composition

    def handle(self) -> dict[str, str]:
        """Serializable identity for a child process attaching to this environment."""
        return {
            "pipeline": self.pipeline,
            "v2": str(self.v2_writer_enabled),
            "schema": self.schema,
            "config": str(self.config_path),
            "content_root": str(self.content_root),
            "tenant": str(self.tenant),
            "knowledge_base": str(self.knowledge_base),
            "actor": str(self.actor),
            "membership": str(self.membership),
        }


def attach(url: str, handle: dict[str, str]) -> Isolated:
    """Rebuild an existing isolated environment in another process (no create/drop)."""
    os.environ["BRAIN_LOCAL_CONFIG_PATH"] = handle["config"]
    engine = create_engine(f"{url}?options=-csearch_path%3D{handle['schema']}")
    config = Path(handle["config"])
    return Isolated(
        handle["pipeline"],
        handle["v2"] == "True",
        engine,
        handle["schema"],
        config,
        sha256_file(config),
        Path(handle["content_root"]),
        UUID(handle["tenant"]),
        UUID(handle["knowledge_base"]),
        UUID(handle["actor"]),
        UUID(handle["membership"]),
        compose(engine, POLICY),
    )


@contextmanager
def isolated(url: str, pipeline: str, *, v2_writer_enabled: bool) -> Iterator[Isolated]:
    # The schema name is DDL and cannot be a bound parameter: only the closed
    # pipeline set reaches it (Security SEC-F5-L3).
    if pipeline not in EXTRACTION_PIPELINES:
        raise ValueError("unknown extraction pipeline")
    schema = f"f0005_qual_{pipeline.replace('-', '_')}_{uuid4().hex[:10]}"
    admin = create_engine(url)
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(f"{url}?options=-csearch_path%3D{schema}")
    with tempfile.TemporaryDirectory(prefix="nebula-f0005-qual-") as temporary:
        root = Path(temporary)
        content_root = root / "content"
        content_root.mkdir()
        config_path = root / "local.yaml"
        config_path.write_text(
            yaml.safe_dump(
                {
                    "content": {"v2_writer_enabled": v2_writer_enabled},
                    "extraction": {"pipeline": pipeline},
                    "object_store": {
                        "provider": "filesystem",
                        "root": str(content_root),
                        "immutable": True,
                    },
                },
                sort_keys=True,
            )
        )
        previous = os.environ.get("BRAIN_LOCAL_CONFIG_PATH")
        os.environ["BRAIN_LOCAL_CONFIG_PATH"] = str(config_path)
        try:
            job_metadata.create_all(engine)
            with engine.begin() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist SCHEMA public"))
            Base.metadata.create_all(engine)
            tenant, kb = uuid4(), uuid4()
            with Session(engine) as session, session.begin():
                fixtures.activate_policy(session, POLICY / "model.conf", POLICY / "policy.csv")
                service = fixtures.seed_principal(
                    session, issuer="local", subject=f"f0005-{pipeline}", kind=PrincipalKind.SERVICE
                )
                membership = fixtures.seed_grant(
                    session, service.id, tenant, kb, "ServicePrincipal"
                )
                actor = service.id
            if load_extraction_config().pipeline != pipeline:
                raise RuntimeError("isolated configuration was not selected")
            yield Isolated(
                pipeline,
                v2_writer_enabled,
                engine,
                schema,
                config_path,
                sha256_file(config_path),
                content_root,
                tenant,
                kb,
                actor,
                membership,
                compose(engine, POLICY),
            )
        finally:
            if previous is None:
                os.environ.pop("BRAIN_LOCAL_CONFIG_PATH", None)
            else:
                os.environ["BRAIN_LOCAL_CONFIG_PATH"] = previous
            engine.dispose()
            with admin.begin() as conn:
                conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin.dispose()


class CountingConverter(SupervisedConverter):
    """Counts physical conversions at the supervised converter entry point."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.launches = 0

    def convert(self, *args: Any, **kwargs: Any) -> Any:
        self.launches += 1
        return super().convert(*args, **kwargs)


@dataclass
class LiveSettings:
    provider_url: str
    # Never in a repr: pytest -l and tracebacks print locals (Security SEC-F5-L2).
    api_key: str = field(repr=False)
    model: str
    revision: str

    @classmethod
    def from_environment(cls) -> LiveSettings:
        return cls(
            os.environ.get("BRAIN_INFERENCE_BASE_URL", "http://127.0.0.1:8000/v1"),
            os.environ["BRAIN_INFERENCE_API_KEY"],
            os.environ.get("BRAIN_INFERENCE_MODEL", "microsoft/Phi-4-mini-instruct"),
            os.environ["BRAIN_INFERENCE_MODEL_REVISION"],
        )


@dataclass
class Session_:
    env: Isolated
    guard: HostInferenceGuard
    worker: Any
    converter: CountingConverter
    timings: list[dict[str, Any]] = field(default_factory=list)

    def submit(self, pdf: Path, profile: str) -> UUID:
        return enqueue_document(
            self.env.engine,
            self.env.parts.queue,
            self.env.parts.store,
            self.env.parts.authorization,
            self.env.parts.access,
            source_path=pdf,
            tenant_id=self.env.tenant,
            knowledge_base_id=self.env.knowledge_base,
            actor_id=self.env.actor,
            profile_id=profile,
            classifications=["internal"],
            source_acl_ids=[],
            v2_writer_enabled=load_content_writer_config().v2_writer_enabled,
            pipeline=load_extraction_config().pipeline,
        )

    def drain(self, *, timeout: float = 3600) -> None:
        """Process and import until no work remains; retries wait out their delay."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            worked = self.worker.run_one()
            imported = self.env.parts.importer.run_one()
            if worked or imported:
                continue
            with self.env.engine.connect() as conn:
                pending = conn.scalar(
                    select(func.count())
                    .select_from(jobs)
                    .where(jobs.c.state.in_(["queued", "retry", "running"]))
                )
                undelivered = conn.scalar(
                    text("SELECT count(*) FROM document_job_outbox WHERE delivered_at IS NULL")
                )
            if not pending and not undelivered:
                return
            time.sleep(1)
        raise TimeoutError("qualification queue did not drain")


@contextmanager
def live_session(
    env: Isolated,
    settings: LiveSettings,
    *,
    transport_url: str | None = None,
    guard: HostInferenceGuard | None = None,
    limits: Any = None,
) -> Iterator[Session_]:
    guard = guard or HostInferenceGuard(settings.provider_url)
    owned = not guard.held
    if owned:
        guard.acquire()
    try:
        timings: list[dict[str, Any]] = []
        converter = CountingConverter(guard.staging_root)
        worker = processing_worker(
            env.parts,
            provider_url=settings.provider_url,
            api_key=settings.api_key,
            model=settings.model,
            revision=settings.revision,
            guard=guard,
            transport_url=transport_url,
            supervisor=converter,
            observe=timings.append,
            limits=limits,
        )
        yield Session_(env, guard, worker, converter, timings)
    finally:
        if owned:
            guard.release()


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _selector_text(document: DoclingDocument, binding: dict[str, Any]) -> str | None:
    block = binding.get("block_id") or ""
    if binding["precision"] == "span" and block.startswith("text-"):
        item = document.texts[int(block.split("-", 1)[1])]
        return item.text[binding["char_start"] : binding["char_end"]]
    if binding["precision"] == "table_cell" and block.startswith("table-"):
        table = document.tables[int(block.split("-", 1)[1])]
        box = binding["bbox"]
        page = document.pages[table.prov[0].page_no]
        for cell in table.data.table_cells:
            if cell.bbox is None:
                continue
            cell_box = cell.bbox.to_top_left_origin(page.size.height)
            if all(
                math.isclose(a, b, abs_tol=1e-6)
                for a, b in zip(
                    (cell_box.l, cell_box.t, cell_box.r, cell_box.b),
                    (box["x0"], box["y0"], box["x1"], box["y1"]),
                    strict=True,
                )
            ):
                return cell.text
    return None


def evidence_check(document: DoclingDocument, value: str, bindings: list[dict[str, Any]]) -> str:
    """`unresolved`, `supported` or `fabricated` for one assertion's selectors."""
    resolved = [b for b in bindings if b["precision"] in ("span", "table_cell")]
    if not resolved:
        return "unresolved"
    if resolved[0]["precision"] == "table_cell":
        texts = [_selector_text(document, b) for b in resolved]
        return "supported" if len(texts) == 1 and texts[0] == value else "fabricated"
    pieces = [_selector_text(document, b) for b in sorted(resolved, key=lambda b: b["char_start"])]
    if any(piece is None for piece in pieces):
        return "fabricated"
    # Multi-region selectors over one item must cover the value's characters exactly.
    return "supported" if "".join(pieces) == value else "fabricated"  # type: ignore[arg-type]


def attempt_metadata(env: Isolated, row: Any) -> list[dict[str, Any]]:
    """Run metadata of every attempt that published a run, failed ones included."""
    key = _accepted_key(env, row["payload"]["version_id"])
    found = []
    for attempt in range(1, row["attempt"] + 1):
        try:
            run = env.parts.store.load_run_bundle(
                tenant_id=UUID(row["tenant_id"]),
                knowledge_base_id=UUID(row["knowledge_base_id"]),
                artifact_id=key.artifact_id,
                run_id=uuid5(UUID(row["id"]), f"attempt:{attempt}"),
                artifact_key=key,
            )
        except Exception:  # no run for this attempt (failed before interpretation)
            continue
        found.append(json.loads(run.files["metadata.json"]))
    return found


def score_case(
    env: Isolated, job_id: UUID, profile_id: str, expected: dict[str, Any]
) -> dict[str, Any]:
    with env.engine.connect() as conn:
        row = conn.execute(select(jobs).where(jobs.c.id == str(job_id))).mappings().one()
        reasons = list(
            conn.scalars(
                select(events.c.reason).where(
                    events.c.job_id == str(job_id), events.c.reason.is_not(None)
                )
            )
        )
    case: dict[str, Any] = {
        "job_state": row["state"],
        "attempts": row["attempt"],
        "failure_reasons": reasons,
        "fields": {},
    }
    # Engine identity and call phases whatever the outcome (Code Review M5).
    try:
        attempts = attempt_metadata(env, row)
    except NoResultFound:  # no ready bundle: the job failed before interpretation
        attempts = []
    if attempts:
        case["pipeline_identity"] = attempts[-1].get("pipeline_identity")
        case["requested_configuration"] = attempts[-1].get("requested_configuration")
    case["call_phases"] = sorted(
        {
            str(record.get("phase"))
            for metadata in attempts
            for kind in ("calls", "rejections")
            for record in metadata.get("diagnostics", {}).get(kind, [])
        }
    )
    if row["state"] != "complete":
        case["status"] = "failed"
        for name, spec in expected.items():
            case["fields"][name] = {
                "expected_present": spec["value"] is not None,
                "correct": False,
                # A failed run neither abstains nor answers.
                "abstained": False,
                "evidence": "none",
            }
        return case
    store = env.parts.store
    run_ref = row["result_ref"]
    run_id = UUID(run_ref.split("/")[3])
    key = _accepted_key(env, row["payload"]["version_id"])
    artifact_id = key.artifact_id
    tenant, kb = UUID(row["tenant_id"]), UUID(row["knowledge_base_id"])
    run = store.load_run_bundle(
        tenant_id=tenant,
        knowledge_base_id=kb,
        artifact_id=artifact_id,
        run_id=run_id,
        artifact_key=key,
    )
    result = InterpretationResult.model_validate_json(run.files["result.json"])
    metadata = json.loads(run.files["metadata.json"])
    # S0003-AC3: the provenance ledger and native item references are retained
    # as run outputs (QA review). Only identifiers, never source text.
    ledger = json.loads(run.files["provenance.json"]) or {}
    case["run_files"] = sorted(run.files)
    case["ledger_item_refs"] = sorted(
        {
            ref
            for chunk in (ledger.get("chunks") or {}).values()
            for ref in chunk.get("doc_item_refs", [])
        }
    )
    case["ledger_ref"] = result.provenance_ledger_ref
    bundle = store.load_verified(key)
    document = DoclingDocument.model_validate_json(
        bundle.files[bundle.manifest.docling_document.path]
    )
    template = load_profile(profile_id).template
    values: dict[str, list[str]] = {}
    bindings: dict[str, list[list[dict[str, Any]]]] = {}
    for assertion in result.assertions:
        value = assertion.value.get("value")
        if value is None:
            continue
        values.setdefault(assertion.slot_type, []).append(value)
        bindings.setdefault(assertion.slot_type, []).append(
            [e.model_dump(mode="json") for e in assertion.evidence]
        )
    try:
        template.model_validate({k: v[0] for k, v in values.items() if len(v) == 1})
        schema_valid = all(len(v) == 1 for v in values.values())
    except Exception:
        schema_valid = False
    calls = metadata["diagnostics"]["calls"]
    # Pre-dispatch rejections never become call records (Code Review H1).
    rejections = metadata["diagnostics"].get("rejections", [])
    case.update(
        status=result.status,
        schema_valid=schema_valid,
        run_id=str(run_id),
        artifact_id=str(artifact_id),
        bundle_contract=bundle.key.contract_version,
        warnings=result.warnings,
        calls=len(calls),
        prompt_tokens=sum(c["prompt_tokens"] or 0 for c in calls),
        completion_tokens=sum(c["completion_tokens"] or 0 for c in calls),
        max_reserved_tokens=max((c["reserved_tokens"] for c in calls), default=0),
        over_budget_calls=sum(c["reserved_tokens"] > CONTEXT_TOKENS for c in calls),
        context_rejections=sum(r["outcome"] == "context_limit_exceeded" for r in rejections),
        budget_rejections=sum(r["failure_class"] == "budget" for r in rejections),
        rejections=len(rejections),
        pipeline_identity=metadata.get("pipeline_identity"),
        requested_configuration=metadata.get("requested_configuration"),
    )
    with Session(env.engine) as session:
        case["review_items"] = session.scalar(
            select(func.count())
            .select_from(ReviewItemRow)
            .join(Assertion, Assertion.id == ReviewItemRow.assertion_id)
            .where(Assertion.run_id == run_id)
        )
    for name, spec in expected.items():
        predicted = values.get(name, [])
        expected_value = spec["value"]
        field_row: dict[str, Any] = {
            "expected_present": expected_value is not None,
            "predicted_count": len(predicted),
        }
        if expected_value is None:
            field_row["abstained"] = not predicted
            field_row["correct"] = False
        else:
            field_row["correct"] = len(predicted) == 1 and normalize(predicted[0]) == normalize(
                expected_value
            )
        checks = [
            evidence_check(document, value, binding)
            for value, binding in zip(predicted, bindings.get(name, []), strict=True)
        ]
        field_row["evidence_checks"] = checks
        field_row["fabricated"] = checks.count("fabricated")
        field_row["evidence"] = (
            checks[0] if len(checks) == 1 else ("none" if not checks else "multiple")
        )
        case["fields"][name] = field_row
    return case


def _accepted_key(env: Isolated, version_id: str) -> Any:
    """The ready artifact for the job's document version (v2, or its v1 fallback)."""
    from brain_persistence.content_repository import ContentArtifactRepository
    from brain_persistence.models import ContentArtifact

    with Session(env.engine) as session:
        artifact_id = session.scalars(
            select(ContentArtifact.id).where(
                ContentArtifact.document_version_id == UUID(version_id),
                ContentArtifact.publication_state == "ready",
            )
        ).one()
        return ContentArtifactRepository(session).get_metadata(artifact_id).key


def nearest_rank_p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def aggregate(
    cases: list[dict[str, Any]],
    latencies: list[float],
    documents: int,
    completed_latencies: list[float] | None = None,
) -> dict[str, Any]:
    present = [f for c in cases for f in c["fields"].values() if f["expected_present"]]
    absent = [f for c in cases for f in c["fields"].values() if not f["expected_present"]]
    correct = [f for f in present if f["correct"]]
    completed = [c for c in cases if c["job_state"] == "complete"]
    return {
        "document_profiles": len(cases),
        "completed_runs": len(completed),
        "explicit_failures": len(cases) - len(completed),
        "schema_validity": (
            sum(bool(c.get("schema_valid")) for c in completed) / len(completed)
            if completed
            else None
        ),
        "silently_invalid_runs": sum(not c.get("schema_valid") for c in completed),
        "field_accuracy": len(correct) / len(present) if present else None,
        "abstention": sum(f["abstained"] for f in absent) / len(absent) if absent else None,
        "fabricated_evidence": sum(
            f.get("fabricated", 0) for c in cases for f in c["fields"].values()
        ),
        "evidence_resolution": (
            sum(f["evidence"] == "supported" for f in correct) / len(correct) if correct else None
        ),
        "over_budget_calls": sum(c.get("over_budget_calls", 0) for c in cases),
        "context_rejections": sum(c.get("context_rejections", 0) for c in cases),
        "budget_rejections": sum(c.get("budget_rejections", 0) for c in cases),
        "latency_p95_seconds": nearest_rank_p95(latencies),
        # Secondary: completed runs only, comparable with earlier reports.
        "latency_p95_completed_seconds": nearest_rank_p95(completed_latencies or []),
        "review_items_per_document": (
            sum(c.get("review_items", 0) for c in cases) / documents if documents else None
        ),
        # Failed runs add no review items; compare like for like (QA review).
        "review_items_per_completed_run": (
            sum(c.get("review_items", 0) for c in completed) / len(completed) if completed else None
        ),
        "model_calls": sum(c.get("calls", 0) for c in cases),
        "prompt_tokens": sum(c.get("prompt_tokens", 0) for c in cases),
        "completion_tokens": sum(c.get("completion_tokens", 0) for c in cases),
        "present_fields": len(present),
        "absent_fields": len(absent),
        "correct_fields": len(correct),
    }


def gpu_memory_used_mib() -> int | None:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return int(out.stdout.split()[0])
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return None


def run_pipeline(
    url: str, settings: LiveSettings, corpus: Path, pipeline: str, documents: list[dict[str, Any]]
) -> dict[str, Any]:
    started = time.time()
    gpu_peak = gpu_memory_used_mib()
    with (
        isolated(url, pipeline, v2_writer_enabled=True) as env,
        live_session(env, settings) as live,
    ):
        submitted: list[tuple[str, str, UUID]] = []
        for document in documents:
            for profile in PROFILES:
                job = live.submit(corpus / document["file"], profile)
                submitted.append((document["id"], profile, job))
        try:
            live.drain()
        except WorkerStopped as exc:
            return {"pipeline": pipeline, "void": True, "void_reason": exc.code}
        current = gpu_memory_used_mib()
        gpu_peak = max(filter(None, (gpu_peak, current)), default=None)
        # PRD: p95 wall time per document-profile interpretation. Every attempt of
        # a job counts, failed ones included (Code Review M6).
        timings: dict[str, float] = {}
        for t in live.timings:
            end = t.get("result_published", t.get("interpretation_finished"))
            if end is not None:
                job_id = str(t["job_id"])
                timings[job_id] = timings.get(job_id, 0.0) + end - t["interpretation_started"]
        cases = []
        latencies = []
        completed_latencies = []
        for document_id, profile, job in submitted:
            expected = json.loads((corpus / f"expectations/{document_id}.json").read_text())
            case = score_case(env, job, profile, expected["profiles"][profile])
            case.update(document_id=document_id, profile=profile, job_id=str(job))
            if str(job) in timings:
                case["latency_seconds"] = timings[str(job)]
                latencies.append(timings[str(job)])
                if case["job_state"] == "complete":
                    completed_latencies.append(timings[str(job)])
            cases.append(case)
        provider_failure = sorted(
            {r for c in cases for r in c["failure_reasons"] if r in PROVIDER_FAILURES}
        )
        return {
            "pipeline": pipeline,
            "void": bool(provider_failure),
            "void_reason": provider_failure or None,
            "config_sha256": env.config_sha256,
            "isolated_schema": env.schema,
            "conversions": live.converter.launches,
            "documents": len(documents),
            "metrics": aggregate(cases, latencies, len(documents), completed_latencies),
            "gpu_memory_used_mib_peak_sampled": gpu_peak,
            "started_at": started,
            "finished_at": time.time(),
            "cases": cases,
        }


def pins(settings: LiveSettings) -> dict[str, Any]:
    from brain_extraction.docling_graph_pipeline import DOCLING_GRAPH_WHEEL_SHA256
    from brain_ingestion.item_provenance import ocr_asset_pins

    return {
        "packages": {
            name: version(name)
            for name in (
                "docling",
                "docling-core",
                "docling-graph",
                "rapidocr",
                "openai",
                "transformers",
            )
        },
        "docling_graph_wheel_sha256": DOCLING_GRAPH_WHEEL_SHA256,
        "model": settings.model,
        "model_revision": settings.revision,
        "tokenizer_revision": settings.revision,
        "context_tokens": CONTEXT_TOKENS,
        "ocr_assets": ocr_asset_pins(),
        "python": sys.version.split()[0],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument(
        "--pipelines",
        nargs="+",
        choices=sorted(EXTRACTION_PIPELINES),
        default=["direct-baseline", "graph-dense", "graph-direct"],
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--documents", nargs="*", help="Subset of document ids (smoke only)")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("reports are immutable: choose a new output path")
    url = os.environ["BRAIN_TEST_POSTGRES_URL"]
    settings = LiveSettings.from_environment()
    verify_corpus(args.corpus)
    manifest = yaml.safe_load((args.corpus / "corpus.yaml").read_text())
    documents = [
        d for d in manifest["documents"] if not args.documents or d["id"] in args.documents
    ]
    report: dict[str, Any] = {
        # 2: latency_p95_seconds covers every document-profile and attempt (M6); v1
        # (the recorded F0005 report) measured completed runs only.
        "report_version": 2,
        "corpus_id": manifest["corpus_id"],
        "corpus": corpus_identity(args.corpus),
        "subset": args.documents or None,
        "pins": pins(settings),
        "committed_config_sha256": sha256_file(ROOT / "config/local.yaml"),
        "metric_definitions": (
            "PRD F0005 Qualification Thresholds; normalization = whitespace collapse + NFC"
        ),
        "engines": {},
    }
    for pipeline in args.pipelines:
        print(f"[f0005] running {pipeline} over {len(documents)} documents", flush=True)
        report["engines"][pipeline] = run_pipeline(url, settings, args.corpus, pipeline, documents)
        print(
            f"[f0005] {pipeline}: "
            + json.dumps(report["engines"][pipeline].get("metrics"), sort_keys=True),
            flush=True,
        )
    report["void"] = any(engine.get("void") for engine in report["engines"].values())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(report, handle, indent=2, sort_keys=True, default=str)
    print(f"[f0005] report: {args.output} void={report['void']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
