# Action Context

> Seeded by init-run.py. Fill the judgment sections before G0.

## Run Identity

- **action:** feature
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0001
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0001-repository-and-engineering-foundation
- **feature_slug:** repository-and-engineering-foundation
- **mode:** clean
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-09-12-855d2b93
- **run_id:** 2026-09-12-855d2b93
- **run_id_prior:** 2026-09-08-b5af1e54

## Inputs

- Feature: `F0001`
- Prior approved run: `2026-09-08-b5af1e54`
- Mode: remediation rerun of the `feature` action
- Primary feature path: `planning-mds/features/archive/F0001-repository-and-engineering-foundation/`
- Diff lock: `artifacts/diffs/changed-files.txt`

## Assumptions

- The prior run's proof results and four security scan artifacts remain valid for
  unchanged surfaces and are cited as baseline evidence.
- This remediation adds no new semantic graph nodes or bindings.
- Postgres/AuthentiK Compose health is verified, but managed-sandbox host access to
  Postgres may be unavailable; QE must report that as a bounded skip, not a pass.

## Scope Boundaries

- In scope: credential-failure logging/non-disclosure, security tests, bounded QE
  runtime preflight, archived feature/Blueprint status reconciliation, evidence package
  completion, and validation of existing KG/tracker state.
- Out of scope: new feature capabilities, schema/migration changes, deployment changes,
  frontend behavior, and new canonical KG nodes.

## Lifecycle Stage

- remediation complete; G0–G8 and closeout validators passed
