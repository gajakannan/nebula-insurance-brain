# F0012 Plan Action Context

## Run Identity

- **NEBULA_PRODUCT_ROOT:** `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` — shell environment, resolved once with `_product_root.py` and passed explicitly as `--product-root` thereafter.
- **action:** plan; **feature_id:** F0012; **feature_slug:** foundation-ontology.
- **phase:** A+B; **feature mode:** new; **run_id:** `2026-11-25-120320e9` (minted once by init-run.py in the contract format).
- **contract_version:** 2026-07-11, base-run-only; severity profile `none`; implementation coverage floor 80%.
- **feature path:** `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/features/F0012-foundation-ontology`.
- **run folder:** `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-25-120320e9`.
- **branch:** `plan/F0012-foundation-ontology` cut from `origin/main` 1b4b9dc. Framework: `/home/gajap/uSandbox/repos/nebula/nebula-agents` at 840e724 (matches the product pin).

## Inputs

Operator plan prompt (FEATURE_ID=F0012, PHASE=A+B, FEATURE_MODE=new). `project_context.py --action plan` loaded BLUEPRINT and docs/agent-instructions.md; no required product check is declared for plan. Framework router/map/use/extensions/plan action and spec; REGISTRY, ROADMAP; F0012 README amendments (2026-10-06 prerequisites, 2026-10-08/10 Cedar Bridge and ADR-0070, 2026-11-08 requirement ownership, 2026-11-21 shipped-contract carry-in, 2026-09-25 scope guard); kg-source/features/F0012.yaml (planning-only mapping); ontology and commercial P&C handoffs.

FEATURE_MODE note: the ontology handoff suggested `existing` because a reserved folder with prerequisite notes exists. The operator selected `new`; the folder held only README.md, so new PRD/personas/stories/STATUS were scaffolded and the README amendments were preserved and extended, not overwritten.

## Assumptions

Operator G1 decisions D1–D8 and PM assumptions A1–A5 are recorded in the PRD (Risks & Assumptions) and gate-decisions.md. A1–A5 are presented for explicit review at G3.

## Scope Boundaries

Phase A: PRD, personas, seven stories (46 ACs), acceptance checklist, STATUS skeleton, README story table, BLUEPRINT §3.3 links, regenerated STORY-INDEX. The PM does not edit kg-source or generated projections. Phase B (after explicit G3 approval): assembly plan, ADR, contracts, kg-source bindings, role matrix, GETTING-STARTED. Runtime implementation belongs to the later feature action after plan-review.

## Lifecycle Stage

- plan run initialized
- G1 clarification complete (eight operator decisions, 2026-11-25)
- Phase A artifacts validated; G2 PASS
- G3 PASS: exact operator token approve-phase-a recorded, attested, Phase A approval published by approve-plan.py
- Phase B authored; G4 PASS (compile + check-drift)
- G5 pre-approval exit validation PASS (7/7)
- Phase B approved by exact operator token approve-phase-b; checkpoint attested; G5 rerun performs post-approval refresh and publication
