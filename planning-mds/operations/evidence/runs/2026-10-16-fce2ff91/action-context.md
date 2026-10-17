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
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-10-16-fce2ff91
- **run_id:** 2026-10-16-fce2ff91
- **phase:** A+B
- **feature_mode:** existing
- **run_scope:** targeted rework of plan-review findings
- **source:** NEBULA_PRODUCT_ROOT from the environment, normalized by _product_root.py
- **branch:** docs/f0004-plan-review-rework (product repo)

## Inputs

- Trigger: plan-review run `2026-10-16-a186bc18` returned CONDITIONALLY READY (H-1, H-2, M-1–M-3, L-1–L-4); the operator asked for the plan rework to be done in-session.
- Prior approved plan: run `2026-10-15-bbd8df01` (Phase A and Phase B approved). This run re-opens both phases for targeted edits only and needs fresh `approve-phase-a` / `approve-phase-b` tokens.
- Operator decisions (G1 clarification, 2026-10-16):
  1. **H-1:** new sources keep the existing v1 writer, namespace and identities until a Step 1 spike proves per-item provenance on the pinned converter; v2 writing is enabled only after that proof. S0002's v2 origin criteria stay in scope, gated on the proof.
  2. **H-2:** `legacy_unverified` v1 artifacts stay readable through the v1 verifier (full bundle-hash check on every read). The backfill moves verified rows to `ready`; a failed verification moves the row to `quarantined` (409 `ARTIFACT_INTEGRITY`) with an audit event.
  3. **M-1:** the runtime producer of CONTENT/SOURCE_METADATA candidates is an unassigned downstream dependency, recorded as an open decision in BLUEPRINT §4.8. No other feature's plan is edited.
  4. **M-2:** in v0.1, `select` (including clear) requires a verified HUMAN selection decision (F0022 producer; default verifier rejects). ServicePrincipals may append candidates but cannot select. No new grant.

## Assumptions

- Findings L-1–L-4 and M-3 are mechanical and need no business decision; they are fixed under the owning role's normal authority.
- Story and AC identifiers are stable; no AC is deleted or renumbered.

## Scope Boundaries

- PM (Phase A): PRD, the four stories, acceptance checklist, worked examples, STATUS, BLUEPRINT §4.8 open-decision entry.
- Architect (Phase B): feature-assembly-plan.md, ADR-0073, persistence-design.sql, document-date-record schema plus contract examples if the selection shape changes, GETTING-STARTED, KG shard rationale if needed.
- No runtime code, no other feature's planning artifacts, no generated KG/tracker regions edited by hand, no feature evidence package.

## Lifecycle Stage

- plan run initialized
