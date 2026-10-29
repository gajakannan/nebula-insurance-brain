"""F0005 Step 6 / S0004-AC6/AC7: committed pipeline selection, pinning and decisions.

Offline cases prove configuration validation and job identity. The live case
restarts the worker under each decision's settings, submits a new source each
time and verifies engine/writer identity while earlier runs, bundles and pinned
jobs stay unchanged.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from uuid import uuid4

import pytest
import yaml
from brain_content.config import ConfigError, load_extraction_config
from brain_ingestion.document_worker import LEGACY_PIPELINE, DocumentTask
from brain_ingestion.worker_cli import reject_guard_override
from brain_jobs.queue import jobs
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent))
from f0005_live_support import (  # type: ignore[import-not-found]  # noqa: E402
    CORPUS,
    ROOT,
    qualification,
    require_live,
)

COMMITTED = ROOT / "config/local.yaml"

# Assembly plan Step 7 settings table.
DECISIONS = {
    "initial": ("direct-baseline", False),
    "accepted": ("graph-dense", True),
    "threshold_miss": ("direct-baseline", False),
    "failed_verdict": ("direct-baseline", False),
    "operator_rejection": ("direct-baseline", False),
    "rollback_after_acceptance": ("direct-baseline", True),
}


def write_config(path: Path, pipeline: object, v2: bool, root: Path, **extra: object) -> None:
    data = {
        "content": {"v2_writer_enabled": v2},
        "extraction": {"pipeline": pipeline},
        "object_store": {"provider": "filesystem", "root": str(root), "immutable": True},
        **extra,
    }
    path.write_text(yaml.safe_dump(data))


def test_committed_configuration_selects_the_direct_baseline_with_v2_disabled():
    data = yaml.safe_load(COMMITTED.read_text())
    assert data["extraction"]["pipeline"] == "direct-baseline"
    assert data["content"]["v2_writer_enabled"] is False


@pytest.mark.parametrize("value", ["graph", "Graph-Dense", "", None, 7])
def test_unknown_or_missing_pipeline_fails_startup(tmp_path, monkeypatch, value):
    config = tmp_path / "local.yaml"
    write_config(config, value, False, tmp_path)
    monkeypatch.setenv("BRAIN_LOCAL_CONFIG_PATH", str(config))
    with pytest.raises(ConfigError):
        load_extraction_config()
    config.write_text(yaml.safe_dump({"content": {"v2_writer_enabled": False}}))
    with pytest.raises(ConfigError, match="explicitly"):
        load_extraction_config()


def test_no_environment_variable_selects_a_pipeline(tmp_path, monkeypatch):
    config = tmp_path / "local.yaml"
    write_config(config, "direct-baseline", False, tmp_path)
    monkeypatch.setenv("BRAIN_LOCAL_CONFIG_PATH", str(config))
    for name in (
        "BRAIN_EXTRACTION_PIPELINE",
        "EXTRACTION_PIPELINE",
        "BRAIN_ENABLE_GRAPH_CANDIDATE",
    ):
        monkeypatch.setenv(name, "graph-dense")
    assert load_extraction_config().pipeline == "direct-baseline"


def test_isolated_config_cannot_move_the_host_guard(tmp_path, monkeypatch):
    config = tmp_path / "local.yaml"
    write_config(config, "graph-dense", False, tmp_path, inference_guard={"directory": "/tmp/x"})
    monkeypatch.setenv("BRAIN_LOCAL_CONFIG_PATH", str(config))
    with pytest.raises(ConfigError, match="guard"):
        reject_guard_override()


def test_historical_job_without_pipeline_keeps_its_pre_change_meaning():
    legacy = {
        "document_id": str(uuid4()),
        "version_id": str(uuid4()),
        "source_sha256": "a" * 64,
        "recipe_sha256": "b" * 64,
        "profile_id": "gl-limits-a",
        "profile_version": "1",
        "schema_sha256": "c" * 64,
        "actor_id": str(uuid4()),
        "correlation_id": str(uuid4()),
    }
    task = DocumentTask.model_validate(legacy)
    assert task.pipeline is None and task.effective_pipeline == LEGACY_PIPELINE == "graph-direct"
    # Its payload is not rewritten with the current default.
    assert "pipeline" not in task.model_dump(mode="json", exclude_defaults=True)


def _tree_digest(root: Path, prefixes: tuple[str, ...]) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.relative_to(root).parts[0] in prefixes
    }


def test_decision_branches_restart_and_new_sources_use_the_selected_engine_and_writer(tmp_path):
    url, settings = require_live()
    committed_before = hashlib.sha256(COMMITTED.read_bytes()).hexdigest()
    # gl-q-005 and gl-q-009 are the corpus documents that publish v2: the accepted
    # and rollback branches use them, so v2 readability is actually exercised (M5).
    documents = ["gl-q-004", "gl-q-005", "gl-q-002", "gl-q-003", "gl-q-006", "gl-q-009"]
    rows = []
    with qualification.isolated(url, "direct-baseline", v2_writer_enabled=False) as env:
        previous: dict[str, str] = {}
        pinned: dict[str, dict] = {}
        for (decision, (pipeline, v2)), document in zip(DECISIONS.items(), documents, strict=True):
            write_config(env.config_path, pipeline, v2, env.content_root)
            # Restart: a new composition reads the changed settings.
            with qualification.live_session(env, settings) as live:
                job = live.submit(CORPUS / f"documents/{document}.pdf", "gl-limits-b")
                live.drain(timeout=900)
            with env.engine.connect() as conn:
                row = conn.execute(select(jobs).where(jobs.c.id == str(job))).mappings().one()
            assert row["payload"]["pipeline"] == pipeline
            pinned[str(job)] = row["payload"]
            case = qualification.score_case(
                env,
                job,
                "gl-limits-b",
                json.loads((CORPUS / f"expectations/{document}.json").read_text())["profiles"][
                    "gl-limits-b"
                ],
            )
            identity = case.get("pipeline_identity") or {}
            # The writer decision is visible on the published artifact even when the
            # later interpretation fails organically.
            contract = qualification._accepted_key(
                env, row["payload"]["version_id"]
            ).contract_version
            expected_engine = (
                "direct-baseline" if pipeline == "direct-baseline" else "docling-graph"
            )
            # Engine identity whatever the outcome; no run mixes engines (M5).
            assert identity, f"no published run for {decision}"
            assert identity["name"] == expected_engine
            phases = case["call_phases"]
            if pipeline == "direct-baseline":
                assert case["requested_configuration"]["engine"] == "direct-baseline"
                # No Graph call on rejection/default/rollback jobs.
                assert not any(
                    p.startswith("dense_") or p == "direct_extraction" for p in phases
                ), phases
            elif case["job_state"] == "complete":
                assert phases and all(p.startswith("dense_") for p in phases), phases
            elif any(not p.startswith("dense_") for p in phases):
                # Graph's dense-to-direct fallback happened: never accepted, and the
                # job records a model reason (the failed call's, or the fallback's).
                assert case["failure_reasons"], phases
                assert all(r.startswith("model_") for r in case["failure_reasons"]), case
            # Writer: v1 when disabled; v2 (or the audited per-document v1 fallback) when enabled.
            if not v2:
                assert contract == 1
            if decision in ("accepted", "rollback_after_acceptance"):
                # The qualified v2 writer survives rollback, and its bundle reads back.
                key = qualification._accepted_key(env, row["payload"]["version_id"])
                assert key.contract_version == 2
                assert env.parts.store.load_verified(key).key == key
            rows.append(
                {
                    "decision": decision,
                    "pipeline": pipeline,
                    "v2_writer_enabled": v2,
                    "document": document,
                    "job_state": case["job_state"],
                    "engine": identity.get("name"),
                    "bundle_contract": contract,
                    "config_sha256": hashlib.sha256(env.config_path.read_bytes()).hexdigest(),
                }
            )
            # Every earlier accepted byte and run is unchanged by the new decision.
            current = _tree_digest(env.content_root, ("bundles", "runs", "sources"))
            assert all(current.get(path) == digest for path, digest in previous.items())
            previous = current
        # A legacy queued candidate (pre-selection payload) keeps graph-direct even
        # though the current default is the baseline; its payload is not rewritten.
        write_config(env.config_path, "direct-baseline", False, env.content_root)
        with qualification.live_session(env, settings) as live:
            legacy = live.submit(CORPUS / "documents/gl-q-012.pdf", "gl-limits-b")
            with env.engine.begin() as conn:
                payload = conn.execute(
                    select(jobs.c.payload).where(jobs.c.id == str(legacy))
                ).scalar_one()
                payload = {k: v for k, v in payload.items() if k != "pipeline"}
                conn.execute(jobs.update().where(jobs.c.id == str(legacy)).values(payload=payload))
            live.drain(timeout=900)
        legacy_case = qualification.score_case(
            env,
            legacy,
            "gl-limits-b",
            json.loads((CORPUS / "expectations/gl-q-012.json").read_text())["profiles"][
                "gl-limits-b"
            ],
        )
        with env.engine.connect() as conn:
            assert (
                "pipeline"
                not in conn.execute(
                    select(jobs.c.payload).where(jobs.c.id == str(legacy))
                ).scalar_one()
            )
        if legacy_case["job_state"] == "complete":
            requested = legacy_case["requested_configuration"]
            assert requested["extraction_contract"] == "direct" and "pipeline" not in requested
            assert legacy_case["pipeline_identity"]["name"] == "docling-graph"
        rows.append(
            {
                "decision": "legacy_queued_candidate",
                "job_state": legacy_case["job_state"],
                "engine": (legacy_case.get("pipeline_identity") or {}).get("name"),
                "reasons": legacy_case["failure_reasons"],
            }
        )
        with env.engine.connect() as conn:
            for job_id, payload in pinned.items():
                assert (
                    conn.execute(select(jobs.c.payload).where(jobs.c.id == job_id)).scalar_one()
                    == payload
                )
    assert hashlib.sha256(COMMITTED.read_bytes()).hexdigest() == committed_before
    assert any(r.get("bundle_contract") == 2 for r in rows if r.get("v2_writer_enabled"))
    print(json.dumps({"decision_branches": rows}))


def test_queue_depth_is_committed_and_validated(tmp_path, monkeypatch):
    from brain_content.config import load_job_queue_config

    assert yaml.safe_load(COMMITTED.read_text())["jobs"]["max_queue_depth"] == 100
    config = tmp_path / "local.yaml"
    for bad in (0, -5, "100", 2.5):
        write_config(config, "direct-baseline", False, tmp_path, jobs={"max_queue_depth": bad})
        monkeypatch.setenv("BRAIN_LOCAL_CONFIG_PATH", str(config))
        with pytest.raises(ConfigError, match="max_queue_depth"):
            load_job_queue_config()
    write_config(config, "direct-baseline", False, tmp_path, jobs={"max_queue_depth": 7})
    assert load_job_queue_config().max_queue_depth == 7
