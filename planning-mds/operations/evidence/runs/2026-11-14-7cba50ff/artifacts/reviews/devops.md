# Deployability

Reviewer: Codex DevOps lane (role switch after reading `agents/devops/SKILL.md`). Scope: F0064 PRs 48–50, approved run `2026-11-14-3325803a`. NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`.

Canonical evidence prefix below: `planning-mds/operations/evidence/runs/2026-11-14-3325803a/`. Audit artifacts are under review run `2026-11-14-7cba50ff/`.

## Findings by severity

No DevOps-owned Critical, High, Medium or Low finding. The original closeout text names PR #49 for the last CI re-check although closeout landed in PR #50; PM owns this evidence-provenance drift. The audit obtained the actual final PR #50 results and all jobs passed, so there is no unresolved deployability or S0004 AC4 failure.

## Completion checks

| Check | Result and concrete evidence |
|---|---|
| Changed infrastructure and manifest booleans | PASS. The exact aggregate diff `35631a459d2cfd6aa2c2f3d1627f23c31524d691..6acd80560c0bc486bf9a7b28041631f907c2e901` has no Dockerfile, Compose, workflow, dependency, environment, migration, startup or runtime-source changes. This supports canonical `evidence-manifest.json` values `runtime_bearing=false`, `deployment_config_changed=false`, and the approved tooling-only scope (`feature-assembly-plan.md:7–30`). DevOps remains required because re-verification includes the existing CI contract. |
| Original runtime/toolchain preflight | PASS. Canonical `artifacts/test-results/g1-preflight.txt:1–27` records the framework SHA, clean framework tree, matching CI pin, product Python 3.12.13/PyYAML 6.0.2/pytest 9.0.3, framework/system Python 3.14.4, selected branch/base and explicit absolute product root. Those are the necessary tools for this repository-only feature; no server/container is needed. A fresh read-only framework HEAD probe also matches the pin (`artifacts/reviews/devops-framework-head.txt:1`). |
| CI fail-closed guard and shared executor | PASS. Raw `.github/workflows/ci-gates.yml:298–348` checks out product/framework separately, pins the framework at the full SHA, exits 1 if project-check support is absent, loads product context with an explicit root, generates a contract run ID, invokes the declared check through the executor, and uploads its evidence even after a check failure. This was checked in source, not accepted only from the inspection report. |
| Full pin agreement | PASS. `.github/workflows/ci-gates.yml:307` and `planning-mds/BLUEPRINT.md:33` both name `d90bbb6fc70dffcfa6d70379d42015e895a49fa0`. The audit did not change the pin. |
| Negative executor path and failure classification | PASS. Canonical `artifacts/test-results/s0004-ac3-negative.txt:1–5,20–21` records a deliberately broken temporary copy, executor exit 1, and no mutation/run in the real tree. The exact cited `s0004-ac3-copy-run/artifacts/project-checks/PR2-plan-readiness-b5192693076344109f8f450bb7297608.result.json:1–20` records `ok=false`, exit 1, no timeout, and `BRAIN-CHECKLIST` for missing `BRAIN-EXAMPLES`. Its sibling `.stdout.json` contains the same failure. This is an expected negative test, not a broken live toolchain or an accepted product defect. |
| Original PR #49 CI proof | PASS for the delivery commit. Canonical `artifacts/test-results/s0004-ac4-ci-checks-run1.txt:127–141` ends with every job passing and exit 0. Canonical `artifacts/test-results/s0004-ac4-ci-framework-validators.txt:1–22` pins head `db723d59964f12798b737114442b3ef15883e5f9`, records all extension steps succeeding, executor `ok=true`, and the uploaded evidence artifact URL. |
| Final closeout PR #50 CI proof | PASS. Fresh GitHub connector results are preserved in audit `artifacts/ci-workflows.json` and `artifacts/ci-pr50-jobs.json`. The latter names final head `abe5045f785bf4aea4c6dfa09783cc145d2cf1b7` at line 3. It records success for experience (line 10), runtime-stack (98), framework-validators (264), runtime-suites (364), product-gates (524), and reproducibility (611). Framework job `132622580186` in run `43652089357` explicitly passes support guard/context/executor/evidence-upload steps (313–335). Thus the actual closeout head meets S0004 AC4, independently of the stale original PR reference. |
| Environment/configuration/setup | PASS. `CONTRIBUTING.md:7–14,28–43` documents Python/dependencies, hook and merge-driver setup, and explicit product-root commands. `nebula.code-workspace:1–6` resolves `.` and `../nebula-agents`. Read-only Git config queries confirm `.githooks` and `true` for this clone. No new environment variable, service, port, job, runtime secret or config contract was introduced. |
| Rollback | Applicable scope is documentation and lifecycle record changes; no runtime/data state or migration was introduced. Runtime rollback rehearsal is unnecessary for this scope. |

## Explicit skips and limits

- No local container startup/build/smoke or deployment rehearsal was run by this audit: the feature has no runtime-bearing change, and the relevant executable surface is the repository CLI/CI toolchain. This follows the approved scope, not an unrecorded skipped layer.
- Production deployment, new environments, migrations and secrets rollout are not claimed; no such deliverable exists in F0064.
- The CI runtime-stack failure-diagnostics step is `skipped` because its condition is `if: failure()`; the job succeeds and teardown runs. This does not mean an acceptance test was skipped.
- GitHub workflow/job metadata and canonical raw CI executor output were checked. No additional CI rerun, workflow mutation, remote comment, deployment or evidence-package repair was performed.
- The standing pin-agreement rule is manual by approved design (`PRD.md:82`; S0004 `Out of Scope:55`). A new automatic pin guard is not required for this audit.

## FR3 self-review

PASS. All conclusions cite concrete workflow source, preflight commands, negative-test result JSON, or fresh final-head CI jobs. The original deployability summary was used only to find exact raw evidence. Expected failures and conditional skips have explicit explanations. PM retains ownership of stale closeout PR provenance; no DevOps issue is duplicated or silently repaired.
