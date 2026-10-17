# Action Context

> Seeded by init-run.py. Fill the judgment sections before the first gate.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** plan-review
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0004
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0004-content-artifact-model
- **feature_slug:** content-artifact-model
- **mode:** clean
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-10-16-a186bc18
- **run_id:** 2026-10-16-a186bc18

## Inputs

- **PLAN_SCOPE:** feature (operator selection, 2026-10-16)
- **TARGET:** F0004
- **DIFF_RANGE:** not supplied — the review covers the approved planning package at product HEAD `99efd49` (merge of PR #23, "approve F0004 content artifact model plan")
- **FEATURE_SLUG:** content-artifact-model (REGISTRY.md row F0004)
- **FEATURE_PATH:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/features/F0004-content-artifact-model
- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain (source: environment, confirmed by `_product_root.py`)
- **Prior plan run:** 2026-10-15-bbd8df01 (plan action, Phase A + B approved)
- **Framework used for gate execution:** nebula-agents pin `c218bf1776f509a30f71967a1ee79879caa9a000` (BLUEPRINT §0 / ci-gates.yml), run from a detached worktree. Framework `main` (`3716308`) cannot load the product's `.nebula-project.yaml` because #94 renamed the `{PRODUCT_ROOT}` placeholder to `{NEBULA_PRODUCT_ROOT}`; see README Open Follow-ups. The run skeleton was initialized with `main`'s init-run.py.

## Assumptions

- The product's declared framework pin is the authoritative executor for its manifest checks.
- KG lookup and coverage are routing aids only; every readiness judgment cites the raw feature, ADR, schema, SQL, API or source file.
- Runtime paths labelled "implementation target" in the assembly plan are allowed to be absent (plan-review-checklist Evidence boundary). Existing paths cited as audited behavior must exist.

## Scope Boundaries

- In scope: everything under FEATURE_PATH; ADR-0073 and the ADRs F0004 is governed by (0003/0004/0037/0040/0058/0059/0060/0064/0065); schemas content-artifact-manifest{,-v2,-read}, content-records-v2, document-date-record, interpretation-output-manifest; the `/content` paths in api/brain-api.yaml; security/policies/policy.csv; the F0004 KG shard and its nodes; the existing source files the assembly plan names as audited behavior.
- Out of scope, except to record discovered impact: F0005, F0016, F0022 and F0026 plans; implementation; any edit to plan, KG, tracker, story, schema, contract or source files; feature evidence packages.
- Read-only: this run writes only inside its own run folder.

## Lifecycle Stage

- plan-review run initialized
