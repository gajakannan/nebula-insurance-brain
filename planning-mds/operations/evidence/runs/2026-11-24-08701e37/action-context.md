# Action Context

> Seeded by init-run.py. Fill the judgment sections before the first gate.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** feature
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0009
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0009-provenance-and-human-correction-lineage
- **feature_slug:** provenance-and-human-correction-lineage
- **mode:** clean
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-24-08701e37
- **run_id:** 2026-11-24-08701e37

## Inputs

- FEATURE_ID: F0009 (from the operator's prompt template edit); MODE: clean; SLICE_ORDER_SOURCE: assembly-plan
- NEBULA_PRODUCT_ROOT: environment (`/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`)
- Baseline: `main` 3729dbe (PR #66 merged: plan, plan review 2026-11-24-2af6f972, Phase B rework 2026-11-24-c32acf46)
- RUN_ID_PRIOR: null (no `latest-run.json`; the only F0009 manifests are base-run-only planning runs)
- Branch: `feature/f0009-provenance-and-human-correction-lineage`

## Assumptions

- The approved assembly plan is the baseline. G0 reconciles it and does not re-author it.
- Plan-review Medium/Low findings PR-M1, PR-M2, PR-L1–L5 are resolved at G0 (PR-L3 at G7) without requirement changes.
- The local Docker PostgreSQL 18 runtime (`brain-postgres`) is the validation database.

## Scope Boundaries

- In: internal provenance reader, migration 0016 (two append-only tables plus a decision marker), review-boundary preflight/reservation/refusal attribution, the `prepare_reads` facade hook, F0011 contract registration.
- Out: new routes, grants, UI, model/parse/producer, canonical orchestration (F0018), retraction semantics (F0010), learning (F0041), public provenance API (F0020).

## Lifecycle Stage

- G0 assembly plan reconciled (PASS); manifest in-progress
