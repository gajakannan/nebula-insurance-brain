# F0002 — Getting started

## Current state

Phase A is approved. Phase B is validated and approved by user (`approve-phase-b`, 2026-09-25); it is not delivered runtime behavior. All six stories remain Not Started. Start with PRD.md, feature-assembly-plan.md, ADR-0061/0062 and the v1 internal schema; exact new/modified runtime files and test commands are in the assembly plan.

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
- New migration 0005/0006, operational scripts and tests are proposed paths; they are not executable yet. Commands under “Verification and handoff” are future implementation checks.

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
