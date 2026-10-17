# Plan Run README — F0004-content-artifact-model run 2026-10-16-fce2ff91

## Run Summary

A targeted `plan` rework (PHASE=A+B, FEATURE_MODE=existing) of the findings from plan-review run `2026-10-16-a186bc18` (CONDITIONALLY READY: 2 high, 3 medium, 4 low). It was run by Claude Code for the operator on 2026-10-16, on product branch `docs/f0004-plan-review-rework`. The rework applies four operator decisions recorded in action-context.md: new sources stay on the v1 writer until a per-item provenance spike passes; legacy v1 artifacts stay readable through the v1 verifier, and failures quarantine; the date-candidate producer is an open decision (BLUEPRINT §4.8); only a verified human decision can select a date in v0.1.

## Status

**approved.** Phase A token `approve-phase-a` and Phase B token `approve-phase-b`, both typed verbatim by the operator, attested via run-gate. G1–G5 completed.

## Evidence Index

- `action-context.md`: identity, operator decisions, scope
- `gate-decisions.md`: G1–G5, including both approval tokens
- `gate-state.json`, `commands.log`, `lifecycle-gates.log`: driver journal and validator telemetry
- `artifacts/diffs/changed-files.txt`: changed planning paths
- `artifacts/test-results/`: plan-readiness, contract examples (40 cases), API contract (6 warnings, unchanged from baseline)

## Validation Summary

- validate-stories, validate-trackers (after the STORY-INDEX restore), KG compile, coverage report, drift and reproducibility, and validate_templates: all exit 0.
- Supplementary: plan-readiness, validate-contract-examples, validate-api-contract and pglast parsing of persistence-design.sql: all pass.

## Finding Disposition

| Finding | Disposition |
|---|---|
| H-1 | Fixed: Step 1a provenance spike with exit decision; v1 writer for new sources until PASS; S0002 gated; ADR-0073 §1/§3 |
| H-2 | Fixed: publication_state machine, v1-verifier legacy reads, quarantine, state events, content_artifact guard; ADR-0073 §2, S0004-AC3, OpenAPI 409 |
| M-1 | Fixed: open decision in BLUEPRINT §4.8; PRD/S0003 dependency rows |
| M-2 | Fixed: human-only select/clear (HumanDateSelectionVerifier, schema `human_decision`, SQL columns, S0003-AC6) |
| M-3 | Fixed: `content_repair_record` table, DevOps-owned |
| L-1 | Fixed: stale Phase A wording replaced |
| L-2 | Fixed: S0002-AC7 shares S0001-AC6's single audit event |
| L-3 | Fixed: trigger DDL |
| L-4 | Fixed: Reviewer-only negative test; PRD clarification |

## Open Follow-ups

1. Re-run `plan-review` for F0004 to confirm the verdict.
2. Framework: `generate-story-index.py` copies trailing hard-break `\` into STORY-INDEX.md, so validate-trackers fails on every plan run.
3. Framework/product: `.nebula-project.yaml` still uses `{PRODUCT_ROOT}` while nebula-agents `main` expects `{NEBULA_PRODUCT_ROOT}`.
4. Assign the document-date candidate producer (BLUEPRINT §4.8) before planning F0005 activation or F0016.
