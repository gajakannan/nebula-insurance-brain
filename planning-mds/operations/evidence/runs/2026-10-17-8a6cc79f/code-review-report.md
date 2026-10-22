# Code Quality Review Report — F0004

Reviewer: Codex, independent `f0004_code_review` subagent (separate pass from the
implementation author; no external human review claimed). Date: 2026-10-20.
Run: `2026-10-17-8a6cc79f`. Baseline: current `HEAD` worktree on
`docs/f0004-plan-review-rework` ; including untracked implementation.

## Reviewed files

The scope is [artifacts/diffs/changed-files.txt](artifacts/diffs/changed-files.txt),
including the added `test_docling_adapter.py` behavioral regressions. Primary
specification: approved F0004 assembly plan, all four stories, authored schemas,
SOLUTION-PATTERNS and implementation-decisions.md. The Python/FastAPI/SQLAlchemy
architecture in that approval governs this review.

Inspected the shared content contracts/verifier/stores/checkpoints/identities;
revision 0008 and immutable index/date/repair metadata; authorized API, worker
publication/access/importer and queue fence; native projection/provenance,
submission/reuse/Graph integration; and backup/inventory/restore/citation paths.
Inspected the affected unit/integration expectations and raw test/coverage
evidence. Dependency vulnerability disposition belongs to the parallel Security
report. No production code, git state, shared database or lifecycle gate was
mutated by this reviewer.

## Validation artifacts

- Started with README.md, action-context.md, evidence-manifest.json, then
  g2-self-review.md, test-plan.md, test-execution-report.md, coverage-report.md
  and implementation-decisions.md.
- Baseline raw application evidence: `artifacts/test-results/g2-final-engine-tests.txt`
  (227 passed), `g2-final-neuron-tests.txt` (85 passed, four explicitly optional
  production-inference/tokenizer skips), `g2-final-restore-tests.txt` (four passed),
  and `g2-durable-table-index-tests.txt` (one supplemental PostgreSQL proof).
- Corrections: `artifacts/test-results/g3-engine-regression.txt` (229 passed),
  `g3-date-read-regression.txt` ; `g3-date-repository-types.txt` ;
  `g3-date-read-clean-lint.txt` ; `g3-all-changed-python-lint.txt` ;
  `g3-sec-h1-tests.txt` ; `g3-sec-h1-final-lint.txt` ;
  `g3-sec-h1-types-corrected.txt` ; and `g3-restore-regression.txt` (four passed).
  The older `g3-date-read-final-lint.txt` is a retained failed diagnostic;
  it is superseded by the clean logs, not counted as a pass.
  Current full neuron evidence is `g3-neuron-regression.txt` (93 passed, the
  same four optional skips); current coverage combine/JSON/XML/threshold logs
  are `g3-current-coverage-*.txt`. These refreshed source maps supersede the
  pre-correction maps; the now-included durable-table case is not counted
  twice in the current engine total.
- [Independent application checks](artifacts/review/independent-code-checks.md):
  54 pure versioned-content/date cases passed, then the current date-race and
  durable-table PostgreSQL cases both passed independently. The original real
  database counterexample is retained in
  [date-read-race-result.json](artifacts/review/date-read-race-result.json).
- [Routing/risk summary](artifacts/review/routing-summary.json) and per-node raw
  JSON retain the read-only KG checks. Framework tracker validation passed
  with zero errors/warnings, deliberately without invoking later-stage G6.
  The scoped quality scan found no TODO/FIXME or oversized file; its seven
  line-length advisories are exact packaged schema descriptions, not source
  maintainability defects. Application lint/type evidence supplies stack checks.

## Severity-ranked findings

Current open counts: **Critical 0; High 0; Medium 0; Low 0**.
Confirmed code findings during this pass: **one High and one Medium, both fixed
and reassessed**. The separate Security finding is not double-counted here.

### CR-H1 — High — inconsistent selected-date read under concurrency — resolved

**Location:** `engine/packages/brain-persistence/src/brain_persistence/document_dates.py:498`
(`read`), with locking helper at line 136.

**What/why:** Under PostgreSQL READ COMMITTED, the old implementation fetched
candidates, then selected the latest selection in another statement. A real
authorized writer could append a candidate and verified human selection between
those statements. The read returned that new selection without its candidate and
silently returned `selected_date=None`. This contradicted the S0003 attributable
date/readback and explicit-selection contract.

**Evidence:** `artifacts/review/date_read_race_probe.py` reproduced the issue
using the actual services, audit boundary and controlled human verifier in an
owned throwaway PostgreSQL database. The returned candidate set omitted the
selected candidate; a stable reread returned `2025-03-01`. The retained result
explicitly labels this historical defective behavior.

**Correction/verification:** Date reads now acquire `DocumentVersion FOR SHARE`
after current authority and hold it through the read audit commit. Candidate and
selection writers already use `FOR UPDATE` on that same row. The new
`test_date_read_keeps_selected_candidate_consistent_during_concurrent_write`
starts a real writer after the candidate query, observes actual
`pg_blocking_pids` contention at `FOR UPDATE` ; verifies the old coherent read,
then verifies the new coherent read after the writer resumes. This reviewer
reran that test successfully. The authority → version lock order matches writes;
unlocked referenced-content metadata does not introduce a second version lock.

### CR-M1 — Medium — quadratic JSONL splitting in index operations — resolved

**Location:** `engine/packages/brain-persistence/src/brain_persistence/content_repository.py:325`
and `:389` (`_insert_indexes` ; `verify_indexes`).

**What/why:** Whole-file `splitlines()` ran inside each block/table loop,
repeatedly scanning and allocating the same JSONL bytes. Every verified read
repeated that avoidable work as record counts grew. This was a structural scaling
issue; no unmeasured latency or throughput breach is asserted.

**Correction/verification:** Each payload is now split once per method/record
family and the exact original line is indexed for hashing. The retained hash/
ordinal semantics are unchanged. Current independent durable-table testing and
the 229-case engine regression pass.

## Recommendations with owner/follow-up

Open code findings remain **0**. The following low-priority recommendations
record bounded later-stage obligations or optional qualification work; they do
not reopen the resolved findings or assert those future stages are complete.

- [low] Complete actual F0004 runtime bindings, symbols/caller references and decision-marker regeneration/validation — owner: Architect; follow-up: G7 is explicitly pending under the approved build order. No graph completion is claimed by this review. Refresh risk/blast routing after those bindings exist.
- [low] Attach this independent pass as hotspot second-reviewer evidence and obtain `primary_owner` acknowledgement on a future PR — owner: Change owner / repository owner; follow-up: parse-once hotspot rank 3 and the bus-factor flag require these PR/merge controls. There is currently no PR or merge, so no acknowledgement is fabricated.
- [low] Retain explicit limits on producer metadata when later qualifying OCR/model reproducibility — owner: AI Engineer / F0026 qualification owner; follow-up: optional enrichment, not an unmet F0004 AC. Actual RapidOCR receipts retain observed engine class and pinned package version, while model/model_version are paired nulls. Step 1a explicitly requires OCR engine name/version and the approved schema permits paired nulls. Those fields establish bounded producer attribution; they do not prove model-weight identity or imply that OCR used no ML. Do not invent model labels from package names.

No recommendation authorizes production Graph activation, a new grant, a new
human decision producer, or enabling the default-false v2 writer.

## Vertical-slice completeness

The reviewed path connects trusted enqueue → existing job lease/fence → current
authority → strict verified bytes → manifest-last publication → transactional
ready metadata/indexes/publication audit → authorized saved-native reuse and
result import. It preserves the original queued fence for deterministic v1
fallback, authorizes the actual fallback resource, and retains an immutable,
identity/hash-bound fallback receipt before a marker can outlive readiness.
Missing/tampered receipts fail adoption; they confer no permission.

The date slice uses trusted artifact ownership, exact retained CONTENT line/hash/
quote, default-deny metadata/human ports, append-only candidate/selection history,
version lock/CAS/idempotency and atomic semantic/auth audit identities. The read
race found by this review is corrected. No source priority, timestamp substitution,
canonical temporal interval or new human grant is introduced.

The compatibility slice uses trusted keys for public/worker reads, preserves v1
bytes and nullable legacy metadata before/after expansion/backfill, and separates
failed reads from authorized operator quarantine/repair. Restore uses actual
database dumps and complete content inventories in isolated targets. Full
production model/Graph qualification remains outside these storage proofs.

## AC/test adequacy

All 25 criteria were traced to code and behavior, not just the prose mapping.
Test names below are executable cases in the cited modules. `M` denotes
`engine/tests/integration/test_content_migration_states.py`; `V` denotes
`engine/packages/brain-content/tests/test_versioned_content.py`; `P` denotes
`neuron/packages/brain-ingestion/tests/test_content_projection_v2.py`.

| AC | Implementation / concrete behavior evidence | Assessment |
|---|---|---|
| S0001-AC1 | shared verified stores; V exact-marker roundtrip; owned-PG marker recovery and actual restore v1/v2 | Covered |
| S0001-AC2 | `validation.verify_bundle` ; manifest-last store; V missing/hash/asset failures; M orphan/expiry failures | Covered |
| S0001-AC3 | strict versioned manifests/execution/quality; P real native/scanned/mixed projection and empty/failed conversion rejection | Covered |
| S0001-AC4 | source registry before conversion; `test_content_consumer_versions.py::test_two_profiles_and_restart_use_saved_native_without_parser_or_ocr`; worker reuse test forbids actual conversion/OCR entry points | Covered |
| S0001-AC5 | exclusive immutable bytes and identity locks; V conflict/exact retry; `test_content_worker_v2.py::test_concurrent_profiles_share_pending_identity_and_preserve_restrictions` | Covered |
| S0001-AC6 | publisher current authority + queue pre/post fence + one transaction; M `test_ready_registration_indexes_and_audit_commit_once_and_detect_incomplete_restore` ; audit/commit/expiry fault cases | Covered |
| S0002-AC1 | native hierarchy projection, shared record validation and durable indexes; P real fixtures; M durable-table reopen/owner/missing-link proof | Covered |
| S0002-AC2 | schema/model origin-producer-anchor union; observed per-item receipts; P actual origins and hard missing-producer rejection | Covered within approved engine-attribution contract |
| S0002-AC3 | native/scanned OCR actually executes; V schema/example origin-anchor roundtrip; transcript/description cases are explicitly storage fixtures only | Covered within approved scope |
| S0002-AC4 | explicit layout/transform/code-point model; V astral/multi-region/unavailable geometry; P missing rotation remains coarse | Covered |
| S0002-AC5 | cell/header/merge/continuation relations and same-artifact validation; V table negative matrix; P distinct repeated amounts/cell IDs; M persisted table/link proof | Covered |
| S0002-AC6 | schema/semantic failures; P missing origin → explicit v1 fallback, missing producer → hard failure; worker fallback/accepted-corruption cases | Covered |
| S0002-AC7 | same deterministic publication event as S0001; M exact retry yields one publication event and indexed structures | Covered |
| S0003-AC1 | `DocumentDateService.append_candidate/read`; M all three basis kinds with semantic audit UUID distinct from audit-row UUID; new read interleaving regression | Covered after CR-H1 correction |
| S0003-AC2 | no automatic selection or system-time fallback; M default-undated candidates; pure date source/precision negatives | Covered |
| S0003-AC3 | append correction/selection/clear and pinned output reference; M idempotency/stale/clear/history; `test_run_outputs.py` exact historical basis | Covered |
| S0003-AC4 | exact source line/hash/quote, owner FKs, trusted receipts and atomic audit; M default-deny/revoked/mismatched receipts and mutation-event rollback | Covered |
| S0003-AC5 | M `test_june_example_retains_issued_date_without_deriving_canonical_time` checks exact June 1/10/12/14 semantics | Covered |
| S0003-AC6 | separate candidates, verified-human-only selection, version CAS; M competing selections/default denial and current read consistency regression | Covered after CR-H1 correction |
| S0004-AC1 | API `_load_verified` ; `SourceContentAccess` ; actual accepted-artifact authorization/import; API exact v1/v2 bytes and worker delivery tests | Covered |
| S0004-AC2 | API Reviewer-only/cross-tenant/cross-KB/revocation denial before object reads; M denied publisher prevents writes; trusted fallback resource checks | Covered |
| S0004-AC3 | 0007-compatible metadata reader, additive 0008, no v1 relabel; M legacy/blocked/backfill/quarantine/repair/uniqueness tests; V unknown-version rejection | Covered |
| S0004-AC4 | `backup.sh` ; `backup_inventory.py` ; isolated `restore.sh` ; common inventory/citation checks; actual four-case restore proof rejects missing bytes/index/files | Covered |
| S0004-AC5 | existing worker/process-kill suites and real pinned Graph two-profile saved-native consumers; honest partial/unresolved ledger; controlled ledger separately proves BoxSelector translation | Covered without production-activation claim |
| S0004-AC6 | four worked-example reproductions, structured schema/model examples and explicit expected/observed persisted outcomes; synthetic fixtures remain outside frozen holdout | Covered |

The tests assert persisted identities, bytes, audit/state/index inventories,
authorization-before-read and failures/rollback, rather than success flags alone.
The date counterexample demonstrated that high statement coverage alone did not
establish concurrency correctness; the added database interleaving regression
now verifies that missing boundary. No UI changes make browser/visual/a11y lanes
applicable. Optional live inference/tokenizer skips do not replace required
converter, storage, authority or parser-free reuse proofs.

## Architecture compliance

| Review dimension / pattern | Assessment |
|---|---|
| 1. Correctness and logic | Checked identity/version dispatch, byte inventory, origin/anchors, geometry/tables, dates and retries. CR-H1 fixed and independently verified. |
| 2. Clean architecture | Shared `brain_content` serialization/verification has no Docling/FastAPI/SQLAlchemy dependency. Engine does not import the AI runtime. Composition/adapters use application ports and trusted keys. |
| 3. SOLID | Narrow content/authority/verifier protocols; persistence participates in caller transactions. The service/persistence split follows the approved Python architecture. |
| 4. Test quality and coverage | Actual converter, PostgreSQL, crash/recovery and restore proofs supplement pure contract tests. New read consistency test observes real lock contention. Coverage verification is separately stated below. |
| 5. Error handling | Explicit unsupported/integrity/conflict/unavailable errors; sanitized 400/404/409/503 content boundary; corrupt accepted bytes never become conversion misses. Failed read decisions alone do not quarantine. |
| 6. Performance | Full verification/no cache is the approved choice. CR-M1's repeated JSONL scanning was removed. No new throughput claim is inferred. |
| 7. Readability and naming | Core helpers identify authority, identity, verification and transaction roles. Non-obvious audit ordering, fallback receipt, submission lock, native hierarchy and read locking have rationale comments; new risk fixes use explicit WHY markers. |
| 8. Acceptance criteria | All 25 ACs mapped above, including truthful legacy/producer/date/Graph boundaries. |
| 9. Over/under-engineering | Reuses the existing F0005 queue/fence/outbox; no duplicate scheduler, new model engine, service or UI, speculative grant or canonical writer. Extra fallback receipt is justified by the marker/DB crash boundary. |

Authorization/audit patterns are preserved: staged mutation authorization and
immediate date FK commit atomically; operation failure rolls staged success back
before a failed decision is written. Publisher/operator paths recheck current
authority and commit readiness/state/repair effects together. The reviewed PDF
signature correction executes before either parser; Security owns its final
reachability/verdict.

Tracker governance check passes for the current In Progress state. G5 signoffs,
G6 candidate, G7 runtime graph/symbol/decision reconciliation and G8 closeout are
not complete. Define lookups for new classes currently have zero matches; the
approved G7 binding plan must remedy that debt before closeout. This report does
not call stale graph projections synchronized. Tracked diff impact identifies
backup-and-restore, durable-authorization-decisions, local-inference-service,
parse-once-content-artifact, runtime-roots-and-toolchain and
semantic-interpretation-run. These integration surfaces were reviewed directly.

Existing nodes score 4/elevated; the new planning-only nodes score 0 because
their runtime signals are absent. No score reaches the high/critical risk bands.
Parse-once hotspot rank 3 requires a second reviewer despite that aggregate
score: this independent pass supplies the code review evidence. The graph's
zero-test-file signal is superseded by inspected actual runtime/test artifacts,
not treated as missing tests. Future owner acknowledgement on a PR remains a
merge condition, as stated above.

## Coverage verification

Independently read and recomputed the refreshed
`artifacts/coverage/changed-runtime.json` totals:

| Current changed Python runtime | Covered / statements | Actual |
|---|---:|---:|
| Engine | 1683 / 1830 | 91.97% |
| Neuron | 504 / 569 | 88.58% |
| Operations | 184 / 218 | 84.40% |
| Combined | 2371 / 2617 | 90.60% |

All 44 changed Python runtime files are measured; every layer exceeds 80%.
The denominator includes tracked HEAD changes and untracked runtime statements;
missing measurements count as misses. The current five-map combine excludes
the stale standalone table-index map because the current full engine lane now
executes that case. Raw current `engine.json` ; `neuron.json` ; `restore.json` ;
migration/CLI JSON and `combined.json`/`combined.xml` ; plus
`g3-current-coverage-combine.txt` and `g3-current-coverage-threshold.txt` ; support
these figures. Pre-correction numbers are retained historically, not used as
current proof. Frozen SQL and shell are verified through actual PostgreSQL/CLI
execution, not mislabeled as Python coverage.

## Result

**APPROVED WITH RECOMMENDATIONS**

Current open findings: **Critical 0; High 0; Medium 0; Low 0**. CR-H1 and CR-M1
are resolved. The current application regressions pass: engine 229, neuron 93
with four optional out-of-scope skips, and restore four. Current changed-runtime
coverage is 90.60%. All nine review dimensions and 25 AC mappings were assessed.

This is the Code Reviewer change-set verdict only. Security disposition, G4
operator approval, G5 implementation signoffs and G6–G8 remain separate ordered
requirements. No overall feature approval, signoff or completion is recorded.
