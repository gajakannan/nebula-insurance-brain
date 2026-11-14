# Feature Assembly Plan — F0064: Repository instructions and planning-check adoption

**Created:** 2026-11-10
**Author:** Architect Agent
**Status:** Approved 2026-11-14 (`approve-phase-b`) — Phase B of plan run `2026-11-10-819c4124`

> Infrastructure variant of the assembly template: the tooling already exists. Each step is a re-verification of delivered behavior at framework pin `d90bbb6`, with exact commands, expected results and the repair rule. The entity, DTO, Casbin, timeline, HTTP, serialization and DI sections do not apply: there is no runtime code, endpoint, permission or persisted product data.

## Overview

Re-verify the Brain-side project-extension adoption delivered on 2026-09-07 against all 23 acceptance criteria, repair every defect found (G1 decision 3), and produce feature evidence for closeout. Expected source changes are limited to the documentation repairs in Step 4. Any further change is a defect repair and is logged as one.

## Build Order

| Step | Story | Kind | Expected source change |
|---|---|---|---|
| 1 | S0001 | Verify manifest resolution | None |
| 2 | S0002 | Verify instructions and checklist | None, unless a stale statement is found |
| 3 | S0003 | Verify validator contract and fixtures | None |
| 4 | S0004 | Verify CI wiring, pins, negative path; refresh docs | `docs/framework-adoption.md`, `planning-mds/framework-adoption-plan.md`, and `CONTRIBUTING.md` line 26 if the KG-test claim is stale |

## Existing Code (Must Be Modified)

| File | Current state | Change |
|---|---|---|
| `docs/framework-adoption.md` | "Remaining local hygiene" paragraph says the framework clone is still on a publication branch and local `main` is at `4eaf7b3`; "Both pins now name" `c218bf1` | State the current pin (`d90bbb6`, from BLUEPRINT section 0), mark hygiene complete, link F0064, and keep the 2026-09-07 publication record as dated history (S0004 AC6) |
| `planning-mds/framework-adoption-plan.md` | Header `Status: Local implementation verified; lifecycle review and release/pin coordination pending.`; the closing sections describe publication as blocked | Header becomes `Status: Delivered 2026-09-07; closed out by F0064 (plan run 2026-11-10-819c4124)`. Add a dated note that later sections are historical. Do not rewrite history (S0004 AC6) |
| `CONTRIBUTING.md` | Line 26 claims existing failures in framework-specific KG lookup fixtures | If Step 4.6 shows `scripts/kg/tests` passing, replace the claim with the observed result; if failures exist, they are defects (G1 decision 3) |

No other existing file is expected to change.

## New Files

None in source. Feature-run evidence lives under `planning-mds/operations/evidence/runs/{FEATURE_RUN_ID}/`.

## Step 1 — Manifest resolution (S0001)

Run from the `nebula-agents` checkout at `d90bbb6` with `NEBULA_PRODUCT_ROOT` unset, passing the root explicitly.

1. AC1/AC2: parse `.nebula-project.yaml` with `yaml.safe_load` and assert the exact fields: `version == 1`; instruction paths and the `actions` filter; one check with `id/action/stage/event/cwd/timeout_seconds`; `argv[1]` ends with `scripts/validation/validate_plan_readiness.py`; the placeholder set in `argv` equals `{NEBULA_PRODUCT_ROOT, PLAN_SCOPE, TARGET}`. Save the assertion script and output under `artifacts/test-results/s0001-*`.
2. AC3: `python3 agents/scripts/project_context.py --product-root ../nebula-insurance-brain --action plan-review --json`, then again with `--action plan`. Assert the instruction path order and the SHA-256 presence. Run each twice and diff the outputs to show determinism (NFE).
3. AC4: `python3 agents/scripts/project_checks.py --product-root ../nebula-insurance-brain --action plan-review --plan-scope project --target project --list` exits 0 with one check, `plan-readiness`.
4. AC5: for each `inputs` pattern, `glob.glob(pattern, recursive=True)` from the product root is non-empty. Enumerate the validator's reads (BLUEPRINT, two docs, eight governing sources, REGISTRY, feature README/STATUS/PRD/stories) and assert each matches a pattern.
5. Edge case: copy the repository to a temporary directory, delete `docs/agent-instructions.md` in the copy, and rerun step 2 against the copy. Expect a non-zero exit with a missing-instruction error. A zero exit is a framework-side defect: fix it in `nebula-agents`, advance the pin in CI and BLUEPRINT section 0 together, and redo Steps 1–4.

## Step 2 — Instructions and checklist (S0002)

1. AC1: inspect `docs/agent-instructions.md` for the source order, the explicit-root rule and the kg-source/compile rule; record line references.
2. AC2: run the three commands it lists from the product root and record their exit codes (expect 0). The instructions show `python3`; run with the repository `.venv` interpreter and record which one was used.
3. AC3: parse the checklist table, assert the header, the exact eight rule IDs, owners in the allowed set, and that each governing source resolves.
4. AC4: record the line references for the "not approval or regulatory compliance" statement and the not-applicable-rationale requirement.
5. AC5: `grep -rn "BRAIN-" ../nebula-agents/agents ../nebula-agents/*.md` and a search for a distinctive sentence of each Brain document. Expect no hits outside synthetic test fixtures; record the output.

## Step 3 — Validator contract (S0003)

1. AC1: project-scope run; assert the exact JSON and exit 0.
2. AC2: invoke `--plan-scope project --target F0001`, `--plan-scope feature --target F0001,F0002`, `--plan-scope feature-set --target F0001,F0001` and `--target F01`. Expect exit 2 with a `BRAIN-INVOCATION` finding each time. Then run a failing-structure case in a temporary copy (empty PRD section) and expect exit 1.
3. AC3: `python3 -m pytest -q scripts/validation/tests/test_plan_readiness.py` → 11 passed (record the count and names).
4. AC4: in a temporary copy, add an Active registry row whose folder has no PRD, and confirm it is selected. Confirm archived features are not selected.
5. AC5: `python3 scripts/kg/validate_plan_compliance.py planning-mds/features/F0064-.../PRD.md` → exit 0; with `README.md` (repository root) → exit 2.
6. AC6: `--plan-scope feature --target F0064` → pass.
7. AC7: hash every tracked file before and after Steps 3.1–3.6 (`git ls-files -z | xargs -0 sha256sum`); the outputs must be identical. Also run `git status --porcelain` before and after.
8. NFE: record the wall time of the project-scope run (must be under 60 s).

## Step 4 — CI wiring, pins and setup docs (S0004)

1. AC1: inspect the `framework-validators` job in `.github/workflows/ci-gates.yml` and record the line references for the fail-closed guard, the context resolution, the executor invocation with a generated run ID, and `if: always()` evidence upload.
2. AC2: compare the `ref:` in `ci-gates.yml` with the BLUEPRINT section 0 pin; they must be equal full SHAs.
3. AC3: copy the repository to a temporary directory and remove the `BRAIN-EXAMPLES` row from the copy's checklist. Run `project_checks.py --product-root <copy> --action plan-review --plan-scope project --target project --run-id <id>`. Expect a non-zero exit and a recorded `fail` result with a `BRAIN-CHECKLIST` finding. Copy that run folder into the feature evidence `artifacts/` and confirm the real working tree is unchanged.
4. AC5: confirm every script path named in `CONTRIBUTING.md` exists, and that the workspace folder paths resolve relative to `nebula.code-workspace`.
5. AC6: apply the documentation changes listed under Existing Code.
6. `CONTRIBUTING.md` line 26: run `.venv/bin/python -m pytest -q scripts/kg/tests` and repair the stale claim per the Existing Code table.
7. AC4: open the PR and record the CI run URL and per-job results. A red job blocks closeout.

## Scope Breakdown

| Layer | Required work |
|---|---|
| Backend / Frontend / AI | None |
| Documentation | Step 4 repairs |
| Quality Engineering | Steps 1–4 verification and evidence |
| DevOps | CI job inspection, pin agreement, CI run on PR (Step 4) |
| Code Review | Review the doc diffs and any defect repair |

## Dependency Order

Step 1 → Step 2 → Step 3 → Step 4. Step 4.7 (CI) runs last, on the PR that contains the closeout.

## Integration Checkpoints

### After Step 3

The project-scope validator, the fixtures and the shared executor `--list` agree (all pass) before any document is edited.

### Cross-Story Verification

The shared executor's real execution (Step 4.3 against the broken copy, and CI against the real tree) must use the same manifest the local runs used. Compare `manifest_hash` across the Step 1.2 output and the executor result.

## Integration Checklist

- [ ] All 23 ACs evidenced under the feature run's `artifacts/test-results/`
- [ ] Every defect found is repaired and re-verified; none deferred
- [ ] KG compile, drift and reproducibility pass after the doc edits; coverage report refreshed after `git add`
- [ ] CI green on the PR

## Risks and Blockers

- A framework-side defect blocks closeout until it is fixed in `nebula-agents` and the pin advances in CI and BLUEPRINT section 0 together (G1 decision 3).
- `hint.py` deliberately returns nothing for paths with fewer than two slashes. The root-level files (`.nebula-project.yaml`, `CONTRIBUTING.md`, `nebula.code-workspace`) are reachable through `lookup.py capability:<id>`. This is designed behavior, not a defect.

## Required Signoff Roles

| Role | Required | Why |
|---|---|---|
| Quality Engineer | Yes | Owns the Steps 1–4 verification evidence for all 23 ACs |
| Code Reviewer | Yes | Independent review of the doc repairs and any defect fix |
| DevOps | Yes | S0004 covers the CI workflow and the pin contract |
| Security Reviewer | No | No authentication, authorization, data boundary or secret handling changes. Project checks run repository code under the same trust model as other build scripts; the manifest forbids shell evaluation (S0001 AC2) |
| Architect | No | No architecture-risk exception; no ADR is created or changed |
