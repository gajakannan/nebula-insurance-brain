# F0011 Plan Review — 2026-11-21-b4cd07e4

## Decision

**READY** (`gate_policy.py --profile review-family`: 0 Critical, 0 High, 2 Medium, 4 Low).

- **Scope:** PLAN_SCOPE=feature, TARGET=F0011.
- **Plan reviewed:** the plan from run `2026-11-20-ccb1bd39`, on product `main` at `3673715`.
- **Result:** an implementation agent can start `feature.md` Step 0 without inventing product rules, contract shapes, authorization order, error mapping or the build/check command contract.
- **Recommendations:** the two Medium findings should be addressed at the feature run's G0. They do not block the feature run.
- **ADRs:** ADR-0079 and ADR-0039 correctly remain Proposed. This review does not accept either one.

## Findings By Severity

### Critical

None.

### High

None.

### PR-M1 — Medium — Rollout to existing reads has no check that stored versions pass the new response guard (Architect)

- **Evidence:**
  - `feature-assembly-plan.md:241` and `:250-251` add schema validation of the serialized `GET /facts/{factSlotId}` response. An invariant failure becomes a generic 500 `contract_invariant_failed` (`:267`).
  - `feature-assembly-plan.md:240` and `:247-249` add the same validation to the commit response inside the `operation`.
  - The planned proof is fixture-based: "old flat response unchanged" (`:241`) and "legacy/current response" (`:240`).
  - No step runs the already-stored `fact_versions` rows, which include legacy pilot values and F0008 temporal blocks, through the new response guard before the guard is enabled.
  - `fact-version-read-v1.schema.json` makes `temporal` a `$ref` to `fact-temporal-v1#/$defs/version_temporal` and asserts `date-time` and `uuid` formats on every timestamp and ID.
- **Impact:** any stored row that today's `FactVersionOut` serializes successfully but the stricter source schema rejects would turn a working historical read into a 500. That would break S0005-AC4 ("retain their declared wire shapes") for real data, even though every fixture passes.
- **Owner and route:** Architect (QE executes). At feature G0, add one of these to the S0005 proof:
  - a read-only sweep that serializes and validates every stored version in the integration and dev databases; or
  - an explicit statement that no non-fixture stored data exists in any v0.1 environment.
- **Not blocking:** the existing ACs already require unchanged history. This finding asks for the evidence method, not for a new requirement.

### PR-M2 — Medium — The planning inventory gives every resource the same disposition and no consumer entry point (Product Manager / Architect)

- **Evidence:**
  - Every one of the 17 existing resources in `contract-inventory.yaml` (`:15`, `:22`, `:29`, …) carries the same text: "shared-source-adapter; preserve native compatibility entry point".
  - No resource has a consumer, compatibility test or version-selector field.
  - S0001-AC2 requires the inventory to name "packaged/generated consumers, owner and version selector for every in-scope contract".
  - S0005-AC1 requires each resource's "consumer entry point, compatibility test and disposition".
  - `contract-design.md:122-130` lists consumers by group only.
  - A read-only search found no non-test runtime validator for `content-artifact-manifest-read` or `problem-details`. They are referenced only from `brain-content/tests/test_versioned_content.py`, `tests/security/conftest.py` and the OpenAPI document. So "preserve native compatibility entry point" does not describe them.
- **Impact:** the feature run must derive the per-resource mapping before it can author `scripts/contracts/sources.yaml`. A uniform disposition invites a "delegate" wrapper for a resource that has no runtime entry point, or a missing compatibility test for one that does.
- **Owner and route:** Architect, at feature G0. Expand `sources.yaml` and the S0005-AC1 inventory per resource with these fields:
  - consumer entry point, or "OpenAPI/doc-only";
  - compatibility test;
  - version selector;
  - one disposition: adopt, delegate, or retain a versioned boundary.
- **Not blocking:** both ACs already make this mapping a feature-run deliverable.

### PR-L1 — Low — The tracker rationale still mentions an F0011 migration (PM)

- **Evidence:**
  - `features/ROADMAP.md:30` and `kg-source/features/F0011.yaml:14` say "Its migration is numbered after F0008's 0015".
  - The approved plan adds no migration: `feature-assembly-plan.md` "Data Model, Cache and Deployment", ADR-0079 decision 7, and `README.md` ("No database registry/migration").
- **Route:** PM. Change the text to "any future migration…" on the next KG shard touch. The ROADMAP row is generated from the shard.

### PR-L2 — Low — STATUS header says Draft while the README and REGISTRY say Planned (PM)

- **Evidence:** `STATUS.md:3` has "Overall Status: Draft". `README.md:3` and `REGISTRY.md:35` have "Planned".
- **Note:** `validate-trackers` passes, so this is a wording inconsistency only.
- **Route:** PM, on the next touch.

### PR-L3 — Low — The GET response guard can fail after the read audit already recorded success (Architect / Security)

- **Evidence:**
  - `feature-assembly-plan.md:250-251` places GET output validation after `execution.read` completes.
  - In the current code, `routes/facts.py:138-151` builds `FactVersionOut` after the read facade returns.
  - On the commit path, the plan validates inside `operation`. There, `brain_security/execution.py:480-484` records a FAILED decision before the exception propagates.
  - The GET path has no equivalent, so an invariant 500 follows a SUCCEEDED read audit.
- **Impact:** the audit trail and the client outcome disagree only in the internal-invariant case. No data is disclosed.
- **Route:** Security reviewer. At G3, either accept this as an internal-invariant case or record a follow-up. No plan change is required before build.

### PR-L4 — Low — The stories' user-story sentences are ungrammatical (PM)

- **Evidence:** all six stories (for example `F0011-S0001-…md:13`, "I want resolve an explicit…") are missing "to" after "I want".
- **Note:** this is cosmetic. `validate-stories` passes.

## Product Readiness

*Owner: product-manager.*

**Value and non-goals**
- The PRD states user value, the business objective and a numeric success definition: 41 ACs, 100% case agreement and at least 80% changed-line coverage.
- The out-of-scope list is explicit and names each later owner: F0012/F0013/F0015 for ontology and compiler, F0014/F0023 for package completeness and display, F0016 for scopes, F0017 for entity resolution, F0018 for commit orchestration.

**Stories and acceptance criteria**
- Six stories with 7/7/7/7/7/6 ACs.
- Each AC is specific and testable, and each includes negative cases. Examples:
  - S0002-AC2 lists the five rejected shapes;
  - S0003-AC2 lists rejected money encodings;
  - S0004-AC3 says a skipped case or a crash counts as failure;
  - S0005-AC3 forbids retrying through a more permissive reader.
- No TODO, placeholder or vague build-critical wording was found.

**Mutation contract**
- The feature adds no new write path.
- Each story's Interaction Contract names its entry points, editable versus immutable artifacts, the persistence evidence (a fresh read after a write), the role (maintainers publish; runtime principals are unchanged), the failure behavior (a non-disclosing diagnostic) and audit (no business timeline event; existing write audit stays mandatory).
- S0005-AC5 requires a re-query of authoritative state after a refusal.

**UI**
- The PRD "Screen Layouts (ASCII)" section justifies "No UI". The JS consumer is headless, so F0021 is correctly not a prerequisite.

**Personas and trackers**
- `personas.md` reuses existing engineering personas, and no new runtime role is introduced.
- REGISTRY, ROADMAP, the README, STATUS, the acceptance checklist and the KG shard agree on status, the 6/41 counts and the approval tokens. Exceptions: PR-L1 and PR-L2.

**Product checklist rule — BRAIN-SCOPE:** PASS. Evidence: the PRD "Scope & Boundaries" section and each story's Acceptance Criteria and Out of Scope sections.

## Architecture Readiness

*Owner: architect.*

**Source authority and dialect**
- ADR-0079 (Proposed) settles each Phase B design task the PRD listed:
  - one authored source in `planning-mds/schemas`;
  - a generated root `schemas/contracts/v1` snapshot;
  - a single installed `brain_contracts/resources/v1`;
  - source-gated Pydantic;
  - headless AJV;
  - a self-contained OpenAPI snapshot.
- Alternatives are considered and the proof conditions are explicit.

**Raw artifact verification (performed in this review)**
- All 21 inventoried sources exist, and every SHA-256 matches `contract-inventory.yaml`. Both tooling schemas also exist.
- Every packaged schema copy under `brain-contracts/src/.../schemas` and `brain-content/src/.../schemas` is byte-identical to its planning source. Delegating to the shared bundle therefore changes no current acceptance set. The only differing copies are in the git-ignored `brain-content/build/lib` build output.
- A keyword scan of all 21 resources found no keyword outside `schema-validation-profile.yaml`. The formats in use are exactly `uuid`, `date`, `date-time` and `uri-reference`, which matches the profile.
- All 74 cases in `contract-examples.json` validate against `schema-conformance-cases-v1`. The 68 instance cases replay with zero mismatches under a local Draft 2020-12 validator. As the design states, this is planning evidence only, not AJV, Pydantic or consumer proof.
- `fact-version-read-v1` matches `FactVersionOut` (`brain_api/schemas/facts.py:108-153`) field by field. That includes the seven-value `ChangeReasonLiteral` (`:17-19`) and the optional F0008 fields.
- The `canonical-commit-request` `oneOf` matches the `CommitProposalIn._one_time_shape` rule.
- `brain-api.yaml:640-643` already references the new schema.

**Existing-code claims**
- These all exist as described:
  - the `brain_content/contracts.py:61-80` parent-directory planning fallback;
  - the `assertions.py` offline `Registry(retrieve=_no_remote_reference)`;
  - `FactSlotResolver.resolve`, `FactAnswerPolicy.canonical_value` and `source_keys`;
  - `CanonicalCommitService._commit_v1` and `_remainder`;
  - `create_app`'s `/openapi.json`.
- The proposed dependency direction (content, factslots and temporal depending on brain-contracts) creates no cycle, because brain-contracts depends only on pydantic, jsonschema and brain-domain.
- Neuron reaches brain-contracts and brain-content through path dependencies, so the plan's dual-lock requirement (`feature-assembly-plan.md:51`) is necessary and correctly stated.
- The proposed `ContractError(ValueError)` does not collide with an existing broad `except ValueError` on the commit path. The only catches are the narrow `_uuid` helpers and `bounds.py` parsing.

**Authorization and errors**
- The resource/action policy is unchanged.
- The plan pins validation after tolerant source-key discovery and after the source READ checks, and preserves the existing 401/404/409/422/503 precedence.
- The single new error is a generic 500 that carries no pointer or input data.
- The commit-side guard runs inside `AuthorizationExecution.mutate`'s `operation`, which already rolls back and records FAILED (`execution.py:480-484`). See PR-L3 for the GET asymmetry.

**Data, workflow and NFRs**
- No DDL, table, queue or route is added, and the README presents the artifact model as an ER view.
- The portable-profile limits are measurable: 16 MiB, depth 128, one million nodes, 256 resources, and safe-integer and format rules.
- No latency SLO is set. Stories state this explicitly (for example `F0011-S0001-…md:67`), which is acceptable for build-time infrastructure. Feature QE should still record GET and commit overhead.

**KG**
- The `F0011.yaml` shard binds real planning artifacts only, in line with the "Do not bind nonexistent paths" rule at `feature-assembly-plan.md:81-82`.
- `lookup.py F0011` resolves unambiguously. KG validate and drift pass (PR2).
- The only KG wording issue is PR-L1.

**Product checklist rules**

| Rule | Outcome | Evidence |
|---|---|---|
| BRAIN-AUTHORITY | PASS | ADR-0013/0077/0078 Accepted; ADR-0079/0039 Proposed, with acceptance conditions in ADR-0079 "Required Proof Before Acceptance" and the PRD Risks section |
| BRAIN-EVIDENCE | PASS (scoped) | Structural validity explicitly grants no evidence authority: PRD "Problem Statement", S0002-AC7, S0003-AC7, ADR-0079 D2 |
| BRAIN-PARSE-ONCE | PASS (exclusion) | S0005-AC7 and ADR-0079 D7: no reparse or reinterpretation |
| BRAIN-TEMPORAL | PASS | F0008 temporal carriers preserved: S0002-AC7, S0005-AC4, `feature-assembly-plan.md:246-248` (no revalidation or rewrite of legacy remainders) |
| BRAIN-AUTHORIZATION | PASS | `feature-assembly-plan.md:237-241, 270-272`; negative tests "Denied source remains 404 even if payload would fail validation"; S0002-AC6, S0005-AC6 |
| BRAIN-EXAMPLES | PASS | S0006-AC4, `acceptance-criteria-checklist.md` links to EX-GL-001, EX-OWN-002/003 and the glossary; synthetic data labeled and kept outside the holdout |

## Buildability Challenge

*Owner: code-reviewer.*

**Vertical slice and order**
- The five-step build order maps one-to-one to the stories, and each step has an integration checkpoint (`feature-assembly-plan.md:22-30`).
- The feature is broad: 5 packages, the API, Neuron, experience and CI. Its scope is bounded by "no new route, grant, DDL or screen".
- The KG risk is 7/10 (`feature-assembly-plan.md:377-388`). The plan already requires an additional independent reviewer and primary-maintainer acknowledgement before merge.
- Recommendation: merge in the plan's step order rather than as one change, so each integration checkpoint can be reviewed on its own.

**Role handoffs**
- Each role owns distinct paths with no conflict: Backend (bundle and adapters), Frontend (headless `experience/scripts/contracts/*` only), QE, DevOps, Security, and Architect (`:341-357`).
- Five signoff roles are required per story (`STATUS.md` signoff table), and the AI Engineer is consulted only for Neuron regression.

**Testability**
- The AC-to-proof map (`:310-325`) covers all 41 ACs and names concrete test files and commands (`:279-286`).
- The negative paths that matter are named: dormant-branch missing refs, hash and identity corruption, drift injection, a duplicate-key JSON parser, no-network installation outside the checkout, and a PostgreSQL re-read after refusal.

**File, API and schema direction**
- The plan gives exact existing files and their required changes (`:36-53`), new files with owners (`:60-79`), Python and TS interface signatures (`:91-121`, `:171-189`), the closed error codes (`:143-146`) and the HTTP mapping (`:259-268`).
- Implementation should not need broad code search or speculative design.

**Dependencies and sequencing**
- F0001 and F0006 are done. F0004/F0007/F0008 are compatibility baselines, and each has an approved evidence manifest cited in `runs/2026-11-20-ccb1bd39/artifact-trace.md:38-41`.
- F0012 plans in parallel but builds after F0011.
- The archived case-inventory path decision is assigned to feature G0 (`:288-292`).

**Risk hotspots for extra review**
- `routes/facts.py` commit `operation`: the response must now be built inside the UoW.
- `AuthorizationExecution` read and mutate ordering.
- `brain_content.contracts.schema`: removing the fallback.
- `neuron/uv.lock` coherence.
- Generator fidelity of `datamodel-code-generator` for `if`/`then`/`else`, `contains` and nullable unions. This is mitigated by the source gate and the fail-closed rule at `:194-196`.

**Product checklist rule — BRAIN-BUILDABILITY:** PASS. Ownership, prerequisites, interfaces and validation are stated. PR-M1 and PR-M2 are G0 refinements.

## Validation Evidence

PR2 ran through `run-gate.py --action plan-review --stage PR2 --plan-scope feature --target F0011`. The full results are in `lifecycle-gates.log`, `commands.log`, `gate-state.json` and `artifacts/project-checks/`.

| Check | Exit | Result |
|---|---|---|
| `check-plan-approvals.py --plan-scope feature --target F0011` | 0 | PASS |
| `validate-stories.py {FEATURE_PATH}` | 0 | PASS |
| `validate-trackers.py` | 0 | PASS |
| `scripts/kg/validate.py` | 0 | PASS |
| `scripts/kg/validate.py --check-drift` | 0 | PASS |
| `validate_templates.py` | 0 | PASS |
| Project check `plan-readiness` (`validate_plan_readiness.py --plan-scope feature --target F0011`) | 0 | PASS |

All seven PR2 checks exited 0.
- `check-plan-approvals` found one current base-run-only planning approval for F0011 and no active rework.
- The project check `plan-readiness` returned `{"status": "pass", "findings": []}`. Its output is in `artifacts/project-checks/PR2-plan-readiness-4af9ca53c07141bcaa71e28054ec979f.*`.

These checks were also run during the review. They are read-only and were not run through run-gate:
- `scripts/kg/lookup.py F0011`: unambiguous, exit 0.
- A SHA-256 comparison of the 21 sources.
- A comparison of the packaged copies against the planning sources.
- The profile keyword and format scan.
- A local replay of the 74 cases.

## Artifact Trace

**Feature package:** `features/F0011-json-schema-contract-system/**`. That covers the PRD, personas, the 6 stories, STATUS, the README, GETTING-STARTED, the acceptance checklist, `feature-assembly-plan.md`, `contract-design.md`, `contract-inventory.yaml`, `schema-validation-profile.yaml` and `contract-examples.json`.

**Architecture and schemas**
- `architecture/decisions/ADR-0079-*.md`; the status of ADR-0013, ADR-0039, ADR-0077 and ADR-0078.
- `schemas/*.schema.json`: the 21 inventoried resources and the 2 tooling schemas.
- `api/brain-api.yaml`: `FactVersion` and `ProblemDetails`.

**Trackers and KG**
- `features/REGISTRY.md`, `features/ROADMAP.md`, `kg-source/features/F0011.yaml`, `BLUEPRINT.md` §4.16.

**Prior evidence**
- `operations/evidence/runs/2026-11-20-ccb1bd39/artifact-trace.md`, for the dependency evidence references.

**Existing code (read-only verification)**
- `engine/packages/brain-content/src/brain_content/contracts.py`
- `engine/packages/brain-contracts/src/brain_contracts/assertions.py`
- `brain-factslots/.../resolution.py`, `answers.py`
- `brain-temporal/.../commit.py`
- `engine/apps/api/src/brain_api/schemas/facts.py`, `routes/facts.py`, `app.py`, `errors.py`
- `engine/packages/brain-security/src/brain_security/execution.py`
- the package `pyproject.toml` files
- `neuron/pyproject.toml` and `neuron/packages/*/pyproject.toml`
- `experience/package.json`
- `.github/workflows/ci-gates.yml`

**Local guidance:** `docs/agent-instructions.md`, `docs/plan-review-checklist.md`.
