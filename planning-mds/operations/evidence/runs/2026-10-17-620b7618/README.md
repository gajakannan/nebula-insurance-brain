# Plan Run README — F0004-content-artifact-model run 2026-10-17-620b7618

## Run Summary

A targeted `plan` rework (PHASE=A+B, FEATURE_MODE=existing) of six gaps found by an in-session full review of the F0004 package after plan run `2026-10-16-06e0131a`. Claude Code ran it for the operator on 2026-10-16/17, on product branch `docs/f0004-plan-review-rework` (uncommitted). The review itself was not recorded as a separate plan-review run; its findings and dispositions are in action-context.md.

## Status

**approved.** Phase A: `approve-phase-a`. Phase B: `approve-phase-b`. Both tokens were typed by the operator and attested through run-gate.py (G3, G5).

## Finding Disposition

| Gap | Severity | Fix |
|---|---|---|
| Sync paths named async `AuthorizationExecution.mutate` | High | Step 2 items 6 and 9, the migration sequence and the test row now use synchronous in-transaction authorization (`decide` over `SyncAuthorityStore`, decision and effects in one commit), and exclude the worker's pre-step gate. SQL comments, ADR-0073 §2 and proof gates, GETTING-STARTED and STATUS are updated. |
| Fallback identity conflicted with ADR-0073 §3 | Medium | A fallback keeps the §3 version ID; only the bundle contract, namespace and artifact derivation are v1 (item 10, compatibility matrix, test row, ADR §1/§3). Operator accepted the recommendation. |
| Quarantine insert order vs foreign keys | Low | repair → audit → state event → UPDATE (item 9, backfill, SQL comment) |
| Orphan authorization key | Low | CONTENT_ARTIFACT key with `require_record=False` (item 9) |
| Writerless RESTORE_DRILL / RESTORE_MISMATCH | Low | Removed from the SQL enums, comments and ADR; the restore drill reports in its own evidence |
| Stale status lines | Low | Assembly plan header, PRD, checklist |

## Validation

- **G4/G5 run-gate:** pass. validate-trackers first failed on the known story-index generator defect; the committed index was restored and the stage resumed.
- **After the approval-text edits:**
  - KG compile, coverage, drift and reproducibility pass;
  - plan-readiness passes with 0 findings;
  - contract examples pass;
  - stories and trackers pass.
- **SQL:** pglast parses 27 statements and 3 plpgsql bodies.

## Open Follow-ups

- Framework: the generate-story-index.py backslash defect; manifest `{PRODUCT_ROOT}` placeholder drift on framework main.
- Independence: the same session wrote and reviewed this work. A fresh-session plan-review is recommended before build.
