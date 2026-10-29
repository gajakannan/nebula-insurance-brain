# QA Qualification Verdict — F0005 run 2026-10-25-4020923b, G3 round 2 (S0004-AC4)

- **Role:** Quality Engineer, independent review session. I did not author the code, the tests, the corpus, the report or its summary. I also wrote the round-1 QA verdict; where that verdict was wrong, this one says so.
- **Date:** 2026-10-28.
- **Scope:**
  - the round-2 rework on branch `feature/f0005-live-qualification` (uncommitted working tree; every F0005 test file and the harness are untracked, so there is no `git diff` for them);
  - the immutable round-1 measurement `artifacts/qualification/report.json` ;
  - the round-2 raw results `artifacts/test-results/g2r-*` and the first-attempt failures `artifacts/test-results/g2r-attempt1/` .
- **Method:** read-only.
  - I recomputed every threshold from the per-case rows, ignoring the stored `metrics` blocks.
  - I ran `sha256sum -c` against the corpus hashes.
  - I read every live and offline test cited for an AC, and checked their assertions against the AC wording.
  - I reconstructed test changes by comparing the source pytest printed in the attempt-1 and round-1 failure logs with the current files and their mtimes.
  - I checked the coverage hits of the fail-closed lines in `artifacts/coverage/neuron-coverage.xml` .
  - I inspected the native corpus PDFs with pdfium, and the installed Docling 2.126 OCR code.
  - I ran no live lane, benchmark or quiescence.

## Summary

- **The measurement stands.**
  - `report.json` still hashes to `55ce3484…aede`, the value the round-1 Architect recorded. Its mtime is unchanged (2026-10-26 01:27).
  - Every aggregate recomputes exactly from the per-case rows.
  - Graph dense misses field accuracy, abstention, evidence resolution and relative latency. It also misses review workload, read like for like.
  - Nothing in round 2 touches the recorded report.
- **The corpus is intact.** `sha256sum -c` gives 26/26 OK, and the run-folder `CORPUS-HASHES.txt` (sha256 `fbc5e263…2dc9`) is byte-identical to the fixture copy. It is still untracked in git.
- **The round-1 findings that blocked AC ticks are closed:**
  - F-01, S0003-AC4: now proven by a deterministic offline test.
  - S0003-AC3: ledger retention is asserted live on all 8 completed runs.
  - F-06: the kill-point and competing-worker lane was re-run on the final code, with JUnit XML.
  - F-02: OCR page count and engine are now recorded on v1 and v2 bundles and asserted live.
  - F-03 and F-10: corrected in `report-summary.md` .
- **Still open:**
  - F-04: predictions are not retained.
  - F-05: the corpus is not committed, and `commands.log` is batch-stamped.
  - F-08: the gl-q-004 convention.
  - The loose assertions in F-09.
  - The partly-proven ACs. Their gaps are unchanged and are disclosed by the authors.
- **One discrepancy, which originates in my own round-1 verdict.** `report-summary.md` and ADR-0060 give the like-for-like review workload as "1.64–1.67×".
  - 1.645× (per completed run) is right.
  - 1.67× is wrong. Round 1 compared "20 vs 12 on the 8 cases both engines ran", but the baseline failed gl-q-010/b, so only **7** cases completed on both engines. There it is 17 vs 12 = **1.42×**.
  - The threshold is still MISSED (> 1.25×), so the outcome does not change.
- **Retries:**
  - The 10 s → 30 s fault timeout is a legitimate correction of a test parameter.
  - The native-document OCR relaxation is legitimate in direction, but its stated rationale is wrong for this corpus. It also exposes an undefined "OCR page count" semantic (R2-03). It does not hide a defect that bears on the rejection.
- **S0004-AC4 QA verdict:** the evidence permits only the operator's recorded **rejection** (S0004-AC3/AC7). Activation (S0004-AC5, S0005-AC5) is not permitted.

## Threshold Recomputation

The source is `engines.<engine>.cases[]` in `artifacts/qualification/report.json` . My script is in my scratch dir and applies the PRD definitions to the per-case flags. Every value equals the stored aggregate to full float precision.

| Metric (PRD) | Graph-dense threshold | Direct baseline | Graph dense | Result | `report-summary.md` correct? |
|---|---|---|---|---|---|
| Schema validity | 100%, none silently invalid | 25/25; 1 explicit failure | 8/8; 18 explicit failures; 0 silently invalid | **MET** | Yes |
| Field accuracy | ≥ 90% and ≥ baseline − 5 pp | 24/58 = 41.38% | 16/58 = 27.59% (13.79 pp below) | **MISSED** (both conditions) | Yes |
| Abstention | ≥ 95% | 3/7 = 42.86% | 0/7 = 0.00% | **MISSED** | Yes |
| Fabricated evidence | 0 | 0 (25 supported, 13 unresolved checks) | 0 (9 supported, 11 unresolved) | **MET** | Yes; the "grounded" wording is now corrected |
| Evidence resolution | ≥ 80% and ≥ baseline | 16/24 = 66.67% | 8/16 = 50.00% | **MISSED** (both conditions) | Yes |
| Context budget | 0 calls over 4,096 | 0 (max reserved 1,191) | 0 (max reserved 2,735) | **MET**, for completed runs. The measured-run log `artifacts/qualification/report-run.log` shows only `incomplete_response` ×96 and `invalid_response` ×12 skeleton rejections. It shows no budget, context or deadline rejection, which supports the summary's H1 note. | Yes |
| Latency p95 | ≤ 120 s and ≤ 3× baseline | 1.481 s (n = 25, nearest rank) | 9.844 s (n = 8, completed only); the limit is min(120, 4.444) = 4.444 s; the ratio is 6.65× | **MISSED** (relative limit) | Yes |
| Review workload | ≤ 1.25× baseline per document | 38/13 = 2.923 | 20/13 = 1.538 (0.53×) | **MISSED like for like**: per completed run 2.50 vs 1.52 = **1.645×**; on the 7 commonly completed cases 17 vs 12 = **1.42×** | Verdict yes. The "1.64–1.67×" range should read "1.42–1.64×" (R2-01) |
| Recovery | 0 reconversions after publication; 0 duplicate effects | — | — | **MET** from the round-2 S0002 lanes: 10/10 provider faults, 4/4 kill points and storage ×1 have single effects, with 0 conversions after publication; storage ×2 has 2 conversions and ends `failed`. | Mostly. The competing-worker lane does not assert single effects (R2-07) |

**Outcome:** five thresholds are MISSED: accuracy, abstention, evidence resolution and latency, plus review workload read like for like. The summary's outcome line, "five thresholds missed", is correct.

## Corpus Integrity

| Check | Result |
|---|---|
| `sha256sum -c` of `artifacts/qualification/CORPUS-HASHES.txt` , run inside `neuron/fixtures/qualification/` | 26/26 OK (13 PDFs, 13 expectation files) |
| Run-folder copy vs fixture copy | Byte-identical; sha256 `fbc5e263c861…2dc9`, which equals `report.json corpus` |
| Files changed since the hashes were written | None (`find -newer` is empty) |
| Committed | **No.** `neuron/fixtures/qualification/` is still untracked. S0004-AC1 "when it is committed" is unmet, and F-05 remains open. |

## Round-1 Finding Closure

| Round-1 finding | Status | Evidence | What remains |
|---|---|---|---|
| F-01 (High), S0003-AC4 not proven | **Closed** | `neuron/tests/integration/test_interpretation_rejections.py` `::test_relationship_output_fails_closed_with_no_assertions[direct-baseline]` and `[graph-direct]` pass in `artifacts/test-results/g2r-neuron-full.xml` . They assert `status == failed`, an `unsupported_output` warning, and no assertions, relationships or entities. Coverage hits: `graph_interpretation.py` lines 83, 89 and 198–201. `test-execution-report.md` no longer claims the live probe proves it. | Low (R2-02): the dense contract is not exercised. The job-level bridge `document_worker.py` line 357 has 0 hits, and the foreign-type branch (line 86) has 0 hits. |
| S0003-AC3, not proven | **Closed** | `test_live_reinterpretation_qualification.py::test_both_profiles_reinterpret_saved_json_with_zero_conversion` lines 111–115 → `artifacts/test-results/g2r-live-reinterpretation.log` : on all 8 completed runs, the run files include `provenance.json` and `graph.json` ; the ledger ref is the run's `provenance.json` ; and the ledger item refs are non-empty and a subset of the saved DoclingDocument's `self_ref`s. | "Graph IDs never become enterprise identity" is not asserted (Low; covered structurally by the importer). |
| F-06, kill lane stale | **Closed** | `artifacts/test-results/g2r-live-kill-points-and-competing-workers.xml` ran 23:10–23:23, 5/5 passed. The last product-source edit was 22:41:37 (`openai_compatible_adapter.py` ). | — |
| F-02, S0001-AC2 partly proven | **Closed (substantively)** | `extraction_quality.ocr` is added on v1 and v2 (ADR-0073 amendment). `test_live_conversion_qualification.py` lines 76–88 → `artifacts/test-results/g2r-live-conversion.log` : all 13 bundles record engine `RapidOcrModel` 3.9.2, 3 asset digests, the OCR page count and the pages; scanned documents OCR every page. | R2-03: "OCR page count" semantics |
| F-03, review workload | **Closed** | The `report-summary.md` row now reads MISSED like for like | R2-01: the 1.67× figure |
| F-04, no predicted values | **Open** | `score_case` still keeps only booleans and counts (`f0005_qualification.py` lines 518–540) | Carry forward to any re-measurement |
| F-05, corpus not committed; batch-stamped `commands.log` | **Open** | The corpus is still untracked. The round-2 entries in `commands.log` are all stamped 22:46:45 or 23:54:10, and there is no corpus-generation entry. | Disclosed by the authors |
| F-07, calls and rejections of failed attempts not reported | **Closed for future runs** | Harness lines 491–507 and 596–597 record rejections. The recorded report is unchanged (see Retries) | — |
| F-08, gl-q-004 convention | **Open** (by design) | Fixing it requires re-hashing and re-measuring | For any re-plan |
| F-09, loose assertions | **Partly closed** | The decision-branch engine is now asserted whatever the outcome (`test_pipeline_selection.py` lines 159–174) | These remain: `test_fault_injection_qualification.py` line 88 `assertion_runs <= 1`; line 314 cancellation `<= 2`; and the conditional identity check at `test_live_reinterpretation_qualification.py` line 138. The conditional did execute this time, because both profiles completed for gl-q-004, 006 and 007. |
| F-10, summary wording | **Closed** | "Grounded" corrected; storage ×2 has 2 conversions | — |
| F-11, baseline without tables; strict dense policy | **Closed** | Recorded in ADR-0060's qualification-outcome section | — |

## Acceptance Criteria Verdicts

"Live" means the opt-in lane against the real vLLM, Docling and PostgreSQL. All round-2 live lanes ran 22:50–23:41 on 2026-10-27, after the last product edit at 22:41:37.

| AC | Verdict | Evidence (test :: case → raw) | QA notes |
|---|---|---|---|
| S0001-AC1 pins | Partly proven (unchanged) | `report.json pins`; `uv.lock` | No negative test fails a pin mismatch before conversion |
| S0001-AC2 bundle identities | **Proven** | `test_live_conversion_qualification.py::test_every_corpus_document_publishes_before_the_first_model_request` → `artifacts/test-results/g2r-live-conversion.log` (13 rows) and `g2r-live-conversion.xml` (2/2). Offline: `neuron/packages/brain-ingestion/tests/test_ocr_quality.py` (10/10) | Asserted live: source sha256, `docling==2.126.0`, page count, OCR engine name, `ocr.page_count == len(ocr.pages)`, 3 asset digests, failed pages (gl-q-013 `[2]`), and every scanned page OCR'd. Parser configuration (`configuration_hash`) and `warnings` are required fields of the `extra=forbid` manifest, so `load_verified` enforces their presence; neither value is asserted. The OCR engine version is printed (3.9.2 ×13) but not asserted. See R2-03 on what the native-page count means. |
| S0001-AC3 checkpoint before model | Proven | same test: `model_unavailable`, `retry`, ready bundle, 13 launches, `proxy.records == []` | |
| S0001-AC4 partial | Proven | same test: gl-q-013 `partial`, failed pages `[2]` | |
| S0001-AC5 stage guard | Partly proven (unchanged) | `::test_installed_stage_layout_mismatch_raises_before_extraction_and_registers_nothing` (live); `test_document_worker_reasons.py` `[1-stage_guard_mismatch-fail]` | No end-to-end job ends `stage_guard_mismatch` with nothing ready; the checkpoint-callback failure is not exercised live |
| S0001-AC6 / S0002-AC7 / S0003-AC7 / S0004-AC8 / S0005-AC6 audit | **Partly proven** (unchanged) | `engine/.../test_job_event_reason_migration.py` (0009/0010, 8 cases); `test_queue.py` reason tests; `AuditEventRow` denial in the revocation test | No test asserts a single record carrying actor, job, correlation, attempt, artifact/run reference, outcome and timestamp, or asserts that secrets and source text are absent. The authors agree. |
| S0002-AC1 provider faults | Proven | `test_fault_injection_qualification.py::test_provider_fault_records_distinct_reason_and_resumes_from_saved_json` with 5 modes × 2 engines → `artifacts/test-results/g2r-live-provider-storage-auth-faults.log` (8) and `g2r-live-timeout-faults.log` (2) | All 10 cases end `complete`: the first reason is distinct, there is 1 conversion, single effects, and `max_concurrency` 1. The test's `failed` fallback branch (lines 167–171) predates round 2 and was not taken. |
| S0002-AC2 kill points | **Proven** | `::test_worker_killed_at_each_point_recovers_with_single_effects[bundle,run,import,imported]` → `artifacts/test-results/g2r-live-kill-points-and-competing-workers.log` | Each point ends with 1 ready artifact, 1 run, 3 assertions in 1 run, 1 acknowledgement, 1 complete job, and 0 conversions by the replacement. The replacement made 0 requests after `run`/`import`/`imported`, and 2 after `bundle` (expected). The assertion is still `<= 1` (R2-06); the observed value is 1. |
| S0002-AC3 storage | **Partly proven** | `::test_storage_failure_before_marker_is_never_ready_and_reconverts_at_most_once[1,2]` → `g2r-live-provider-storage-auth-faults.log` | "At most 2 conversions" is proven: ×1 → 2 conversions, `complete`, 1 ready; ×2 → **exactly 2** conversions, `failed`, 0 ready, reasons `storage_write_failed` ×2. Offline, `test_document_worker_reasons.py[2-conversion_timeout-fail]` covers the durable launch count for a crash mid-publication. Not proven live: a *crash* before the completion marker, and cleanup of the partial objects. |
| S0002-AC4 duplicates / competing / leases / cancellation / concurrency | **Partly proven** | `::test_second_worker_is_refused_and_killed_holder_requires_confirmed_quiescence` (live, round 2: B refused with `inference_guard_busy`; A killed while the provider was busy, `busy_at(killed)` asserted; B refused with `provider_quiescence_required`, 0 claims, 0 requests; provider busy at quiescence; quiescence 91 s; `max_concurrency` 1 over 29 requests); `::test_cancellation_stops_scheduling_and_temporary_exports_are_removed` (1 request observed); `test_postgres.py::test_postgres_expired_lease_fences_old_worker` and `::test_postgres_fence_uses_time_after_waiting_for_a_lock` | Proven: competing workers, lease fencing, cancellation, and provider concurrency ≤ 1. That includes Graph-dense runs of 5 sequential calls measured at the proxy, which covers internal fan-out in practice. Not proven: duplicate submissions are idempotent only in the SQLite unit test `test_queue.py::test_duplicate_key_is_idempotent_and_conflicting_payload_is_rejected`, with no PostgreSQL or live case. The cancellation assertion is still `<= 2`. |
| S0002-AC5 tenant / revocation | Partly proven (unchanged) | `::test_revoked_grant_between_attempts_denies_audits_and_stops` | Not exercised: a different tenant, an inactive principal, and reader paths |
| S0002-AC6 temp exports and scope | Partly proven (unchanged) | cancellation test | Only the cancelled path is checked; retention parity is not asserted |
| S0003-AC1 saved JSON only | Partly proven | `test_live_reinterpretation_qualification.py::test_both_profiles_reinterpret_saved_json_with_zero_conversion` → `artifacts/test-results/g2r-live-reinterpretation.log` | Zero conversions; `SupervisedConverter.convert`, `DoclingAdapter.parse` and `RapidOcrModel.__call__` are forbidden; bundle digests are unchanged; 13 publications. Per-profile identities are disjoint. The tokenizer, chunking and template identities are not asserted individually. 8/26 runs completed (the same 8 as the measurement). |
| S0003-AC2 evidence | Partly proven (unchanged) | same test, `fabricated == 0` on 8 runs | Repeated, ambiguous and multi-region values are not asserted as such |
| S0003-AC3 provenance retained | **Proven** | same test, lines 111–115; harness `score_case` lines 455–469 | 8/8 completed runs; see closure table |
| S0003-AC4 unsupported output | **Proven (offline, service boundary)** | `test_interpretation_rejections.py::test_relationship_output_fails_closed_with_no_assertions[direct-baseline,graph-direct]`; the worker maps it to terminal in `test_document_worker_reasons.py[1-unsupported_output-fail]` | R2-02. The live probe ended `model_malformed_output` ×3 again, and the report now says so honestly. |
| S0003-AC5 budgets | Proven | the reinterpretation test (max 2,735 ≤ 4,096); `report.json` (0 over budget); `test_interpretation_rejections.py::test_a_budget_rejection_before_dispatch_fails_the_run` (H1) | |
| S0003-AC6 targeting | Proven | `::test_targeted_request_fails_before_any_model_call` | |
| S0004-AC1 corpus | Partly proven | Corpus Integrity above | Not committed (F-05) |
| S0004-AC2 report | Proven | `report.json` | F-04 caveat |
| S0004-AC3 thresholds marked | Proven | `report-summary.md` , plus this recomputation | R2-01 is a wording fix with no outcome change |
| S0004-AC4 verdicts | This file (QA) | — | Architect, Security and the operator are recorded separately |
| S0004-AC5 activation | Not reachable (correctly) | thresholds missed | |
| S0004-AC6 rollback | Proven (isolated configuration) | `test_pipeline_selection.py::test_decision_branches_restart_and_new_sources_use_the_selected_engine_and_writer` → `artifacts/test-results/g2r-live-decision-branches.log` (11/11) | Rollback runs with the direct-baseline engine; earlier digests are unchanged; the v2 bundle (gl-q-009) reads back; no Graph call phase on direct-baseline branches; the legacy job keeps graph-direct |
| S0004-AC7 rejection closure | Partly proven (pending the operator record) | `::test_committed_configuration_selects_the_direct_baseline_with_v2_disabled`; `config/local.yaml` (`pipeline: direct-baseline`, `v2_writer_enabled: false`); the ADR-0060 qualification outcome (stays Proposed) | |
| S0005-AC1 per-item origin | Partly proven (unchanged) | live conversion: OCR producer only on gl-q-009 | `STATED` with producer is not asserted live for native items |
| S0005-AC2 OCR asset identity | Proven | `test_ocr_asset_provenance.py` ; 3 pinned digests on all 13 live bundles | |
| S0005-AC3 v1 fallback audited, rate reported | **Partly proven** (unchanged) | `report.json bundle_contract`: 11/13 = 84.6% fallback | No corpus-level assertion of `writer_fallback_reason = ORIGIN_UNAVAILABLE` or of its audit event; a search of the F0005 live tests and the harness finds none |
| S0005-AC4 consumers read v2 | **Partly proven** (unchanged) | the evidence reader, importer and Graph saved-JSON path in the harness over gl-q-005/009; the decision-branch v2 read-back; F0004 suites | The authorized content reader and the restore drill are not run over corpus v2 bundles |
| S0005-AC5 writer switch | Not reachable (correctly) | | |

## Retries And Reruns

1. **The first live attempt (22:45–22:55) had 6 failing lanes. This was a cascade, not six defects.**
   - The attempt-1 provider-fault log (`artifacts/test-results/g2r-attempt1/g2r-live-provider-storage-auth-faults.log` ) shows `graph-dense/stopped` failing inside `live.drain`.
   - A normal Graph-dense call hit the 10 s client timeout (`InferenceRejected: provider_timeout`). The guard then went uncertain, and every later case and lane was refused with `provider_quiescence_required`. The reinterpretation, kill, timeout and decision lanes all fail at `live_session` setup with that code.
   - This is the guard behaving correctly: it fails closed on an uncertain request.
2. **The fault timeout change from 10 s to 30 s is a legitimate test correction. It is not a relaxation.**
   - The production request timeout is 60 s (`report.json requested_configuration.limits`), so 10 s was below a normal dense call. In round 2, record 1 of `graph-dense/stopped` took 8.3 s upstream, and the measured dense p95 is 9.8 s.
   - 30 s is still below production, and the `timeout` mode still forces a genuine client timeout against a busy provider. In `direct-baseline/timeout` the upstream request ran 90 s and was ended by quiescence (status 599). In `graph-dense/timeout` it ended at 30.2 s, at about the moment quiescence must have started, having been confirmed busy at the timeout and at quiescence.
   - Comparing the test source pytest printed in the three attempt-1 fault logs with the current file, the only test line that differs is `limits=InferenceLimits(request_timeout_seconds=10)`. Two comment lines were also added.
   - Round 2 *adds* the assertions `proxy.busy_at(timed_out)` (line 143) and `busy_at(killed)` (line 492), which tighten M4. The `failed` fallback branch is already present in the round-1 source printed in `artifacts/test-results/live-timeout-faults.log` .
   - The test file mtime is 22:56:04: after attempt 1 ended and before the re-run started at 22:57. No product source changed between the attempts.
3. **The native-document OCR assertion was relaxed to "observed pages are valid". This is legitimate, but under-justified.**
   - The attempt-1 conversion log was overwritten. Only `artifacts/test-results/g2r-attempt1/summary.log` (1 failed) remains, so the old assertion is not recoverable from evidence.
   - I checked the claim independently. The native PDFs gl-q-002, 003, 004 and 006 report OCR pages, yet pdfium finds **zero image objects** on any of their pages. The test comment's rationale, "Docling also OCRs bitmap regions (logos, stamps)", is therefore false for this corpus.
   - The real cause is in Docling 2.126 `models/base_ocr_model.py` lines 191–199. In DEFAULT mode, OCR runs on layout clusters that overlap a non-text region, "e.g. bitmap, shape", and these documents contain vector boxes and shaded table rows.
   - So the product observation is genuine, and "native never OCRs" was a wrong test assumption.
   - However, the observer at `item_provenance.py` line 125 counts a page when OCR *emits* cells, before the PDF_FIRST merge discards cells that duplicate the text layer. The count therefore means "pages OCR ran on", not "pages whose content is OCR-derived".
   - The relaxed assertion (`test_live_conversion_qualification.py` line 86) would not catch over-counting. Scanned documents keep the strict every-page check, and nothing checks the image page of the mixed documents.
   - This does not affect S0001-AC2's recording obligation or the rejection. It needs a defined semantic (R2-03).
4. **The H1 and M6 harness changes leave the recorded report untouched and interpretable.**
   - `report.json` is byte-identical to the round-1 Architect's hash. The harness file mtime is 2026-10-27 22:36, after the report (2026-10-26 01:27), and the harness refuses to overwrite an existing output.
   - The recorded `latency_p95_seconds` is a completed-only p95. I recomputed it from the 8 completed `latency_seconds` rows, and failed rows carry no latency, so the value cannot be misread as all-attempt.
   - The new `review_items_per_completed_run` reproduces my like-for-like 1.645×.
   - Defect for future reports: the harness now writes all-attempt p95 under the **same key**, with `report_version` still `1` (`f0005_qualification.py` line 738) and unchanged `metric_definitions` text. A future report would therefore be indistinguishable from this one (R2-04).
5. **The 300 s deadline lane** passed in attempt 1 and was not repeated. `g2r-live-production-deadline.xml` is identical to the attempt-1 copy, and it ran on the corrected test file (mtime 22:48:47, before the lane started at 22:50:01).
6. **The live lanes were driven by an unretained scratch script** (`<scratch>/live-rework.sh` in `commands.log` ). The JUnit timestamps and the attempt-1 `summary.log` corroborate the ordering.

## Findings

| ID | Severity | Location | Finding | Recommendation |
|---|---|---|---|---|
| R2-01 | Low | `planning-mds/operations/evidence/runs/2026-10-25-4020923b/artifacts/qualification/report-summary.md:19` ; `planning-mds/architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md:116` | "1.64–1.67×" like for like. The 1.67× figure came from my round-1 error (8 shared cases); only 7 cases completed on both engines (gl-q-010/b failed on the baseline), giving 17/12 = 1.42×. Still MISSED. | Change it to "1.42× on the 7 commonly completed cases; 1.64× per completed run". |
| R2-02 | Low | `neuron/tests/integration/test_interpretation_rejections.py:166` ; `neuron/packages/brain-ingestion/src/brain_ingestion/document_worker.py:357` ; `neuron/packages/brain-extraction/src/brain_extraction/graph_interpretation.py:86` | The S0003-AC4 test covers `direct-baseline` and `graph-direct`, not the `graph-dense` candidate. The worker bridge from the warning to `AttemptFailed("unsupported_output")` has 0 coverage hits, and the foreign-entity-type branch has 0 hits. | Add one worker-level case that asserts the job reason `unsupported_output`, plus a dense-contract and foreign-type case. This is needed before any re-plan that could activate dense. |
| R2-03 | Low | `neuron/packages/brain-ingestion/src/brain_ingestion/item_provenance.py:125` ; `neuron/tests/integration/test_live_conversion_qualification.py:84-86` | "OCR page count" counts pages where OCR emitted cells before the PDF_FIRST merge, so native pages with shapes count even when no OCR text survives. The test's "bitmap regions (logos, stamps)" rationale is factually wrong for this corpus (0 image objects on natives 002/003/004/006), and the relaxed assertion cannot detect over-counting. | Architect: define the semantic in the ADR-0073 amendment (OCR ran, versus OCR-derived content). QE: assert expected OCR pages per document from the corpus layout, including the image page of the mixed documents, and correct the comment and the `test-execution-report.md` wording. |
| R2-04 | Low | `neuron/benchmarks/f0005_qualification.py:598` ; `neuron/benchmarks/f0005_qualification.py:738` | `latency_p95_seconds` changed meaning (completed-only → all-attempt), but `report_version` stays 1 and `metric_definitions` is unchanged. | Bump `report_version` to 2 and spell out each metric's population in `metric_definitions` before any re-measurement. |
| R2-05 | Low | `neuron/tests/integration/test_fault_injection_qualification.py:150-153` | The timeout timeline records the quiescence duration but not its start and end. The Graph-dense "busy at quiescence" claim rests on a margin of about 0.2 s, reconstructed from the upstream end at 30.2 s with status 200. | Record `quiesce_started` and `quiesce_finished` in the printed timeline, together with the upstream end status. |
| R2-06 | Low | `neuron/tests/integration/test_fault_injection_qualification.py:88` ; `neuron/tests/integration/test_fault_injection_qualification.py:314` ; `neuron/tests/integration/test_live_reinterpretation_qualification.py:138` | Carried from F-09: `assertion_runs <= 1`, cancellation `<= 2`, and the conditional identity check. The observed values were stricter. | Tighten to `== 1`, `== 1` and an unconditional check. |
| R2-07 | Low | `planning-mds/operations/evidence/runs/2026-10-25-4020923b/artifacts/qualification/report-summary.md:20` | The Recovery row says every "competing worker ended with single accepted effects". That lane asserts no claim before quiescence and concurrency ≤ 1, not single effects; 3/5 jobs failed organically. | Reword the row, or add a single-effect assertion over the completed jobs. |
| R2-08 | Medium | `neuron/fixtures/qualification/` (untracked); `planning-mds/operations/evidence/runs/2026-10-25-4020923b/commands.log` ; `neuron/benchmarks/f0005_qualification.py:518-540` | Carried F-05 and F-04: the corpus is not committed; `commands.log` is batch-stamped and has no corpus-generation entry; predicted values are not retained. | Commit the corpus ahead of the report; stamp commands at execution time; retain predictions in any future report. |
| R2-09 | Low | `neuron/tests/integration/test_content_worker_v2.py` | The `[False]` failure is called "identical on clean HEAD", but only an engine HEAD baseline artifact exists (`artifacts/test-results/head-baseline-engine-full.log` ). The file is also modified on this branch (`pipeline="graph-direct"`). | Attach a neuron HEAD-baseline run of this test, or log it as a tracked follow-up with that evidence. |
| R2-10 | Info | the carried partly-proven ACs above | The audit ACs, S0002-AC3 (crash before marker, cleanup), S0002-AC4 (duplicates), S0002-AC5/AC6, S0003-AC1/AC2, and S0005-AC1/AC3/AC4 remain partly proven, as the authors disclose. | STATUS must not tick them as verified. |

Recommendations, in the consumer-contract format:

- [medium] The corpus is uncommitted, `commands.log` is batch-stamped, and predictions are not retained (R2-08) — owner: Quality Engineer; follow-up: commit the corpus before the report commit and fix the harness before any re-measurement.
- [low] The like-for-like review-workload figure (R2-01) — owner: Quality Engineer, with the Architect for ADR-0060; follow-up: correct the two lines; no outcome change.
- [low] The OCR page-count semantic and the native assertion (R2-03) — owner: Architect, then Quality Engineer; follow-up: define the semantic in the ADR-0073 amendment and tighten the live assertion.
- [low] R2-02 and R2-04 to R2-07, R2-09 — owner: Quality Engineer; follow-up: next test and harness revision, before any re-plan that could activate Graph dense.

## S0004-AC4 QA Verdict

- **Report validity.**
  - The measured report is unchanged since round 1 (hash verified), `void=false`, and recomputes exactly from its per-case rows.
  - The corpus is hash-intact.
  - The round-2 harness changes alter no recorded value. They do need a version bump before reuse (R2-04).
- **Thresholds.** Graph dense **misses** field accuracy (27.6%), abstention (0%), evidence resolution (50.0%), relative latency (6.65×) and, like for like, review workload (1.42–1.64×). No caveat in this review reverses any of these misses.
- **Round-2 evidence quality.**
  - The rework closes the blocking round-1 gaps: S0003-AC4 offline, S0003-AC3 live, the S0002-AC2/AC4 kill and competing-worker lane re-run on the final code, the S0002-AC3 two-conversion bound, and the S0001-AC2 OCR fields.
  - Both first-attempt corrections are legitimate test fixes. Neither relaxes a budget, threshold or product rule.
  - The remaining gaps are disclosed partial proofs and Low or Medium hygiene items.
- **Permitted outcome.** The evidence permits the operator to record **rejection** only. Under S0004-AC3/AC7:
  - `extraction.pipeline: direct-baseline` stays the default;
  - `content.v2_writer_enabled: false` stays;
  - ADR-0060 records the failed gates (it stays Proposed, with a reopen condition);
  - no partial activation remains.

  `config/local.yaml` already holds these values. Activation under S0004-AC5 and S0005-AC5 is **not permitted**.
- **ACs that must not be ticked as verified:** the partly-proven ACs in R2-10. These are S0001-AC1/AC5, S0002-AC3/AC4/AC5/AC6, S0003-AC1/AC2, S0004-AC1/AC7 (pending the operator record), S0005-AC1/AC3/AC4, and all five audit ACs.

Result: PASS WITH RECOMMENDATIONS
