"""F0005 S0004-AC7 post-decision check (G4 approved rejection, 2026-10-28).

Loads the committed config/local.yaml unchanged except for the content root,
starts a fresh worker composition (a restart), processes one ordinary source and
shows it ran the direct baseline with a v1 bundle and no Graph call.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import yaml
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[7]
spec = importlib.util.spec_from_file_location("f0005_qualification", ROOT / "neuron/benchmarks/f0005_qualification.py")
qualification = importlib.util.module_from_spec(spec)
sys.modules["f0005_qualification"] = qualification
spec.loader.exec_module(qualification)
from brain_jobs.queue import jobs  # noqa: E402

COMMITTED = ROOT / "config/local.yaml"
committed_sha = hashlib.sha256(COMMITTED.read_bytes()).hexdigest()
committed = yaml.safe_load(COMMITTED.read_text())
url = os.environ["BRAIN_TEST_POSTGRES_URL"]
settings = qualification.LiveSettings.from_environment()
with qualification.isolated(url, "direct-baseline", v2_writer_enabled=False) as env:
    config = dict(committed)
    config["object_store"] = {**committed["object_store"], "root": str(env.content_root)}
    env.config_path.write_text(yaml.safe_dump(config, sort_keys=True))
    with qualification.live_session(env, settings) as live:
        job = live.submit(ROOT / "neuron/fixtures/qualification/documents/gl-q-001.pdf", "gl-limits-a")
        live.drain(timeout=900)
    with env.engine.connect() as conn:
        row = conn.execute(select(jobs).where(jobs.c.id == str(job))).mappings().one()
    expected = json.loads((ROOT / "neuron/fixtures/qualification/expectations/gl-q-001.json").read_text())
    case = qualification.score_case(env, job, "gl-limits-a", expected["profiles"]["gl-limits-a"])
    key = qualification._accepted_key(env, row["payload"]["version_id"])
    result = {
        "committed_config_sha256": committed_sha,
        "committed_pipeline": committed["extraction"]["pipeline"],
        "committed_v2_writer_enabled": committed["content"]["v2_writer_enabled"],
        "job_state": row["state"],
        "job_pinned_pipeline": row["payload"]["pipeline"],
        "bundle_contract_version": key.contract_version,
        "run_engine": (case.get("pipeline_identity") or {}).get("name"),
        "requested_engine": (case.get("requested_configuration") or {}).get("engine"),
        "call_phases": case.get("call_phases"),
    }
    print(json.dumps({"post_decision_check": result}))
    assert result["committed_pipeline"] == "direct-baseline"
    assert result["committed_v2_writer_enabled"] is False
    assert result["job_pinned_pipeline"] == "direct-baseline"
    assert result["bundle_contract_version"] == 1
    assert result["run_engine"] == "direct-baseline"
    assert not any(p.startswith("dense_") or p == "direct_extraction" for p in result["call_phases"])
    print("POST-DECISION CHECK PASS")
