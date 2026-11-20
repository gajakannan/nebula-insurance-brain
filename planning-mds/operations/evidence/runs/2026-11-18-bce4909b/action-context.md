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
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-18-bce4909b
- **run_id:** 2026-11-18-bce4909b
- **run_id_prior:** 2026-11-17-1a4ae2f0

## Inputs

- FEATURE_ID F0008, MODE clean (targeted remediation). The prior approved completion run `2026-11-17-1a4ae2f0` (PR #55) becomes RUN_ID_PRIOR and is superseded at G8.
- Findings: review `2026-11-18-d34a095e` (NOT DONE) and audit `2026-11-18-a3709ba0`.
- Operator decisions (2026-11-18): implement AC7 in the commit response; amend S0004 AC1 and keep the F0002 audit; fix lineage now in migration 0015.
- Branch `fix/F0008-review-remediation` from `origin/main` 339c920.

## Assumptions

- The feature folder stays archived and is edited in place, as F0007's remediation run `2026-11-09-81798e61` did.
- The superseded run's evidence is not rewritten; its label errors are corrected by errata in this run.

## Scope Boundaries

- In scope: the findings listed in the assembly plan's "Review Remediation" section.
- Out of scope: ADR-0078 acceptance (an operator decision) and F0018 delivery.

## Lifecycle Stage

- feature run initialized
