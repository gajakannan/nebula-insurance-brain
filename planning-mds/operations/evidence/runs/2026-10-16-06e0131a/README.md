# Plan Run README — F0004-content-artifact-model run 2026-10-16-06e0131a

## Run Summary

A targeted `plan` rework (PHASE=A+B, FEATURE_MODE=existing) of the findings from re-review run `2026-10-16-b98c71c4` (CONDITIONALLY READY: R-H1 high, R-M1 medium, R-L1 low). Claude Code ran it for the operator on 2026-10-16, on product branch `docs/f0004-plan-review-rework` (uncommitted). It builds on the first rework run, `2026-10-16-fce2ff91`.

## Status

**approved.** Phase A: `approve-phase-a`. Phase B: `approve-phase-b`. Both tokens were typed by the operator on 2026-10-16 and attested through run-gate.py (G3, G5).

## Finding Disposition

| Finding | Operator decision | Where it lands |
|---|---|---|
| R-H1 (High) | A read fails and the job quarantines | Assembly plan Step 2 item 8 (a read only fails), new item 9 (integrity sweep through `mutate` as the ingestion ServicePrincipal with `content_artifact:ingest`) and item 6 (the orphan path moves to the sweep); migration sequence; failure table; S0004-AC3 and checklist; ADR-0073 §2; SQL lifecycle/repair comments, `INTEGRITY_SWEEP` trigger, `authorization_decision_id NOT NULL`; OpenAPI 409; glossary; tests |
| R-M1 (Medium) | Per-document v1 fallback | Assembly plan Step 1a evidence (fallback rate), On PASS, Step 1b item 4, new Step 2 item 10, compatibility "New source" row, failure table, S0002 test row; S0002 provenance gate; PRD compatibility risk; ADR-0073 §1; SQL `writer_fallback_reason` with check and guard immutability |
| R-L1 (Low) | (architect) | SQL `f0004_stamp_state_event` BEFORE INSERT trigger and event-first ordering comment |

Discovered impact: under the R-H1 rule, the revoked-permission orphan path could not have appended its repair record (a denied `mutate` rolls back), so orphan detection moved into the sweep.

## Validation

- **G4/G5 run-gate exit commands:** pass. validate-trackers first failed on the known story-index generator defect; the committed STORY-INDEX.md was restored and the stage resumed.
- **After the approval-text edits:**
  - KG compile, coverage, drift and reproducibility pass;
  - plan-readiness passes with 0 findings;
  - contract examples: 40 cases, 0 failures;
  - stories and trackers pass.
- **SQL:** pglast parses 27 statements and 3 plpgsql bodies.

## Open Follow-ups

- Framework: generate-story-index.py copies markdown hard-break backslashes; manifest `{PRODUCT_ROOT}` placeholder drift on framework main.
- Independence: the same session wrote and reviewed this rework, so a fresh-session plan-review is recommended.
