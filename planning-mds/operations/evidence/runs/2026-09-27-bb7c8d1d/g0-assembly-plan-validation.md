# G0 — Assembly Plan Validation — F0002 run 2026-09-27-bb7c8d1d

**Role:** Architect (agents/architect/SKILL.md)
**Date:** 2026-09-27
**Verdict:** PASS

Result: PASS

## Step 0 — Authoring

`feature-assembly-plan.md` already exists. It was authored and approved in plan run
2026-09-25-3c64470a (`approve-phase-a`, `approve-phase-b`). Mode is `clean`, but the
prompt forbids overwriting an existing plan, so this gate validates and reconciles it
against the code as it stands today. It does not re-author it. The umbrella
`planning-mds/architecture/feature-assembly-plan.md` already references the
feature-local plan (plan-run changed_paths).

## Step 0.5 — Validation checklist

| Check | Result | Evidence |
|---|---|---|
| Scope split matches the six stories | PASS | Build-order table maps S0001–S0006 to steps 1–6; the story-AC-to-case map (EX-AUTHX-001–018) matches the acceptance checklist |
| Agent dependencies identified | PASS | Steps 1→6 are ordered security boundaries (ownership → identity → scope → restrictions → delegation → consumers + audit). No frontend. AI Engineer is limited to the worker CLI trusted-submission change (see R3) |
| Integration checkpoints feasible | PASS | Each step names an observable checkpoint. All consumers exist today: routes content/facts/reviews, CanonicalCommitService, DocumentJobAuthorization, DocumentResultImporter, worker_cli |
| No missing or conflicting artifact ownership | PASS | Backend owns engine code and migrations. DevOps owns migration apply, restore, and config. QE owns test plan and report. Security owns the verdict. Architect owns the schema and KG shards (unchanged in G0) |
| Existing-code inspection still accurate | PASS with deltas | Re-inspected every file in the "Existing code and concrete gaps" table on 2026-09-27. Deltas R1–R5 below |
| Required Signoff Roles matrix initialized | PASS | STATUS.md already lists Quality Engineer, Code Reviewer, Security Reviewer, DevOps, and Architect as Required=Yes (set 2026-09-25). The manifest required_roles is updated to match |

## Reconciliation deltas (plan wins; recorded in workstate.yaml decisions #0–#6)

- **R1 — worker ingest metadata.** At `ingest`, the job targets an artifact ID whose row
  does not exist yet. The plan also says missing security metadata denies. The trusted
  submitter therefore provisions the `resource_access` row for the pre-assigned
  artifact ID. The worker hydrates from it and checks that any existing
  `content_artifact` row agrees on ownership. The API requires both rows.
- **R2 — no restriction defaults.** New membership restriction columns and
  `resource_access` labels carry no defaults. Legacy rows are filled only from a
  reviewed reconciliation mapping, and migration 0006 enforces NOT NULL.
- **R3 — AI-scope boundary.** Only `neuron/.../worker_cli.py` changes: the `--enqueue`
  trusted submission gains explicit `--classification`/`--source-acl` inputs and
  provisions artifact security metadata. There are no model, prompt, or inference
  changes.
- **R4 — brain-jobs IDs.** PostgreSQL columns convert from String(36) to uuid in the
  migration. Queue metadata uses a portable TypeDecorator, so SQLite contract tests
  and random-schema PostgreSQL proofs keep working. Ownership FKs for job tables are
  DB-level (migration), not queue metadata.
- **R5 — legacy authorizer removed.** `AuthorizationService` and `ResourceRef`
  (caller-supplied snapshot, first matching membership) are deleted, and all
  consumers migrate to the execution facade. Keeping them would leave an unchecked
  bypass.
- **Noted, not in approved scope:** BLUEPRINT §4.11 lists Utopia-derived follow-up
  safeguards: ownership immutability triggers, link-table triggers, and deferred
  self-references. §4.11 marks them as "a follow-up for the F0002 implementation
  run, not an amendment to the approved plan". They are carried as an explicit
  follow-up in README.md, not silently added.

## Knowledge-Graph Binding Plan (G0 declaration; G7 diffs against this)

- Expected capability bindings: `structural-tenancy-and-entity-identity`
  (brain_domain/tenancy.py, brain_persistence/tenancy.py, migrations 0005/0006),
  `credential-verification-and-principal-resolution` (brain_security
  verification/principals/identity profile), `current-resource-scope` (scope.py,
  resources.py), `authorization-enforcement` (evaluation.py, casbin_adapter.py),
  `bounded-delegation` (delegation.py, provision_delegation.py), and
  `durable-authorization-decisions` (execution.py, audit.py, brain_persistence/authx.py).
- Existing F0002 capability/entity nodes were authored at plan time. No new canonical
  nodes are expected; any emergent surface is added at G7.

## Test and release checklist

- Real PostgreSQL migration, backfill, and FK tests (test_authx_migration.py). Skipped
  DB tests are not a pass.
- Security suite covering all 18 EX-AUTHX cases plus the no-mixed-slice, expiry, and
  audit-failure cases, through the API and worker consumers.
- F0001 API/commit/review and F0005 worker regressions stay green.
- Changed-kernel coverage ≥ 80% (brain_security, brain_domain); measured local p50/p95
  decision latency.
- pg_dump snapshot before applying 0004–0006 to the dev database; a restore drill is
  recorded by DevOps.
