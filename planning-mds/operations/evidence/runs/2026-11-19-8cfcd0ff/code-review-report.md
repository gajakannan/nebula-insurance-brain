# Feature Code Review Report

Feature: F0008 — Bitemporal canonical facts, second remediation (run `2026-11-19-8cfcd0ff`)

- Role: Code Reviewer
- Reviewer: Claude (Opus 5.5) / Code Reviewer
- Date: 2026-11-19
- Result: APPROVED
- Base: `origin/main` e024cd7 (#56)

## Summary

- Assessment: APPROVED
- Production files changed:
  - `engine/packages/brain-temporal/src/brain_temporal/commit.py`: `DisclosureCheck` hook, `returns_attestation`, docstring
  - `engine/packages/brain-persistence/src/brain_persistence/repositories.py`: `current_attesting_artifact_keys`
  - `engine/apps/api/src/brain_api/routes/facts.py`: up-front keys, `disclosure_check`, `_conservative_window`
- Open issues: Critical 0, High 0, Medium 0, Low 0

## Disposition

| Finding | Status | Verification |
|---|---|---|
| SEC-F8-NEW-01 (High) | Fixed | Unreadable predecessor document: whole commit refused with a non-disclosing 404 and zero rows written. Readable: full `versions[]`. No overlap: no predecessor READ needed. Concurrent predecessor: 409 `stale_version`, zero rows. Tests: `test_sec_f8_new_01_*` (3 integration, 2 unit). |
| R2-ARCH-L1 | Fixed | Plan lines 48 and 343 and the `_remainder` docstring now say three source timestamps plus the new acceptance. |
| PM2-L1, PM2-L2, QE2-L1 | Fixed | NUL-safe path sync (asserts every path exists); STATUS and BLUEPRINT pointers; preflight recorded first; errata for the superseded run. |

## Pattern Compliance

- **Authorization stays in `AuthorizationExecution.mutate`.** The service only exposes the predecessors, and the route decides from the decisions mutate already took in the same unit of work. There is no nested read facade.
- **The check runs before any effect** (after the guards, before `register_commit`). It is skipped for an end revision, which leaves no remainder, and for predecessors without dates.
- **The up-front window is a superset of the real overlap.** An unknown or malformed bound is unbounded, so it can only over-check, never under-check.

## Recommendation

APPROVE.
