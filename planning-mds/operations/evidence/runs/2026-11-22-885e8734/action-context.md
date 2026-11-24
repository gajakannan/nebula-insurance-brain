# Action Context

Feature action, policy 2026-07-11. Same run continued after a usage interruption.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** feature
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0011
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0011-json-schema-contract-system
- **feature_slug:** json-schema-contract-system
- **mode:** clean
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-22-885e8734
- **run_id:** 2026-11-22-885e8734

## Inputs

- FEATURE_ID=F0011; MODE=clean; SLICE_ORDER_SOURCE=assembly-plan.
- Approved Phase B revision: 2026-11-21-e4098d22; six stories and 41 ACs.
- Canonical product root selected from the shell environment, resolved before discovery.

## Assumptions

- No new business rules. Existing native readers retain their fixed compatibility profile.
- All 443 portable cases passed JSON Schema, generated/source-gated Pydantic and AJV (1329 results). All 21 source conditionals have79 executed branch witnesses.
- Existing dev/integration databases are inventoried individually; empty databases
  require actual complete read-only sweeps and QE/DevOps inventory signoff.

## Scope Boundaries

- Only F0011 contract publication, headless validation and existing consumer adoption.
- No new HTTP route, grant, schema migration, model activation, UI or document reparse.
- Restore dev only to already shipped migration 0015; no historical cleanup.
- Response guards activated only after both signed full-history candidate sweeps
  passed; final current-code cutover sweeps also passed.
- ADR-0079 and ADR-0039 remain Proposed; no formal acceptance is implied.

## Lifecycle Stage

- G0 and G1 passed. G2 report/packaging refresh is in progress after passing runtime
  tests, conformance and final history sweeps; G2–G8 have not passed.
- Resume helper incorrectly reports all gates complete despite partial completed gates;
  this advisory defect is tracked in README.md. The actual gate journal controls.
