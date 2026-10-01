# F0002 — Getting started

## Current state

Done and archived (2026-09-28). The implementation was delivered on branch `feature/F0002-tenancy-kernel` by feature run `2026-09-27-bb7c8d1d`. Evidence is in `planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/`. Start with PRD.md, feature-assembly-plan.md, ADR-0061/0062 (accepted for the bounded F0002 scope), the v1 internal schema, and the run's test-plan.md.

## Key implemented files

- Domain carriers: `engine/packages/brain-domain/src/brain_domain/{tenancy,authx}.py`
- The only allow/deny rules: `engine/packages/brain-security/src/brain_security/evaluation.py`
- Transaction and audit facade: `brain_security/execution.py`. Identity: `verification.py`, `principals.py`, `identity_profile.py`. Delegation rules: `delegation.py`
- Persistence: `engine/packages/brain-persistence/src/brain_persistence/{authx,tenancy,identity,grants}.py`; synthetic test fixtures in the dev-only `engine/packages/brain-testing` package
- Migrations: `engine/migrations/versions/0005_tenancy_authx_expand.py`, `0006_tenancy_authx_constrain.py`, `0007_tenancy_authx_safeguards.py` (BLUEPRINT §4.11: immutable ownership, append-only audit, deferrable self-references)
- Consumers: `engine/apps/api/src/brain_api/{deps.py,routes/*}`, `brain_temporal/commit.py`, and `engine/apps/worker/src/brain_worker/document_delivery.py` (sync adapter over the same evaluator)
- Operational scripts: `scripts/dev/reconcile_authx.py`, `provision_delegation.py`, `revoke_membership.py`
- Config: `config/authx-identity-profile.yaml` (non-secret; `BRAIN_OIDC_ISSUER` must be listed)

## Operator runbook (fresh or upgraded database)

1. Snapshot the database (`pg_dump -Fc`), then run `cd engine/migrations && uv run alembic upgrade 0005`.
2. Write a reviewed mapping (format in the `reconcile_authx.py` docstring): tenants, workspaces and KBs for every existing KB; entity tenants; one complete restriction slice per existing membership; security metadata for every protected record. Nothing is inferred.
3. Run `uv run --project engine python scripts/dev/reconcile_authx.py --mapping <file> --dry-run`, which prints counts, orphans, conflicts, and the mapping digest. Resolve every `blocking` entry.
4. Run the same command with `--apply --expected-digest <digest> --actor-id <operator uuid> --approval-ref <ref> --activate-policy`. It is one audited transaction; re-applying the same digest is a no-op.
5. Run `uv run alembic upgrade 0006` (it refuses with a counts-only report if anything is still unreconciled), then `uv run alembic upgrade head` for the 0007 safeguards.

Protected routes return a sanitized 503 until a policy release is active (fail closed). Service and agent identities must be provisioned to their kind (`brain_persistence.identity.provision_principal`). Only human clients listed in the identity profile self-provision, and they get no grants. `worker_cli --enqueue` now requires at least one `--classification` (and optional `--source-acl`) for the artifact's security metadata.

Running the engine PostgreSQL security suites locally resets the shared dev database's F0002 registries. Re-run step 4 with an empty mapping and `--activate-policy` afterwards.

## Repository and run

Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`.
Framework root: `/home/gajap/uSandbox/repos/nebula/nebula-agents`.
Existing Plan A+B run: `2026-09-25-3c64470a`. Do not initialize a different run to resume this plan.

Always pass `--product-root` explicitly to framework scripts. This session’s tool shells did not inherit NEBULA_PRODUCT_ROOT; a parent-shell export is not proof the launcher forwards it.

From the framework checkout:

```bash
python3 agents/scripts/resume-brief.py --run-id 2026-09-25-3c64470a --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --workstate /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-09-25-3c64470a/workstate.yaml
python3 agents/scripts/project_context.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --action plan
```

## Implementation prerequisites

- Reuse F0001’s Python 3.13+/uv/PostgreSQL 18 and authentik local foundation; follow the existing repository setup and dependency matrix, not new unpinned dependencies.
- Preserve principal/resource UUIDs. Inventory existing data before migrations; supply an explicitly reviewed workspace/restriction mapping. Never infer missing grants from email, KB IDs or entity references.
- Reuse TenantMember, Reviewer and ServicePrincipal permissions exactly. A principal kind is not a role. Reviewer-only does not imply content_artifact:read.
- Existing worker authorization is synchronous and independently commits audit. Share the evaluator through adapters without removing lease/fencing or adding a second event loop.
- Migrations 0005/0006/0007, the operational scripts, and the tests listed in the assembly plan now exist and pass (run `2026-09-27-bb7c8d1d`).

## Verify

From `engine/`:

```bash
export BRAIN_TEST_POSTGRES_URL=postgresql+psycopg://brain:brain@localhost:5432/brain
uv run pytest -q tests/contract tests/integration tests/security   # contract, migration, EX-AUTHX suites
uv run pytest -q                                                   # full engine suite (282 in the run)
```

From `neuron/`: `BRAIN_TEST_POSTGRES_URL=... uv run pytest -q tests/integration` (worker delivery, recovery, CLI enqueue).

## Contract examples

worked-examples.md contains 18 independent expected behavior cases. contract-examples.json contains synthetic valid/invalid schema examples. Schema validation proves shape only; the feature run must execute the behavior cases through consumers and record actual results. Keep development fixtures outside the frozen holdout.

## Architecture boundaries

No automatic review-to-truth promotion: F0002 authorizes existing review/commit consumers independently, F0018 owns full orchestration, F0022 owns the review UI. ADR-0042/0052/0053 remain proposed for broader security surfaces. F0005 production activation remains separately gated.

## Verified planning checks

G4 compile/drift and all seven automated G5 operations passed in plan run `2026-09-25-3c64470a`. User explicitly approved Phase B with `approve-phase-b` on 2026-09-25. Additional plan-readiness, semantic examples, AuthX contract examples and OpenAPI validation passed. OpenAPI retains advisory health/public-status and review-receipt warnings; protected-resource denial remains 404.

Reproduce the 12 synthetic contract shape cases from the product root:

```bash
python3 scripts/validation/validate_authx_contract_examples.py
```

This does not run the future runtime security suite.
