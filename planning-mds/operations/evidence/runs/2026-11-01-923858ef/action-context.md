# Action Context

Read-only F0006 plan-readiness audit with three independent lanes: Product Manager, Architect and Code Reviewer.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** plan-review
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0006
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0006-assertion-plane-origin-and-interpretation-basis
- **feature_slug:** assertion-plane-origin-and-interpretation-basis
- **mode:** clean
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-01-923858ef
- **run_id:** 2026-11-01-923858ef

## Inputs

- PLAN_SCOPE=`feature`; TARGET=`F0006` (operator answer in chat, 2026-11-01); DIFF_RANGE: not supplied (review the current working tree at product HEAD `8228fec`, framework pin `308c81d`).
- NEBULA_PRODUCT_ROOT=/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain (source: shell environment, normalized by `_product_root.py`).
- FEATURE_SLUG=`assertion-plane-origin-and-interpretation-basis` (REGISTRY.md row F0006, v0.1A, Planned).
- FEATURE_PATH=/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/features/F0006-assertion-plane-origin-and-interpretation-basis
- PLAN_REVIEW_RUN_FOLDER=/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-01-923858ef
- Plan run under review: `2026-11-01-7d6d19ce` (manifest status `approved`; tokens approve-phase-a and approve-phase-b recorded).
- `lookup.py F0006` returned an exact `feature:F0006` match (artifacts/lookup-F0006.txt). This is first-pass routing only.

## Assumptions

- Raw artifacts take precedence over KG mappings and prior approval tokens. Any mismatch is recorded as a drift finding.
- `feature-assembly-plan.md` exists, but it is not required as a plan deliverable. It is read as context only.

## Scope Boundaries

- In scope: everything in FEATURE_PATH (PRD, 5 stories, checklist, personas, examples, contract-examples, STATUS, README, GETTING-STARTED and the assembly plan), plus ADR-0075 and the F0006-touched schemas, API, data-model, glossary, KG shards and trackers listed in the plan manifest `changed_paths`.
- Out of scope: other features, except to record discovered impact (F0005, F0016, F0018, F0022 and F0066 handoffs).
- Read-only: this run writes only inside its own run folder. It does not edit plan, KG, tracker or feature-evidence artifacts.

## Lifecycle Stage

- PR0–PR4 complete; verdict CONDITIONALLY READY
