from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/validation/validate_plan_readiness.py"
spec = importlib.util.spec_from_file_location("brain_readiness", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


@pytest.fixture
def product(tmp_path):
    root = tmp_path / "brain"
    for path in ["docs/agent-instructions.md", "docs/plan-review-checklist.md", "planning-mds/BLUEPRINT.md", "planning-mds/features/REGISTRY.md", "planning-mds/examples/README.md"]:
        dest = root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, dest)
    for folder in ["planning-mds/architecture", "planning-mds/security", "planning-mds/features/F0001-repository-and-engineering-foundation"]:
        shutil.copytree(ROOT / folder, root / folder)
    shutil.copy2(ROOT / "planning-mds/features/TRACKER-GOVERNANCE.md", root / "planning-mds/features/TRACKER-GOVERNANCE.md")
    return root


def run(root, cwd, *args):
    result = subprocess.run([sys.executable, str(SCRIPT), "--product-root", str(root), *args], cwd=cwd, text=True, capture_output=True)
    return result.returncode, json.loads(result.stdout)


def test_valid_plan_with_future_runtime_paths(product, tmp_path):
    assert not (product / "engine").exists()
    for cwd in [tmp_path, product, product / "docs"]:
        rc, result = run(product, cwd, "--plan-scope", "feature", "--target", "F0001")
        assert rc == 0 and result["status"] == "pass"


@pytest.mark.parametrize("mutation,rule", [("empty", "BRAIN-SECTIONS"), ("reference", "BRAIN-REFERENCE"), ("checklist", "BRAIN-CHECKLIST"), ("missing", "BRAIN-ARTIFACT")])
def test_invalid_inputs_fail(product, mutation, rule):
    prd = product / "planning-mds/features/F0001-repository-and-engineering-foundation/PRD.md"
    if mutation == "empty": prd.write_text("")
    if mutation == "reference": prd.write_text(prd.read_text() + "\n[Required planning](missing-plan.md)\n")
    if mutation == "missing": prd.unlink()
    if mutation == "checklist": (product / "docs/plan-review-checklist.md").write_text("# Nothing to check\n")
    rc, result = run(product, product, "--plan-scope", "feature", "--target", "F0001")
    assert rc == 1 and rule in {f["rule_id"] for f in result["findings"]}


def test_project_and_feature_set_scopes(product):
    for scope, target in [("project", "project"), ("feature-set", "F0001")]:
        assert run(product, product, "--plan-scope", scope, "--target", target)[0] == 0
    assert run(product, product, "--plan-scope", "project", "--target", "F0001")[0] == 2
    assert run(product, product, "--plan-scope", "feature", "--target", "F9999")[0] == 1


def test_missing_governing_source_fails(product):
    (product / "planning-mds/architecture/decisions/ADR-0010-provenance-is-mandatory.md").unlink()
    assert run(product, product, "--plan-scope", "feature", "--target", "F0001")[0] == 1


def test_examples_review_rule_is_required(product):
    checklist = product / "docs/plan-review-checklist.md"
    checklist.write_text("\n".join(line for line in checklist.read_text().splitlines()
                                   if not line.startswith("| BRAIN-EXAMPLES |")))
    rc, result = run(product, product, "--plan-scope", "feature", "--target", "F0001")
    assert rc == 1
    assert any("BRAIN-EXAMPLES" in finding["message"] for finding in result["findings"])


def test_validation_does_not_mutate_plans(product):
    before = {p: p.read_bytes() for p in product.rglob("*") if p.is_file()}
    validator.validate(product, "feature", "F0001")
    assert before == {p: p.read_bytes() for p in product.rglob("*") if p.is_file()}


def test_project_scope_detects_deleted_active_prd(product):
    (product / "planning-mds/features/F0001-repository-and-engineering-foundation/PRD.md").unlink()
    assert run(product, product, "--plan-scope", "project", "--target", "project")[0] == 1


def test_story_planning_reference_must_resolve(product):
    folder = product / "planning-mds/features/F0001-repository-and-engineering-foundation"
    story = next(folder.glob("F0001-S*.md"))
    story.write_text(story.read_text() + "\n[Missing source](missing-plan.md)\n")
    rc, result = run(product, product, "--plan-scope", "feature", "--target", "F0001")
    assert rc == 1 and any(f["rule_id"] == "BRAIN-REFERENCE" for f in result["findings"])
