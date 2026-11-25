# Feature Evidence README — F0009-provenance-and-human-correction-lineage run 2026-11-24-08701e37

## Run Summary

Feature action for F0009 (provenance + human-correction lineage), run by Claude (Opus 5.5) acting as Architect, Backend, QE, DevOps, Code Reviewer, Security and PM, with operator approval at G4. It delivers the internal metadata-first provenance reader, migration 0016 (learning-candidate reservations and refused-submission attempts), review-boundary preflight and atomic reservation, and F0011 contract registration.

## Status

`in-progress` (agrees with `evidence-manifest.json`).

## Evidence Index

- `evidence-manifest.json`, `action-context.md`, `artifact-trace.md`, `gate-decisions.md`, `commands.log`, `lifecycle-gates.log`
- `g0-assembly-plan-validation.md`, `g1-runtime-preflight.md`
- G2: `g2-self-review.md`, `test-plan.md`, `test-execution-report.md`, `coverage-report.md`, `g2-deployability-check.md`, `artifacts/security/scan-summary.json`

## Open Follow-ups

- Framework: `agents/security/scripts/check-secrets.sh --mode filesystem` runs `gitleaks detect` without `--no-git`; with gitleaks 8.30 it scans 0 bytes. This run passed `-- --no-git`. Owner: framework maintainer.
- KG tooling: `scripts/kg/symbols.py` caches symbols by file hash only, so a re-bound unchanged file keeps its old owning node (8 dangling-symbol warnings until `.kg-state/symbols-cache.json` was cleared). Owner: KG tooling.

## Validation Summary

Recorded per gate in `gate-decisions.md` and `lifecycle-gates.log`.
