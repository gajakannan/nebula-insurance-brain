# Action Context

> Seeded by init-run.py. Fill the judgment sections before the first gate.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** feature
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0064
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0064-repository-instructions-and-planning-check-adoption
- **feature_slug:** repository-instructions-and-planning-check-adoption
- **mode:** clean
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-14-3325803a
- **run_id:** 2026-11-14-3325803a

## Inputs

- FEATURE_ID `F0064`; MODE `clean`; SLICE_ORDER_SOURCE `assembly-plan` (Steps 1→4 of the approved feature-assembly-plan.md).
- NEBULA_PRODUCT_ROOT `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`, source: shell environment, resolved by `_product_root.py`.
- Framework `nebula-agents` at `d90bbb6fc70dffcfa6d70379d42015e895a49fa0`, which equals the CI `ref:` and the BLUEPRINT section 0 pin.
- Product base `origin/main` `fcb249d` (includes plan-approval PR #48); branch `feature/F0064-retro-closeout`.
- Plan run `2026-11-10-819c4124` (A+B, approved 2026-11-14). RUN_ID_PRIOR: null (no prior `latest-run.json`).
- KG lookup `F0064 --tier 2`: affects `capability:plan-readiness-validation`, `capability:project-check-ci-enforcement`, `capability:project-context-manifest`.

## Assumptions

- This is a retroactive re-verification. The tooling was delivered 2026-09-07 (Brain PR #1, framework PR #91 at `c218bf1`). Only Step 4 documentation repairs and defect repairs change source.
- G1 decision 3 (fix everything first) applies: no defect found here may be deferred.
- Negative cases run against temporary copies of the repository in the session scratchpad. The working tree is never broken to stage a failure.

## Scope Boundaries

- In scope: the four stories, 23 ACs, and the documentation repairs named in the assembly plan's Existing Code table.
- Out of scope: framework F0009 internals, native host adapters, new checklist rules, and an automated CI pin guard.
- No runtime code, UI, model call, endpoint, permission or migration.

## Lifecycle Stage

- feature run initialized
