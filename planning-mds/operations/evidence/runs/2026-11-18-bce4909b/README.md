# Feature Evidence README — F0008-bitemporal-canonical-facts run 2026-11-18-bce4909b

## Run Summary

This is a targeted remediation feature run for F0008, after independent review `2026-11-18-d34a095e` (NOT DONE) and closeout audit `2026-11-18-a3709ba0`. The operator decided its scope on 2026-11-18 and approved at G4 on 2026-11-19. It supersedes completion run `2026-11-17-1a4ae2f0`.

## Status

`approved` at G8 (see `evidence-manifest.json`).

## Evidence Index

- `evidence-manifest.json`, `action-context.md`, `gate-decisions.md`, `commands.log`, `lifecycle-gates.log`, `gate-state.json`
- G0–G1:
  - `g0-assembly-plan-validation.md`
  - `g1-runtime-preflight.md`
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
- `prior-run-errata.md`: corrections for the superseded run's evidence labels

## Validation Summary

Every per-gate `validate-feature-evidence.py` stage passed. G6/G7 passed with no waiver, because the reentry resolver defect was fixed upstream in nebula-agents PR #101.

## Open Follow-ups

- **SEC-F8-02 and refusal reason codes:** F0018 (recorded there).
- **ADR-0078 acceptance:** operator decision.
- **F0011:** renumber its migration after 0015.
- **Framework pin:** bump it after nebula-agents PR #101 merges.
