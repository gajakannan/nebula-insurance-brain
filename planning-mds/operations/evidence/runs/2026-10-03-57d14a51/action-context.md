# Action Context

> Seeded by init-run.py. Fill the judgment sections before the first gate.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** feature
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0003
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0003-postgresql-persistence
- **feature_slug:** postgresql-persistence
- **mode:** clean
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-10-03-57d14a51
- **run_id:** 2026-10-03-57d14a51

## Inputs

- FEATURE_ID: F0003 — PostgreSQL persistence
- MODE: clean
- SLICE_ORDER_SOURCE: assembly-plan
- NEBULA_PRODUCT_ROOT: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain (explicit operator value, resolved by `_product_root.py`)
- RUN_ID: 2026-10-03-57d14a51
- RUN_ID_PRIOR: null (no prior `latest-run.json` was found by setup)
- RERUN_OF: null

## Assumptions

- Phase A and Phase B planning were approved in plan run `2026-09-30-6632006b`; this run starts the separate feature-completion scope.
- The approved feature assembly plan and raw story acceptance criteria govern implementation; KG lookup is routing context only.
- PostgreSQL 18 and the accepted F0002 migration head are the baseline. No runtime or implementation acceptance is inferred from the plan run.
- The F0002 `role` and `permission` representation remains an explicit reconciliation owned outside F0003; this run will not add those tables or change F0002 policy.

## Scope Boundaries

- F0003 stories S0001–S0004 and the approved `feature-assembly-plan.md` only.
- Shared persistence, PostgreSQL integrity, transaction boundaries, and compatible schema evolution; domain-specific tables and behavior remain with their owning features.
- No frontend, AI, public API, new ADR, or future-phase table activation unless the approved plan is formally reconciled by Architect.
- No shared-semantics edits outside Architect ownership. Any code search begins with `scripts/kg/hint.py`; any shared-semantics edit requires `blast.py` and Architect review.
- This is a candidate feature run. It remains draft until G8 PM closeout; no `latest-run.json` is written before final validation.

## Lifecycle Stage

- G0 — Architect assembly plan authoring and validation: PASS.
- G1 — Runtime preflight: PASS.
- G2 — self-review, QE, and deployability: FAIL; `run-gate.py` and the direct validator diagnostic recorded non-passing QE verdicts because PostgreSQL integration and current coverage evidence are incomplete.
- Action stopped at G2 per the feature evidence contract. G3–G8 have not run.
