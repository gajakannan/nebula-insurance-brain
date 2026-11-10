# Action Context

> Seeded by init-run.py. Fill the judgment sections before the first gate.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** feature
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0007
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0007-factslot-model
- **feature_slug:** factslot-model
- **mode:** clean
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-09-b94cfa12
- **run_id:** 2026-11-09-b94cfa12

## Inputs

- FEATURE_ID: F0007 (FactSlot model); MODE: clean; SLICE_ORDER_SOURCE: assembly-plan
- NEBULA_PRODUCT_ROOT bound from the environment and passed explicitly to every script
- Approved plan run: `2026-11-09-60865e32` (A+B); Proposed ADR-0077; three design schemas
- Product branch at start: `roadmap/F0007-now` at `ff0a619` with the operator's uncommitted Now-lane move (ROADMAP.md, kg-source/features/F0007.yaml)
- Framework: nebula-agents at the pinned `d90bbb6`

## Assumptions

- The local Compose PostgreSQL (`brain-postgres`, healthy) is the application runtime; F0007 suites use owned per-test databases created through `BRAIN_MIGRATION_ADMIN_URL`.
- No producer calls the resolver in F0007; trusted test composition and fixtures exercise it.

## Scope Boundaries

- In: S0001-S0006 (39 ACs) per the assembly plan: identity, cardinality, answer carrier, money/identifiers, names, pilot preservation and ownership.
- Out: F0008 temporal close and version-table DDL, F0011 schema publication, F0012/F0013 predicate registry, F0016 scope production, F0017/F0023 display precedence, F0018 RLS, F0020 HTTP states.

## Lifecycle Stage

- feature run initialized
