# Feature Code Review Report — F0005-one-time-docling-ingestion run 2026-10-25-4020923b (G3 round 2)

Feature: F0005 — One-time document ingestion

Reviewer: independent Code Reviewer session with a fresh context. I did not author the code, the corpus, the expectations or any evidence. Reviewed on 2026-10-28 against the uncommitted working tree on `feature/f0005-live-qualification`, using `git diff` plus untracked files and excluding the run folder. Round-1 report: `code-review-report-round1.md`. The G4 rework scope comes from the operator row in `gate-decisions.md` (2026-10-27T22:12:58).

Result: APPROVED WITH RECOMMENDATIONS

## Summary

- Assessment: **APPROVED WITH RECOMMENDATIONS**.
  - C1 and H1 are closed in code and covered by tests: offline unit tests, real Graph 1.9.1 tests over a recorded transport, and the live conversion lane.
  - M1, M3, M4, M5 and M6 are closed. M2 is closed for the round-1 scenario, but a two-fault variant remains (N1, Medium).
  - No Critical or High defect remains. The new findings are one Medium and four Low. None can publish a wrong result: each fails closed, with an extra reconversion or a misattributed or terminal reason.
- Files reviewed: 43. That covers:
  - 19 runtime modules;
  - migrations 0009 and 0010;
  - `config/local.yaml` and the four manifest schema copies;
  - 15 test modules and the support modules (fault proxy, relationship probe, live support);
  - the harness `neuron/benchmarks/f0005_qualification.py`;
  - ADR-0073 §6, ADR-0074 and the ADR-0060 outcome.
  The canonical changed-file list is `artifacts/diffs/changed-files.txt` .
- Issues found: Critical 0, High 0, Medium 1, Low 4.

## Round-1 Finding Closure

| Round-1 finding | Status | Evidence (code and test) |
|---|---|---|
| C1 — OCR page count and engine missing from the bundle | **Closed** | `ExtractionQuality.ocr` (`engine/packages/brain-content/src/brain_content/manifest.py:47-75`) is optional and add-only, with a validator for page count = len(pages). It is written on both paths: v1 at `bundle_writer.py:30-47` and `:185`, v2 at `content_projection.py:248-252`. `OcrObserver` (`item_provenance.py:113-132`) records the pages where the running engine actually produced OCR cells, on every conversion (`docling_adapter.py:42-46`, `:62`, `:101-102`). The data survives the child handoff (`conversion_process.py:139-155`). v1 also gets the OCR asset digests (`bundle_writer.py:177`). The repo and package schema copies are identical (I diffed them). Tests: `neuron/packages/brain-ingestion/tests/test_ocr_quality.py:43,64,75,95,110,126` (I re-ran them: pass). Live: `artifacts/test-results/g2r-live-conversion.log` shows every corpus row with `ocr_page_count`, `ocr_pages` and the engine `RapidOcrModel 3.9.2`; the scanned gl-q-007/008/010 rows are v1 with 2 OCR pages each. The contract change is recorded in ADR-0073 §6. |
| H1 — dense run can complete around rejected or fallback calls | **Closed** | Every pre-record rejection is now recorded in `_rejections` before re-raising (`vllm_graph_client.py:248-266`). In-call rejections carry a `failure_class` (`:414-423`). The acceptance rule fails the run on any rejection or non-`complete` call (`graph_interpretation.py:207-216`). Any non-`dense_*` call phase in a dense run fails it with `dense_contract_fallback` (`:217-225`). The worker maps these to the reasons `model_budget_exceeded`, `model_deadline_exceeded` and `model_contract_fallback` (`document_worker.py:56-66`, `:107-118`, `:355-366`), which are in the migration 0010 CHECK. Tests: `neuron/tests/integration/test_interpretation_rejections.py:132` (empty skeleton, so dense falls back to `direct_extraction` and the run fails) and `:143` (`call_budget_exceeded` before dispatch, so the run fails). Both use real Graph 1.9.1 and the real SDK client over a mock transport. Also `test_document_worker_reasons.py:88,105`. The harness counts `context_rejections` from `rejections` (`f0005_qualification.py:491-507`). Residual: L-N2 (a token-counter exception escapes unrecorded). |
| M1 — post-publication errors counted as `conversion_failed` | **Closed** | `_published` is set after `load_or_convert_content` (`document_worker.py:279`). After it, any pre-publication reason becomes `interpretation_failed` (`:225-228`), which is retryable and never counts as a conversion. The model sub-reasons are now distinct (`:56-66`). Tests: `test_document_worker_reasons.py:324,339`. |
| M2 — reconvert-at-most-once across crash plus storage failure | **Partly** | The round-1 scenario is fixed. Launches are recorded durably (`queue.py` `conversion_started` / `conversion_launches`, called at `content_workflow.py:186-187`). `_record_failure` makes a pre-publication failure terminal at 2 or more launches (`document_worker.py:241-250`). Test: `test_document_worker_reasons.py:246` (parametrised). **Not closed:** the count is checked only after a failure, never before a launch. Two pre-publication faults that record no reason still allow a third conversion. See N1. |
| M3 — guard infrastructure fault drains the queue | **Closed** | `inflight_marker_not_durable` is detected as a guard fault and raises `WorkerStopped`, so no reason is recorded and the job is left for reclaim (`document_worker.py:67-68`, `:121-126`, `:214-217`, `:353-354`). `_atomic_write` unlinks its temporary file on failure (`worker_guard.py:128-133`). Tests: `test_document_worker_reasons.py:114,346`; `test_worker_guard.py:203`. Residual: L-N3 (a stale marker left by a failed clear is not treated as a guard fault). |
| M4 — fault proxy never kept the provider busy | **Closed** | In `timeout` mode the proxy forwards a fixed 3,800-token generation with `ignore_eos` (`neuron/tests/support/fault_proxy.py:23-27`, `:103-114`). `busy_at` is asserted at the timeout and the kill (`test_fault_injection_qualification.py:143`, `:492`), with `max_concurrency() <= 1` (`:191`, `:507`, `:532`). Live: `artifacts/test-results/g2r-live-timeout-faults.log` and `artifacts/test-results/g2r-live-kill-points-and-competing-workers.log` both record `provider_busy_at_quiescence: true` and `max_concurrency: 1` (5/5 and 2/2 pass). |
| M5 — decision-branch test skips engine checks on failure | **Closed** | `test_pipeline_selection.py:157-185` checks engine identity whatever the outcome. It also checks that baseline jobs make no Graph call (`dense_*` / `direct_extraction`), that a fallback records a `model_*` reason, and that v2 bundles stay readable in the accepted and rollback branches (`load_verified`). Live: `artifacts/test-results/g2r-live-decision-branches.xml` (11/11). |
| M6 — harness latency counts only the surviving attempt | **Closed** | Attempt times are summed per job, and the headline p95 is taken over all document-profiles. The completed-only p95 is kept as a secondary figure (`f0005_qualification.py:596-600`, `:650-669`). |
| L1 — asset "revision" is the package version | **Closed** | Documented in ADR-0073 §6 (last bullet). |
| L2 — baseline copies the F0001 prompt | **Closed** | `baseline_prompt` is a single source shared by both callers (`openai_compatible_adapter.py:41-52`, `:133`; `graph_interpretation.py:60`). The test `test_interpretation_rejections.py:182` pins the prompt sent. |
| L3 — PID-reuse receipt across reboot; tmpfiles aging | **Partly** | The runbook warns about `/tmp` cleanup (`docker/local-inference-runbook.md:132`). There is still no `boot_id` in the receipt. The operator ordered no fix; it is carried as a recommendation. |
| L4 — guard released after `converter_cleanup_unconfirmed` | **Closed** (documented) | The behaviour and the fail-closed startup reaper are documented in `docker/local-inference-runbook.md:132`. |
| L5 — queue-bound race leaves orphan source objects | **Partly** (accepted limitation) | Recorded as a known limit in ADR-0074 §4. No sweep yet. |
| L6 — missing `# WHY:` tags | **Open** (deferred) | Not in the G4 rework scope. Carried as a recommendation for G7 decision indexing. |

## Per-Story Verdicts

| Story | Verdict | Basis / evidence |
|---|---|---|
| F0005-S0001 | **PASS** | AC2 is now met (C1 closed): `artifacts/test-results/g2r-live-conversion.log` (2/2) and `test_ocr_quality.py` . AC1 and AC3–AC6 are unchanged from round 1 and still pass: `artifacts/test-results/g2r-live-production-deadline.xml` (1/1) and `test_conversion_process.py` . |
| F0005-S0002 | **PASS** (recommendation N1) | `artifacts/test-results/g2r-live-provider-storage-auth-faults.xml` (12/12), `artifacts/test-results/g2r-live-timeout-faults.xml` (2/2), `artifacts/test-results/g2r-live-kill-points-and-competing-workers.xml` (5/5), and `test_document_worker_reasons.py` . The AC3 single-fault cases are met; the two-fault case is N1. |
| F0005-S0003 | **PASS** | H1 is closed. `artifacts/test-results/g2r-live-reinterpretation.xml` (3/3). AC4 is now deterministic in `test_interpretation_rejections.py:167`. |
| F0005-S0004 | **PASS** for code scope | Selection, pinning, rollback and legacy meaning: `artifacts/test-results/g2r-live-decision-branches.xml` (11/11). Committed config is `direct-baseline` with v2 off (`config/local.yaml:8-16`). AC4 and AC7 need reviewer verdicts and the operator decision; AC5 cannot be reached because Graph dense was rejected. |
| F0005-S0005 | **PASS** | `test_ocr_asset_provenance.py` . Engine identity follows one rule (`identify_ocr_engine`, `item_provenance.py:84-108`), shared by item origins and the bundle block. 11/13 documents fall back to v1, which is reported. |

## Independent Verification Performed

- Offline neuron run, with the PostgreSQL URLs:
  - Scope: `packages/brain-ingestion/tests`, `test_interpretation_rejections.py`, `test_pipeline_selection.py`, `test_worker_cli_enqueue.py`, `test_vllm_graph_client.py`, `test_fault_injection_qualification.py` and `test_content_worker_v2.py`.
  - Result: **194 passed, 20 skipped** (live-only), **1 failed**. The failure is `test_content_worker_v2.py::test_publication_import_and_second_profile_reuse[False]` (content-block count 1 ≠ 2, Docling merging fixture lines on this host). It is pre-existing and disclosed. The only F0005 edit to that test adds `pipeline="graph-direct"`.
- Offline engine run: `packages/brain-jobs/tests`, `brain-content/tests/test_config.py`, `test_job_event_reason_migration.py` and `test_content_migration_states.py`. Result: **83 passed**.
- Raw XML totals match the authors' claims:
  - `artifacts/test-results/g2r-neuron-full.xml` : 265 tests, 1 failure, 29 skipped.
  - `artifacts/test-results/g2r-engine-full.xml` : 435 tests, 11 failures, all pre-existing authx.
  - All seven `g2r-live-*` XMLs: 0 failures.
- Changed-line coverage is 83.1% (1,073/1,291) in `artifacts/coverage/changed-line-coverage.md` , which matches `coverage-report.md`.
- The pypdf pin is 6.21.2 in `neuron/uv.lock`, with floor `>=6.21.2`. `artifacts/security/g2r/dependency-neuron.json` lists pypdf 6.21.2 with no vulnerabilities.
- Upstream check (read-only, installed Graph 1.9.1): dense calls use the phases `dense_skeleton`, `dense_fill`, `dense_reconcile` and `dense_root_identity`. The fallback uses `direct_extraction`. The only other model call is `alias_reconcile` in graph conversion, which a flat single-node template does not trigger. So the fallback rule at `graph_interpretation.py:217-225` is sound for the qualified profiles.
- KG: the symbol check (`validate.py --check-symbols`, read-only) passes. Symbol regeneration for the new modules belongs to G7.

## Vertical Slice Completeness

- [x] Backend complete: reasons, migrations 0009 and 0010, depth bound, worker, guard, supervisor and conversion child. F0005 has no API endpoint.
- [x] Frontend: not in scope (the PRD has no UI).
- [x] AI layer complete: dense result acceptance is now sound (H1), the baseline shares F0001's prompt, and unsupported output fails closed.
- [x] Tests complete: unit, PostgreSQL, real-Graph recorded-transport and seven live lanes.
- [x] Can be deployed independently: committed config is `direct-baseline` with v2 off. Readers and writers of the ADR-0073 §6 field ship together; both are in this repo.

## Findings

### Critical

None.

### High

None.

### Medium

**N1 — "At most one reconversion" is checked only after a failure. Two pre-publication faults that record no reason allow a third conversion.**
- Location: `neuron/packages/brain-ingestion/src/brain_ingestion/content_workflow.py:186-188` and `document_worker.py:241-250`.
- What: `before_conversion` records `conversion_started` and then always launches. `conversion_launches` is consulted only inside `_record_failure`, after an attempt has already failed with a reason.
- Failure scenario:
  - Attempt 1 launches (launch 1), and the worker is SIGKILLed mid-conversion. No reason is recorded and the lease expires.
  - Attempt 2 launches (launch 2) and is killed again, or is killed after a `conversion_timeout` retry. Again no reason is recorded.
  - Attempt 3 calls `load_or_convert_content` and launches **a third conversion**.
  - Example: a document that pushes the host into the OOM killer on every attempt. The bound is only `max_attempts=3`.
- Why it matters: ADR-0074 §3 states "a job converts at most twice (one reconversion) … counted from durable `conversion_started` events … so a crash still counts", and S0002-AC3 says "reconverts at most once". The single-fault cases hold; this two-fault case does not. The extra conversion is wasted work, not unsafe publication.
- Fix: before `before_conversion()`, read `queue.conversion_launches(lease.job_id)`. If it is 2 or more, fail terminally with `conversion_failed` (or the last recorded pre-publication reason) without launching. Add a worker test with `launches=2` and no prior reason, asserting that no conversion starts.

### Low

- **L-N1 — pypdf's own exceptions escape the damaged-page tolerance.**
  - Location: `docling_adapter.py:110-117` and `:69`.
  - `_count_pages_needing_ocr` catches `ValueError`, `KeyError`, `TypeError` and `OSError`, but pypdf raises `PdfReadError` / `PdfStreamError`. Their MRO is `PyPdfError → Exception`, which I checked against the installed 6.21.2.
  - The new `len(PdfReader(...).pages)` at `:69` is also unguarded.
  - Scenario: a content stream that ends early raises `PdfStreamError` in `extract_text`, so the whole parse raises. The job gets `conversion_failed` instead of a `partial` bundle with that page failed, which is the S0001-AC4 intent.
  - Fix: add `PdfReadError` to the tuple and derive `page_total` from Docling's page list when pypdf cannot read it.
- **L-N2 — a token-counter exception is neither recorded nor converted.**
  - Location: `vllm_graph_client.py:302`.
  - `self._counter(...)` runs before the call record exists, and anything it raises other than `InferenceRejected` (a tokenizer `ValueError` or a Jinja template error) leaves `get_json_response` unrecorded.
  - Graph 1.9.1 swallows per-call exceptions, so a dense run can drop that chunk and still complete. This is H1's pattern, through a narrower door.
  - Direct contracts are unaffected (single call, so `output=None`). Graph dense is rejected, so there is no current exposure.
  - Fix: wrap the counter so any exception becomes `InferenceRejected("invalid_token_estimate")`.
- **L-N3 — a stale marker left by a failed clear drains jobs instead of stopping the worker.**
  - Location: `worker_guard.py:325-327` together with `document_worker.py:68` and `:183-187`.
  - If `marker_path.unlink()` or the directory fsync fails after a confirmed response, the marker stays on disk and `guard.uncertain` stays False.
  - Every later dispatch is then refused with `provider_quiescence_required`. That code is classed `unavailable` → `model_unavailable` and is not in `_GUARD_FAULTS`. The worker keeps claiming, and each job is retried until it ends `failed`.
  - Fix: add `provider_quiescence_required` to `_GUARD_FAULTS`, or set `uncertain` when the clear fails; also check `marker_path.exists()` in `run_one`.
- **L-N4 — `usage_exceeds_reservation` is classed as a terminal budget failure, but it signals a provider misconfiguration.**
  - Location: `vllm_graph_client.py:69`, `:380-386`; `document_worker.py:53`.
  - A restarted server with a different tokenizer or chat template, or one that ignores `max_tokens`, makes every job's first call exceed its reservation. Each queued job then fails terminally with `model_budget_exceeded`. Resubmission is idempotent on the request key, so it returns the failed job.
  - Quiescence re-checks the pins, which makes this unlikely, but a provider fault should stop the worker rather than fail documents.
  - Fix: give it its own failure class that raises `WorkerStopped`, or at least make it retryable.

## Recommendations

- [medium] N1: enforce the two-launch limit before each conversion starts (`content_workflow.py:186`, `document_worker.py:241-250`) so two reason-less crashes cannot trigger a third conversion, and add a worker test — owner: Backend Developer; follow-up: fix before ADR-0074 acceptance or the next F0005 re-measurement
- [low] L-N1: catch pypdf `PdfReadError`/`PdfStreamError` in `_count_pages_needing_ocr` and guard the `PdfReader` page count so damaged pages yield `partial`, not `conversion_failed` — owner: Backend Developer; follow-up: next F0005/F0014 conversion change
- [low] L-N2: convert any token-counter exception into a recorded `InferenceRejected("invalid_token_estimate")` (`vllm_graph_client.py:302`) — owner: AI Engineer; follow-up: before any Graph-dense reopen under ADR-0060
- [low] L-N3: treat a stale or uncleared in-flight marker as a guard fault that stops the worker (`worker_guard.py:325-327`, `document_worker.py:68`) — owner: Backend Developer + DevOps; follow-up: F0005 follow-up or the SEC-F5-M1 isolation work
- [low] L-N4: classify `usage_exceeds_reservation` as provider misconfiguration that stops the worker instead of a terminal per-job budget failure — owner: AI Engineer; follow-up: F0005 follow-up before activation of any pipeline other than the baseline
- [low] Round-1 L3/L5/L6 remain: add `boot_id` to the conversion launch receipts, add an orphan-source sweep for the queue-bound race, and tag key decisions with `# WHY:` — owner: DevOps (L3), Backend Developer (L5, L6); follow-up: L6 at this run's G7 KG step, L3/L5 deferred to F0026 hardening

## Pattern Compliance

- [x] Clean architecture respected. Engine `brain_content.config` does not import the AI runtime. Neuron imports stay within ADR-0060 ownership. The new `brain_ingestion → brain_extraction.graph_interpretation.PIPELINES` import in `submission.py` is in the same layer.
- [x] SOLID principles followed. The new responsibilities (`OcrObserver`, `identify_ocr_engine`, rejection recording) are narrow and reused, not duplicated.
- [x] SOLUTION-PATTERNS.md applied: expand-only migration 0010 with a frozen enumeration, a guarded downgrade and a mirrored application `Literal`; fenced `conversion_started` events; append-only job history with codes only.
- [x] Test coverage ≥80% for feature logic: 83.1% changed-line. The weak spots are `content_workflow.py` at 42.3%, where the supervised branch is live-only, `worker_cli.py` at 64.4% and `provider_supervisor.py` at 69.5%. The live lanes exercise all three.

## Acceptance Criteria

- [x] All feature ACs in code scope are met. S0001-AC2 is now met. S0002-AC3 is met for single faults, with N1 as a recommendation. S0004-AC4/AC7 wait on the operator decision, and S0004-AC5 cannot be reached.
- [x] Edge cases handled: empty pages become failed pages, unpinned assets give a null engine and the v1 fallback, `queue_depth_exceeded`, and the legacy `graph-direct` meaning. L-N1 is the damaged-stream gap.
- [x] Error scenarios covered: pre-dispatch rejections, dense fallback, post-publication errors, marker fault, provider busy during timeout and kill, and revocation and cancellation.

## Recommendation

APPROVE WITH MINOR CHANGES. C1 and H1 are closed with tests. No Critical or High finding remains. N1 should be fixed before ADR-0074 is accepted, because the ADR states the two-launch limit as unconditional.
