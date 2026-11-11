# F0007 FactSlot model — Feature Review

## Decision

**NOT DONE — 1 Critical, 2 High, 4 Medium.** The archived completion claim is not supported under these counterexamples. Route the Critical/High repairs to the owning lifecycle roles and obtain fresh regression/review/closeout evidence. This audit does not reopen or change the canonical feature status, approval or evidence pointer.

Mode: closeout-audit. Product commit `fa8fc1d`; diff `ff0a619..fa8fc1d`. Approved feature run: `2026-11-09-b94cfa12`, matching `latest-run.json`. RUN_DEVOPS=yes. Review actions/roles are consumed from the sibling `nebula-agents/agents/**` tree. The current feature evidence, trackers, KG symbols/drift and templates pass validation, but concrete correctness defects override prior PASS reports. `artifacts/completion-verdict.txt` records the `review-family` result.

## Findings By Severity

### FR-C1 — Critical — A MULTI member accepts the value of a different member

- **Location:** `engine/packages/brain-factslots/src/brain_factslots/answers.py:102` and `_check_value_detail` at line 106.
- **Trigger and observed result:** Resolve a member for entity A, then submit a PRESENT answer naming entity B in the same KB. The actual resolver/policy accepts it; the member key remains A. A production `sys:hasTradeName@v1` member keyed `acme restoration` similarly accepts `Zed Services` with eligible evidence.
- **Impact:** Immutable identity and the accepted answer disagree. Distinct slots can contain the same member value, resolution no longer describes the value, and a close/change addressed to one member can affect an answer describing another. This violates S0002 AC3 and ADR-0077 D4/D6, including the delivered system-name predicates.
- **Test gap:** `engine/tests/integration/test_factslot_answers.py:382` through 399 explicitly expects HTTP 201 when a fresh insured member receives the different entity `w.subject`. The existing test encodes the broken invariant.
- **Repair/owner:** Backend Developer must derive the PRESENT answer's member key using the pinned predicate contract and compare it with `StoredSlot.member_key` before writing. Architect defines the named rejection; QE corrects the acceptance test and adds entity/name/identifier mismatch negatives plus canonical-equivalence positives. Fix before renewed closeout.
- **Proof:** `artifacts/code-member-identity-repro.py`, `artifacts/code-member-identity-repro.txt`, independently rerun in `artifacts/member-repro-rerun.txt`; lane analysis in `artifacts/code-review.md`. Uses repository fakes with actual resolver/policy; no product/database writes.

### FR-H1 — High — Accepted decimal/money values can become unreadable after canonicalization

- **Location:** `engine/packages/brain-domain/src/brain_domain/fact_values.py:143`, output construction/check at lines 158–167, constants at lines 26–27; `fact_answers.py:224` revalidates stored values. Shared schema decimal and money limits are in `planning-mds/schemas/fact-slot-key-v1.schema.json:108` and line 178.
- **Reproduction:** `parse_answer` accepts `1E+64` as a decimal or money amount and emits 65 canonical characters. `stored_answer` then rejects that same emitted envelope with `DECIMAL_INVALID`: input is limited to 64 characters, output permits 128. The emitted value also exceeds the shared schema limit.
- **Impact:** An accepted answer can commit but fail typed reload, and canonical encoding is not idempotent. The feature's ordinary money round-trip tests miss this supported exponent boundary. Current production registry exposes name predicates only; this defect is in the delivered numeric carrier/library contract and numeric test/integration composition, not a currently exposed public money endpoint.
- **Repair/owner:** Backend and Architect align input/output/stored schema bounds or define a separate trusted canonical parser. QE adds normalization idempotence and commit/reload boundary tests. Fix before renewed closeout.
- **Proof:** both money/decimal cases in `artifacts/architect-probes.json`, script `artifacts/architect-probes.py`, details in `artifacts/architect-review.md`.

### FR-H2 — High — Database identity CHECK admits incomplete identity rows

- **Location:** `engine/migrations/versions/0012_f0007_factslot_identity.py:75`, partial unique index at line 90, generated subject-KB key at line 69.
- **Reproduction:** The exact CHECK returns UNKNOWN for a v1 SINGLE SLOT with NULL fingerprint, and for a row with NULL identity version plus populated v1 fields. PostgreSQL accepts UNKNOWN in CHECK. Read-only PostgreSQL evaluation returned `t|t` (is UNKNOWN; CHECK accepts) for both cases.
- **Impact:** The required identity shape has no reliable database backstop. NULL fingerprints evade uniqueness; NULL version bypasses the generated subject-KB association key. Existing composite tenant/owner FKs still apply; this is not a demonstrated cross-tenant public API bypass. The deferred trigger checks members/qualifier parents and does not reject these SLOT shapes.
- **Repair/owner:** Backend/Architect add a follow-up migration requiring a complete legacy-or-v1 expression to be TRUE, with all mandatory fields constrained. Inspect existing data before tightening. QE adds direct-SQL NULL-field and partial-legacy negatives. Fix before renewed closeout.
- **Proof:** `artifacts/architect-postgres-raw.json` contains exact successful commands, SQL, output and exit codes; `artifacts/architect-postgres-proof.md` explains the result. No shared row/schema was changed. The same error is in the approved plan SQL (plan review PR-H2).

### FR-M1 — Medium — Scope authorization expires before the protected answer is loaded

- **Location:** `engine/packages/brain-factslots/src/brain_factslots/service.py:122`; matching HTTP sequence in `engine/apps/api/src/brain_api/routes/facts.py:90`. `brain_security/execution.py:383` commits each individual read and releases its authority locks.
- **Scenario:** A principal can read a restricted absence-scope artifact. That permission is revoked after the scope READ commits but before the separate slot READ loads the answer. The slot can remain readable. A deterministic interleaving with real AuthorizationExecution/evaluator and repository authority fakes returns NOT_FOUND pages `[7,8]` while a current read of the scope is denied at the new grant revision.
- **Impact:** A narrow concurrent revocation can disclose scope details after authorization is lost, contrary to S0003 AC6/T-08. This differs from the explicitly deferred F0018 restriction re-derivation policy: the missing check here concerns the exact scope being returned and current grants.
- **Repair/owner:** Backend/Security should authorize slot and actual scope and load the selected envelope under one authority unit of work; QE adds the revocation interleaving. Proposed target: 2026-11-16 or before exposure to untrusted users, subject to owner acceptance. No acceptance is asserted by this audit.
- **Proof:** `artifacts/scope-revocation-repro.py`, `artifacts/scope-race-proof.txt`, `artifacts/authorization-read-citations.txt`. This is a deterministic fake-store interleaving, not a live concurrency test or observed incident.

### FR-M2 — Medium — Decimal size validation happens after exponent expansion

- **Location:** `engine/packages/brain-domain/src/brain_domain/fact_values.py:160` and line 162 allocate the expanded string before the length check at line 165.
- **Observed:** A short exponent-form input reaches an isolated process's 128 MiB memory cap and raises MemoryError before the named decimal rejection. The probe imposes that cap before calling the function and invokes neither HTTP nor PostgreSQL.
- **Reachability:** Current HTTP composition registers only the four system NAME predicates (`brain_api/deps.py:119`, `brain_factslots/predicates.py:35`). Decimal inputs are not reachable through a current production numeric predicate or public resolver route. This is a delivered-library resource hazard for trusted/custom registry callers and future numeric predicate adoption; no unauthenticated public-service exploit is claimed.
- **Repair/owner:** Backend computes canonical length from digits/exponent/sign before allocating and bounds work before expansion; QE verifies both exponent signs and exact limits. Proposed target: 2026-11-16 and before broader numeric predicate adoption, subject to owner acceptance.
- **Proof:** `artifacts/decimal-bound-probe.py`, `artifacts/decimal-bound-proof.txt`. Kept separate from FR-H1 because the failure mode and reachability differ.

### FR-M3 — Medium — Final changed-file evidence omits post-closeout Neuron test fixes

- **Location:** completion run `evidence-manifest.json` `changed_paths` / its cited `artifacts/diffs/changed-files.txt`.
- **Evidence:** Actual `ff0a619..fa8fc1d` includes `neuron/tests/integration/test_document_delivery.py` and `test_document_process_recovery.py`; neither appears in the declared paths. Generated `coverage-report.yaml` is also omitted. The test execution report's post-closeout addendum documents the Neuron CI repair, so these are known final changes rather than undiscovered runtime expansion.
- **Impact:** Manifest-driven review/scanning does not cover the full merged set. Earlier “no neuron change”/41 skipped-lane rationale no longer describes the final test delta. The omission of generated coverage alone would be minor; the two test files make the scoped review inventory incomplete.
- **Repair/owner:** PM/Architect reconcile final diff inventory and explicitly link post-fix validation/review scope. Proposed target: next evidence closeout (2026-11-16 target for follow-up), subject to owner acceptance. No audit repair was made.
- **Proof:** `artifacts/changed-path-crosscheck.txt`, actual changed paths in `artifacts/actual-changed-files.txt`, cited post-closeout addendum in original `test-execution-report.md`.

### FR-M4 — Medium — Archived feature entry documents still claim work has not started

- **Location:** archived `PRD.md:7` says implementation not started; archived `README.md:86` story table says Not Started for all six stories. STATUS, the story headers, registry and roadmap say Done/Archived.
- **Impact:** The feature's entry points disagree about completion and make handoffs ambiguous. The machine tracker validator does not check this prose/table drift.
- **Repair/owner:** PM reconciles the feature entry status and story table with the canonical closeout after technical repairs. Proposed target: next closeout, 2026-11-16 target for follow-up, subject to owner acceptance. This does not alter the retrospective planning requirements.
- **Proof:** `artifacts/pm-citation-lines.txt`, original README/PRD/STATUS. No broader tracker failure was inferred; generated tracker and story-index checks pass.

## Completion Checks

### Requirements Satisfaction — Product Manager

All 39 ACs have explicit prior dispositions and test/review mappings in `test-plan.md` and the checklist. The audit challenges the semantic sufficiency of those passes:

| Story | Audit disposition |
|---|---|
| S0001 stable identity | Resolution/concurrency examples evidenced; database identity-shape backstop challenged by FR-H2 |
| S0002 cardinality/members | Fail core canonical member identity invariant, FR-C1; independent per-member storage/exclusion exists |
| S0003 information states | Ordinary states/scopes evidenced; concurrent current-grant protection incomplete, FR-M1 |
| S0004 typed values | Fail accepted canonical round-trip closure, FR-H1; work bound hazard FR-M2 |
| S0005 names | System name predicates implemented; MULTI name identity consistency fails under FR-C1 |
| S0006 pilot/ownership | Pilot up/down/up and composite ownership proofs evidenced; new identity row-shape constraint incomplete, FR-H2 |

The table distinguishes raw passing examples from unproven general claims. Not every AC was freshly rerun, and the audit does not mark unrelated tests failed.

### Signoff and Closeout — Product Manager

The approved latest run and manifest agree. Required QE, Code Reviewer, Security Reviewer, DevOps and Architect verdicts, reviewer/date/evidence entries, PM approval and archive decision exist. The formal closeout validator passes. Prior implementation/testing/reviews disclose the same author/session; their prior approvals are not independent proof. New counterexamples prevent accepting the unqualified completion claim. No accepted residual risk or waiver covers FR-C1/FR-H1/FR-H2.

### Tracker Sync — Product Manager

Registry, roadmap, blueprint, authored F0007 shard, STATUS and story headers say completed/archived; generated STORY-INDEX matches in-memory generation exactly (43 stories). Entry-document drift is FR-M4. Two post-closeout test paths are absent from the scope inventory (FR-M3).

### Architecture and KG Alignment — Architect

Layering, legacy bypass, per-member temporal exclusion, additive migration, pinned contracts and the RLS inventory match the design. Missing row-shape guarantees and decimal canonical/schema closure are FR-H1/FR-H2; member/value consistency is FR-C1. Authored bindings and symbol/drift checks pass. Global warnings concern F0006 assertion symbol references and unused edge types; no new F0007 graph defect was established. ADR-0077 remains Proposed; formal acceptance, RLS, envelope DB enforcement, producer adoption and display precedence were expressly deferred to their owners, not silently omitted.

### Test Evidence and Coverage — Quality Engineer

Raw JUnit confirms the recorded final F0007 step: **151 tests, zero failures/errors/skips**; final full engine suite: **819, zero failures/errors/skips**. Neuron raw G2 JUnit: 305 tests, 41 skipped, 264 passed. The post-closeout addendum records a subsequent 27-test PostgreSQL lane rerun after CI fixes; the cited console artifact exists. Changed-code summary matches the reported **1211/1223 = 99.02%**, rounded to 99.0%. This is historical execution evidence, not a fresh full-suite run.

Fresh audit run: **118 domain/application/contract unit tests passed**, zero skips, output `artifacts/fresh-unit-tests.txt` and JUnit `artifacts/fresh-unit-tests.xml`. The new member, decimal and scope proofs still expose gaps those tests miss. G1 preflight precedes the recorded G2/G3 suites, names Compose PostgreSQL plus locked engine Python, and documents principal overrides and the excluded OIDC flow. The full integration/migration/security scan suites were not rerun during this read-only audit. PostgreSQL verification here evaluated only the exact identity CHECK expression; the shared schema/data were untouched.

### Code Quality and Merge Readiness — Code Reviewer

Framework quality scan passes for the new application source. No additional layer-boundary or hidden-debug issue was established. KG diff-impact records the affected identity/answers, canonical commit, authorization, backup, assertion and migration nodes; risk output gives the resolver score 3 (routine). These routing signals do not override FR-C1. Correct the existing incorrect acceptance assertion as part of repair. Detailed source/test assessment is `artifacts/code-review.md`.

### Security — Primary reviewer, with security-lane probes

Read authorization, denial mapping, source-scoped evidence lookup, tenant/KB composite FKs, immutable identities, parameterized access and durable decision auditing are present. No new grants, secret, route or RLS bypass was introduced. Prior scope/name fixes protect ordinary denial cases. FR-M1 is a distinct current-authority race; FR-M2 has explicitly limited current reachability.

All four historical scan classes have resolvable raw artifacts. Dependency JSON reports zero vulnerability entries; latest secrets/SAST SARIF report zero results. DAST JSON has two informational risk-code-0 alerts (client error response/session detection), rather than literally no alerts; this is consistent with no WARN/FAIL and the stated unauthenticated reach. See `artifacts/raw-scan-summary.txt` and `artifacts/dast-alert-triage.txt`. Scanners and vulnerability databases were not refreshed, and active DAST was not rerun. No current vulnerability-free assertion is made. The delegated security lane supplied probes but did not finish its final report; the primary reviewer inspected the source, reran the safe proofs and assessed the raw scan artifacts.

### Deployability — DevOps

The diff changes migration 0012, CI steps, package wiring/lockfiles and backup inventory column selection. Raw/cited preflight and deployability evidence cover dependency sync, Compose configuration, startup/OpenAPI smoke, migration up/down/up, downgrade refusal and pilot snapshots. Current container inspection found `brain-postgres` healthy; the audit did not redeploy, migrate, rebuild or restart services. No new environment contract or port was added. FR-H2 requires corrected DDL/negative migration proof; FR-M3 requires a reconciled final inventory. The declared no-UI/no-AI runtime scope remains appropriate; two Neuron test adaptations are still part of the actual changed-file set.

## Validation Evidence

FR2 ran through `run-gate.py` and all required operations passed: closeout evidence, trackers, KG symbols, KG drift and templates. Story-index currency was checked using the real generator in memory, without writing the committed index. PR2/local plan checks and semantic example checks passed as separate planning evidence. Read-only audit does not repair output merely because a validator passes or a proof finds a defect.

Evidence: `artifacts/fr2.txt`, `artifacts/closeout-validation.txt`, `artifacts/tracker-validation.txt`, `artifacts/kg-check.txt`, `artifacts/template-validation.txt`, `artifacts/story-index-currency.txt`, `gate-state.json`, `commands.log`, and `lifecycle-gates.log`. PR/FR driver PASS means the procedure executed; the separate computed FR4 verdict is NOT DONE.

FR3 self-review checked raw paths, reproduced core findings, reconciled role duplicates, distinguished current exposure from future numeric predicates, and treated stated downstream handoffs as exclusions. One Critical finding alone blocks TRULY DONE despite successful evidence validation. Medium targets above are proposed routing dates, not stakeholder commitments or accepted mitigations.

## Artifact Trace

Read the archived feature package; approved latest-run pointer/manifest; only selected manifest-cited role reports, scan/coverage/test/preflight outputs and failure/retry addenda; raw changed source, tests, schemas and governing ADRs. Scope was cross-checked against the real Git diff. Created only this audit package and sibling plan-review package. Role notes, preserved safe probes, outputs, command telemetry and validation artifacts are local to these new runs. Product source/tests/plans/trackers/KG and the canonical completion package were not repaired or reapproved. See `artifact-trace.md` for the consolidated trace.
