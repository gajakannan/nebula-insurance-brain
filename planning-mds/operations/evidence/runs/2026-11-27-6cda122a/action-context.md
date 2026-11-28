# F0021 Plan Action Context

## Run Identity

- **NEBULA_PRODUCT_ROOT:** `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` — shell environment, resolved once with `_product_root.py` and passed explicitly as `--product-root` thereafter.
- **action:** plan; **feature_id:** F0021; **feature_slug:** native-react-semantic-shell-and-oidc-session.
- **phase:** A+B; **feature mode:** new; **run_id:** `2026-11-27-6cda122a` (minted once by init-run.py in the contract format).
- **contract_version:** 2026-07-11, base-run-only; severity profile `none`; implementation coverage floor 80%.
- **feature path:** `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/features/F0021-native-react-semantic-shell-and-oidc-session`.
- **run folder:** `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-27-6cda122a`.
- **branch:** `plan/F0021-native-react-semantic-shell` cut from `origin/main` 4dcdf79. Framework: `/home/gajap/uSandbox/repos/nebula/nebula-agents` at 840e724 (matches the product pin; one unrelated uncommitted framework file left untouched).

## Inputs

Operator plan prompt (FEATURE_ID=F0021, PHASE=A+B, FEATURE_MODE=new). `project_context.py --action plan` loaded BLUEPRINT and docs/agent-instructions.md; no required product check is declared for plan. Framework plan action; REGISTRY, ROADMAP; F0021 README amendments (2026-09-28 F0002 rate-limit carry-in, 2026-10-13 Graph Observatory seam carry-in, 2026-11-08 requirement ownership / ADR-0051 decision); kg-source/features/F0021.yaml (planning-only, coverage_excluded).

## Assumptions

Operator G1 decisions D1–D4 and PM assumptions A1–A8 are recorded in the PRD (Risks & Assumptions) and gate-decisions.md. A1–A8 are presented for explicit review at G3.

## Scope Boundaries

Phase A: PRD, personas (one new persona file), nine stories (55 ACs), acceptance checklist, STATUS skeleton, README story table, BLUEPRINT §3.2/§3.3 links, regenerated STORY-INDEX. The PM does not edit kg-source or generated projections. Phase B (after explicit G3 approval): assembly plan, ADR work, contracts, kg-source bindings, GETTING-STARTED. Runtime implementation belongs to the later feature action after plan-review.

## Lifecycle Stage

- plan run initialized
- G1 clarification complete (four operator decisions, 2026-11-27)
- Phase A artifacts validated; G2 PASS
