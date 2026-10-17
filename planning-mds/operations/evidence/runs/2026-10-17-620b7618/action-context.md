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
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-10-17-620b7618
- **run_id:** 2026-10-17-620b7618
- **phase:** A+B
- **feature_mode:** existing
- **run_scope:** targeted rework of six gaps from an in-session full review (2026-10-17)
- **source:** NEBULA_PRODUCT_ROOT from the environment, normalized by _product_root.py
- **branch:** docs/f0004-plan-review-rework (product repo, uncommitted)

## Inputs

- Trigger: after plan run `2026-10-16-06e0131a`, the operator asked for a full review. An in-session read of the whole F0004 package against product code found six gaps (not recorded as a separate plan-review run). The operator said "go ahead and apply the fixes", which accepts the recommendations below.
- Gaps and dispositions:
  1. **High:** sync paths (integrity sweep, backfill, worker revoked-permission path) named the async `AuthorizationExecution.mutate`. The existing worker gate (`document_delivery.py:77-117`) commits its decision before the job step. Fix: the sync form is `decide` over `SyncAuthorityStore` in the same session/transaction as the effects (as in Step 2 item 2); a denial is appended and committed alone.
  2. **Medium (operator accepted recommendation):** the per-document v1 fallback keeps the ADR-0073 §3 source/version identity, and falls back only in bundle contract, namespace and artifact derivation (`artifact_id = uuid5(version_id, 'content')`).
  3. **Low:** quarantine insert order follows the foreign keys: repair record, audit event, state event, then the row UPDATE.
  4. **Low:** the orphan-marker authorization key is the CONTENT_ARTIFACT key with `require_record=False`, as in the existing worker gate.
  5. **Low:** remove the writerless `RESTORE_DRILL` trigger and `RESTORE_MISMATCH` kind. The drill runs against an isolated target and reports in its own evidence; production effects come from the integrity sweep run after a drill.
  6. **Low:** refresh stale status lines (assembly plan header, PRD, checklist).

## Assumptions

- The independence limit carries over: the same session wrote and reviewed this rework.

## Scope Boundaries

- In scope: F0004 feature files, ADR-0073, `persistence-design.sql`, and the F0004 KG shard with its generated projections.
- Out of scope: product source code, Casbin policy, other features.

## Lifecycle Stage

- plan run initialized
