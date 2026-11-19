# Action Context

> Seeded by init-run.py. Fill the judgment sections before the first gate.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** feature
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0008
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts
- **feature_slug:** bitemporal-canonical-facts
- **mode:** clean
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0
- **run_id:** 2026-11-17-1a4ae2f0

## Inputs

- FEATURE_ID: F0008. MODE: clean. SLICE_ORDER_SOURCE: assembly-plan.
- NEBULA_PRODUCT_ROOT comes from the environment and was resolved by `_product_root.py`.
- RUN_ID_PRIOR: none. There is no `latest-run.json`. The only other F0008 manifest is the approved base-run-only plan run `2026-11-16-208a1193`, which is independent.
- Branch: `feature/F0008-bitemporal-canonical-facts`, cut from `origin/main` 2badb9a (PR #54, the approved plan).
- Primary spec: `planning-mds/features/F0008-bitemporal-canonical-facts/feature-assembly-plan.md` and Proposed ADR-0078.

## Assumptions

- The plan-review action was not run before this feature action, and the operator invoked the feature action directly. G0 records this ordering.
- The local runtime is Docker Desktop `brain-postgres` (`brain-postgres:18-pgvector-age`) plus the locked `engine/.venv`. Docker Desktop was found stopped and was restarted at session start.
- The G0 reconciliations are in the assembly plan section "Feature-Action G0 Reconciliation".

## Scope Boundaries

- In scope: the engine only, meaning migration 0014, `brain_domain.temporal`, `brain_temporal`, `brain_persistence` and the `/facts` API. Also the test harness and cleanup adjustments and the CI wiring.
- Out of scope: UI, neuron, any new route, grant or table, F0010 change-reason vocabulary, F0016 mention grades, F0018 review routing, RLS and refusal-reason persistence, F0020 HTTP information states, and `temporal_kind` activation (F0012/F0013).

## Lifecycle Stage

- feature run initialized
