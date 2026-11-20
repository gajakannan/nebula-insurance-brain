# Fresh Feature Review — F0008

## Decision

**CONDITIONALLY DONE — High conditions unaccepted; completion not cleared.** This is the second independent closeout audit requested after remediation. Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`. Audited latest approved run: `2026-11-18-bce4909b`; review run: `2026-11-19-b21ec2de`. Immutable remediation diff: `339c9209385290247c01d1eea97a7c2c8b47fada..3290d17750b62d70b9130ac9010d096a584eead5` (198 paths). Full F0008 source was also checked against `2badb9a..3290d17`. DevOps is required.

**What remains pending:** one new **High** output-authorization finding and four **Low** documentation/evidence findings. The original missing commit-response fields and losing-audit requirement conflict are resolved by implementation plus explicit operator-approved amendments. The legacy serializer and same-slot lineage fixes are also present. The remainder of the old timestamp wording finding is still incomplete. Prior passing summaries and the remediation approval were not accepted as proof of these conclusions.

The new response includes copied predecessor/remainder attestation dates. Source authorization on POST checks the current proposal's sources, while equivalent GET reads check the returned version's sources. No matching check for the newly returned predecessor metadata was found. This is a **source-supported missing control**, not a claimed live reproduction. The attempted targeted runtime probe was stopped by automated cybersecurity safeguards; it was not retried. Source inspection and existing tests support the finding, but no new mixed-authority runtime result is asserted.

The recorded raw suite has **1,085 passing tests, zero failures/errors/skips**, with **217 F0008 cases**. Fixed-diff coverage is **24/24 remediation lines (100%)** and **718/732 whole-feature lines (98.087432%)**, both above 80%. The amended 46 functional criteria have executed mapping for the tested caller, while that coverage does not prove the new response authorization boundary.

Severity counts: **Critical 0, High 1, Medium 0, Low 4**. The High has a role owner and proposed defensive correction, but **no accepted mitigation or committed target date**. The review does not fabricate those commitments or treat the earlier Low SEC-F8-02 acceptance as accepting this new High. A policy result of CONDITIONALLY DONE is not an accepted completion or merge/release clearance; its required High disposition remains pending with the original lifecycle owners.

## Findings By Severity

| ID | Severity | Owner | Finding | Raw evidence |
|---|---|---|---|---|
| SEC-F8-NEW-01 | High | security | New commit response returns predecessor temporal metadata without corresponding predecessor-source READ checks | `engine/apps/api/src/brain_api/routes/facts.py:210`; `engine/packages/brain-temporal/src/brain_temporal/commit.py:505`; `engine/apps/api/src/brain_api/schemas/facts.py:97` |
| R2-ARCH-L1 | Low | architect | Four-copied-timestamps wording remains in the assembly plan and docstring | `planning-mds/features/archive/F0008-bitemporal-canonical-facts/feature-assembly-plan.md:48`; `engine/packages/brain-temporal/src/brain_temporal/commit.py:251` |
| QE2-L1 | Low | quality-engineer | Recorded runtime preflight does not precede the full-suite start | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/artifacts/test-results/full-engine-regression.xml:1`; `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/commands.log:4` |
| PM2-L1 | Low | product-manager | Current manifest splits four space-containing filenames into nonexistent paths | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/evidence-manifest.json`; `artifacts/diffs/manifest-inventory-drift.json` |
| PM2-L2 | Low | product-manager | Feature Run shortcut and blueprint planning label remain stale | `planning-mds/features/archive/F0008-bitemporal-canonical-facts/STATUS.md:9`; `planning-mds/BLUEPRINT.md:260` |

The High is counted only in Security. Architect/QE references to the same new response surface do not add counts. Complete triggers, uncertainty, source flow and repair ownership are in the role sections below.

## Completion Checks

| Lane | Fresh result |
|---|---|
| Product Manager | Current 35 signoffs and latest approved pointer agree; receiving F0018 handoffs exist. Two Low inventory/tracker findings remain. |
| Architect | Legacy omission and migration0015 lineage fixes verified. One Low timestamp-prose residual. New authorization concern transferred to Security. |
| QE | Raw 1,085 tests and fixed-range coverage verified. Prior functional gaps resolved for tested caller; one Low preflight-chronology finding. Mixed-readability response coverage absent. |
| Code Reviewer | Original Critical response omission resolved; source remains bounded to F0008. Security owns the new output-authority concern. |
| Security | One new High missing predecessor-source READ check on returned metadata. Source-only finding; no fresh runtime proof. |
| DevOps | Current local runtime/migration deployability passes; framework pin bump remains an assigned follow-up. |

Six lanes ran concurrently within available slots: parent PM, Architect/DevOps sharing a slot, QE in one slot, Code/Security sharing a slot. Each owns its findings and report section. All canonical artifacts are read-only.

### Requirements Satisfaction, Signoff and Closeout, Tracker Sync — product-manager

Current approved run: `2026-11-18-bce4909b`, at HEAD `3290d17`. Prior review `2026-11-18-d34a095e` is the comparison baseline, not approval evidence. This lane read the latest manifest, raw current story statements and amendments, assembly-plan remediation decisions, closeout/gate records, current provenance and exact receiving F0018 artifacts. Owning reviewers independently checked the raw implementation/test/security evidence.

#### Prior finding dispositions

| Prior item | Current disposition and concrete evidence |
|---|---|
| CR-F8-01 missing commit-response metadata | Implemented: `CommitResponseOut.versions[]`, `CommitResult.version_temporals`, the response JSON Schema and current POST tests now cover metadata. S0007 AC6 is amended and the assembly remediation section records the operator choice. A new authorization question raised by that added output is independently reviewed by Security; resolving the original omission does not settle that question. |
| QE-M1 losing-commit audit clause | S0004 AC1 now explicitly retains failed authorization audits; current test asserts failed count equals losers. Assembly-plan remediation decision and current G4 approval record support the amendment. |
| PM-M1 F0018 carry-over | Resolved: `planning-mds/features/F0018-canonical-commit-service-and-action-authorization/README.md:26–27` explicitly names the application role and durable refusal reasons; `planning-mds/kg-source/features/F0018.yaml:32` carries both; S0005 annotates its reason-persistence deferral. |
| PM-L1 original inventory | The original historical mismatch is acknowledged by the new run's `prior-run-errata.md`; the new inventory itself has a different defect below. |
| PM-L2 stale Last Updated | Resolved: current `STATUS.md:4` is 2026-11-19. Other stale current pointers remain below. |
| Prior reporting/scanner-label drift | Original unsupported execution/scan labels are acknowledged in `prior-run-errata.md`; QE/Security verify the new raw outputs, rather than adopting the errata's PASS as execution proof. |

Current provenance is complete: the latest 35 `(story, role)` rows in STATUS name the current run, a reviewer, date and passing reported verdict. The current signoff ledger points to the same role evidence; the earlier passing and PENDING rows remain append-only history. The latest-run pointer and approved manifest agree, and the prior feature manifest is superseded. Mechanical source/provenance checks are in `artifacts/review/pm-source-checks.json`. Existing signoffs do not waive new source-supported findings.

#### Remaining findings

**PM2-L1 — Low — The current manifest splits four paths containing spaces into nonexistent entries.** Owner: Product Manager / canonical evidence owner. Raw `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/evidence-manifest.json` declares four truncated paths ending in `ci-nodb-gate-brain_api`, `brain_domain`, `brain_factslots`, `brain_temporal`, plus stray `apps/api/tests.txt` and `packages/brain-*/tests.txt` entries. The actual four tracked files have names containing both the package and test directory, e.g. `artifacts/test-results/command-output/ci-nodb-gate-brain_api apps/api/tests.txt`. Locked git diff lists 198 paths while the manifest lists 202. The exact comparison is `artifacts/diffs/manifest-inventory-drift.json`. The actual raw gate outputs exist and are inspected by QE; this is an inventory accuracy defect, not an allegation that the tests never ran. Rebuild the manifest list preserving complete filenames in the owning lifecycle; do not split paths on whitespace. The audit makes no repair.

**PM2-L2 — Low — Current planning/status shortcuts still select stale feature state.** Owner: Product Manager. `planning-mds/features/archive/F0008-bitemporal-canonical-facts/STATUS.md:9` still labels the superseded `2026-11-17-1a4ae2f0` as **Feature Run**, although the current approved remediation is named at lines3/8. `planning-mds/BLUEPRINT.md:260` still lists F0008 as Planned, while §4.15, §6, registry, roadmap and current README report Done/Archived after remediation. This is textual tracker drift; the canonical latest-run pointer and archive path remain correct. Align the current shortcuts during owning-role closeout rework without erasing historical summaries.

#### Pending follow-ups already assigned downstream

`pm-closeout.md` Deferred Follow-ups assigns: SEC-F8-02 non-superuser application role to Architect/DevOps in F0018; durable refusal reason codes to Architect in F0018; formal ADR-0078 acceptance to Operator; migration renumbering after0015 to F0011; coordinated framework BLUEPRINT/CI pin update to DevOps; older valid/recorded naming drift to Architect and tzdata pinning to DevOps. These remain pending and should not be described as newly introduced blockers by this review. The framework checkout advanced during the audit; the actual validation revision is recorded at FR2.

#### FR3 self-review and limits

Checked the raw current artifact statements and exact receiving handoffs. The two low findings cite actual current paths and the independent immutable diff; historical summaries were not silently rewritten. No future-feature implementation was reviewed beyond the explicit F0008 handoff. No new High acceptance, mitigation deadline, operator approval or ADR acceptance is inferred. No UI/AI lane is required: F0008 adds neither. Required validation/currency checks are run by the parent at FR2, with canonical story files and generated trackers kept read-only.


### Architecture and KG Alignment — Architect

Reviewer: Codex, independent Architect lane. Product root `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`; current audited feature run `2026-11-18-bce4909b`; remediation `339c9209385290247c01d1eea97a7c2c8b47fada..3290d17750b62d70b9130ac9010d096a584eead5`. Full F0008 source remains in scope through HEAD. The historical review was used as a comparison checklist, not as completion proof.

**Architecture-owned counts: 0 critical, 0 high, 0 medium, 1 low.** Prior implementation fixes are verified below. A newly introduced response-authorization concern is owned and counted by Security as `SEC-F8-NEW-01`; it is not duplicated in these counts. An architecture section with only a low finding does not establish an overall completion verdict.

#### Prior finding dispositions

| Previous item | Current disposition | Raw evidence checked |
|---|---|---|
| FR-ARCH-M1, legacy `temporal:null` | **Resolved.** The current serializer omits the field for legacy versions. | `engine/apps/api/src/brain_api/schemas/facts.py:129` wraps serialization and removes absent temporal metadata; `engine/tests/integration/test_temporal_reads.py:307` now asserts the key is absent. Fresh narrow serializer diagnostic `artifacts/review/architect-legacy-serialization.json` confirms omission using the actual current response class. The raw new-run JUnit records `test_legacy_slot_reads_keep_pilot_behaviour` passing. |
| FR-ARCH-L1, current-selection and timestamp prose | **Partially resolved.** ADR D4 correctly gives a current clear precedence, and ADR D5 now distinguishes three copied source timestamps from new acceptance. The assembly plan and implementation docstring retain the obsolete four-copied-timestamps wording. | Corrected ADR-0078 `:111`, `:144`, `:147`; residual source references in R2-ARCH-L1 below. |
| FR-ARCH-L2, cross-slot split lineage | **Resolved.** Migration 0015 requires the parent to be in the same slot, scans for existing violations under a table lock and refuses with row IDs; it does not repair rows. | `engine/migrations/versions/0015_f0008_split_lineage_same_slot.py:38`, `:54`, `:77`; `engine/tests/integration/test_temporal_immutability.py:303` proves the direct-insert negative; `engine/tests/integration/test_temporal_migration.py:273` proves preflight refusal, unchanged snapshot and up/down/up retaining 0014 guards. Both are present and passing in the raw new-run JUnit. |
| Original missing S0002 AC7 commit metadata | **Original shape omission resolved; new response-security concern remains.** Current `versions[]` carries each written version's temporal block in ID order, omitting inapplicable legacy metadata. Operator-approved S0007 AC6 amendment reconciles the former request/read-only restriction. | `brain_domain/facts.py:60`; `brain_temporal/commit.py:306`, `:505`, `:529`; `brain_api/schemas/facts.py:75`; response schema `planning-mds/schemas/canonical-commit-response.schema.json`; `engine/tests/integration/test_temporal_v1_commit.py:769`; `test_contract_examples.py:141`. Amendment is recorded in `feature-assembly-plan.md:354`. Security owns the newly exposed predecessor-metadata path described below. |

#### Finding

**R2-ARCH-L1 — Low — Four-copied-timestamps wording remains in the current assembly plan and remainder docstring.** Owner: Architect, with Backend Developer for the explanatory docstring. `planning-mds/features/archive/F0008-bitemporal-canonical-facts/feature-assembly-plan.md:48` still says remainders take the predecessor's four timestamps; G0 item 7 at `:343` repeats that statement. `engine/packages/brain-temporal/src/brain_temporal/commit.py:251` likewise says the four timestamps are copied. Actual code at `:268` copies the three source timestamps and at `:271` gives the remainder the new `canonical_accepted_at`. This actual behavior matches `F0008-S0003-split-intervals-and-close-recorded-time.md:24`/`:27` and the corrected ADR-0078 `:144`/`:147`. A reader following the still-current assembly plan can reintroduce the old contradiction or assert the wrong acceptance time. Finish reconciling these remaining descriptions through the original owning action. This is residual design/documentation drift, not a failing timestamp implementation.

#### Additional inspection and cross-role concern

The new response metadata adds a disclosure surface beyond the old commit response. The current call flow copies predecessor attestation dates into remainders at `brain_temporal/commit.py:622` and `:642`, records every remainder's `piece.temporal` at `:505`, and returns that mapping from `_finish`. `CommitResponseOut.from_domain` serializes each temporal block at `brain_api/schemas/facts.py:97`. POST source authorization at `brain_api/routes/facts.py:210` includes the new proposal's positive/ending evidence and answer scope, while the final return at `:265` has no equivalent of GET's returned-version evidence check at `:115`. A caller allowed to commit the slot and read its own new evidence can therefore potentially receive predecessor attestation dates whose source artifact it cannot read. The existing restricted-artifact test at `test_temporal_reads.py:248` establishes that slot authority and attesting-artifact READ authority can differ, but it exercises GET. The new response test at `test_temporal_v1_commit.py:769` exercises matching source authority only. This source-backed concern was independently corroborated with Security and transferred to `SEC-F8-NEW-01`; no live exploit or runtime reproduction is claimed in this lane.

The remainder of the reviewed structure follows the approved bounded design: the existing table and GiST exclusion remain, new fields are in existing domain/API/persistence packages, unknown ends stay finite integrity bounds, attestation uses selected document dates, STATE remains the only activated kind, and the known F0018 source-authority/RLS/refusal-routing handoffs stay explicit. Migration 0015 is additive and attached to the existing migration node, rather than introducing unrelated semantics.

#### KG, proof evidence and pending obligations

- Verified `planning-mds/kg-source/bindings/f0008-planning.yaml:30` binds migration 0015 to `migration:f0008-bitemporal-contract`. Other remediation source files retain their prior bindings. Parent FR2 owns fresh generated-symbol and drift validation; this lane performs no graph regeneration.
- Read the current canonical manifest and its cited Architect, DevOps, KG/preflight reports, then the exact current raw runtime artifacts. Parsed `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/artifacts/test-results/full-engine-regression.xml`: **1085 tests, 0 failures, 0 errors, 0 skips**, including the new response/schema/lineage/migration cases. Selection and observed outcomes are retained in `artifacts/review/architect-remediation-runtime.json`. Passing pre-existing tests do not prove the newly identified mixed-authority response case.
- ADR-0078 still requires the operator's acceptance decision. Successful implementation proofs and feature G4 approval do not automatically accept that ADR.
- SEC-F8-02 and durable refusal reason persistence are now recorded on F0018, including `planning-mds/kg-source/features/F0018.yaml:32`. Their handoff is delivered; F0018's implementation is future scope. The old `valid`/`recorded` versus runtime field-name drift and tzdata pinning remain acknowledged follow-ups in current `pm-closeout.md:25`.

#### FR3 self-review and limits

Every resolution and finding above was checked against the actual changed source, exact tests and current raw JUnit, not the remediation report's resolved labels. The narrow serializer diagnostic uses current runtime classes and writes only into this review. Evidence entry points and subsequent artifact reads respect the manifest/citation guard. No code, tests, feature docs, canonical evidence, KG or trackers were changed. No UI, new model service, new route or production hosting assessment is added because none is introduced by the feature. No live database probe or full suite was run by this lane; the response-security concern is explicitly source-based, with Security owning final severity and validation limits. Parent FR2/FR4 determine the combined validator and done result.


### Test Evidence and Coverage — Quality Engineer

Reviewer: Codex QE lane, 2026-11-19. Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`. Audited approved run: `2026-11-18-bce4909b`. Remediation diff: `339c9209385290247c01d1eea97a7c2c8b47fada..3290d17750b62d70b9130ac9010d096a584eead5`; whole-feature comparison starts at `2badb9ad2756f38ee9a1d84930787a3df989a245` and ends at the same locked head.

`CAN/` below means product-relative `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/`. Other source/test references are product-relative.

**Result:** the two previously unresolved acceptance criteria now have executed regression assertions matching the amended requirements. Final suite and coverage claims are supported by the raw artifacts. One low finding remains in the recorded preflight chronology. Test evidence does not establish authorization of newly returned predecessor/remainder metadata under different source-readability scopes; Security owns that separate completion judgment, and its finding must not be double-counted in QE totals.

#### New finding

**QE2-L1 — Low — Recorded runtime preflight follows the full-suite start.**

`CAN/artifacts/test-results/full-engine-regression.xml:1` records the suite start as `2026-11-18T22:51:27.253773-05:00`. `CAN/commands.log:4` records the health/version/migration probe at 22:52:35, and line 5 records the G1 validator at 22:52:45; `CAN/gate-decisions.md:10` also records G1 PASS at 22:52:45. Thus the package does not demonstrate that its recorded runtime preflight preceded that full validation execution, as required by the QE completion checklist.

The fresh database upgrade is recorded at 22:51:27 in `CAN/commands.log:1`, and its raw transcript (`CAN/artifacts/test-results/command-output/fresh-db-upgrade-head.txt:1`) proves upgrade through 0015. The runtime was usable and the suite passed. This is a chronology/evidence finding; it does not imply a product failure or that the database was unavailable. Log timestamps alone do not establish the exact invocation start of the probe, so no stronger ordering claim is made.

Owner: Quality Engineer, with DevOps supplying the earlier raw probe if one exists. Follow-up: preserve preflight evidence before launching subsequent full validation and record command start/completion timing explicitly. No runtime restart or canonical evidence rewrite was performed by this review.

#### Prior finding dispositions checked against raw source and execution

| Prior issue | Fresh disposition and exact evidence |
|---|---|
| CR-F8-01, S0002 AC7 metadata absent from POST response | Functionally resolved for the tested caller. `engine/tests/integration/test_temporal_v1_commit.py:769` asserts POST `versions[]` order, OPEN and UNKNOWN state/attestation/start metadata, remainder lineage and equality with GET. `engine/apps/api/src/brain_api/schemas/facts.py:61`/75 build and serialize the new response; `engine/packages/brain-domain/src/brain_domain/facts.py:63` carries domain metadata; `engine/packages/brain-temporal/src/brain_temporal/commit.py:487` collects each version's temporal block. The new testcase appears once and passes in `CAN/artifacts/test-results/full-engine-regression.xml:1`. Authorization of a predecessor's metadata is a distinct test-coverage limitation described below. |
| QE-M1, S0004 AC1 loser audit contradiction and unchecked failed rows | Resolved by explicit amendment and assertion. The current story at `planning-mds/features/archive/F0008-bitemporal-canonical-facts/F0008-S0004-enforce-temporal-integrity-under-concurrency.md:22` permits/requires the durable FAILED authorization audit while prohibiting business effects and successful commit audit for losers. `engine/tests/integration/test_temporal_concurrency.py:89` now asserts failed commit decisions equal the number of losers; the race at line 60 still asserts conflicts, one winner, no overlap on at least 200 coordinates and winner outbox/version counts. The amended test passes in the final JUnit and three separately preserved race reruns. This preserves the F0002 security guarantee. |
| S0002 AC7 versus S0007 AC6 scope conflict | Explicitly reconciled: S0002 story line 28 identifies `versions[].temporal`; `planning-mds/features/archive/F0008-bitemporal-canonical-facts/F0008-S0007-preserve-pilot-versions-through-migration.md:27` now permits additive commit-response fields. `planning-mds/features/archive/F0008-bitemporal-canonical-facts/feature-assembly-plan.md:354`/355 records the operator's implementation and audit-amendment decisions. |
| QE-L1 unsupported repeat/no-database claims | Resolved for the new run. `CAN/commands.log:10`–12 cites three separate race transcripts, each with six passed at its line 13. Four corrected no-database commands are retained at lines 17–20 with their raw transcripts and passing coverage floors. `CAN/prior-run-errata.md:15` identifies the old unsupported claims rather than treating old report prose as proof. This review adopts the new November 18 execution evidence and does not infer a November 18 rerun for the superseded November 17 package. |
| Legacy `temporal: null` response/schema drift | Regression now checks omission: `engine/tests/integration/test_temporal_reads.py:293` checks the legacy commit has exactly its original three fields and the GET omits `temporal`. `engine/packages/brain-temporal/tests/test_contract_examples.py:141` validates actual serialized v1/legacy responses and legacy-remainder omission against the response schema. Both testcases pass in the new raw JUnit. |
| Cross-slot split lineage integrity | `engine/tests/integration/test_temporal_immutability.py:303` directly attempts a cross-slot split predecessor and expects database refusal. `engine/tests/integration/test_temporal_migration.py:273` first installs 0014, seeds a bad split, verifies 0015 refuses without mutation and names the row, then checks a clean upgrade/downgrade/upgrade leaves 0014's guard intact. Both new tests pass in the raw JUnit. Architecture/DevOps own the DDL and rollout verdicts. |

#### Authorization regression coverage limitation — shared with Security, not a duplicate QE finding

The newly added metadata regression at `engine/tests/integration/test_temporal_v1_commit.py:769` uses the default service principal for both commits and supplies the **same positive evidence document** for predecessor and successor (lines 775, 777 and 790). No `principal=` override or differing classification is present. `engine/tests/fixtures/temporal/harness.py:224`–229 selects `principal or self.service`.

`engine/packages/brain-temporal/tests/test_contract_examples.py:141` tests serialization only and has no authorization boundary. Existing `engine/tests/integration/test_temporal_reads.py:248` tests a restricted-source GET; line 268 tests unreadable attesting evidence included in the **current proposal**. Neither exercises a readable successor proposal that splits a predecessor whose attesting document the caller cannot read, then checks the metadata returned for that remainder.

Accordingly the coverage percentage and passing AC7 testcase cannot establish non-disclosure at this newly returned data surface. Security owns the source-path finding and severity. QE identified this missing negative by source inspection only; no further runtime probe was executed. Any eventual repair needs a regression with different readability scopes, an authorized predecessor commit, a restricted successor caller and assertions on the POST body/transaction behavior.

#### Raw execution verification

`CAN/artifacts/test-results/full-engine-regression.xml:1` has **1,085 actual testcase elements**, with **0 failures, 0 errors and 0 skips**. Its start timestamp is 2026-11-18 22:51:27-05:00; duration is 277.400 seconds. `CAN/artifacts/test-results/command-output/full-engine-regression.txt:56` independently prints 1,085 passed and 390 warnings in 277.41 seconds. Raw coverage timestamp is November 18 22:56:04, consistent with completion of this suite; the command log's 22:56:11 entry is compatible with post-completion recording.

F0008 suite groups account for **217 cases**: bounds 56, contract examples 40, temporal service 12, temporal v1 commits 51, immutability 36, concurrency 6, reads 11 and migration 5. All four newly introduced testcases, the amended race testcase and the amended legacy-shape testcase are individually present and passing in that XML.

| Additional execution | Verified raw result |
|---|---|
| Race repeat 1/2/3 | `CAN/artifacts/test-results/command-output/concurrency-repeat-1.txt:13`, `concurrency-repeat-2.txt:13`, `concurrency-repeat-3.txt:13`: each 6 passed; commands.log lines 10–12 record rc 0. |
| Temporal no-database gate | `CAN/artifacts/test-results/command-output/ci-nodb-gate-brain_temporal.txt:17`: 97.40% floor passed; line 18 reports 129 passed. |
| API no-database gate | `CAN/artifacts/test-results/command-output/ci-nodb-gate-brain_api.txt:30`: 81.78% floor passed; line 31 reports 38 passed and 4 skipped. The fact API fixture explicitly skips when PostgreSQL is unavailable (`engine/apps/api/tests/test_facts.py:93`–102). The final full-engine run has no skipped cases, so this is not a skipped final database/HTTP layer. |
| Domain no-database gate | `CAN/artifacts/test-results/command-output/ci-nodb-gate-brain_domain.txt:22`: 90.84% floor passed; line 23 reports 103 passed. |
| FactSlot no-database gate | `CAN/artifacts/test-results/command-output/ci-nodb-gate-brain_factslots.txt:16`: 87.65% floor passed; line 17 reports 59 passed. |

The four preceding failed no-database attempts are explicitly documented at `CAN/test-execution-report.md:17` and retained in `CAN/commands.log:13`–16. Exact raw paths, including spaces, are provided in those JSONL entries. Their output reports 692 passed, 393 skipped and a 0% coverage failure, consistent with the documented mistaken selection/coverage arguments. They are not silently omitted or used as final proof. Corrected attempts and full regression supersede them. The malformed manifest inventory produced from those names is owned by the PM lane and is not double-counted here.

#### Coverage recomputation against immutable ranges

Raw input: `CAN/artifacts/coverage/engine-coverage.json:1`, intersecting changed source-line hunks with executed/missing executable statements. This review recomputed both ranges directly rather than reusing the historical helper's moving `origin/main` reference.

| Coverage scope | Independently observed result |
|---|---|
| Remediation source, `339c920..3290d17` | **24/24 = 100.00%**: API schemas 20/20, domain facts 1/1, commit service 3/3. Matches `CAN/artifacts/coverage/changed-code-summary.txt:5`. |
| Whole F0008 source, `2badb9a..3290d17` | **718/732 = 98.087432%**, above the 80% floor. |
| All source measured in this raw run | 5,019/5,194 = 96.630728%; kept distinct from changed-line coverage. |

Migration 0015 is explicitly not measured by source-line coverage (`CAN/coverage-report.md:23`); its raw executed integration/migration cases establish behavior. The unchanged missing changed-source statements total fourteen, and are recorded in this review's derived `artifacts/review/qe-raw-artifact-check.json` alongside per-file numerators and denominators. The derived file references raw artifacts; it is not substituted for them.

#### Story and proof-gate completion checks

The new `CAN/test-plan.md:9` explicitly carries forward the detailed 46-criterion mapping from `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/test-plan.md`. That referenced plan was read during the prior independent review, and its mapped tests are executed again in this run's new raw JUnit. The prior 44/46 disposition was caused by the two precise gaps above; both now have matching requirements and assertions. Per-story functional mappings are S0001 6/6, S0002 7/7, S0003 7/7, S0004 6/6, S0005 7/7, S0006 7/7 and S0007 6/6, subject to Security's independent finding at the new response boundary.

The six ADR proof groups retain executed cases for retroactive facts/concurrency, close-only immutability, zones/precision, unknown-validity examples, state/envelope/member guards and migration preservation. Existing F0001/F0007 regression suites execute in the new full-engine run. Tests are therefore not approved solely from the remediation report's 46/46 statement. Passing the functional mapping does not establish every authorization edge case, as the new remainder-response gap demonstrates.

#### Justified omissions and limits

- This lane reviews preserved execution evidence and source assertions; no redundant full-suite rerun was necessary, and no new runtime execution is claimed.
- Historical runtime is the locked host engine environment (Python 3.14.4) using Docker PostgreSQL 18.6, not an engine-container invocation. This is explicit in `CAN/g1-runtime-preflight.md:12`; raw runtime and migration probes are cited above. Production database-role qualification is a separate Security/DevOps boundary.
- UI/component/browser/visual/accessibility layers are inapplicable: no experience change or UI is included. Neuron/model/evaluation layers are inapplicable: no AI/model behavior changed. No new login flow or user-facing browser path was added; test principals are injected while the server-side authorization path remains active.
- No new latency SLA is introduced. The explicit concurrency/transaction grid is executed; this review does not claim deployment load qualification.
- Scanner interpretation and the newly returned predecessor metadata's authorization belong to Security. This lane does not claim that serialization tests or line coverage substitute for those proofs.
- Superseded run errata now identify the old unsupported repeated-run/no-database claims and prior 44/46 state. The new raw artifacts, rather than historical audit verdicts, support this review.

#### FR3 self-review

Verified raw JUnit counts, statuses and named new cases; exact source assertions for the two prior gaps; operator-amended criteria and the former scope conflict; all three repeat outputs; four successful and four superseded no-database attempts; fixed-range coverage arithmetic; raw preflight timestamps; and the missing differing-readability response scenario. Each finding cites concrete raw evidence. The authorization issue is counted only in Security's lane; the inventory issue only in PM's lane. All skipped layers are justified above. Only this review folder and temporary diagnostic code were written; canonical implementation, tests, docs, trackers, KG and feature evidence were not edited.


### Code Quality and Merge Readiness — code-reviewer

Reviewer: Codex, fresh review of F0008 remediation. Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`. Audited feature run: `2026-11-18-bce4909b`, read only. Remediation range: `339c9209385290247c01d1eea97a7c2c8b47fada..3290d17750b62d70b9130ac9010d096a584eead5`; original feature remains in scope through `2badb9a..3290d17`.

**Owned finding counts: Critical 0, High 0, Medium 0, Low 0.** The prior Critical CR-F8-01 is resolved at source, contract and test level. Overall merge readiness remains pending the separately counted Security finding SEC-F8-NEW-01 and the other lanes' evidence judgments.

#### Prior finding dispositions

| Prior finding | Current disposition | Direct verification |
|---|---|---|
| CR-F8-01 — S0002 AC7 metadata absent from commit response | Fixed | `brain_domain/facts.py:60` adds version temporals; `brain_temporal/commit.py:312` creates entries in exactly `fact_version_ids` order, and lines 505/529 populate remainder/new-version entries. `brain_api/schemas/facts.py:92` serializes them as `versions[].temporal`. `canonical-commit-response.schema.json:30` admits `versions`. `test_temporal_v1_commit.py:769` now checks actual POST metadata and ordering. |
| CR-F8-01 — conflict with S0007's API scope | Explicitly reconciled | `F0008-S0007-preserve-pilot-versions-through-migration.md:27` now admits additive commit-response fields; S0002 AC7 records the chosen `versions[].temporal` shape. `feature-assembly-plan.md:348` records the operator's remediation decision. This is a recorded change in requirements, not an inferred waiver. |
| FR-ARCH-M1 — legacy reads returned `temporal: null` | Fixed in source/test | `schemas/facts.py:129` omits only absent temporal metadata. `test_temporal_reads.py:293` now checks absence. The selective wrap serializer preserves meaningful pilot null fields such as the finite/open range fields. |
| QE-M1 — losers claimed to write no audit row | Reconciled in requirement and test | S0004 AC1 now distinguishes FAILED authorization decisions from successful commit audit/effects; `test_temporal_concurrency.py:87` checks the failed count against losing requests. The F0002 authorization facade retains failed-decision auditing. |
| FR-ARCH-L2 — split lineage could cross slots | Fixed in source/test | Migration `0015_f0008_split_lineage_same_slot.py:36` requires the predecessor's slot to equal the new row's slot; preflight at line 54 refuses existing crossings under a table lock, without repair. The existing ownership FK still checks tenant/KB. Tests at `test_temporal_migration.py:273` and `test_fr_arch_l2_split_lineage_cannot_cross_slots` cover the negative and migration cycle; Architect/QE own raw execution verification. |
| Old scan-label evidence drift | Resolved in current manifest and superseding errata | The current manifest labels both SAST and secrets `findings-triaged`; current raw artifacts match those outcomes. `prior-run-errata.md` preserves corrections to the superseded run rather than rewriting its files. Security independently parsed the new scan outputs. |

PM owns scope inventory, tracker/header currency and handoff completeness, including any remaining defects; those are not counted again in this lane.

#### Functional and code checks

| Dimension | Judgment |
|---|---|
| Correctness / AC mapping | The original missing-response behavior is corrected, including split remainders and legacy omission. The positive HTTP test now asserts response fields rather than inferring them from a later GET. The new output's authority requirements are a separate Security concern, not counted twice. |
| Architecture boundaries | Metadata remains a pure domain `VersionTemporal` value; the commit service uses repository protocols, persistence maps rows, and API DTOs serialize. Migration 0015 is additive and does not add a route, table, grant or producer. |
| SOLID / scope | The remediation reuses the existing result DTO and serializer seams, without a generic new framework or a second source of temporal derivation. |
| Test quality | `test_temporal_v1_commit.py:769` checks one-version and split response ordering; `test_contract_examples.py:141` validates the actual model output, including a legacy remainder and pilot response. The mixed-authority predecessor/current-response case is not covered by these tests; Security owns the missing output authorization finding. |
| Error handling | The original SQLSTATE mapping and sanitized database failures remain in `routes/facts.py:256`; 0015 raises a generic check violation and its preflight reports only bounded migration IDs. No changed route error branch was introduced. |
| Performance | The response reuses temporal objects already computed during commit, with no new per-entry query. The same-slot trigger performs a primary-key predecessor lookup. No fresh load-performance claim is made. |
| Readability / rationale | `CommitResult.version_temporals` documents order and legacy semantics; serializers explicitly explain omission; migration rationale explains its relationship to 0014 and trigger ordering. |
| Dead/debug/TODO paths | No new debug or abandoned alternative path was identified in the inspected production diff. Legacy behavior stays explicit and exercised. |
| Over/under-engineering | Selective field omission avoids global `exclude_none`; the default empty tuple keeps existing legacy result callers compatible. No new abstraction is needed solely to carry these fields. |

No additional independent code correctness or maintainability defect was established beyond the security output-check concern. Static migration review found the new same-slot condition consistent with its intended invariant; this is not a fresh runtime proof that every database state or permission profile is covered.

#### FR3 self-review, scope and limits

All dispositions above were checked against current source, current amended requirements and actual current test assertions, not the previous approval summaries. Original CR-F8-01 is closed; it is not retained merely because the previous audit blocked completion. Existing all-feature test execution, coverage arithmetic, concurrency repetitions and fresh gate validators are owned by QE and the orchestrator.

This lane performed no fresh runtime access-boundary verification. A proposed runtime probe was blocked by automated safeguards, and no retry or replacement probe was made. Only source and existing recorded evidence support the new Security concern. No executable exploit fixture, database operation or implementation/test repair was created by this lane. Reports and read-only scan summaries are confined to this review folder; the canonical feature package remains untouched. Frontend, model/prompt, new authentication handlers and external integrations remain outside the changed feature scope. Current KG and generated-layer freshness are checked by Architect/FR2, not assumed from the previous audit.


### Security — security

Reviewer: Codex, fresh review of F0008 remediation at `3290d17750b62d70b9130ac9010d096a584eead5`. Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`. Canonical run: `2026-11-18-bce4909b`, read only.

**Verdict: REQUEST CHANGES pending output-authorization remediation or owning-lifecycle verification.** New owned findings: **Critical 0, High 1, Medium 0, Low 0**. SEC-F8-NEW-01 is a source-supported missing output check; runtime disclosure was **not** demonstrated. The previously accepted Low SEC-F8-02 remains a disclosed residual and is not counted as a new finding.

#### SEC-F8-NEW-01 — High — inherited remainder metadata is serialized without corresponding predecessor-evidence READ checks

**Observed source path.** The remediation adds a successful commit-response path for temporal blocks belonging to **every written version**, including remainders:

1. `_remainders` copies predecessor `attested_from` and `attested_through` at `engine/packages/brain-temporal/src/brain_temporal/commit.py:622`; a right remainder also copies `attested_to` at line 644. These dates can therefore describe predecessor evidence rather than the new proposal's evidence.
2. `_commit_v1` includes each remainder's `piece.temporal` in its result at `commit.py:505`; `_finish` places them in `CommitResult.version_temporals` at line 312.
3. `engine/apps/api/src/brain_api/schemas/facts.py:97` serializes every result entry using `temporal.to_json()`. `brain_domain/temporal.py:192` includes the inherited dates; line 198 includes the predecessor version identifier. Raw evidence-reference lists are **not** part of that temporal serializer and are not claimed to be disclosed here.
4. `engine/apps/api/src/brain_api/routes/facts.py:210` builds POST `source_keys` only from the proposal's positive/ending evidence and the proposal's answer sources. The call at line 234 authorizes those keys and slot COMMIT. `AuthorizationExecution.mutate` in `engine/packages/brain-security/src/brain_security/execution.py` performs its extra READ checks before the operation and has no returned-payload READ stage. The POST returns the new response at `routes/facts.py:265`.
5. `SqlAlchemyFactCommitRepository.require_commit_sources` in `engine/packages/brain-persistence/src/brain_persistence/repositories.py` forwards only the supplied proposal refs; `engine/packages/brain-persistence/src/brain_persistence/assertions.py:827` discovers those refs and review decision. Its `closes_existing` parameter controls eligibility and does not add predecessor attestation artifacts to the authorized READ set.

**Missing/current control.** The GET path already derives READ keys from the **exact returned version's** evidence and ending evidence in `routes/facts.py:115`, and joins those checks to `execution.read` at line 138. The new POST result has no equivalent check for predecessor-derived output dates. The selected feature run's `security-review-report.md`, "Commit-response disclosure" row, asserts that same-slot commit authorization covers predecessor documents; the inspected code does not establish that implication.

**Slot restrictions do not supply a general proof.** `brain_factslots/resolution.py:238` provisions access from creation sources only when the slot is created; `brain_persistence/fact_slots.py:94` derives restrictions from those source resources. No inspected commit path unions all later predecessor-source restrictions into slot access. `planning-mds/security/policies/policy.csv:15` and lines 18–19 distinguish artifact READ, slot READ and slot COMMIT actions. Same tenant/KB membership is not itself proof of satisfying each artifact's current classification/ACL conditions. The existing source test `test_temporal_reads.py:248` explicitly places restricted attesting evidence on an otherwise readable slot and expects a whole-read 404. Thus a universal invariant that slot access implies access to every later attesting artifact cannot be assumed.

**Potential impact and uncertainty.** Where an authorized slot committer can use allowed proposal sources but lacks READ to a predecessor's attesting artifact, the current result-building path can include that predecessor's document dates in a split remainder response without adding that artifact to the READ set. This is an information-disclosure risk at the new output boundary, under the existing T-08 requirement. Actual reachability with deployed grants, resource restrictions and source data remains unverified in this review. No cross-tenant leak, disclosure of raw evidence refs, or executed exploit is claimed.

**Why the recorded tests/scans do not prove the boundary.** `test_temporal_v1_commit.py:769` exercises the new response using the same privileged actor and positive evidence across both commits; it verifies serialization/order, not a changed authority boundary between predecessor and new sources. `test_temporal_reads.py:268` checks unreadable evidence named in the **new** proposal, while the read negative at line 248 proves the GET guard. Neither test shown covers inherited predecessor metadata in a successful POST. The current DAST is explicitly unauthenticated and its protected POST observations are 401 paths. Scanner success and the existing positive response test therefore do not settle this missing output check.

**Severity and ownership.** **High**, Security-owned: the source shows a newly returned sensitive field set without the independent artifact READ checks already required for equivalent GET output. This is not Critical and is not labeled runtime-confirmed. Repair/verification owners: Backend Developer + Architect, with Security accountable and QE responsible for regression evidence. No operator-approved mitigation, owner-accepted completion date or acceptance of this new concern exists; those are **pending**, not invented here.

**Defensive remediation / owning-lifecycle verification.** Ensure the exact metadata returned by a commit is authorized against every attesting artifact that contributes to it while retaining the existing same-UoW authority guarantees. Reconcile any necessary response behavior with the AC7 contract rather than silently disclosing or redacting fields. The owning lifecycle should verify predecessor/current-source permission differences, revocation/current grants, allowed complete responses, and unchanged legacy behavior, then obtain renewed Security/QE evidence. No repair was made during this review.

**Runtime limitation.** A proposed runtime verification was blocked by automated safeguards. No fresh runtime proof of this possible remainder-metadata authorization issue was obtained, and no retry, replacement access-boundary probe, database operation or executable exploit fixture was performed by this lane. This finding is grounded in the source paths and existing recorded tests above, with its remaining uncertainty stated explicitly.

#### Prior finding dispositions and raw scan review

| Prior item | Current disposition / direct evidence |
|---|---|
| SEC-F8-L1 / SEC-L1 — clean label versus triaged SAST hits | Resolved. Current `evidence-manifest.json` uses `findings-triaged` for SAST and secrets. `prior-run-errata.md` accurately distinguishes the original seven migration-0014 hits from a clean scan. No old artifact was rewritten. |
| SEC-F8-01 — database error text leakage | Remains fixed. `routes/facts.py:256` maps SQLSTATE and returns a generic non-exclusion error without `str(IntegrityError)`. |
| SEC-F8-02 — superuser local/CI application role | Carried accepted Low, not a new finding. The new security report and PM closeout retain the F0018/F0026 ownership. This review does not claim production least-privilege qualification. |
| CR-F8-01 / AC7 | Serialization gap is fixed; the newly added output path exposes the distinct authorization concern above. Prior code finding is not re-counted. |
| Losing-commit audit and split lineage | Requirement amendment retains failed authorization-decision audit. Migration 0015 adds same-slot lineage without new role/grant/SECURITY DEFINER behavior. |

Independent parsing of the exact manifest-cited outputs is recorded in `artifacts/review/security-scan-review.jsonl`:

- **Dependency:** `artifacts/security/dependency-engine.json`, 35 packages, zero listed vulnerabilities at the recorded scan time. No fresh vulnerability-database query is claimed.
- **Secrets:** `artifacts/security/secrets/secrets-gitleaks-20261118-225256.sarif`, three `generic-api-key` findings at the prior review's `initial-canonical-hashes.json` lines 39/76/124. These are file SHA-256 digests, not new credentials; the current triaged label is accurate.
- **SAST:** `artifacts/security/sast/sast-semgrep-20261118-225256.sarif`, three SQLAlchemy-text warnings at migration 0015 lines 57/58/62. Inspection shows only module-owned table/predicate strings; no request interpolation. False-positive triage is supported by current source.
- **DAST:** `artifacts/security/dast/api-scan.json` has two informational riskcode-0 alert categories. `run-dast.log` records `zap exit=0`, FAIL-NEW 0, WARN-NEW 0, PASS 113. `run-dast.sh:2` explicitly says no credentials are configured; it does not establish authenticated response authorization.
- **Targets:** manifest-cited `artifacts/security/scan-targets.txt` lists the four changed production files (DTO, migration 0015, domain result and commit service) plus changed tests. No protected authorization path was added to the scanner merely by returning metadata, so manual output-boundary review remains necessary.

#### Security dimensions and FR3 self-review

Injection resistance remains backed by parameterized ORM queries and constant-only migration SQL. Authentication behavior is unchanged. Access control and sensitive data output require the High finding above. No new deployment secret, CORS/cookie rule, cryptographic component, network integration, model call or file parsing surface was introduced. Audit effects remain under the existing facade and outbox transaction, and losing attempts retain failed authorization auditing. Slot locking, exclusion constraints and stale-version checks remain the concurrency/resilience controls. The prior sanitized-error fix remains visible. New migration functions use SECURITY INVOKER with a pinned search_path, and ownership FKs remain alongside the new same-slot check.

STRIDE coverage: spoofing/elevation use existing verified principal/current-grant controls; tampering uses close-only/exclusion/ownership/lineage controls; repudiation uses durable authorization and commit audit; information disclosure is the newly identified output concern; DoS adds no new external dispatch or unbounded input mechanism in this remediation. No additional independent source-supported security finding was established.

FR3 checked every substantive assertion against current source, exact current test assertions, current amended requirements and cited raw scanner files. The missing READ-set path is distinguished from the unverified runtime impact. All skipped runtime verification is explicitly disclosed; authenticated DAST is not claimed. Findings are routed to lifecycle owners, and neither implementation nor canonical evidence was edited. Architecture/QE references to SEC-F8-NEW-01 are cross-references to this single Security-owned finding, not additional severity counts.


### Deployability — DevOps

Reviewer: Codex, independent DevOps lane. Product root `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`; canonical feature run `2026-11-18-bce4909b`; HEAD `3290d17750b62d70b9130ac9010d096a584eead5`. DevOps is required because remediation adds migration 0015 and full F0008 still includes migration 0014 and CI changes.

**Deployability result: PASS for the declared local-development runtime. No new critical/high/medium/low DevOps finding.** The framework pin update below is an explicit pending follow-up, not evidence of failure in the current closeout. Security owns the new commit-response disclosure concern.

#### Current evidence checks

| Check | Disposition and raw evidence |
|---|---|
| Current preflight | Raw `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/artifacts/test-results/g1-runtime-probe.txt` records `brain-postgres:18-pgvector-age` healthy, PostgreSQL 18.6, schema 0015 and btree_gist 1.8. The cited preflight keeps the original locked engine/Python plus Compose PostgreSQL topology and explicitly leaves shared development DB at 0010. |
| Fresh database upgrade | Read raw `.../artifacts/test-results/command-output/fresh-db-upgrade-head.txt`: transactional DDL applies 0001 through 0015 and logs the installed same-slot guard. This is actual execution output, not only the deployability verdict. |
| Migration 0015 behavior | `engine/migrations/versions/0015_f0008_split_lineage_same_slot.py:23` declares revision 0015/down_revision 0014. `:35` is SECURITY INVOKER with pinned search_path; `:38` checks same-slot ancestry; `:54` locks then refuses existing cross-slot rows, naming samples. `:77` drops only its added trigger and function. No table, new privilege, new secret or data rewrite is introduced. |
| Migration-cycle and refusal proof | Read source `engine/tests/integration/test_temporal_migration.py:273`: install refusal leaves snapshot and revision 0014 unchanged; after test-only fixture cleanup, upgrade/downgrade/upgrade removes only the 0015 trigger and retains 0014's insert guard. The raw new-run JUnit marks this test passing. Migration 0014's original guarded rollback policy is retained. |
| Full regression | The current raw `.../artifacts/test-results/full-engine-regression.xml` contains 1085 tests with no failure/error/skip, including the same-slot direct-insert negative and 0015 preflight/cycle case. `artifacts/review/architect-remediation-runtime.json` records the exact parsed suite and selected outcomes. No current HTTP mixed-authority predecessor-response test is present; that is Security's newly identified gap. |
| CI scope | Existing `.github/workflows/ci-gates.yml:214` already runs the changed temporal unit, commit, immutability, concurrency, read and migration files against owned PostgreSQL databases with a >=80% brain_temporal floor. Runtime setup still applies fresh migrations to head. The remediation adds no unrelated workflow, dependency, environment variable, service, port or container. |
| Prior DevOps findings | The prior independent DevOps lane had no feature-blocking finding. Fresh 0015 and current raw runtime evidence were checked independently, rather than carrying forward the old PASS. |

#### Framework pin follow-up — owner: DevOps

The product still pins framework `d90bbb6fc70dffcfa6d70379d42015e895a49fa0` in `planning-mds/BLUEPRINT.md:33` and `.github/workflows/ci-gates.yml:323`. Current closeout `pm-closeout.md:24` explicitly defers a coordinated update until framework PR #101 merges. During this audit a logged local framework read observed merged commit `840e724` (`fix(validator): accept G6/G7 reentry candidates while latest-run names the prior approval (#101)`), following d90. The parent records the exact revision used by fresh FR2 validation; this lane did not update or merge framework code.

Inspected the actual d90→840e724 validator diff. The change adds reentry-candidate recognition only in the `resolve_run` branch for **G6/G7**; closeout behavior is unchanged. Product CI at `.github/workflows/ci-gates.yml:334` invokes registry-wide feature validation with its default **closeout** stage. Therefore the old pin does not by itself make this completed feature's current closeout/CI invalid. It does lack the corrected pre-G8 reentry-candidate behavior for future remediation. The explicit remaining task is to advance BLUEPRINT and CI pins together through DevOps ownership. No remote merge or product repair is required to finish this read-only audit.

#### Other pending, bounded follow-ups

- F0011 must number its future migration after 0015; current `pm-closeout.md:23` and the remediation assembly plan record that coordination.
- The local superuser application role remains SEC-F8-02, an explicitly accepted low boundary assigned to F0018, now present in F0018's README/KG handoff. Its production qualification is not established by this feature.
- PostgreSQL/Python timezone-data pinning remains the prior documented follow-up (`pm-closeout.md:25`); the current preflight explicitly cites the unchanged recorded versions from the original proof rather than claiming newly pinned data.
- Production hosting remains F0026 scope. No production deployment or rollout approval is inferred from local deployability.

#### FR3 self-review and limits

Checked the exact migration/workflow source and manifest-cited raw preflight/upgrade/JUnit artifacts. No runtime restart, database mutation, new test suite execution or publication was performed. No canonical evidence, implementation, tests, feature docs, trackers, config or KG was changed. No new frontend/model-runtime lane is needed because remediation introduces no such surface. All shell reads used this review's telemetry wrapper. Fresh validator outcomes and substantive security findings must be combined by the parent before the overall done verdict.


### Pending work already assigned outside this audit

- **Backend + Architect, verified by Security/QE:** correct and test SEC-F8-NEW-01; obtain a documented High disposition and target date through the owning lifecycle. This audit does not authorize or perform a repair.
- **Architect:** finish timestamp wording in the current plan/docstring. **PM:** preserve complete space-containing inventory paths and align current run/status shortcuts. **QE/DevOps:** preserve preflight chronology for the next validation run.
- **Operator:** formal ADR-0078 acceptance remains a separate decision.
- **F0018 / Architect + DevOps:** non-superuser application role and durable refusal reason persistence. The handoffs are now recorded; future implementation remains pending.
- **DevOps:** update BLUEPRINT and CI framework pins together; timezone-data pinning remains an older documented follow-up.
- **F0011:** number its future migration after0015. **Architect:** previously acknowledged valid/recorded API naming drift remains for the next contract revision. Production hosting remains F0026 scope.

## Validation Evidence

| Check | Exit | Result | Raw output |
|---|---|---|---|
| Feature evidence — closeout | 0 | PASS | `artifacts/validators/fr2-validate-closeout.stdout.txt` |
| Trackers | 0 | PASS | `artifacts/validators/fr2-validate-trackers.stdout.txt` |
| KG symbols | 0 | PASS | `artifacts/validators/fr2-kg-check-symbols.stdout.txt` |
| KG drift | 0 | PASS | `artifacts/validators/fr2-kg-check-drift.stdout.txt` |
| Framework templates | 0 | PASS | `artifacts/validators/fr2-validate-templates.stdout.txt` |
| Story-index currency | 0 | PASS | `artifacts/test-results/fr2-story-index-currency.json` |

Required validation: **PASS**. Fresh validator streams are retained through the gate runtime’s supported capture parameters; checks are not inferred from old report PASS labels. Actual framework revision: `840e724b72fdbaf8157dacfee579488252e1a193`; source-only security finding is independent of structural validator success.

`gate_policy.py --profile review-family --variant feature` returns **CONDITIONALLY DONE** with Critical=0/High=1 and requires_justification=true. Raw domain input/output: `artifacts/test-results/fr4-policy.json`. Mandatory High acceptance details remain incomplete; no completion acceptance is issued.

## Artifact Trace

- Current root/run/diff binding: `action-context.md`; context reload: `artifacts/review/product-context.txt`; exact changed sets and patch: `artifacts/diffs/`.
- Entry points: F0008 `latest-run.json` and current feature-run `evidence-manifest.json`. Role sections cite the exact raw source, contracts, JUnit, JSON coverage, migration/runtime and final scanner outputs reached from these manifest citations. `CAN/` means the selected run `2026-11-18-bce4909b`; bare story names mean the archived F0008 feature directory.
- Original review findings are used only for comparison. New raw source and evidence establish each resolved/partial/pending disposition. No global lane substitutes for feature-scoped evidence.
- Independent raw checks: `artifacts/review/pm-source-checks.json`, `qe-raw-artifact-check.json`, `architect-remediation-runtime.json`, and the source-only Security section. No fresh runtime access-boundary probe was completed. The automated safeguard rejection is explicitly retained as a verification limit, not a product test failure.
- Required gates: `gate-state.json`, `gate-decisions.md`, `lifecycle-gates.log`. Shell telemetry: `commands.log`; bootstrap records transparently distinguish recording time. Driver invocation uses unchanged `run-gate.py` with a temporary wrapper forwarding the supported stdout_path/stderr_path options and explicit tracker root binding; no framework source is edited.
- Fresh per-validator stdout/stderr/result metadata: `artifacts/validators/`. Story currency is checked using the identical generator against a byte-identical temporary story mirror; the canonical index is never regenerated in place.
- Framework checkout advanced from6d19d91 to840e724 during the audit. Exact validation revision is recorded. Product HEAD advanced from the reviewed3290d17 to squash-merge e024cd7 during the final integrity check; `artifacts/diffs/merge-tree-equivalence.json`, `merge-tree-hashes.txt` and an empty `merge-tree-equivalence.diff` prove the tracked trees are identical. The original immutable diff therefore reviews the current merged content. The initially strict commit-ID guard failed, this equivalence was verified, and FR3 was rerun after that check; no changed source was silently ignored. Canonical protected-file hashes and final tracked/staged diff checks verify that the audit made no repairs.
- Role sections include FR3 self-review and all justified omissions: no UI/AI change, no production rollout, no scanner rerun claim, no fresh mixed-authority runtime verification, and explicit current-role boundaries.
