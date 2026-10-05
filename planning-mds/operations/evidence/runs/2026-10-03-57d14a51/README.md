# F0003 — PostgreSQL persistence — run 2026-10-03-57d14a51

## Run Summary

Feature-completion evidence for F0003. The approved PostgreSQL persistence plan was retained at G0. G0 and G1 passed. G2 remains FAIL: hosted CI passed focused PostgreSQL smoke suites, but its broader engine pytest and coverage steps stopped at a Ruff issue. The issue is fixed on the continuation branch; the F0003 integration/migration suite and current-run coverage are still outstanding.

## Status

`in-progress` — G0/G1 passed; G2 did not pass; matches `evidence-manifest.json`.

## Evidence Index

- `evidence-manifest.json`
- `action-context.md`
- `artifact-trace.md`
- `gate-decisions.md`
- `commands.log`
- `lifecycle-gates.log`
- `g0-assembly-plan-validation.md`
- `g1-runtime-preflight.md`
- G2: `g2-self-review.md`, `test-plan.md`, `test-execution-report.md`, `coverage-report.md`, `g2-deployability-check.md`, and the validator-compatible `deployability-check.md`.
- Later gates are not started: G3 reviews; G4 approval; G5 signoff ledger; G6 candidate validation; G7 reconciliation; G8 PM closeout.

## Validation Summary

- G0 validation: PASS (`run-gate.py`, 2026-10-03).
- G1 runtime preflight: PASS; service health and PostgreSQL readiness are recorded.
- G2: FAIL; `run-gate.py` returned exit 1. The validator rejected the failing self-review and QE verdict because the complete F0003 integration/migration evidence and current coverage are not yet available. Hosted CI details are in the test-results evidence index; the latest validator run still reports only the self-review and QE verdicts as non-passing.
- G3–G8: not run. The action stopped at the first non-passing stage.

## Open Follow-ups

- Run the PostgreSQL integration and migration lanes, then collect current-run coverage in an environment with database access. Continuation commit `038a87d` fixes the Ruff error that previously skipped runtime pytest; obtain a hosted rerun against it before G2 is rerun.
- Continuation branch `feature/F0003-postgresql-persistence-g2-resume-2026-10-04` is pushed. The workflow only runs on pushes to `main`, pull requests, or manual dispatch; local manual dispatch could not connect to GitHub. A PR check or another hosted-runner trigger is needed to collect the pending suite and coverage evidence.
- The rendered G2 contract names `g2-deployability-check.md`, while the evidence validator/template still consumes `deployability-check.md`; both files are present pending framework reconciliation.
