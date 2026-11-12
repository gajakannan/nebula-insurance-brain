# Action Context

> Seeded by init-run.py. Fill the judgment sections before the first gate.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** plan
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0064
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0064-repository-instructions-and-planning-check-adoption
- **feature_slug:** repository-instructions-and-planning-check-adoption
- **mode:** clean
- **phase:** A+B
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-10-819c4124
- **run_id:** 2026-11-10-819c4124

## Inputs

- `planning-mds/framework-adoption-plan.md` and `docs/framework-adoption.md` (design and delivery record)
- Delivery commit `22410ed` (Brain PR #1) and `nebula-agents` PR #91 (`c218bf1`); current pin `d90bbb6`
- Plan-review `2026-10-30-ff4c758d` finding L1; roadmap review commit `2e9caac`
- Delivered files: `.nebula-project.yaml`, `docs/agent-instructions.md`, `docs/plan-review-checklist.md`, `scripts/validation/validate_plan_readiness.py` and fixtures, `scripts/kg/validate_plan_compliance.py`, `.github/workflows/ci-gates.yml`

## Assumptions

- Pre-plan observation at `d90bbb6` (2026-11-10, not closeout evidence): validator project scope `pass` with no findings; 11/11 fixtures pass; `project_context.py` and `project_checks.py --list` resolve the manifest.
- Pin agreement between CI and BLUEPRINT section 0 stays a manual rule (PRD assumption for G3).

## Scope Boundaries

- Brain-side deliverables only; framework F0009 mechanism is a pinned dependency (G1 decision 1).
- Native host adapters are a non-goal (G1 decision 2).
- Every re-verification defect is fixed before closeout (G1 decision 3).
- No runtime product code, API, schema, permission or migration.

## Lifecycle Stage

- plan run initialized
