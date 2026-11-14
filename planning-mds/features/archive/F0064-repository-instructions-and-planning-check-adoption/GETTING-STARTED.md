# F0064 — Repository instructions and planning-check adoption — Getting Started

## Prerequisites

- This repository and `nebula-agents` checked out as siblings, with `nebula-agents` at the pin recorded in BLUEPRINT section 0 and `.github/workflows/ci-gates.yml` (`d90bbb6` at planning time).
- Python 3.12+ (the repository `.venv`) and the framework `.venv`.

## Services to Run

None. Repository tooling only.

## Environment Variables

- `NEBULA_PRODUCT_ROOT` — absolute path to this repository, or pass `--product-root` on every framework command. The framework must not infer the product from the working directory.

## Seed Data

None.

## How to Verify

```bash
# From this repository
python3 scripts/validation/validate_plan_readiness.py --plan-scope project --target project
python3 -m pytest -q scripts/validation/tests/test_plan_readiness.py

# From the nebula-agents checkout
python3 agents/scripts/project_context.py --product-root ../nebula-insurance-brain --action plan-review --json
python3 agents/scripts/project_checks.py --product-root ../nebula-insurance-brain --action plan-review \
  --plan-scope project --target project --list
```

## Key Files

- `.nebula-project.yaml`
- `docs/agent-instructions.md`, `docs/plan-review-checklist.md`
- `scripts/validation/validate_plan_readiness.py`, `scripts/validation/tests/test_plan_readiness.py`, `scripts/kg/validate_plan_compliance.py`
- `.github/workflows/ci-gates.yml` (`framework-validators` job)
- `CONTRIBUTING.md`, `nebula.code-workspace`, `docs/framework-adoption.md`, `planning-mds/framework-adoption-plan.md`

## Notes

- `project_checks.py` without `--list` needs a `--run-id`, and it writes evidence only inside the product (`planning-mds/operations/evidence/runs/`). A run folder outside the product is rejected with `path_escape`.
- `scripts/kg/hint.py` returns nothing for paths with fewer than two slashes (by design), so the root-level files (`.nebula-project.yaml`, `CONTRIBUTING.md`, `nebula.code-workspace`) resolve through `python3 scripts/kg/lookup.py capability:project-context-manifest` (or `capability:project-check-ci-enforcement`).
- For negative checks, copy the repository to a temporary directory and break the copy. Never stage a failure in the working tree.
- Once a feature has a `PRD.md`, project-scope readiness includes it, so this feature's own package must pass the Brain validator.
