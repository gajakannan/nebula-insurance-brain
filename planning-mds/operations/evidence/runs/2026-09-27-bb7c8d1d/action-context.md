# Action Context — F0002 feature run 2026-09-27-bb7c8d1d

## Run Identity

- **action:** feature
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0002
- **feature_slug:** tenancy-aware-domain-kernel-and-principal-contracts
- **feature_index_root:** planning-mds/operations/evidence/features/F0002-tenancy-aware-domain-kernel-and-principal-contracts
- **mode:** clean
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain (resolved explicitly; the framework default points at the CRM repo)
- **framework_root:** /home/gajap/uSandbox/repos/nebula/nebula-agents (main at dde49dc)
- **run_folder:** planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d
- **run_id:** 2026-09-27-bb7c8d1d
- **run_id_prior:** None (no feature latest-run.json exists; the only prior F0002 run is plan run 2026-09-25-3c64470a, status approved)
- **branch:** feature/F0002-tenancy-kernel, off origin/main 2024fc0

## Inputs

- Approved PRD, six stories, acceptance checklist, worked examples EX-AUTHX-001–018 and contract-examples.json in the feature folder.
- Approved Phase B feature-assembly-plan.md (plan run 2026-09-25-3c64470a), ADR-0061, ADR-0062 (both Proposed), `planning-mds/schemas/authx-kernel.schema.json` (v1), `planning-mds/api/brain-api.yaml` 0.2.0.
- Existing runtime: engine/ packages brain-domain, brain-security, brain-persistence, brain-temporal, brain-review, brain-jobs, apps api and worker; migrations 0001–0004; neuron F0005 worker consumer.
- Product instructions: `planning-mds/BLUEPRINT.md`, `docs/agent-instructions.md` via `project_context.py --action feature` (no required product checks for this action).
- KG lookup: `scripts/kg/lookup.py F0002 --tier 1` (6 capabilities, 9 entities, 6 endpoints, 8 governing ADRs, 3 roles).

## Assumptions

- The dev PostgreSQL volume is disposable proof state. It is snapshotted with pg_dump before migrations are applied; it is at revision 0003 (0004 never applied to it).
- Local proof runs in the existing Docker Compose stack (PostgreSQL 18 + authentik). No production host exists (F0026).
- Baseline before any change: engine 145 passed / 4 skipped (the skips are brain-jobs PostgreSQL proofs gated on BRAIN_TEST_POSTGRES_URL); neuron delivery/recovery 20 passed / 5 skipped (same gate).
- A skipped PostgreSQL test is not a pass. QE sets BRAIN_TEST_POSTGRES_URL for G2 evidence.

## Scope Boundaries

- In scope: engine/ kernel, persistence, migrations 0005/0006, API consumers (content, facts, reviews), commit service, worker authorization adapter, brain-jobs UUID reconciliation, trusted dev scripts, non-secret identity profile config, the minimal neuron worker CLI change to provision artifact security metadata at trusted submission.
- Out of scope: new pilot grants or roles, UI, BFF/session (F0021), review UI (F0022), full review-to-canonical orchestration (F0018), MCP/A2A transports (F0047), cross-runtime parity and production qualification (F0026), ADR-0060 activation.
- Shared semantics (schema, ADRs, KG nodes) change only in the Architect role; the v1 schema is implemented as written.

## Lifecycle Stage

- G0 assembly-plan validation in progress (Architect).
