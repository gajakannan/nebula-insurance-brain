# Feature Evidence README — F0064-repository-instructions-and-planning-check-adoption run 2026-11-14-3325803a

## Run Summary

This is the `feature` action for F0064, a retroactive re-verification and closeout of the Brain-side project-extension adoption delivered 2026-09-07 (Brain PR #1, `nebula-agents` PR #91). Claude Opus 5.5 ran it at the operator's request, coordinating the Architect, QE, DevOps, Code Reviewer and PM roles. All 23 acceptance criteria were re-verified at framework pin `d90bbb6`. Three stale documentation statements were repaired: in `docs/framework-adoption.md`, `planning-mds/framework-adoption-plan.md` and `CONTRIBUTING.md`. There were no runtime, UI or AI changes. PR #49.

## Status

`approved` (agrees with `evidence-manifest.json` `status`); `latest-run.json` written at G8 after `patch-prior-manifest.py` exited 0.

## Evidence Index

- `evidence-manifest.json` — schema v1
- `action-context.md`, `artifact-trace.md`, `gate-decisions.md`, `commands.log`, `lifecycle-gates.log`
- G0 `g0-assembly-plan-validation.md`; G1 `g1-runtime-preflight.md`
- G2 `g2-self-review.md`, `test-plan.md`, `test-execution-report.md`, `coverage-report.md`, `deployability-check.md`, `g2-deployability-check.md`
- Raw evidence: `artifacts/test-results/`, `artifacts/coverage/`, `artifacts/diffs/`, `artifacts/gates/`
- Later gates add `code-review-report.md`, `signoff-ledger.md`, `feature-action-execution.md`, `kg-reconciliation.md` and `pm-closeout.md`

## Validation Summary

| Stage | Validator | Exit | Notes |
|---|---|---|---|
| G0 | `validate-feature-evidence.py --stage G0` (via `run-gate.py`) | 0 | Two earlier failures were fixed in-run: a missing diff artifact, and run-folder paths listed in the diff |
| G1 | `--stage G1` | 0 | One earlier failure: the G1 gate-decision row was missing |
| G2 | `--stage G2` | 0 | Required self-review headings added before the gate |
| G3–G7 | `--stage G3`…`G6`, G7 KG ops | 0 | G5 failed once before passing: STATUS heading `Required Role Matrix`, and an unchanged-path mention |
| G8 | closeout ops (see `lifecycle-gates.log`) | 0 | compile, patch-prior, latest-run, coverage, drift, telemetry, closeout evidence, trackers, plain validate |

## Open Follow-ups

None for F0064. One out-of-scope observation is recorded in `test-execution-report.md`: six dangling tracked symlinks in F0004's evidence.
