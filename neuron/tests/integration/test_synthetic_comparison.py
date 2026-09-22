"""Synthetic orchestration/evidence expectations, never model-accuracy assertions."""

from __future__ import annotations

import runpy
from pathlib import Path


def test_baseline_direct_and_dense_comparison_with_recorded_responses(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[2] / "benchmarks/docling_graph_comparison.py"
    report = runpy.run_path(str(script))["run_comparison"](tmp_path)
    assert report["development_checks_passed"]
    assert report["model"] == "none — HTTP MockTransport only"
    assert len(report["rows"]) == 9
    for case in ("unique", "ambiguous", "multi-region"):
        rows = [row for row in report["rows"] if row["case"] == case]
        assert len({row["native_sha256"] for row in rows}) == 1
        dense = next(row for row in rows if row["engine"] == "dense")
        assert dense["model_calls"] == 2
        assert dense["checks"]["evidence_matches_expected"]
        assert dense["chunk_count"] > 1
        assert dense["estimated_prompt_tokens"] > 0
        assert next(row for row in rows if row["engine"] == "baseline")["model_calls"] == 1
    # Missing Graph refs must not be disguised as precise property evidence.
    direct = next(
        row for row in report["rows"] if row["engine"] == "direct" and row["case"] == "unique"
    )
    assert direct["status"] == "partial"
    assert not direct["checks"]["evidence_matches_expected"]
