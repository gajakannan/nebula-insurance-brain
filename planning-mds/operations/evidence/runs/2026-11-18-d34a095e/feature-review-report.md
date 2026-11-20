# Feature Review — F0008 Bitemporal canonical facts

## Decision

**NOT DONE.** Mode: closeout-audit. Audited approved run: `2026-11-17-1a4ae2f0`; review run: `2026-11-18-d34a095e`; product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`. Locked diff: `2badb9ad2756f38ee9a1d84930787a3df989a245..339c9209385290247c01d1eea97a7c2c8b47fada` (135 paths). DevOps: yes. No implementation or canonical feature evidence was changed.

One Critical completion finding remains: the delivered commit response omits temporal metadata required by S0002 AC7, while S0007 limits API scope to request/read changes. PM and Architect must explicitly reconcile the requirement and prove the agreed behavior before the feature can be called complete. Critical is the Code Reviewer skill's classification for an unmet acceptance criterion; no Critical security exploit was established.

The raw artifacts substantiate **1,081 passing engine tests**, zero failures/errors/skips, and **695/709 changed executable production lines covered (98.025388%, floor 80%)**. Nevertheless, only **44/46 criteria are verified**: S0002 AC7 and S0004 AC1's losing-audit clause remain unresolved. The blanket 46/46 completion claim is not adopted. Existing signoffs and operator feature approval remain historical provenance and do not override contradictory raw evidence.

Counts: **Critical 1; High 0; Medium 3; Low 6.** The FR4 policy input includes each owning domain once. No new mitigation acceptance or calendar deadline is fabricated. Repair routes: original feature/review/test/closeout owners; never this read-only review.

## Findings By Severity

| ID | Severity | Owner | Finding and exact evidence |
|---|---|---|---|
| CR-F8-01 | Critical | code-reviewer | Commit response cannot satisfy S0002 AC7; conflicting API scope has no recorded reconciliation. `engine/apps/api/src/brain_api/schemas/facts.py:47`; `engine/apps/api/src/brain_api/routes/facts.py:152`; `planning-mds/features/archive/F0008-bitemporal-canonical-facts/F0008-S0002-distinguish-open-bounded-and-unknown-ends.md:28` |
| FR-ARCH-M1 | Medium | architect | Legacy GET emits temporal:null against the new object-only contract. `planning-mds/api/brain-api.yaml:694`; `engine/apps/api/src/brain_api/schemas/facts.py:84`; `engine/tests/integration/test_temporal_reads.py:304` |
| QE-M1 | Medium | quality-engineer | Concurrency proof counts only successful audit rows; literal zero-audit loser criterion remains unresolved. `planning-mds/features/archive/F0008-bitemporal-canonical-facts/F0008-S0004-enforce-temporal-integrity-under-concurrency.md:22`; `engine/tests/integration/test_temporal_concurrency.py:52`; `engine/packages/brain-security/src/brain_security/execution.py:480` |
| PM-M1 | Medium | product-manager | Exact F0018 carry-overs are absent from receiving planning inputs; current refusal-reason wording is stale. `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/pm-closeout.md:30`; `planning-mds/kg-source/features/F0018.yaml:31` |
| FR-ARCH-L1 | Low | architect | ADR prose conflicts with current date-selection and remainder timestamp semantics. `planning-mds/architecture/decisions/ADR-0078-bitemporal-version-contract-and-close-only-immutability.md:111`; `engine/packages/brain-persistence/src/brain_persistence/repositories.py:533`; `engine/packages/brain-temporal/src/brain_temporal/commit.py:268` |
| FR-ARCH-L2 | Low | architect | Direct-insert predecessor lineage lacks same-slot binding. `engine/migrations/versions/0014_f0008_bitemporal_contract.py:175`; `engine/migrations/versions/0014_f0008_bitemporal_contract.py:331` |
| QE-L1 | Low | quality-engineer | Supplemental repeat/no-database execution claims and report dates lack their cited raw support. `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/test-execution-report.md:24`; `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/commands.log:16`; `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/artifacts/test-results/g3-full-engine-regression.xml:1` |
| PM-L1 | Low | product-manager | Manifest changed_paths inventory differs from the actual locked diff. `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/evidence-manifest.json:15`; `artifacts/diffs/manifest-scope-drift.json` |
| PM-L2 | Low | product-manager | Feature status Last Updated predates recorded closeout. `planning-mds/features/archive/F0008-bitemporal-canonical-facts/STATUS.md:4` |
| SEC-F8-L1 | Low | security | Manifest SAST clean label hides seven safely triaged raw findings. `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/evidence-manifest.json:318`; `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/artifacts/security/sast/sast-semgrep-20261117-052326.sarif#/runs/0/results` |

Detailed triggers, impact, scope boundaries and owning repair routes appear in the role-owned sections below. The shared CR-F8-01 is counted only in Code Review; QE and Architect references do not add severity counts. The accepted local superuser residual, production-role work and formal ADR acceptance are disclosed separately and are not reopened as new findings.

## Completion Checks

| Role | Result |
|---|---|
| Product Manager | Provenance/trackers align structurally; completion claim must be reconciled with raw AC gaps. 1 Medium, 2 Low. |
| Architect | Design largely implemented; new legacy-read schema mismatch and two guard/prose follow-ups. 1 Medium, 2 Low. |
| Quality Engineer | Raw execution/coverage pass; 44/46 criteria verified, two unresolved; unsupported supplemental claims disclosed. 1 Medium, 1 Low. |
| Code Reviewer | REQUEST CHANGES; one Critical unmet-AC/reconciliation finding. |
| Security | PASS WITH RECOMMENDATIONS for scoped controls; one Low raw-SAST labeling mismatch. |
| DevOps | PASS for declared local runtime; no new deployment finding. No production rollout or live daemon state asserted. |

All role lanes ran concurrently within available execution slots, with PM in the parent, Architect/DevOps sharing one reviewer, QE one, and Code/Security one. Each role owns its findings and section. All reviewers checked raw source/artifact paths; no global evidence lane replaces feature-scoped evidence.

### Requirements Satisfaction — owner: product-manager

Reviewer: Codex / Product Manager. Scope: F0008, latest approved run `2026-11-17-1a4ae2f0`, merged diff recorded at FR0. This lane reviewed the raw PRD, all 46 story criteria, the assembly reconciliation, closeout, approval record, current trackers, and both signoff ledgers. Exact story lines are captured in `artifacts/review/pm-raw-criteria.txt`; the source paths remain authoritative.

The seven story files claim Done and tick all 46 criteria. Those claims do not establish completion. S0002 AC7 (`F0008-S0002-distinguish-open-bounded-and-unknown-ends.md:28`) requires temporal metadata in both commit and read responses. S0007 AC6 (`F0008-S0007-preserve-pilot-versions-through-migration.md:27`) instead limits API changes to commit requests and read responses. No explicit reconciliation of that conflict appears in the approved assembly plan or the feature run's `gate-decisions.md`. The narrower implemented response is concrete evidence that AC7 remains unresolved; the Code Reviewer owns CR-F8-01 and the completion severity. The original PM's `pm-closeout.md:20` assertion that every criterion has observed evidence is therefore contradicted. The QE lane separately challenges the zero-audit clause of S0004 AC1; PM must reconcile it against the mandatory authorization audit before any implementation rework.

No new UI, model call, route or grant is required by this feature. Those omissions are explicit in `PRD.md` Scope & Boundaries and Screen Layouts, and the manifest's omissions; they are justified. Future orchestration, full RLS, refusal routing and temporal APIs remain downstream scope. Formal ADR-0078 acceptance is an operator decision and is not inferred from successful tests or prior feature approval.

### Signoff and Closeout — owner: product-manager

All five required roles have a named reviewer, ISO date, concrete run-scoped evidence path and a passing reported disposition for each of seven stories. The 35 unique `(story, role)` rows in feature `STATUS.md:53` onward exactly match the run's `signoff-ledger.md:28` onward. A mechanical cross-check is `artifacts/review/pm-source-checks.json`; owning reviewers in this audit inspected the corresponding raw source/test/scan evidence independently. The Security WITH RECOMMENDATIONS acceptance is recorded in `pm-closeout.md:41` and the G4 approval entry in `gate-decisions.md:13`; it covers the explicitly deferred Low SEC-F8-02, not newly discovered audit findings. There are no existing High acceptances to inherit.

The manifest is approved, the latest-run pointer selects this run, and the folder is archived. G6, G7 and G8 are recorded in the manifest and in raw `lifecycle-gates.log`; the historical G7 compile failure and G8 validation failure have later passing attempts. These procedural passes do not resolve the raw requirement conflicts.

**PM-M1 — Medium — Deferred work is not carried into the receiving feature's authored planning inputs.** `pm-closeout.md:30–31` assigns the non-superuser application role and durable refusal reason persistence to F0018; the source feature shard `kg-source/features/F0008.yaml:36` records the same handoff. The receiving `kg-source/features/F0018.yaml:31–40` and `features/F0018-canonical-commit-service-and-action-authorization/README.md:13–20` carry only the older broad source-authority/RLS amendments. Neither names SEC-F8-02 nor the reason-persistence obligation. In addition, F0008 S0005 `Data Requirements` still says refusal reason codes are in the audit despite the approved deferral. This leaves the later planner dependent on archived F0008 material to discover the exact carry-over. Owner: Product Manager, coordinating Architect and DevOps. Route back to closeout ownership to record the precise obligations in F0018 and annotate the current story's reconciliation before F0018 planning; this review makes no edits and invents no target date.

### Tracker Sync — owner: product-manager

The registry entry at `features/REGISTRY.md:100`, completed roadmap row at `features/ROADMAP.md:126`, seven story links at `features/STORY-INDEX.md:99–105`, `kg-source/features/F0008.yaml:3–5`, feature README archive header and blueprint §4.15 all point at the same archived run/state. FR2 independently validates trackers and performs story-index currency on a temporary mirror so canonical trackers stay read-only.

**PM-L1 — Low — Manifest inventory differs from the actual merged files.** `evidence-manifest.json` declares 133 changed paths, whereas the locked diff has 135. It omits `planning-mds/knowledge-graph/coverage-report.yaml`, the F0008 `latest-run.json`, and the feature run's `token-usage.json`; it lists `artifacts/security/sast/sast-semgrep-20261117-052012.sarif`, which is absent. Exact sets are `artifacts/diffs/manifest-scope-drift.json` and `artifacts/diffs/changed-files.txt`. The missing file is an abandoned scan attempt, not the final manifest-cited SAST result; the completed final scan is reviewed by Security. Owner: Product Manager / original evidence package owner. Reconcile the authored inventory during targeted feature-evidence rework.

**PM-L2 — Low — Feature status update date is stale.** Feature `STATUS.md:4` says Last Updated 2026-11-17, while `STATUS.md:3` and its closeout section record approval/archive on 2026-11-18. Owner: Product Manager. Correct the metadata during original closeout rework; the substantive archive pointers agree.

### PM self-review (FR3)

Every finding above was checked against the raw cited files. Role signoff rows and report claims were checked as provenance, not treated as independent proof of fulfillment. The receiving F0018 files were read only to assess the explicit F0008 handoff; no broader feature review was performed. Implementation repair, story rewrites, graph regeneration, archive moves and formal ADR acceptance are skipped because this action is a read-only audit. No new High mitigation acceptance, owner commitment or date is fabricated.


### Architecture and KG Alignment — Architect

Reviewer: Codex, Architect lane. Audited product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`; run `2026-11-17-1a4ae2f0`; merged HEAD `339c9209385290247c01d1eea97a7c2c8b47fada`. No repairs performed.

**Lane result: PASS WITH FINDINGS; 0 critical, 0 high, 1 medium, 2 low.** This is an architecture assessment, not the overall FR4 verdict; the unmet S0002 AC7 reported by Code Reviewer remains blocking there.

#### Findings

- **FR-ARCH-M1 — Medium — Legacy GET emits `temporal: null` against the new object-only contract.** Owner: Architect, with Backend Developer for any implementation correction. `planning-mds/api/brain-api.yaml:694` says this property is absent for legacy versions and references `fact-temporal-v1.schema.json#/$defs/version_temporal`, an object-only definition (`planning-mds/schemas/fact-temporal-v1.schema.json:101`). In contrast, `engine/apps/api/src/brain_api/schemas/facts.py:84` defaults the property to `None`, `:104` explicitly assigns it for legacy rows, and the GET at `engine/apps/api/src/brain_api/routes/facts.py:81` does not exclude it. `engine/tests/integration/test_temporal_reads.py:304` positively asserts the resulting `temporal: null`. A schema validator or generated consumer that interprets presence of `temporal` as the v1 object cannot accept this legacy response. This field is new in F0008; the issue is distinct from the older `valid`/`recorded` naming drift. The narrow diagnostic in `artifacts/review/architect-temporal-null-schema.json` imports the actual response model and validates its `None` default against the exact schema, obtaining `None is not of type 'object'`. Reconcile the contract and serializer in the original owning action, and add an observed legacy-response contract check. No mitigation acceptance is asserted by this audit.
- **FR-ARCH-L1 — Low — ADR wording disagrees with the approved current-selection and remainder timestamp behavior.** Owner: Architect. `planning-mds/architecture/decisions/ADR-0078-bitemporal-version-contract-and-close-only-immutability.md:111` defines the date source as the highest sequence that is not a clear, while `engine/packages/brain-persistence/src/brain_persistence/repositories.py:533` and its query at `:557` use the highest sequence including a clear. The observed test `engine/tests/integration/test_temporal_v1_commit.py:337` explicitly proves that a later clear leaves evidence undated. That is consistent with the existing F0004 selection semantics and prevents a cleared date from being resurrected. Separately, ADR D5 at `:144` says remainders copy all four timestamps, but `F0008-S0003-split-intervals-and-close-recorded-time.md:24` explicitly copies the three source timestamps and `:27` gives a new acceptance/recorded start. `engine/packages/brain-temporal/src/brain_temporal/commit.py:268` copies three source timestamps and sets `canonical_accepted_at=now` at `:271`. The implementation follows the specific ACs; the prose should say three predecessor source timestamps plus a new acceptance time. Resolve these wording conflicts before formal ADR acceptance. They are documentation drift, not two additional implementation failures.
- **FR-ARCH-L2 — Low — The lineage FK does not establish that a remainder belongs to its predecessor's slot.** Owner: Architect. The legacy-remainder exception queries the predecessor only by ID (`engine/migrations/versions/0014_f0008_bitemporal_contract.py:175`), and the new self-FK at `:331` binds `(id, tenant_id, knowledge_base_id)` without `slot_id`. A direct inserter can therefore point a row at a legacy predecessor in another slot within the same tenant/KB; the D1 exception can then admit a legacy-shaped row for an identity-v1 slot, and provenance would name the wrong parent slot. Normal commit-service remainders use the actual predecessor, so the reviewed service path is correct. Decide whether to strengthen the direct-insert lineage backstop when F0009 consumes it or at ADR acceptance. This is a static guard-gap finding; no live direct-insert reproduction was performed.

#### Completion checks

| Check | Disposition and raw evidence |
|---|---|
| Assembly-plan and implementation shape | The feature plan's exact file handoffs correspond to migration 0014; `brain_domain.temporal`; temporal `bounds`, `attestation`, `commit`, `reader`; persistence models/repository; existing facts routes. No new deployable, route, table, grant, UI or model path appears in `artifacts/diffs/changed-files.txt`. The plan's G0 reconciliation explains fixture cleanup, legacy request compatibility, refusal audit and scope boundaries. |
| AC/contract reconciliation | **Open:** raw S0002 AC7 (`F0008-S0002-distinguish-open-bounded-and-unknown-ends.md:28`) requires temporal data in the commit response, whereas S0007 AC6 (`F0008-S0007-preserve-pilot-versions-through-migration.md:27`) limits API changes to request/read fields and the plan follows that narrower contract. No operator reconciliation was found. This is Code Reviewer's owned blocker, not counted again here. |
| API and schema | The additive validity-unknown route maps `ValidityUnknown` to a 200 without a value; no-version retains 404 (`routes/facts.py:107`, `:147`). `VersionTemporal` read metadata and bound/attestation fields correspond to the schema. The new legacy-null mismatch is FR-ARCH-M1. Older `valid`/`recorded` versus runtime field naming is recorded by the plan's G0 item 6 and remains prior drift. |
| Bounds, attestation, guards and two-coordinate reads | Inspected `bounds.py`, `attestation.py`, commit `_commit_v1`/`_guard`/`_remainders`, and `reader.py`. Unknown ends use the finite attested integrity range; source dates come from selections, not clocks; unanchored successions and prohibited PRESENT-state replacements are refused; readers apply UNKNOWN windows and before-floor behavior in ADR D9 order. |
| Authorization boundary | `routes/facts.py:115` adds exact returned payload and attestation evidence to the existing same-UoW READ checks; commit source eligibility covers positive plus ending evidence at `commit.py:416` and `:439`. Source authority, full orchestration and RLS remain the explicitly deferred F0018 obligations. Security owns the independent security assessment. |
| Temporal database integrity | Inspected 0014 CHECKs, insert/close-only/delete/truncate guards, locked upgrade preflight and guarded downgrade. The two-range GiST exclusion is preserved. Remainder lineage's slot omission is FR-ARCH-L2. EVENT/ETERNAL are reserved shapes; service writes STATE. |
| ADR proof gates | Raw final JUnit `.../artifacts/test-results/g3-full-engine-regression.xml` records 1081 tests, no failures/errors/skips, including 234 temporal cases. Parsed examples are preserved in `artifacts/review/architect-runtime-proof-summary.json`. Source assertions establish the 12-writer and >=200-coordinate grids (`test_temporal_concurrency.py:19`, `:83`, `:123`), close-only and mutation negatives (`test_temporal_immutability.py:58`), EX-SEM-004/EX-PC-014 reads, envelope/guard negatives, and byte-identical seeded migration snapshots (`test_temporal_migration.py:161`). Actual migration cycle and tzdata files were read. These proofs support the delivered design, while the missing commit-response AC is still not proved by those passing tests. |
| ADR state | ADR-0078 remains Proposed. Its proof gates and an approval of the feature do not constitute operator ADR acceptance. ADR-0064 and ADR-0039 likewise remain Proposed. |
| KG and code-index | Verified concrete authored bindings in `planning-mds/kg-source/bindings/f0008-planning.yaml` and `f0001.yaml:86`: reader/API/schema, domain and commit/attestation/bounds, model, migration, and tests. Migration and capability/entity nodes are present. The parent runs fresh symbol/drift validation at FR2; no regeneration or graph repair was performed here. |

#### FR3 self-review, evidence trace and limits

Every finding was checked against exact raw source, contracts and test assertions rather than report verdicts. The temporal-null diagnostic confirms the narrow schema failure without changing implementation or tests. The canonical manifest was the entry point; its cited `architect-implementation-review.md`, `kg-reconciliation.md`, `g1-runtime-preflight.md` and `deployability-check.md` were used to navigate to the exact JUnit, tzdata and migration-cycle artifacts above. Prior audit `2026-11-18-a3709ba0` was not used as approval evidence.

No UI or AI review is required because F0008 introduces neither surface. No full regression was re-run: this is a closeout audit using raw recorded runtime proof and fresh parent FR2 validation. No production deployment is claimed; the feature and production-host choice have separate scope. The optional live Docker status probe was denied by the sandbox and was not used as evidence of product failure or success. No live write probe was used for FR-ARCH-L2. All shell reads and diagnostics went through the run's telemetry wrapper.


### Test Evidence and Coverage — Quality Engineer

Reviewer: Codex QE lane; reviewed 2026-11-18. Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`. Audited feature run: `2026-11-17-1a4ae2f0`; immutable diff: `2badb9a..339c920`.

**Disposition:** executed-test counts and changed-line coverage are substantiated. Literal acceptance-criteria completion is **44/46 verified, two unresolved**. The existing 46/46 completion claim is contradicted by the commit-response omission and the losing-commit audit requirement. Findings affecting runtime/code are counted in their owning lane, as explained below.

For the raw evidence references below, `CAN/` means product-relative `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/`. Source/test paths are product-relative.

#### Findings owned by QE

**QE-M1 — Medium — The concurrency test does not establish the specified zero-audit loser outcome; the implemented outcome contradicts that clause.**

- Requirement: `planning-mds/features/archive/F0008-bitemporal-canonical-facts/F0008-S0004-enforce-temporal-integrity-under-concurrency.md:22` says a losing commit writes zero rows, including no audit/outbox row. `planning-mds/architecture/decisions/ADR-0078-bitemporal-version-contract-and-close-only-immutability.md:157` repeats this for `stale_version` and `temporal_conflict`.
- Raw test: `engine/tests/integration/test_temporal_concurrency.py:52` counts only `operation_outcome = 'succeeded'` at line 55; the race at line 60 checks that successful count and outbox/version counts, so a failed commit audit is invisible to its assertion. `engine/tests/fixtures/factslots/harness.py:193` also omits audit/change/outbox rows from its generic `counts()` helper.
- Raw implementation: `engine/packages/brain-temporal/src/brain_temporal/commit.py:234` raises `StaleVersionError` on the failed optimistic expectation; `engine/packages/brain-security/src/brain_security/execution.py:480` catches the operation exception and persists `FAILED` decisions. Its `_persist_fresh` at line 330 rolls back business work and commits those decisions in a fresh transaction. `engine/packages/brain-persistence/src/brain_persistence/authx.py:264` and line 274 show these become real `AuditEventRow` records in `audit_event`, with the action and outcome retained. This is the same table queried by the race helper.
- Impact: the reported PASS for S0004 AC1 does not prove the literal criterion. Successful transaction integrity and one-version-per-coordinate are still evidenced; the zero-audit clause remains unresolved. This is a requirements/test reconciliation issue, not a recommendation to remove security audit records. F0002's mandatory failure auditing must be preserved unless its governing contract is explicitly changed.
- Owner: Quality Engineer for test/evidence correction; Product Manager for explicit requirement reconciliation, with Architect/Security review of the audit boundary. Follow-up: resolve the contradictory clause, assert the agreed failed-audit behavior, and publish a fresh owning-lifecycle evidence package. No repair was made during review.

**QE-L1 — Low — Supplemental run claims and chronology lack the cited raw support.**

- `CAN/test-execution-report.md:24` claims three repeated standalone concurrency runs plus a final rerun, and line 25 claims four emulated no-database coverage gates; both cite `commands.log`. Inspection of the entire cited command log finds baseline/full-engine pytest invocations at lines 4, 7, 10, 15 and 16, with no standalone concurrency rerun or no-database gate invocation/results. `CAN/lifecycle-gates.log` supplies no missing commands. `CAN/coverage-report.md:14` and line 17 rely on the same unsupported no-database figures.
- `CAN/test-execution-report.md:5` dates the final post-G3 execution to 2026-11-18, while `CAN/artifacts/test-results/g3-full-engine-regression.xml:1` records `2026-11-17T05:29:36.793114-05:00`, `CAN/artifacts/coverage/g3-engine-coverage.json:1` records `2026-11-17T05:34:00.755347`, and `CAN/commands.log:16` is dated 2026-11-17. Raw dates control; a fresh November 18 execution is not established by these artifacts.
- The failed baseline and its passing retry share the same output artifact (`CAN/commands.log:4` and line 7), so the initial raw exception transcript is not preserved separately. The log retains exit statuses, and the preflight narrative classifies the failure as stale database state; the overwritten raw transcript cannot independently establish that diagnosis.
- Impact: extra stability/no-database claims and precise failure chronology cannot be independently reproduced from their citations. This does not invalidate the verified full-engine results or the changed-line coverage floor.
- Owner: Quality Engineer. Follow-up: preserve per-attempt raw command/results and reconcile report dates and claims in a new owning-lifecycle evidence run; do not rewrite this historical package during this audit.

#### Shared finding: commit-response acceptance gap

The Code Reviewer owns and counts the runtime finding (CR-F8-01). QE independently confirms the missing assertion and does not add a duplicate severity count:

- `planning-mds/features/archive/F0008-bitemporal-canonical-facts/F0008-S0002-distinguish-open-bounded-and-unknown-ends.md:28` requires both commit response and fact read to expose end state, attestation dates and the start marker.
- `engine/apps/api/src/brain_api/schemas/facts.py:47` exposes only commit ID, version IDs and accepted-at in `CommitResponseOut` (lines 52–54). `engine/apps/api/src/brain_api/routes/facts.py:152` uses this response model for POST.
- `engine/tests/integration/test_temporal_v1_commit.py:265`, cited for AC7, asserts POST status only, then checks those metadata fields on the later GET at lines 295–300. A passing testcase with AC7 in its name therefore does not establish the POST half of AC7.
- The S0007 AC6 limitation to additive commit-request/read-response fields (`planning-mds/features/archive/F0008-bitemporal-canonical-facts/F0008-S0007-preserve-pilot-versions-through-migration.md:27`) conflicts with S0002 AC7. No explicit reconciliation or waiver of S0002 AC7 was found. Resolve the requirements explicitly rather than silently redefining the criterion around the existing response.

#### Completion checks by story

All cited testcases below are present and passing in `CAN/artifacts/test-results/g3-full-engine-regression.xml:1`. Assertions were inspected in the source files, not inferred from testcase names or report PASS labels.

| Story | Observed criterion disposition | Raw test/source check |
|---|---|---|
| S0001 | 6/6 verified | `engine/packages/brain-temporal/tests/test_bounds.py:60` through zone/DST tests at lines 148/156; `engine/tests/integration/test_temporal_v1_commit.py:65`, 107, 125, 143, 202 exercise refusal/no-write, exact round trips, independently precise bounds, representable EVENT/ETERNAL and authoritative trigger checks. |
| S0002 | 6/7 verified; AC7 unresolved | `engine/tests/integration/test_temporal_v1_commit.py:228`, 265, 318, 337, 352, 381 cover end states, unknown exclusion, floors, undated/cleared evidence, current selection/mismatch and clock exclusion. `test_temporal_reads.py:87`/116 cover unknown windows. AC7 GET half is covered, POST half is absent. |
| S0003 | 7/7 verified within the approved local-role boundary | `engine/tests/integration/test_temporal_v1_commit.py:417`, 437, 465, 498 check retroactive/correction/remainder/untouched behavior; `test_temporal_immutability.py:58`, 71, 101, 119 check forbidden mutations, the single close, deletion/truncation and injected-fault rollback. The application-superuser deployment limitation is owned by Security/DevOps and is not silently treated as production qualification here. |
| S0004 | 5/6 verified; AC1 loser-audit clause unresolved | `engine/tests/integration/test_temporal_concurrency.py:60` uses 12 racers; grid assertion requires at least 200 coordinates and no overlapping answer. Member/relationship tests at 127/187 and `test_temporal_immutability.py:172`, 194, 203, 258 cover exclusion, envelope and scope negatives. The successful-only audit count fails to check literal AC1 (QE-M1). |
| S0005 | 7/7 verified under recorded G0 refusal-audit reconciliation | `engine/packages/brain-temporal/tests/test_bounds.py:254`/265 verify basis rejection and recording; `engine/tests/integration/test_temporal_v1_commit.py:520`, 533, 574, 612, 638, 664, 675, 685 cover anchored bases, C/floor guard, allowed end revision, state succession/refusal and member isolation. Refusal reason persistence is explicitly deferred by G0, not claimed as delivered. |
| S0006 | 7/7 verified | `engine/tests/integration/test_temporal_reads.py:50`, 59, 87, 116, 162, 177, 206, 221 cover the temporal grid, no-version sentinel, validity-unknown, EX-PC-014 A–D, half-open bounds, returned shape, invalid coordinates and historical reads after revocation. Lines 248/268 check unreadable attestation sources at read/commit boundaries. |
| S0007 | 6/6 verified under the explicitly recorded reconciliation | `engine/tests/integration/test_temporal_migration.py:161` snapshots old rows and grants/roles over up/down/up; 209 rejects destructive downgrade, 239 rejects malformed legacy envelopes, 266 proves no route addition. `test_temporal_reads.py:293` preserves legacy request/read behavior. Full-engine execution includes F0001/F0007 suites. The harness shape, ownership-test state, migration pin and cleanup fixture changes are documented approved reconciliation, not literally unchanged test files. |

The six ADR proof-gate groups have executed evidence for retroactive facts/concurrency, immutability, precision/zones, example reads, state/envelope/member guards and migrations. The zero-audit loser clause within concurrency is unresolved, so the blanket statement that every part of every proof gate is met is not adopted.

#### Raw execution and coverage verification

- `CAN/artifacts/test-results/g1-baseline-regression.xml:1`: 74 actual testcase elements; 0 failures/errors/skips; raw start timestamp 2026-11-17 04:51:20-05:00. PostgreSQL health probe precedes this (`CAN/artifacts/test-results/g1-compose-ps.txt:1`, 04:49:56-05:00).
- `CAN/artifacts/test-results/g2-full-engine-regression.xml:1`: 1,076 actual testcase elements, 0 failures/errors/skips; 208 F0008 cases.
- `CAN/artifacts/test-results/g3-full-engine-regression.xml:1`: 1,081 actual testcase elements, 0 failures/errors/skips; 213 F0008 cases: bounds 56, examples 39, temporal service 12, v1 commit 50, immutability 35, concurrency 6, reads 11, migration 4. `CAN/artifacts/test-results/command-output/g3-full-engine-regression.txt:56` independently prints 1,081 passed, 381 warnings, 264.44 seconds.
- Independently recomputed from raw `CAN/artifacts/coverage/g3-engine-coverage.json:1` and the immutable `2badb9a..339c920` diff: **695/709 changed executable production lines = 98.025388%**, above 80%. This reproduces `CAN/artifacts/coverage/changed-code-summary.txt:13`. Coverage denominator is engine source; migration execution is behaviorally evidenced by the migration/integrity tests and is explicitly outside line measurement. Whole measured source is 4,996/5,171 = 96.615742%; this is distinct from changed-line coverage.
- The historical measurement helper uses moving `origin/main`; the independent check deliberately fixes the locked base/head commits. No canonical measurement artifact was rewritten.
- Independent parsed output and fixed-diff arithmetic: this review's `artifacts/review/qe-raw-artifact-check.json` (produced by `/tmp/f0008_qe_probe_d34a095e.py`; invocation recorded in commands.log). This derived audit artifact supplements the cited raw inputs and does not replace them.

#### Scope limitations and justified skipped layers

- No fresh full test rerun was needed to identify these static response/test-contract defects. This is an evidence audit; it does not claim a new runtime execution or a release deployment.
- Historical runtime execution uses the locked host engine virtual environment (Python 3.14.4) against real PostgreSQL 18.6 in Compose, with per-test owned databases. This execution choice is explicit in `CAN/g1-runtime-preflight.md:19` and supported by raw server/tzdata probes. It is not presented as an engine-container run.
- Browser, UI component, visual and accessibility layers are inapplicable: manifest `frontend_in_scope=false`, no experience changes, and no new user interface. Neuron/model/evaluation tests are inapplicable because no AI path or model behavior changed. No model/browser evidence is substituted for engine coverage.
- Real OIDC login is not exercised: F0008 adds no identity flow; HTTP tests override the principal dependency while exercising real server-side authorization/persistence. This omission is explicit in runtime preflight.
- No new latency SLA or load-test requirement is introduced; the declared concurrency grid and transaction integrity checks are the performance-sensitive scope. Production-role/rollout qualification remains the Security/DevOps boundary.
- Scanner interpretation belongs to Security; QE does not duplicate that lane or claim an unavailable scan rerun.

#### FR3 self-review

Verified directly: both disputed AC clauses, relevant runtime branches, assertion locations, all three raw JUnit case counts/statuses, fixed-diff coverage numerator/denominator and cited command-history claims. Every finding above cites raw source/artifact paths; source locations were re-read with line numbers. Shared CR-F8-01 is not double-counted in QE totals. All skipped layers and the chronology limits are explicit. No implementation, tests, feature documentation, trackers, graph or canonical evidence was edited.


### Code Quality and Merge Readiness — code-reviewer

Reviewer: Codex, independent feature-review lane. Scope: F0008, merged commit `339c9209385290247c01d1eea97a7c2c8b47fada`, diff `2badb9a..339c920`. Decision: **REQUEST CHANGES**. Findings: Critical 1, High 0, Medium 0, Low 0. Critical here is the framework's acceptance-criterion completion classification, not a security exploit classification.

#### CR-F8-01 — Critical — S0002 AC7 cannot pass with the delivered commit response; the approved requirements require reconciliation

- **Raw requirement:** `planning-mds/features/archive/F0008-bitemporal-canonical-facts/F0008-S0002-distinguish-open-bounded-and-unknown-ends.md:28` checks AC7 complete and requires **both** the commit response and fact read to return end state, attestation bounds and the start marker.
- **Delivered behavior:** `engine/apps/api/src/brain_api/schemas/facts.py:47` defines `CommitResponseOut` with only `commit_id`, `fact_version_ids`, and `canonical_accepted_at`; its `from_domain` at line 57 returns exactly those. `engine/apps/api/src/brain_api/routes/facts.py:152` fixes the POST response model to that class, and line 265 serializes through it. `planning-mds/schemas/canonical-commit-response.schema.json:7` also forbids any additional response property. No temporal block or requested fields can appear in a successful commit response.
- **Reproduction:** `artifacts/review/code-response-probe.json` comes from the actual `CommitResponseOut.from_domain` using `engine/.venv/bin/python`, without database access. Its serialized output and generated model schema have the three legacy fields and none of the four AC7 fields, even under a nested temporal block. The temporary probe is `/tmp/f0008_response_probe_d34a095e.py`.
- **Contradictory planning evidence, preserved explicitly:** `F0008-S0007-preserve-pilot-versions-through-migration.md:27` limits API changes to additive commit-request and read-response fields, and `feature-assembly-plan.md:65` describes request/read additions. Thus this finding does **not** authorize an unreviewed commit-response expansion. Both checked completion claims cannot stand without a PM/Architect reconciliation. No explicit AC7 waiver or amendment was found in the selected run's recorded reconciliations.
- **Why the passing test does not settle it:** `engine/tests/integration/test_temporal_v1_commit.py:265` claims AC2/AC3/AC7. It checks only status 201 for the POST (line 281); the AC7 assertions at lines 295–300 inspect `carrier.json()["temporal"]` from a later GET. A passing run therefore does not prove AC7's POST-response clause. The raw requirement wins over the 46/46 summary.
- **Severity basis:** `agents/code-reviewer/SKILL.md`, Core Principles 5, says: "If the code doesn't map to the AC, it's a critical finding". Its severity table likewise lists "AC not met" as Critical. This is a completion blocker under that policy; it does not mean the omitted field permits unauthorized access or corrupts stored facts.
- **Owner / repair route:** finding owner **code-reviewer**; route reconciliation to Product Manager + Architect and implementation/tests to Backend Developer + QE. Either approve and record an explicit requirement reconciliation, or implement the response contract under the reconciled scope and prove it at the POST boundary. Rerun feature lifecycle signoffs/evidence and this audit. No repair was performed.

#### Completion checks

| Dimension | Judgment and concrete basis |
|---|---|
| Correctness and AC mapping | The principal temporal algorithms are traceable to `bounds.py`, `attestation.py`, `commit.py`, `reader.py` and migration 0014; CR-F8-01 prevents an all-AC completion claim. |
| Clean architecture | `brain_domain/temporal.py` has pure types; temporal services use repository protocols; `brain_persistence/repositories.py` implements the adapters; routes compose services inside the existing authorization facade, matching SOLUTION-PATTERNS §4. |
| SOLID and scope | v1 and legacy paths are separated; parsing, attestation and resolution have focused modules. Changed fixture cleanup and request-shape changes have explicit G0 reconciliation; no new UI, route, producer or model integration is implied. |
| Test quality and coverage | Direct PostgreSQL integration, authorization, concurrency, migration, immutable-column and outbox-fault tests exist. The reviewed AC7 assertion is incomplete as above. Full JUnit/coverage arithmetic is owned by QE, using raw artifacts rather than the old review verdict. |
| Error handling | `routes/facts.py:256` maps 23P01 to `temporal_conflict` and omits other database detail; `bounds.py:147` converts malformed instants to an application range error. Fixed historical leakage is visibly absent. |
| Performance | Date selections are fetched as one windowed query in `repositories.py:529`; nearest-version lookup at line 620 uses LIMIT 1. Per-slot writes must inspect current disjoint ranges; no newly introduced request-loop I/O was identified. No fresh load benchmark is claimed. |
| Readability / naming | Temporal state and reason enums are explicit; non-obvious authorization UoW, trigger order and timezone decisions carry rationale comments. |
| Over/under-engineering | Existing composition and protocol seams are reused; no additional generic framework or deployment surface was added. |
| Hidden TODO/debug/dead paths | Targeted searches found no TODO/FIXME/breakpoint/print in the changed temporal implementation. `artifacts/review/code-quality-scan.txt`: TODO count 0, no >120-character lines, no files >500 KB in the temporal implementation directory. Legacy paths remain intentionally exercised. |

The explicit ADR D5 rule that a left remainder becomes BOUNDED was checked against `_remainders`; it is not reported as an undocumented implementation deviation. Likewise, failed authorization-decision audit records on losing commits are distinguished from successful commit events; the concurrency test's successful-only filter needs requirements/proof reconciliation in the QE/PM lanes, not removal of mandatory security auditing.

KG routing evidence: `artifacts/review/code-diff-impact.json` lists ten affected nodes: assertion-eligibility-guards, bitemporal-canonical-commit, durable-authorization-decisions, factslot-identity-resolution, runtime-roots-and-toolchain, temporal-fact-resolution, versioned-assertion-semantics, canonical-fact-version, f0007-factslot-identity, f0008-bitemporal-contract. `code-risk-summary.json` records their scores as 4/3/4/3/5/4/5/3/2/0; none triggers the >=7 additional-risk gate. `code-defines-*.json` checks the new TemporalFactReader, VersionTemporal and TemporalProposal names. Tracker consistency and generated-layer validation are owned by PM/Architect and the mandatory FR2 commands. No risk result overrides the raw AC finding.

#### FR3 self-review and limitations

Verified CR-F8-01 against the exact story, conflicting story, live schema/serializer, HTTP response model, response JSON Schema and the actual test assertions. The model probe confirms the claim independently of report summaries. The contradiction and authorized resolution paths are explicit. All writes are confined to this review folder and /tmp. No feature evidence, implementation, test, tracker or KG artifact was changed.

No frontend, AI, additional authentication handler, dependency or external integration was introduced; those layers are explicitly outside F0008. Broad scanner reruns and full runtime regression are not claimed: this action audits the canonical raw evidence, with one targeted model probe needed to establish a concrete contradiction. Fresh validators are the parent's FR2 responsibility. Existing shared authority methods are unchanged and the changed GET/POST paths visibly call their read/mutate facade; a new authorization-enforcement surface is not being inferred.


### Security — security

Reviewer: Codex, independent feature-review lane. Scope: F0008's commit/read paths, evidence-date disclosure, migration invariants, errors, and the four manifest-cited security scan classes. Security verdict: **PASS WITH RECOMMENDATIONS**, with Critical 0, High 0, Medium 0, Low 1 new evidence-drift finding. This does not override the independent code/requirements completion blocker.

#### SEC-F8-L1 — Low — the manifest reports a clean SAST scan whose raw artifact contains seven triaged findings

- **Raw evidence:** `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/evidence-manifest.json:316` sets SAST `result: clean` at line 318. Its cited `artifacts/security/sast/sast-semgrep-20261117-052326.sarif` has seven entries at `/runs/0/results`, all `python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text`, pointing to migration 0014 lines 303, 309, 313, 343, 349, 353 and 357.
- **Judgment:** the raw calls interpolate module-owned table/predicate strings, not request values. Inspection of `engine/migrations/versions/0014_f0008_bitemporal_contract.py:59` and lines 299–359 agrees with the security report's false-positive triage. This is an evidence-description mismatch, not demonstrated SQL injection. `artifacts/review/security-raw-scan-summary.json` records the independent raw parsing.
- **Impact / scenario:** a consumer relying solely on `result: clean` loses the distinction between no scanner hits and reviewer-triaged hits. No exploitable application path was established from these seven hits.
- **Owner / route:** **security** owns the finding. Have the canonical evidence owner accurately record the accepted triage outcome under the allowed manifest schema, and keep the seven-hit raw artifact and reasoning. Target: next owning-role evidence correction/review; this audit does not invent an accepted calendar deadline or repair evidence.

#### Control and threat checks

| Dimension | Raw check and outcome |
|---|---|
| Injection | New ORM queries use SQLAlchemy parameters. Dynamic migration statements use module constants; all seven SAST hits were inspected and triaged as above. No new shell or external-call surface. |
| Authentication | Changed fact routes retain `current_principal` dependencies and use the existing facade; no token/session behavior or grant was added. |
| Authorization / ownership | `routes/facts.py:138` invokes `execution.read` with `additional_reads=scope_reads`; line 234 invokes `execution.mutate` with source reads. `repositories.py:530` filters evidence/document selections by authorized tenant and KB; line 597 resolves evidence artifact resources under the same scope. The commit service checks its locked slot against `authorized_scope`. |
| Sensitive date/value disclosure | `scope_reads` in `routes/facts.py` rechecks attesting artifacts for both resolved and unknown reads. UNKNOWN response at `schemas/facts.py:108` has no value field. `test_temporal_reads.py:248` checks unreadable attestation is a non-disclosing 404; line 268 tests matching/mismatching expected dates cannot reveal an unreadable document date. |
| Security configuration | Migration functions are SECURITY INVOKER with pinned search_path; no new role, grant or SECURITY DEFINER function. Test-only replica mode is an explicit reconciliation, not ordinary application SQL. |
| Components | Manifest-cited `dependency-engine.json`: 35 dependencies, zero listed vulnerabilities at scan time; no dependency changed in F0008. This is not a claim that a fresh vulnerability database was queried. |
| Audit / repudiation | Commit effects remain inside the authorization mutation UoW with transactional outbox. `_persist_fresh` records FAILED authorization outcomes after rollback; durable business refusal reason is an explicitly deferred F0018 item. Existing immutable-event guards remain, and 0014 adds close-only/version/change guards. |
| Secrets | Manifest-cited final gitleaks SARIF contains zero results. Source changes introduce no production secret. Synthetic local test configuration is not represented as production credential management. |
| Abuse / resilience | Slot locks serialize commits, exclusion protects overlapping valid/recorded ranges, stale requests fail; enums, IANA-zone allowlist, timezone length cap and UUID parsing constrain added input. No new public producer or rate-control surface is introduced. |
| Failure safety | `routes/facts.py:256` maps temporal exclusion conflicts and drops non-exclusion IntegrityError text. `bounds.py:147` rejects malformed inputs with generic range errors; no new database text is echoed. |

STRIDE assessment: spoofing/elevation rely on verified principals, current grants and scoped source READ checks; tampering is constrained by the retained GiST exclusion, composite ownership keys and new close-only/delete/truncate guards; repudiation uses immutable authorization/commit audit; information disclosure is checked for current and historical reads plus attesting documents; DoS has no new external dispatch surface and added parsing is bounded by the existing request boundary. No independently established High/Critical exploit emerged in this scoped review.

#### Raw scanner evidence and limits

- Dependency: `artifacts/security/dependency-engine.json` — 35 packages, no listed vulnerability.
- Secrets: `artifacts/security/secrets/secrets-gitleaks-20261117-052326.sarif` — zero results.
- SAST: `artifacts/security/sast/sast-semgrep-20261117-052326.sarif` — seven constant-SQL warnings, individually triaged as above.
- DAST: `artifacts/security/dast/api-scan.json` — only riskcode 0 informational alert categories (client-error responses and session-management identification); no higher-risk alert. Its protected commit route observations are 401 responses, so it does not prove authenticated business authorization. `test_temporal_reads.py:221` tests current-grant revocation across historical coordinates, while lines 251 and 273 test attestation access. QE owns verification that those cases executed in the cited JUnit.

Accepted residual **SEC-F8-02** remains: the local/CI application role is a superuser and can bypass ordinary triggers with replica mode. `pm-closeout.md:30` names Architect + DevOps and F0018/F0026; `pm-closeout.md:41` and `gate-decisions.md:13` explicitly record operator acceptance of this deferred non-blocking Low. This audit records the residual without silently reopening an accepted scope decision or claiming the feature is production-hardened. The missing durable business reason is likewise explicit in the G0 reconciliation, separate from authorization outcome persistence.

#### FR3 self-review and limitations

SEC-F8-L1 is grounded in the raw manifest field, actual SARIF result array and seven concrete source locations; severity reflects accurate triage and no demonstrated injection. Skipped full scanner reruns are intentional for this read-only closeout audit: the required four recorded raw outputs were inspected; no output is overwritten in the canonical feature run. Authenticated DAST is explicitly not claimed. No frontend rendering, model prompt, remote integration or new authentication implementation changed. Production privilege/RLS and business-reason persistence have explicit later-feature ownership, so they are disclosed scope boundaries rather than silently skipped checks. All new evidence is under this review run or /tmp.


### Deployability — DevOps

Reviewer: Codex, DevOps lane. Product root `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`; closeout run `2026-11-17-1a4ae2f0`; merged HEAD `339c9209385290247c01d1eea97a7c2c8b47fada`. `RUN_DEVOPS=auto` resolves to yes because migration 0014 and `.github/workflows/ci-gates.yml` changed.

**Lane result: PASS for the declared local-development runtime; 0 critical, 0 high, 0 medium, 0 low DevOps findings.** No production rollout approval is implied.

| Check | Result and exact evidence |
|---|---|
| Declared runtime and prerequisites | Raw `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/artifacts/test-results/g1-compose-ps.txt` records `brain-postgres:18-pgvector-age` healthy, PostgreSQL 18.6, pgvector 0.8.6, AGE 1.8.0 and btree_gist 1.8. The same raw file shows the shared development database at 0010 and a superuser role; the approved run uses disposable databases rather than claiming that shared DB was current. |
| Runtime preflight and failure history | `g1-runtime-preflight.md` points to the raw compose/upgrade/baseline artifacts; the missing identity_version baseline failure is attributable to the stale shared database and the rerun is recorded against a migrated disposable DB. Full final JUnit records 1081 passing cases and no skips. No failure was silently presented as a successful run. |
| Additive migration and lineage | `engine/migrations/versions/0014_f0008_bitemporal_contract.py:26` has revision 0014 and down_revision 0013. Upgrade at `:321` adds nullable columns, CHECKs, self-FK, partial index, three SECURITY INVOKER functions and six triggers. It does not create a table, role, grant or SECURITY DEFINER function, and preflight locks before scanning invalid envelopes (`:300`). |
| Actual rollback cycle | Raw `.../artifacts/test-results/command-output/g2-migration-cycle.txt:3` reports 0014; `:8` downgrades to 0013; `:15` upgrades back to 0014; `:19` confirms head. The raw final JUnit includes `test_s0007_ac1_ac2_ac4_ac6_up_down_up_keeps_every_version_identical` and `test_s0007_ac4_downgrade_refuses_while_v1_rows_exist_and_names_them`; source `engine/tests/integration/test_temporal_migration.py:161` compares seeded snapshots across the entire cycle. The guard at migration `:347` names blocking v1/lineage rows and leaves roll-forward as the supported recovery once those rows exist. |
| Environment/dependency contract | The locked diff has no new environment variable, dependency, lockfile, compose service, port, secret or deployable. The new CI step reuses existing test-only `BRAIN_MIGRATION_ADMIN_URL`; code runs in the already locked engine environment. Migration 0014 is the only migration added. |
| CI wiring | `.github/workflows/ci-gates.yml:122` builds/starts the runtime and waits for health; `:162` applies migrations to fresh CI DB; new F0008 step at `:214` includes unit, commit, immutability, concurrency, read and migration suites against owned PostgreSQL databases, with a 10-minute timeout and `--cov=brain_temporal --cov-fail-under=80`. Existing F0007/persistence/identity gates remain in the workflow. |
| Timezone environment | Raw `.../artifacts/test-results/g1-tzdata-versions.txt` records PostgreSQL system tzdata 2025b and host Python tzdata 2026e. The run explicitly records that difference, uses fixture zones with unchanged relevant rules and treats the database check as authoritative, as the approved ADR requires. |
| Security/configuration boundaries | The local application superuser is the known SEC-F8-02 boundary routed to F0018, not a newly introduced grant. The raw compose output warns about unset authentik bootstrap configuration; F0008 does not require the OIDC flow and its fixture principal override is declared. Neither is evidence of a validated production runtime. Security and PM own risk disposition and handoff completeness. |

#### FR3 self-review, trace and limits

Checked the raw artifacts named above and the actual migration/workflow/test assertions; report summaries alone were not accepted as proof. No new runtime start, migration or fixture execution was necessary for the historical closeout assessment. The optional Docker status read failed with sandbox socket permission denied, so this lane makes no claim about the live daemon state. No implementation, canonical evidence, tests, trackers or configuration was changed. No frontend/model/deployment lane was added because the feature introduces no such surface. Production hosting remains the separately owned F0026 decision. Parent FR2 owns fresh structural validators; those results must be combined with the substantive requirements findings before the overall done verdict.


## Validation Evidence

| Required check | Exit | Result | Artifact |
|---|---|---|---|
| Feature evidence — closeout | 0 | PASS | `artifacts/test-results/fr2-operation-results.json#fr2-validate-closeout` |
| Trackers (driver) | 0 | PASS | `artifacts/test-results/fr2-operation-results.json#fr2-validate-trackers` |
| KG symbols | 0 | PASS | `artifacts/test-results/fr2-operation-results.json#fr2-kg-check-symbols` |
| KG drift | 0 | PASS | `artifacts/test-results/fr2-operation-results.json#fr2-kg-check-drift` |
| Framework templates | 0 | PASS | `artifacts/test-results/fr2-operation-results.json#fr2-validate-templates` |
| Story-index currency | 0 | PASS | `artifacts/test-results/fr2-story-index-currency.json` |
| Trackers (explicit absolute root) | 0 | PASS | `artifacts/test-results/fr2-explicit-trackers.txt` |

Required evidence validation: **PASS**. Structural validation cannot settle a semantic AC conflict or a missing response field.

Policy: `gate_policy.py --profile review-family --variant feature`; computed status **NOT DONE**, totals {"critical": 1, "high": 0}. Input and output are `artifacts/test-results/fr4-policy.json` and `commands.log`. Validation PASS is required for any done outcome; a Critical finding independently forces NOT DONE.

## Artifact Trace

- Input binding and assumptions: `action-context.md`; product instructions: `artifacts/review/product-context.txt`.
- Source inventory, exact implementation patch and pre-existing untracked files: `artifacts/diffs/changed-files.txt`, `implementation.diff`, `initial-working-tree.txt`. No tracked edits existed at start; pre-existing audit `2026-11-18-a3709ba0` was preserved and its verdict was not treated as completion proof.
- Raw evidence entry points: `planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts/latest-run.json` and selected run's `evidence-manifest.json`. Role sections cite precise raw evidence reached from that manifest, including JUnit, JSON coverage, runtime/migration probes and four final scanner outputs. `CAN/` and ellipses in role tables refer to that selected canonical run; bare feature story names refer to `planning-mds/features/archive/F0008-bitemporal-canonical-facts/`.
- Actual response-model and schema diagnostics: `artifacts/review/code-response-probe.json`, `architect-temporal-null-schema.json`. Independent execution/coverage arithmetic: `qe-raw-artifact-check.json`. Signoff row comparison: `pm-source-checks.json`.
- Currency check: same story generator on byte-identical story files at identical relative paths in a temporary mirror, with the canonical product root passed explicitly. Original STORY-INDEX and feature files are never regenerated in place. The resulting diff and hashes are retained under `artifacts/diffs/fr2-story-index-currency.diff` and `artifacts/test-results/fr2-story-index-currency.json`.
- Protected canonical inputs were hashed before review; end-of-run hashes and tracked Git state establish that no source/evidence/tracker/KG repair occurred. Audit output is confined to this review run and /tmp.
- Gate procedure: `gate-decisions.md`, `gate-state.json`, `lifecycle-gates.log`. Shell commands: `commands.log`; retrospective bootstrap rows explicitly identify their recording-time limitation. Role-specific probes and reads are logged with rebinding of the canonical root.
- Self-review: every owned role section includes FR3 evidence and omission checks. No new broad regression or scanner run is claimed. UI, AI, live OIDC and production-role/deployment limits are justified in the relevant sections.
