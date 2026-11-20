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
