# Plan review report — F0004 content artifact model

**Run:** `2026-10-16-a186bc18` · **Action:** plan-review · **PLAN_SCOPE:** feature · **TARGET:** F0004\
**Product root:** `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` at `99efd49`\
**Reviewed plan run:** `2026-10-15-bbd8df01` (Phase A and Phase B approved)\
**Framework executor:** nebula-agents pin `c218bf1` (see Validation Evidence)

## Decision

**CONDITIONALLY READY.** Findings: 0 critical, 2 high, 3 medium, 4 low. The verdict comes from `gate_policy.py` (review-family profile) at PR4.

The package is unusually complete. All four stories have specific Given/When/Then criteria. Every existing code path the assembly plan cites as audited behavior exists. The schemas, OpenAPI error codes, Casbin actions and KG bindings agree with the plan, and every PR2 validator passed. Two build-critical gaps remain. Each would force an implementer to invent a rule:

1. **H-1:** what a *new* source publishes if per-item text-origin provenance can't be obtained from the pinned converter;
2. **H-2:** how the new `publication_state` column governs reads of existing v1 artifacts, and who moves it.

Both should go back to the architect for targeted rework before `feature.md` Step 0. The alternative is that the operator records explicit risk acceptance, with an owner and a target date.

## Findings By Severity

| ID | Severity | Owner | Summary | Evidence |
|---|---|---|---|---|
| H-1 | High | code-reviewer | Fallback for new sources is undefined when per-item origin provenance is unavailable | assembly plan Risk 1 (line 273), Step 1 item 4 (line 102), compatibility matrix "New source" row (line 235); ADR-0073 §3 (line 49) and §5 (line 69); `neuron/.../docling_adapter.py:23-44` and `neuron/.../parsed_content.py:20` expose only page-level `ocr_page_count` |
| H-2 | High | architect | `publication_state` lifecycle and legacy-row read semantics are unspecified | `persistence-design.sql:11-13, 207-212`; assembly plan Step 2 item 7 (line 144) and migration sequence (line 155); compatibility matrix v1 row (line 229); S0004-AC3/AC5. `publication_state` appears in no schema, ADR or plan text |
| M-1 | Medium | product-manager | No feature owns creating CONTENT/SOURCE_METADATA date candidates or calling `select` at runtime | assembly plan Step 3 ("No date route or UI is added", line 161), Risk 3 (line 275); S0003 Interaction Contract; no document-date reference in the `kg-source/features/F0016.yaml`, F0016 or F0005 READMEs; only `F0022/README.md:43` names reviewer-set dates |
| M-2 | Medium | architect | Date selection is authorized by `content_artifact:ingest`, so a ServicePrincipal can choose among conflicting dates | assembly plan Step 3 item 1 (line 200) and traceability row "select/clear" (line 250); S0003-AC6 ("explicit authorized selection"); BLUEPRINT §4.11 v0.1 scope guard (no automated deciders) |
| M-3 | Medium | architect | "Concrete repair record" for blocked legacy backfill and orphan bytes has no table, schema or owner | assembly plan migration sequence (line 155) and Step 2 item 6 (line 143); `persistence-design.sql` defines none |
| L-1 | Low | product-manager | Approved artifacts still carry Phase A "Phase B must…" wording | all four stories, Questions & Assumptions; `acceptance-criteria-checklist.md:3` ("Phase A draft"); `worked-examples.md` lines 14, 24, 36, 50; PRD lines 62, 94, 96, 100, 124 |
| L-2 | Low | product-manager | S0001-AC6 and S0002-AC7 are identical publication-audit criteria | both story files; assembly plan Step 2 item 5 emits one `content_artifact_published` event |
| L-3 | Low | architect | Ready-row immutability trigger on `content_artifact` exists only as prose | `persistence-design.sql:207-212`, unlike the six DDL triggers at lines 182-198 |
| L-4 | Low | code-reviewer | Reviewer-only principals have no `content_artifact:read`, but stories describe Reviewer reads | `security/policies/policy.csv:10-17`; PRD Role-Based Access; each story's Role-Based Visibility |

No critical findings. Every build-critical area has a named owner: the five signoff roles are set per story in STATUS.md, and step owners are in the assembly plan build order.

## Product Readiness

*Owner: product-manager.*

**Checklist BRAIN-SCOPE: pass.** The PRD gives seven numbered Must requirements, seven explicit out-of-scope groups, an R1–R4 → story mapping and a "No UI" justification (PRD "Screen Layouts"). Each story has 6–7 testable criteria with edge cases, plus an interaction table naming entry point, editable state, mutation result, reload evidence and role constraint. "Display/manage" language is absent, and every story requires persisted readback after restart, which rules out a render-only implementation.

The personas reuse existing product personas and don't add permission roles. Priorities (all Critical, v0.1A) agree with REGISTRY (Planned, v0.1A), ROADMAP (§Next, order 3) and the KG shard. Scope respects the §4.11 v0.1 guard: dates and origins are storage and contract only, and time-mention resolution, alignment and deciders are excluded.

**M-1: the S0003 value has no runtime producer.** F0004 builds `DocumentDateService` but adds no route, worker step or extractor that calls `append_candidate` or `select`. The HUMAN verifier rejects by default, so HUMAN dates can't be recorded (assembly plan Risk 3). Once F0004 ships, every document reads as undated to consumers until some downstream feature calls the service, and none is named:

- F0016's shard and README don't mention document dates;
- F0005's README doesn't either;
- only F0022 README line 43 covers reviewer-set dates.

This doesn't block building F0004, since the stories are satisfiable with controlled fixtures. It does leave the persona outcome ("downstream time interpretation never substitutes receipt time") without an owner. **Route:** the PM records in F0004's dependency table and in the owning feature(s) which feature creates CONTENT and SOURCE_METADATA candidates and who selects. This is likely F0005 (ingestion handoff) and F0016 (time context), but that is the PM's call, not this review's.

**L-1:** wording such as "Physical schema … must be completed in Phase B before architecture approval" is stale; the assembly plan supplies those details. It is harmless to the build, but it can mislead a reader about approval state. **L-2:** S0001-AC6 and S0002-AC7 can share one test, but QE should cite the shared evidence once rather than duplicating it.

**Trackers:** README, STATUS, REGISTRY, ROADMAP, STORY-INDEX and the KG shard agree: Planned, Phase A+B approved, 0/4 stories implemented. The Phase A token was normalized from the operator's "proceed with Phase B". Plan run `gate-decisions.md` line 31 records that transparently, so it is not a finding.

## Architecture Readiness

*Owner: architect.*

**Contracts and code audit.** I checked all 17 existing paths the assembly plan and GETTING-STARTED cite (the 14 reconciliation-table paths plus `deps.py`, `docling_graph_pipeline.py` and `config/local.yaml`). Every one exists, and the spot-checked claims match the source:

- `ArtifactManifest` is strict v1;
- `queue.publish_transaction(lease, operation)` is at `queue.py:360`;
- `register_document_artifact` is at `document_delivery.py:191`;
- `content_artifact.document_version_id` is `unique=True` at `models.py:81`;
- `AuthorizationExecution.read`/`mutate` are at `brain_security/execution.py:355/388`;
- `SyncAuthorityStore` is at `authx.py:315`.

The six schemas the plan lists exist and are bound in the F0004 KG shard. The OpenAPI `/content/{artifactId}` and `/files/{path}` responses carry `ARTIFACT_INTEGRITY`, `ARTIFACT_VERSION_UNSUPPORTED` and `CONTENT_UNAVAILABLE`. `content_artifact:ingest`/`read`/`interpret` exist for ServicePrincipal in `policy.csv`, so no new grant is needed. The only caller that assumes one artifact per version, apart from tests and dev scripts, is `document_delivery.py:176-184`, so removing the single-artifact uniqueness has a small blast radius.

**Checklist outcomes:**

- **BRAIN-AUTHORITY: pass.** ADR-0073 is Proposed with explicit proof gates (ADR §"Proof Gates"). ADR-0060/0064/0065 are kept Proposed and only bounded carry-ins are used (PRD "Risks & Assumptions").
- **BRAIN-EVIDENCE: pass.** A CONTENT date basis binds artifact, block, JSONL ordinal, line SHA-256 and exact quote (Step 3 item 2). Every block carries origin, producer and anchor (Step 1).
- **BRAIN-PARSE-ONCE: pass.** S0001-AC4 and S0004-AC5 forbid converter/OCR calls on reuse. ADR-0073 §2 says corruption never triggers a reparse, and a recipe change returns `PARSER_MIGRATION_REQUIRED`.
- **BRAIN-TEMPORAL: pass, by explicit exclusion.** The PRD excludes bitemporal mutation. Dates are append-only metadata with `created_at`, and correction lineage goes through `supersedes_id` and the selection sequence (`persistence-design.sql:111-180`). Interpretation runs pin `document_date_selection_id` (interpretation-output-manifest schema).
- **BRAIN-AUTHORIZATION: pass with M-2.** Every read and mutation path names its AuthX call, action, lock order and audit (traceability table, lines 245-252). S0004-AC2 plans the negative tests.
- **BRAIN-EXAMPLES: pass.** EX-CONTENT-001–004 are listed in `examples/README.md:31` and the glossary has `## F0004 content contract refinements` (line 367). `contract-examples.json` has 39 valid/invalid cases across four schemas, and `validate-contract-examples.py` passed at PR2.

**H-2: the `publication_state` lifecycle is undefined.** `persistence-design.sql` adds `publication_state` (`legacy_unverified` | `ready` | `quarantined`, default `legacy_unverified`). It says lifecycle changes "require current authority and an append-only artifact-state audit" (lines 207-212). That column appears nowhere else: not in ADR-0073, the assembly plan, the schemas or any story. Three things are missing:

- **(a) Read behavior for existing rows.** After the expand migration, every existing v1 artifact is `legacy_unverified` with a null `manifest_sha256`. Step 2 item 7 requires readers to "verify DB manifest/content identity", and the GET contract returns 404 for "not-ready". The compatibility matrix says v1 bundles stay readable. The plan doesn't say whether `legacy_unverified` rows are served, which affects S0004-AC3/AC5 and the existing F0005 proof seam.
- **(b) Transitions.** Nothing names who moves a row to `ready` (the backfill? which principal?) or to `quarantined` (the read path on `ARTIFACT_INTEGRITY`? the restore drill?). The Casbin action, the audit event type and an error code are also unspecified.
- **(c) Acceptance criteria.** No AC covers quarantine.

**Route:** the architect adds a state-transition table (state, trigger, actor/action, audit event, read visibility) to the assembly plan and reconciles ADR-0073.

**M-2: a ServicePrincipal can select dates.** `select` uses the existing `ingest` authority (Step 3 item 1), so the only principal that can select among conflicting candidates is a ServicePrincipal. A service choosing between conflicting CONTENT and SOURCE_METADATA dates is an automated decision. The §4.11 v0.1 guard excludes automated deciders, and S0003-AC6 calls for an "explicit authorized selection". The plan prevents an implicit priority rule but not an automated chooser. **Route:** the architect states in v0.1 that `select` is exercised only through controlled fixtures or the future F0022 human path, or binds it to a distinct action. Security Reviewer should confirm.

**M-3:** the migration says blocked legacy backfill creates "a concrete repair record". Step 2 item 6 retains orphan bytes "for a later explicitly authorized repair". Neither has a defined carrier (table, schema, log or report) or owner. **L-3:** the ready-row immutability guard should be DDL like the other six triggers, so that DevOps and Security review the same artifact.

**KG alignment:** the shard maps all four stories, 11 affected nodes, six schemas plus problem-details, two endpoints and ADR-0073. That is consistent with the raw artifacts. PR2 `--check-drift` passed, and no drift finding is recorded.

## Buildability Challenge

*Owner: code-reviewer.*

The slice is buildable in the four declared steps. Each step lists new and modified files, typed Python interfaces (`ArtifactKey`, `VerifiedBundle`, `ArtifactRepository`, `VerifiedContentStore`, `publish_ready`, `DocumentDateService` and the verifier protocols), failure states with observable outcomes (Step 2 table), an internal error vocabulary, and target test suites per story (lines 258-265). Role boundaries are explicit:

- Backend and AI engineer: steps 1–2;
- Backend: step 3;
- Backend, QA and DevOps with Security review: step 4.

No frontend work is needed. The stories map to unit, integration (PostgreSQL 18), security-negative, restart and restore checks, and the 80% coverage floor is stated. High-blast-radius nodes are flagged: the dual store adapters, the uniqueness reconciliation, lock ordering and the restore drill.

**Checklist BRAIN-BUILDABILITY: conditional, because of H-1 and H-2.**

**H-1: no fallback for new sources when per-item origin is unavailable.** S0002-AC1/AC2 require native and scanned PDF fixtures published as v2, with each block's origin truthfully attributed. The code available now provides only page-level OCR counts (`docling_adapter.py:23-44`, `ParseResult.ocr_page_count`). The plan forbids deriving block origin from them or inferring STATED from "not OCR" (Step 1 item 4, line 102; ADR-0073 §5). The assembly plan's Risk 1 says the hook is unproven, and the plan run's `gate-decisions.md:54` says the same.

Failing closed with `ORIGIN_UNAVAILABLE` is specified, but what happens to a **new source** afterwards is not. The compatibility matrix says "V2 only after read paths and actual per-block provenance are proven", which implies the v1 writer keeps serving new sources. ADR-0073 §3, however, gives every genuinely new source the v2 identity and namespace. An implementer must choose between two outcomes:

- keep writing v1 bundles for new sources (and under which identity scheme);
- fail their publication, which blocks F0005 ingestion of new documents.

That is a product and architecture rule, not an implementation detail. If the hook doesn't exist in the pinned Docling 2.126.0, S0002 can't pass at all.

**Route:**
1. Add a Step 1 entry spike with an exit decision: prove a per-item provenance hook on the pinned converter, or stop.
2. Have the architect state the new-source behavior for each outcome.
3. If the hook is absent, have the PM confirm whether S0002 stays in scope.

**L-4:** a principal holding only the Reviewer role is denied `content_artifact:read` (`policy.csv`). Stories say "TenantMember/Reviewer reads require current artifact/evidence permission". This is consistent if reviewers also hold TenantMember. QE should include a Reviewer-only negative case so the behavior is pinned rather than assumed.

Implementation can otherwise begin without searching the codebase. GETTING-STARTED names every integration point and says test commands must be discovered from package configuration at build time, which is acceptable for a Python workspace with existing suites.

## Validation Evidence

| Validator | Exit | Summary |
|---|---|---|
| `validate-stories.py {FEATURE_PATH}` (framework, PR2 op) | 0 | PASS |
| `validate-trackers.py` (framework, PR2 op) | 0 | PASS |
| `scripts/kg/validate.py` (product, PR2 op) | 0 | PASS |
| `scripts/kg/validate.py --check-drift` (product, PR2 op) | 0 | PASS: no KG drift, so no drift finding |
| `validate_templates.py` (framework, PR2 op) | 0 | PASS |
| Project check `plan-readiness`: `validate_plan_readiness.py --plan-scope feature --target F0004` (run-gate `before_stage_complete`) | 0 | `status: pass`, 0 findings; artifacts in `artifacts/project-checks/PR2-plan-readiness-55a3ac5b…` |
| Supplementary: `validate-contract-examples.py` | 0 | 6 schemas, 39 cases (18 valid / 21 invalid), 0 failures; `artifacts/test-results/contract-examples.json` |
| Supplementary: `scripts/kg/validate.py --check-reproducible` | 0 | Generated files match compile(source); `artifacts/test-results/kg-reproducible.txt` |

Every PR2 command is logged in `lifecycle-gates.log` and `commands.log`. Validators check structure only; the findings above are reviewer judgment.

Execution note: framework `main` (`3716308`) can't drive this product's gates. `run-gate.py` fails with `unresolved_placeholder {PRODUCT_ROOT}`, because nebula-agents #94 renamed the manifest placeholder to `{NEBULA_PRODUCT_ROOT}` while the product's `.nebula-project.yaml` still uses `{PRODUCT_ROOT}`. The product pins the framework at `c218bf1` (BLUEPRINT §0, ci-gates.yml line 251), so PR0–PR4 ran from a detached worktree at that pin. This is a process follow-up, not a plan finding.

## Artifact Trace

Raw artifacts inspected (read-only):

- `planning-mds/features/F0004-content-artifact-model/`: README.md, STATUS.md, PRD.md, personas.md, F0004-S0001…S0004 story files, acceptance-criteria-checklist.md, worked-examples.md, feature-assembly-plan.md, persistence-design.sql, GETTING-STARTED.md, validate-contract-examples.py, contract-examples.json (case inventory)
- `planning-mds/architecture/decisions/ADR-0073-versioned-content-contracts-and-document-metadata.md`
- `planning-mds/BLUEPRINT.md` §0, §3.3, §4.1–4.11, §5, §6; `docs/agent-instructions.md`; `docs/plan-review-checklist.md`; `.nebula-project.yaml`
- `planning-mds/security/policies/policy.csv`; `planning-mds/api/brain-api.yaml` (`/content` paths); the six F0004 schemas under `planning-mds/schemas/` (existence and date-selection reference)
- `planning-mds/kg-source/features/F0004.yaml`; the F0016 and F0005 shards and READMEs, plus `F0022/README.md` (date ownership search); `planning-mds/examples/README.md`; `planning-mds/domain/glossary.md`
- `planning-mds/features/REGISTRY.md`, `ROADMAP.md`
- `planning-mds/operations/evidence/runs/2026-10-15-bbd8df01/gate-decisions.md`
- Source: `engine/packages/brain-content/src/brain_content/{manifest,store,checkpoints}.py`, `engine/packages/brain-persistence/src/brain_persistence/{models,authx}.py`, `engine/packages/brain-security/src/brain_security/execution.py`, `engine/packages/brain-jobs/src/brain_jobs/queue.py`, `engine/apps/worker/src/brain_worker/document_delivery.py`, `engine/apps/api/src/brain_api/{routes/content,deps}.py`, `neuron/packages/brain-ingestion/src/brain_ingestion/{bundle_writer,document_worker,worker_cli,docling_adapter}.py`, `neuron/packages/brain-interpretation/src/brain_interpretation/parsed_content.py`, `neuron/packages/brain-extraction/src/brain_extraction/docling_graph_pipeline.py`, `scripts/ops/{backup.sh,restore.sh,verify_citations.py}`, `config/local.yaml`, Alembic `0001`–`0007`

Written: only files inside this run folder.
