# Action Context

> Seeded by init-run.py. Fill the judgment sections before the first gate.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** plan
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0008
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts
- **feature_slug:** bitemporal-canonical-facts
- **mode:** clean
- **phase:** A+B
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-16-208a1193
- **run_id:** 2026-11-16-208a1193

## Inputs

- FEATURE_ID `F0008`, PHASE `A+B`, FEATURE_MODE `new` (operator prompt, 2026-11-16).
- NEBULA_PRODUCT_ROOT resolved from the environment to the absolute path above.
- Product branch `plan/F0008-bitemporal-canonical-facts` from `origin/main` `fe651dd`. Framework `nebula-agents` at `d90bbb6` (the BLUEPRINT pin).
- Feature folder pre-existed as a reserved identifier (README only) with kg-source shard `features/F0008.yaml` (`coverage_excluded`).

## Assumptions

- The four G1 operator decisions and PM assumptions A1–A4 are recorded in gate-decisions.md and the PRD.
- The F0001 pilot (migration 0003, `brain_temporal.commit`) is the baseline F0008 generalizes; it is not re-proved by planning.

## Scope Boundaries

- Base run only. No feature evidence package, no role reports, no implementation files.
- Phase A: PRD, personas, seven stories, AC checklist, STATUS skeleton, README sections, STORY-INDEX regeneration.
- Phase B: assembly plan, GETTING-STARTED, ADR, contract and schema updates, kg-source shards, compiled projections.
- Out of scope: F0009, F0010, F0016, F0018, F0019 and F0020 obligations, which are listed in the PRD.

## Lifecycle Stage

- plan run initialized
- G1 PASS, G2 PASS (2026-11-16)
- G3 PASS (`approve-phase-a`, 2026-11-16)
- G4 PASS (compile + drift)
- G5 pre-checkpoint exit validation
