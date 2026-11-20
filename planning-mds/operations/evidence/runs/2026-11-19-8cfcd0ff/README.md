# Feature Evidence README — F0008-bitemporal-canonical-facts run 2026-11-19-8cfcd0ff

## Run Summary

This is the second remediation run for F0008, after review `2026-11-19-b21ec2de` (CONDITIONALLY DONE: SEC-F8-NEW-01 High plus 4 Low). The operator decided on 2026-11-19 to refuse the whole commit with 404 and approved at G4 the same day. It supersedes `2026-11-18-bce4909b`.

## Status

`approved` at G8 (see `evidence-manifest.json`).

## Evidence Index

- `evidence-manifest.json`, `action-context.md`, `gate-decisions.md`, `commands.log`, `lifecycle-gates.log`, `gate-state.json`
- G0–G1:
  - `g0-assembly-plan-validation.md`
  - `g1-runtime-preflight.md` (the preflight is recorded before every test)
- G2:
  - `g2-self-review.md`
  - `test-plan.md`
  - `test-execution-report.md`
  - `coverage-report.md`
  - `deployability-check.md`
- G3:
  - `code-review-report.md`
  - `security-review-report.md`
  - `architect-implementation-review.md`
- G5–G8:
  - `signoff-ledger.md`
  - `feature-action-execution.md`
  - `kg-reconciliation.md`
  - `pm-closeout.md`
- `prior-run-errata.md`

## Validation Summary

Every per-gate `validate-feature-evidence.py` stage passed, including G6/G7 with no waiver.

## Open Follow-ups

- SEC-F8-02 and refusal reason codes: F0018.
- ADR-0078 acceptance: operator.
- Framework pin PR #57.
- F0011 renumbers after 0015.
