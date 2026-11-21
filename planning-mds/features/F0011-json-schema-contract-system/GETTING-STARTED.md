# F0011 — Getting started

## Current planning state

Phase A and Phase B are approved in plan run `2026-11-20-ccb1bd39` (operator
Phase B token `approve-phase-b`, 2026-11-20). Six stories are Not Started. Read
[PRD](PRD.md), the assembly plan and contract design; independent plan-review
precedes the feature action.
No new runtime setup or migration is delivered by this plan.

## Prerequisites

- Use `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` as
  `NEBULA_PRODUCT_ROOT` for this run and pass it explicitly to framework scripts.
- Framework checkout: `/home/gajap/uSandbox/repos/nebula/nebula-agents`, pinned to
  `840e724b72fdbaf8157dacfee579488252e1a193`.
- Existing F0001/F0006 runtime contracts are prerequisites. F0004/F0007/F0008
  are impacted compatibility baselines, including migration head 0015.
- The feature action follows completed plan approvals and independent plan-review.

## Existing reference files

| Path relative to product root | Use |
|-------------------------------|-----|
| `engine/packages/brain-contracts/src/brain_contracts/assertions.py` | Offline assertion validation and Pydantic adapter |
| `engine/packages/brain-contracts/src/brain_contracts/dispatch.py` | Explicit legacy/v2 result reader |
| `engine/packages/brain-content/src/brain_content/contracts.py` | Packaged content contract validation |
| `planning-mds/schemas/fact-answer-v1.schema.json` | Shipped answer envelope definition |
| `planning-mds/schemas/fact-slot-key-v1.schema.json` | Shipped typed-value definitions |
| `planning-mds/schemas/fact-temporal-v1.schema.json` | Shipped temporal result metadata |
| `engine/packages/brain-factslots/tests/test_contract_examples.py` | Existing design/schema/domain comparison |
| `experience/package.json` | Existing JS build/test host; AJV is not installed yet |

## How to verify

Planning checks validate stories and trackers; they do not demonstrate runtime
conformance. The future feature run must document and execute schema generation,
Python/Pydantic/AJV shared cases, OpenAPI reference checks, installed-package
offline proof and real consumer compatibility tests. Exact commands are a Phase B
deliverable and must be verified in implementation before being described as run.

## Services, environment and seed data

Planning needs no runtime service or credentials. Contract conformance requires
the existing Python/JavaScript toolchains; any database integration proof uses
the existing local stack selected by the assembly plan. No new secret, environment
variable or production fixture is introduced. Synthetic fixtures stay outside the
frozen holdout.

## Resume this run

From the framework checkout, run:

```bash
python3 agents/scripts/resume-brief.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --run-id 2026-11-20-ccb1bd39
python3 agents/scripts/project_context.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --action plan
```

Reuse this run ID. The feature evidence index is not created during plan.

## Gotchas

- The blueprint's repository-root `schemas/` path does not exist yet; existing
  contracts live in package resources and design-time planning schemas. Phase B
  must settle authority and reproducible publication before consumer integration.
- A correct schema cannot establish artifact ownership, supported ISO currency,
  predicate-required basis, evidence admissibility or permission to read an answer.
- F0008 validity-unknown belongs to the temporal envelope, not information state.
- Do not reinterpret legacy pilot values as identity-v1 answers or silently
  downgrade a failed v2 contract to a legacy reader.

## Proposed implementation and verification

Read [feature-assembly-plan.md](feature-assembly-plan.md) for exact future files,
interfaces, generator/check command contract and integration order. Those tools
are not implemented or claimed to have run by this planning action.

Source definitions stay in planning-mds/schemas; the feature run generates the
root schemas/contracts/v1 snapshot, installs the same resources in brain_contracts,
and generates Pydantic, JS, metadata and the self-contained OpenAPI snapshot.
No runtime lookup may depend on a feature-folder or planning-directory path.

Native current readers keep their exact compatibility policy. Do not put a new
strict schema guard before the tolerant source-key discovery/current source READ
checks or replace a domain reason with a schema error. Commit output validation
must occur before the outer authorized mutation commits; no nested UoW.

The JS contract proof is headless. No server, browser, live inference, PDF reparse
or new database migration is needed for structural checks. PostgreSQL integration
remains required for affected mutation/authorization regressions in the feature run.
