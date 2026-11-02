# Action Context

Targeted Phase B Architect rework of F0006. It resolves plan-review findings AR-1 and AR-2 from plan-review run 2026-11-01-923858ef.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** plan
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0006
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0006-assertion-plane-origin-and-interpretation-basis
- **feature_slug:** assertion-plane-origin-and-interpretation-basis
- **mode:** clean
- **phase:** B
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-01-512e9303
- **run_id:** 2026-11-01-512e9303

## Inputs

- FEATURE_ID=F0006; PHASE=B; FEATURE_MODE=existing. Operator request: "use the plan action to resolve the two findings AR-1 and AR-2".
- NEBULA_PRODUCT_ROOT=/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain (shell environment, normalized by the framework resolver).
- Prior approved plan run: 2026-11-01-7d6d19ce (A+B). Plan-review report: runs/2026-11-01-923858ef/plan-review-report.md.
- Operator decision on AR-1, 2026-11-01, chosen from three options: "Inherit; v1 unchanged". v2 corrections inherit the original basis. v1 corrections keep the existing EXPLICIT behaviour as a documented legacy boundary.

## Assumptions

- AR-2 is resolved by Architect judgment (technical persistence mapping only). No business rule is added.
- The approved Phase A requirements are unchanged. No PRD, story or checklist edits are made. The v1 legacy boundary is read under S0005 AC3 (preserve existing review behaviour), and S0001 AC4 is enforced for v2 claims. This interpretation is flagged in the approval package for operator review.

## Scope Boundaries

- Edited: feature-assembly-plan.md (Data Model `assertion` row; review-correction section; validation matrix S0001/S0005 rows), ADR-0075 §3, api/brain-api.yaml review description (text only) and architecture/data-model.md F0006 section (one paragraph).
- Not edited: PRD, stories, personas, checklist, schemas, policies or compiled KG projections.

## Lifecycle Stage

- plan run initialized
