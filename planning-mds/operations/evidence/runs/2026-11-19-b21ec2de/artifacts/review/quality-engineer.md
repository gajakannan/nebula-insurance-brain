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
