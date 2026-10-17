# Action Context

> Seeded by init-run.py. Fill the judgment sections before the first gate.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** plan
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0004
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0004-content-artifact-model
- **feature_slug:** content-artifact-model
- **mode:** clean
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-10-16-06e0131a
- **run_id:** 2026-10-16-06e0131a
- **phase:** A+B
- **feature_mode:** existing
- **run_scope:** targeted rework of re-review findings R-H1, R-M1, R-L1
- **source:** NEBULA_PRODUCT_ROOT from the environment, normalized by _product_root.py
- **branch:** docs/f0004-plan-review-rework (product repo, uncommitted)

## Inputs

- Trigger: plan-review run `2026-10-16-b98c71c4` returned CONDITIONALLY READY (R-H1 high, R-M1 medium, R-L1 low). The operator asked for the rework to be done in-session.
- Prior plan runs: `2026-10-15-bbd8df01` (original, approved), `2026-10-16-fce2ff91` (first rework, approved). This run reopens both phases for targeted edits and needs fresh `approve-phase-a` / `approve-phase-b` tokens.
- Operator decisions (G1 clarification, 2026-10-16):
  1. **R-H1, read fails and a job quarantines:** a read that finds a definitive verification failure returns 409 `ARTIFACT_INTEGRITY`. Its only write is the normal FAILED read decision that `AuthorizationExecution.read` already persists. An operator-run integrity sweep, running as the ingestion ServicePrincipal through `AuthorizationExecution.mutate` with `content_artifact:ingest`, re-verifies the bytes. It writes the state event, the audit event and the repair record in that mutation's unit of work. The API read path never writes, and repair records stay outside tenant/human/API grants.
  2. **R-M1, per-document v1 fallback:** with the v2 writer enabled, a document with any `ORIGIN_UNAVAILABLE` item publishes on the v1 writer, namespace and identities, and records the reason (`writer_fallback_reason=ORIGIN_UNAVAILABLE` and the count of unattributed items) on the row and in the publication audit. Nothing is inferred.
- R-L1 needs no operator decision. The architect fixes it (enforced `created_at` and documented insert ordering).

## Assumptions

- Applying R-H1 shows the same defect in the revoked-permission orphan path (Step 2 item 6): a denied `mutate` rolls back, so it can't append an `ORPHAN_MARKER` repair record. That detection moves into the same integrity sweep. This is recorded as discovered impact of the operator decision.
- The independence limit carries over: the same session wrote this rework.

## Scope Boundaries

- In scope: F0004 feature files, ADR-0073, `persistence-design.sql`, glossary F0004 rows, OpenAPI 409 text, the F0004 KG shard and its generated projections.
- Out of scope: product source code, Casbin policy (no new action), other features.

## Lifecycle Stage

- plan run initialized
