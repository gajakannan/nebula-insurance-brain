# Action Context

> Seeded by init-run.py. Fill the judgment sections before the first gate.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** feature
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0005
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0005-one-time-docling-ingestion
- **feature_slug:** one-time-docling-ingestion
- **mode:** clean
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-10-25-4020923b
- **run_id:** 2026-10-25-4020923b

## Inputs

- Operator selection: `NEBULA_PRODUCT_ROOT=/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` (explicit prompt value, resolved by `_product_root.py`).
- Feature: `F0005` (`one-time-docling-ingestion`); mode `clean`; slice order source `assembly-plan`.
- Current feature PRD, five story files, STATUS, approved feature assembly plan, compatibility evidence, GETTING-STARTED, and product blueprint/instructions.
- Tier 1 KG lookup for F0005, scoped to this run.
- No prior feature-completion run was returned by init-run (`run_id_prior: null`).

## Assumptions

- The existing Phase B rework plan is approved and is the implementation source of truth; this run will validate it rather than overwrite it.
- Synthetic development proof is historical evidence and does not satisfy the remaining live qualification criteria.
- The framework's active evidence contract version is 2026-07-11.

## Scope Boundaries

- Scope is limited to F0005 and its approved S0001–S0005 plan. No production-host rollout, new OCR engine, non-PDF input, or unrelated feature work.
- The plan specifies backend and AI work, QE qualification, DevOps preflight/deployability, independent code/security/architecture reviews, and PM closeout. The PRD introduces no UI; Frontend is not in scope.
- Graph activation is permitted only after measured thresholds, reviewer verdicts, and the operator decision; rejection must retain the explicit direct-baseline/v1 settings.

## Lifecycle Stage

- G0 passed — architect assembly-plan review and required-role initialization. G1 remains failed after Docker startup; PostgreSQL/AuthentiK are healthy and the Brain secret is provisioned, while GPU/loopback access remain unavailable.
