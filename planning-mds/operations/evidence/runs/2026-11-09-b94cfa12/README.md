# Feature Evidence README — F0007-factslot-model run 2026-11-09-b94cfa12

## Run Summary

Feature action for F0007, the FactSlot model, run by Claude (Opus 5.5) acting in each framework role, on the product branch `roadmap/F0007-now`. It implements six stories and 39 ACs:

- KB-owned slot identity with authoritative qualifier rows and a JCS/SHA-256 lookup fingerprint;
- SINGLE, MULTI and RELATIONSHIP slots, with members as child slots;
- the `fact-answer/v1` carrier: nine states, scoped absence, exact money and scheme-scoped identifiers;
- the four system name predicates with a precedence-free display hook;
- additive migration 0012 with ownership keys and triggers;
- the RLS inventory handed to F0018.

The operator approved at G4.

## Status

`approved`, matching `evidence-manifest.json` and `planning-mds/operations/evidence/features/F0007-factslot-model/latest-run.json` (G8, 2026-11-09). There was no prior completion run to supersede.

## Evidence Index

- `evidence-manifest.json`: schema v1
- `action-context.md`, `artifact-trace.md`, `gate-decisions.md`, `commands.log`, `lifecycle-gates.log`, `gate-state.json`
- G0: `g0-assembly-plan-validation.md`
- G1: `g1-runtime-preflight.md`
- G2: `g2-self-review.md`, `test-plan.md`, `test-execution-report.md`, `coverage-report.md`, `deployability-check.md`, `g2-deployability-check.md`
- G3: `code-review-report.md`, `security-review-report.md`
- G5: `architect-implementation-review.md`, `signoff-ledger.md`
- G6: `feature-action-execution.md`
- G7: `kg-reconciliation.md`
- G8: `pm-closeout.md`, `token-usage.json` (advisory)
- Artifacts: `artifacts/test-results/` (JUnit, console output, G0 lineage, G4 gate policy, prior hints); `artifacts/coverage/` (full-run coverage, changed-line summary and script); `artifacts/security/` (SAST, secrets, dependency, DAST); `artifacts/runtime/` (owned-DB regression wrapper, dev-clone migration script); `artifacts/diffs/changed-files.txt`

## Validation Summary

| Stage | Validator | Exit codes (in order) |
|---|---|---|
| G0 | `validate-feature-evidence --stage G0` | 1, then 0 |
| G1 | `--stage G1` | 0 |
| G2 | `--stage G2` | 1, then 0 |
| G3 | `--stage G3` | 0 |
| G4 | `--stage G4` | 0 |
| G5 | `--stage G5` | 1, 1, then 0 |
| G6 | `--stage G6`; `validate-trackers` | 1 (missing G6 row), then 0; trackers PASS |
| G7 | `compile.py`; `validate.py --regenerate-symbols --check-symbols --regenerate-decisions --check-decisions`; `--check-drift` | 0 (re-run with `--force` after the pre-move delta: 0) |
| G8 | checkpoint `archive-move` (attested); compile; `patch-prior-manifest`; `latest-run.json`; `--write-coverage-report`; `--check-drift`; telemetry; `--stage closeout`; `validate-trackers`; plain `validate.py` | all 0 |

Each failure was an evidence-shape issue fixed in this run (lifecycle log structure; a glob reference; a missing G5 decision row; a short path). No waiver was used and no earlier effective date was passed.

## Open Follow-ups

- **ADR-0077 status.** The ADR is still Proposed, and all five of its proof gates now have evidence (`architect-implementation-review.md`). Marking it Accepted is the operator's decision.
- **Handoffs, unchanged and not delivered by F0007:** F0008, F0011, F0012/F0013, F0016, F0017/F0023 (including the name-hook per-slot authorization cost note), F0018, F0020 and F0026.
- **Commit.** The run's code and evidence are uncommitted on `roadmap/F0007-now` until the operator asks.
