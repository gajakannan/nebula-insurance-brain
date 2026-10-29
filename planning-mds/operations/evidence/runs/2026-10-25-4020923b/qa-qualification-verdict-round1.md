# QA Qualification Verdict — F0005 run 2026-10-25-4020923b (S0004-AC4)

- **Role:** Quality Engineer, independent review session. I did not author the code, the tests, the corpus, the expectations, the report or its summary.
- **Date:** 2026-10-26.
- **Scope:** the S0004 measured report and the S0001–S0003 and S0005 evidence in this run folder. The product is on branch `feature/f0005-live-qualification`; the changes are uncommitted, so I reviewed the working tree as it stands.
- **Method:** read-only. I recomputed every metric from the per-case rows in `report.json`, checked hashes with `sha256sum -c`, and regenerated the corpus in a scratch copy. I rendered and extracted PDFs, read every live test, compared JUnit timestamps with file mtimes, and checked the offline coverage XML. I did not run any live lane, the benchmark or provider quiescence.

## Summary

- **The measured comparison is sound and the rejection is robust.** Recomputing from the 26 per-case rows of each engine reproduces every aggregate in `report.json` exactly.
  - Graph dense misses four PRD thresholds by wide margins: field accuracy, abstention, evidence resolution and latency relative to the baseline.
  - None of the scoring caveats I found could turn a miss into a pass.
- **The corpus is valid and independent.**
  - It has 13 documents: 6 native, 4 scanned, 2 mixed and 1 partial.
  - All 26 files match `CORPUS-HASHES.txt`.
  - Running the author's generator again in a scratch copy reproduces every PDF and expectation byte for byte.
  - The generator imports only reportlab, Pillow and pypdfium2.
- **Two interpretation discrepancies with `report-summary.md`:**
  1. Review workload is marked **MET**, but only because the 18 failed Graph-dense runs produce zero review items. Compared like for like it is about 1.64×, above the 1.25× limit.
  2. The summary says every scored value in the completed Graph-dense runs was "grounded". In fact 11 of the 20 predicted values were unresolved; fabricated = 0 means only that no selector contradicted its value.
- **One evidence claim is false.** `test-execution-report.md` says "relationship output fails closed". The live relationship probe actually ended `model_malformed_output` ×3, and the fail-closed path (`UnsupportedOutput`) has 0 hits in the offline coverage. S0003-AC4 is **not proven**.
- **Other gaps, none of which affects the rejection decision:**
  - The kill-point and competing-worker lane ran before the last product edits and was not re-executed.
  - `report.json` keeps no predicted values, so accuracy cannot be re-scored.
  - The corpus is not committed, so the hash timing rests on file mtimes.
  - Several ACs are only partly proven, including S0001-AC2, the five audit ACs, S0002-AC4 and S0005-AC3/AC4.
- **Decision:** the evidence supports the operator recording **rejection**. Under S0004-AC3/AC7 that is the only permitted outcome: `direct-baseline` stays the default, `content.v2_writer_enabled` stays `false`, and ADR-0060 records the failed gates as Proposed or Rejected, at the operator's choice.

## Threshold Recomputation

The source is the `engines.<engine>.cases[]` rows of `artifacts/qualification/report.json`. The script is in my scratch dir; it applies the PRD definitions to the per-case flags and ignores the `metrics` blocks. Every recomputed value equals the stored aggregate to full float precision.

| Metric (PRD) | Threshold for Graph dense | Direct baseline (recomputed) | Graph dense (recomputed) | Result | Agrees with `report-summary.md`? |
|---|---|---|---|---|---|
| Schema validity | 100%, no silently invalid result | 25/25 = 100% (1 explicit failure, gl-q-010/b) | 8/8 = 100%; 18 explicit failures (`model_malformed_output` ×3 each), 0 silently invalid | **MET** | Yes |
| Field accuracy | ≥ 90% and ≥ baseline − 5 pp | 24/58 = 41.38% | 16/58 = 27.59%; 13.79 pp below the baseline | **MISSED**, both conditions | Yes |
| Abstention | ≥ 95% | 3/7 = 42.86% | 0/7 = 0.0%. No absent field falls in a completed dense run; if failed runs were excluded the metric would be undefined, so it is still not demonstrated | **MISSED** | Yes |
| Fabricated evidence | 0 | 0 (25 supported, 13 unresolved) | 0 (9 supported, 11 unresolved) | **MET** | Value yes; the "every scored value was grounded" wording is wrong |
| Evidence resolution | ≥ 80% and ≥ baseline | 16/24 = 66.67% | 8/16 = 50.00% | **MISSED**, both conditions | Yes |
| Context budget | 0 calls over 4,096 | 0 (max reserved 1,191) | 0 (max reserved 2,735) | **MET**, scoped to completed runs only (F-07) | Yes |
| Latency p95 | ≤ 120 s and ≤ 3× baseline p95 | 1.481 s (n = 25, nearest rank) | 9.844 s (n = 8, which is the maximum); the limit is min(120, 4.444) = 4.444 s, and the ratio is 6.65× | **MISSED** (relative limit) | Yes |
| Review workload | ≤ 1.25× baseline per document | 38/13 = 2.923 | 20/13 = 1.538; ratio 0.53× | **MET as defined, but not meaningful.** Per completed run it is 2.50 vs 1.52 (1.64×). On the 8 cases both engines ran it is 20 vs 12 (1.67×). Both exceed 1.25× | **No.** The summary marks MET with a caveat; QA treats it as "not demonstrated" (F-03) |
| Recovery | 0 reconversions after publication / 0 duplicate effects | — | — | **MET** from the S0002 lanes, which are outside `report.json`. Coverage gaps are listed under S0002 | Mostly. "1 conversion" is wrong for the storage case, which has 2 conversions before publication, as AC3 allows |

Reported but not thresholded, all recomputed and matching:

| Item | Direct baseline | Graph dense | Graph direct |
|---|---|---|---|
| Calls | 25 | 16 | 26 |
| Prompt / completion tokens | 6,634 / 1,161 | 24,698 / 4,314 | 18,674 / 1,408 |
| Field accuracy | — | — | 49/58 = 84.48% |
| Abstention | — | — | 1/7 = 14.29% |
| Evidence resolution | — | — | 0/49 |
| Review items per document | — | — | 4.923 |
| GPU memory (sampled only at start and end) | 11,532 MiB | 11,502 MiB | 11,532 MiB |

- Graph dense calls and tokens come from completed runs only.
- The summary's baseline sub-figures are also correct: each-occurrence accuracy 2/12 and general-aggregate 1/11.

**Outcome:** four thresholds are clearly MISSED, and review workload is effectively a fifth. Activation is blocked whichever way review workload is read.

## Corpus Independence And Validity

| Check | Finding |
|---|---|
| Count and kinds (S0004-AC1) | 13 documents: 6 native (001–006), 4 scanned (007–010), 2 mixed (011–012) and 1 partial (013). This meets the ≥ 12 requirement and the 6/4/2 split. There are 65 field expectations: 58 present and 7 absent. |
| Current files vs `CORPUS-HASHES.txt` | `sha256sum -c` gives 26/26 OK. The fixture copy and the run-folder copy of `CORPUS-HASHES.txt` are identical. Their sha256 is `fbc5e263…2dc9`, the value recorded in `report.json`. The expectation-set hash recomputes to `16a29d67…390c`, also as recorded. |
| Reproducibility | I copied the fixture directory to scratch and ran `build_corpus.py` there with `neuron/.venv/bin/python -I`. Every regenerated file matches the committed hashes. Expectations are therefore a deterministic function of the generator's layout spec. |
| Independence from extraction | The generator imports only stdlib, reportlab, Pillow and pypdfium2; nothing from Docling, brain_* or a model client. The author report's independence statement is consistent with that. The author session is the "QE corpus author" role from the assembly plan, separate from the QE execution session and from this review. |
| Hashes before the first measured run | Supported, but only weakly. The fixture files and `CORPUS-HASHES.txt` have mtime 2026-10-25 23:38:44 and `corpus-author-report.md` 23:40. The measured run started 2026-10-26 01:01:30 (`live-suite-summary.log`, `report.json started_at` 1792990894). The harness `verify_corpus()` refuses to run on a mismatch, and the hashes are unchanged now. However, the corpus is **untracked in git**, and `commands.log` has **no entry for corpus generation**. The timing evidence is therefore mtimes plus the author's own statement, not a commit (F-05). The AC wording "when it is committed" is not yet met. |
| `commands.log` timestamps | These are not contemporaneous. The killed lane, the 12-case fault lane and the diagnostic all carry 00:36:21, and the timeout, reinterpretation, deadline, decision and measured lanes all carry 01:36:22. Real ordering comes from `live-suite-summary.log`, the JUnit timestamps and file mtimes. Those show the harness file (00:18:49) and all product source (latest 00:24:47) last changed **before** the 01:01 measurement, so the measured code is the current tree. |
| Spot checks against the source | I extracted text from 001, 003, 004, 005, 006, 011 and 013 and rendered 004, 008 and 011. Every value I checked matches the printed document, including evidence pages: 001 (all five fields); 003 (split named insured over two lines, the repeated $1,000,000 on pages 1–2, and no "General Aggregate" label anywhere); 008 (scanned: $500,000, the repeated $1,000,000 on p1/p2, the named insured and 05/20/2026–05/20/2027); 011 (insured, period and the $3,000,000 aggregate printed in the pixel-only header, and $3,000,000 also in the native table); 013 (page 2 damaged; values on p1 and p3). |
| gl-q-004 `$ 500,000` | In the render, `$` and `500,000` sit in separate cells of an accounting-style table. The expected `$ 500,000` is an artifact of the author's rule of joining split parts with one space, not a value anyone would read as printed; `$500,000` is the natural reading. Under the PRD's whitespace-plus-NFC normalization, a correct `$500,000` scores as a miss. The rule was disclosed before measurement and applies to every engine equally, so it is not biased. **Impact:** at most 2/58 fields per engine (3.4 pp). Even if both counted, Graph dense would be 18/58 = 31.0%, which does not change the outcome. Separately, the evidence mapper cannot resolve a value that spans two cells or two text items, so split values can never count toward evidence resolution for any engine. That is a mapper limitation, also engine-neutral. Under the S0004 edge-case rule, correcting this expectation means re-hashing and re-measuring both engines, so QA recommends fixing the convention before any future re-plan (R-6), not re-scoring this report. |
| Labelling | The corpus is labelled synthetic and kept outside `golden-corpus/` and the frozen holdout, as the PRD requires. |

## Scoring Review

`neuron/benchmarks/f0005_qualification.py`, functions `normalize`, `evidence_check`, `score_case` and `aggregate`.

- **Normalization follows the PRD.**
  - `normalize()` (line 62) is `" ".join(NFC(value).split())`: whitespace collapse plus NFC, nothing else.
  - It is applied to both the predicted and the expected value (line 468).
  - A correct answer must be the only answer for that slot (`len(predicted) == 1`).
  - There is no case folding, currency or number normalization. This is strict but consistent with the PRD edge case "`$1M` is an accuracy miss".
- **Failed runs.** A failed job scores every present field incorrect and every absent field not abstained (lines 386–397). Applying this to every engine is a fair, conservative reading of "over present expected fields" on the full corpus. It does mean Graph dense abstention is 0/7 only because no absent field fell into a completed dense run; the metric is not demonstrated either way.
- **Evidence check.**
  - `evidence_check()` (line 354) reloads the verified bundle and compares the selector's text with the predicted value: exact characters for spans, exact cell text for table cells.
  - Multi-cell bindings always score `fabricated` (line 361). This is latent: the mapper never emits them.
  - Because the mapper binds only exact verbatim matches, "fabricated = 0" is close to guaranteed by construction. It is still a real independent check of offsets and cell geometry against the bundle.
  - Evidence resolution correctly counts only *correct* values that have a `supported` selector.
- **Latency and review workload are computed in ways that flatter Graph dense.**
  - Latency counts completed runs only (line 592), so the 18 slow-failing dense runs are excluded.
  - Review workload divides the review items of all cases by documents (line 534), so failed runs add 0.
  - Both favour the engine that fails more. Neither changes the outcome: latency is still missed, and review workload is misleading, as shown above (F-03).
- **Calls, tokens and context budget** are read from the published run metadata (line 433), so they cover completed runs only. Calls made during the 54 failed dense attempts are not in the report (F-07). The pre-send budget guard (S0003-AC5) and the absence of any `context_limit_exceeded` reason support the 0 result.
- **The baseline is handicapped.**
  - `_direct_baseline` (`graph_interpretation.py:60`) sends only `document.texts`, so table-borne limits are invisible to it, and its grounding ledger contains no tables. This is disclosed.
  - It lowers the baseline and so loosens the four relative thresholds in Graph dense's favour. Graph dense misses the absolute thresholds anyway.
- **Strict product policy.**
  - `graph_interpretation.py:214` rejects any result built around a non-`complete` call. This turns Graph's own skeleton→direct fallback, and any internal repair, into an attempt failure.
  - It is defensible: the PRD requires that invalid output fail explicitly, and the fallback would report a direct-contract answer as dense.
  - Its effect on Graph dense is real: 18 failed runs. Since the skeleton failures are deterministic at temperature 0 (truncation at the 512-token reservation, or duplicate keys), relaxing it would also mean relaxing a budget or validity rule, which S0004-AC3 forbids.
- **Per-case rows do not retain predicted values or selectors.** The isolated schemas and content roots are dropped (line 208). Accuracy therefore cannot be re-audited or re-scored, for example to quantify gl-q-004 (F-04).
- **Verdict on scoring:** fair to both engines, PRD-conformant normalization, no inflation that could change a threshold outcome. Two aggregates, latency and review workload, are biased by excluding failures and should be reported as caveated.

## Acceptance Criteria Verdicts

Raw results are in `artifacts/test-results/`. "Live" means the opt-in lane against the real vLLM, Docling and PostgreSQL.

| AC | Verdict | Evidence (test :: case → raw) | QA notes |
|---|---|---|---|
| S0001-AC1 pins | Partly proven | G1 `uv sync --locked` (commands.log 23:28); `report.json pins`; the version guard at `docling_graph_pipeline.py:103` | The wheel digest is enforced by `neuron/uv.lock:1231`, but the report copies a constant instead of reading the installed wheel. Only the docling-graph version is guarded at runtime. No negative test shows a mismatch failing *before conversion*. |
| S0001-AC2 bundle identities | Partly proven | `test_live_conversion_qualification.py::test_every_corpus_document_publishes_before_the_first_model_request` → `live-conversion.log/.xml` (06:06, 2 passed) | Asserted: source sha256, `docling==2.126.0`, page count, partial status and failed pages. **Not** asserted: parser name and configuration, document-level OCR engine name and version, OCR page count, warnings (counted only). OCR producers are checked only on v2 bundles, so only gl-q-009 among the scanned documents. The v1 manifest has no OCR page count or document-level OCR engine; the authors acknowledge this. |
| S0001-AC3 checkpoint before model | Proven | same test: `model_unavailable`, state `retry`, verified ready bundle, `converter.launches == 13`, `proxy.records == []` | Invalid output after publication is also covered by the S0002-AC1 lanes. |
| S0001-AC4 partial conversion | Proven | same test: gl-q-013 `status=partial`, `failed_pages=[2]`; `report.json` gl-q-013 direct-baseline result `status=partial` for both profiles | |
| S0001-AC5 stage guard | Partly proven | `test_installed_stage_layout_mismatch_raises_before_extraction_and_registers_nothing` (live subprocess, prints `stage_guard_mismatch 0`); `test_conversion_process.py::test_child_errors_are_stable_codes[stage_guard]`; `test_document_worker_reasons.py` | Proven piece by piece. No end-to-end test shows a *job* failing `stage_guard_mismatch` with no ready artifact. A checkpoint-callback failure is not exercised live. |
| S0001-AC6 audit | Partly proven | `test_queue.py` (reasons recorded, unknown reason rejected, cancelled reason); `test_job_event_reason_migration.py`; `AuditEventRow` authorization decisions | `document_job_event` records job, generation, event, time and a bounded reason enum, so no free text is possible. Actor and correlation live in `jobs.payload`, the artifact in `jobs.artifact_id`, and the run in `result_ref`. No single audit record carries all the required fields, and no test asserts the complete field set or the absence of secrets or source text on state changes. |
| S0002-AC1 provider faults | Proven | `test_fault_injection_qualification.py::test_provider_fault_records_distinct_reason_and_resumes_from_saved_json` with 5 modes × 2 engines → `live-provider-storage-auth-faults.*` (8 cases), `live-timeout-faults.*` (direct), `live-timeout-graph-dense-rerun.*` | Each mode records its distinct first reason, `converter.launches == 1` holds, and all 10 cases end `complete` with single effects. |
| S0002-AC2 kill points | Partly proven (re-run required) | `test_worker_killed_at_each_point_recovers_with_single_effects[bundle,run,import,imported]` → `live-kill-points-and-competing-workers.log` (no XML) | The behaviour shown is right: 1 artifact, run, ack and complete job, 3 assertions, 0 reconversion, 0 replacement requests after `run`. But the lane ran about 00:10–00:22 (quiescence receipt epoch 1792988510 = 00:21:50). `queue.py`, `config.py`, `worker_cli.py` and `submission.py` were then modified 00:23–00:24 and the lane was never re-executed (F-06). The assertion is `assertion_runs <= 1` (line 88), not `== 1`. |
| S0002-AC3 storage failure | Partly proven | `test_storage_failure_before_marker_is_never_ready_and_reconverts_at_most_once[1,2]` | Failure ×1 gives complete, 2 conversions, 1 ready. Failure ×2 gives failed, 2 conversions, 0 ready. A *crash* before the completion marker is not exercised (the `bundle` kill point fires after publish), and cleanup of partial objects is not asserted. |
| S0002-AC4 duplicates, competing workers, cancellation, concurrency | Partly proven | `test_second_worker_is_refused_and_killed_holder_requires_confirmed_quiescence` (stale lane, F-06); `test_cancellation_stops_scheduling_and_temporary_exports_are_removed` (proxy saw **1** request); proxy `max_concurrency() <= 1` in every live fault case; `test_postgres.py::test_postgres_expired_lease_fences_old_worker` and the depth bound; `test_worker_guard.py` | Proven: competing workers, expired-lease fencing, cancellation within the in-flight call, and provider concurrency ≤ 1 measured at the proxy. Not proven live: duplicate submissions (only the SQLite unit `test_queue_depth_bound_rejects_new_work_but_keeps_duplicates_idempotent`), and Graph-internal fan-out (completed dense runs made only 2 sequential calls). The cancellation assertion allows ≤ 2 requests (line 307), looser than the AC, although the observed value was 1. |
| S0002-AC5 tenant and revocation | Partly proven | `test_revoked_grant_between_attempts_denies_audits_and_stops` | Revocation between attempts is denied and audited, with no further model call. A different tenant, an inactive principal, and reader access to bundles, run outputs or exports are not exercised live. |
| S0002-AC6 temp exports and retention scope | Partly proven | cancellation test (no `nebula-source-*` or `nebula-interpret-*` left, staging empty, all objects in tenant/KB scope) | Only the *cancelled* path is checked; complete and failed runs are not. Retention parity with the source is not asserted. |
| S0002-AC7 audit | Partly proven | as S0001-AC6 | |
| S0003-AC1 saved JSON only | Partly proven | `test_live_reinterpretation_qualification.py::test_both_profiles_reinterpret_saved_json_with_zero_conversion` → `live-reinterpretation.*` | Proven: `SupervisedConverter.convert`, `DoclingAdapter.parse` and `RapidOcrModel.__call__` are instrumented to fail and were called 0 times; bundle digests are unchanged; 13 conversions before the restart. Only 8 of 26 runs completed. Distinct identities are checked only through a conditional (`if len(by_profile) == 2`, line 131) on `pipeline_identity`. The tokenizer revision, chunking and template identity are not asserted individually. |
| S0003-AC2 evidence | Partly proven | same test (`fabricated == 0` on completed runs); harness `evidence_check` over 3 engines × 26 cases | No contradicted selector anywhere. "Repeated or ambiguous values stay unresolved" and "multi-region coverage" are mapper properties and are not asserted as such in the live lane. |
| S0003-AC3 provenance retained | Not proven (live) | none in this run; the test plan cites harness loading, but `score_case` never reads `provenance.json` | Only regression suites from earlier features (`test_document_delivery.py`) touch the provenance ledger. Nothing in this run asserts that the ledger and native item refs are retained, or that graph IDs never become identity. |
| S0003-AC4 unsupported output fails closed | **Not proven** | `test_relationship_output_fails_closed_with_no_rows` → `live-reinterpretation.log`: `{"state":"failed","reasons":["model_malformed_output" ×3]}` | The test passes on `model_malformed_output` (line 170), so the `UnsupportedOutput` path never ran. `neuron-coverage.xml` shows 0 hits on `graph_interpretation.py` lines 88, 91, 94 (raises) and 205–206 (handler). `test-execution-report.md` misreports this (F-01). |
| S0003-AC5 budgets | Proven | the reinterpretation test (`max_reserved_tokens ≤ 4096`; observed maximum 2,735); `report.json` `over_budget_calls = 0`; offline `test_vllm_graph_client.py` pre-send rejection | Scope is completed runs only (F-07). |
| S0003-AC6 targeting | Proven | `test_targeted_request_fails_before_any_model_call` | `NotImplementedError`, 0 transport requests, classified `unsupported_targeting`. |
| S0003-AC7 audit | Partly proven | as S0001-AC6 | |
| S0004-AC1 corpus | Partly proven | Corpus section above; the regeneration check | Counts, independence and reproducibility are proven. "Committed" is not met, hash timing rests on mtimes, and the gl-q-004 convention is questionable. |
| S0004-AC2 report contents | Proven | `report.json` (`void=false`, pins, configs, 26 cases × 3 engines, aggregates) | Caveats: no predicted values (F-04); calls and tokens cover completed runs only; GPU memory is sampled only at start and end. |
| S0004-AC3 thresholds marked | Proven | `report-summary.md`, plus this recomputation | Every threshold is marked with its measured value and nothing was re-run after the measurement. Review workload is mis-characterised (F-03). |
| S0004-AC4 verdicts and decision | Pending | this file (QA). Architect, Security and the operator decision are still outstanding in STATUS | |
| S0004-AC5 activation | Not reachable (correctly) | thresholds missed | The `accepted` branch in `test_pipeline_selection.py` ran with a failed job (engine `null`), so dense/v2 activation was never observed working end to end. |
| S0004-AC6 rollback | Proven (isolated configuration) | `test_pipeline_selection.py::test_decision_branches_…` → `live-decision-branches-rerun.*` (11/11) | The rollback row uses the `direct-baseline` engine; earlier bundle, run and source digests are unchanged; pinned payloads are unchanged; the legacy job keeps graph-direct. "No Graph call on rollback jobs" is inferred from identity and not asserted at the proxy. |
| S0004-AC7 rejection closure | Partly proven | `test_committed_configuration_selects_the_direct_baseline_with_v2_disabled`; `config/local.yaml` diff (`pipeline: direct-baseline`, `v2_writer_enabled: false`) | The configuration state is correct now. The ADR-0060 record and the operator decision are pending. |
| S0004-AC8 audit | Partly proven | as S0001-AC6 | Activation and rollback state changes have no audit-event test; configuration is a file change recorded only in STATUS. |
| S0005-AC1 per-item origin | Partly proven | live conversion rows; `test_ocr_asset_provenance.py` | OCR origin with engine and version was observed only for gl-q-009 (the one v2 scanned document). `STATED` with producer for native items is not asserted live. 11/13 documents fell back to v1, so their per-item projection was never inspected. |
| S0005-AC2 OCR asset identity | Proven | `test_ocr_asset_provenance.py` (pins equal installed bytes; altered or unresolvable assets give no identity); live manifests carry 3 pinned `name@rapidocr==3.9.2:sha256` digests | |
| S0005-AC3 v1 fallback audited and rate reported | Partly proven | `report.json bundle_contract` (v2 only for gl-q-005 and gl-q-009, so 11/13 = 84.6% fallback); live conversion rows | The rate is reported and recomputes. **No corpus-level assertion** checks `writer_fallback_reason = ORIGIN_UNAVAILABLE` or its audit event; that is asserted only in F0004-era suites on synthetic fixtures (`test_content_worker_v2.py:191`, `test_content_migration_states.py:1343`). The cause, table cells without origin, is the authors' explanation and is not evidenced in this run. |
| S0005-AC4 consumers read v2 | Partly proven | harness importer and evidence reads, plus the Graph saved-JSON path in graph-direct over the 2 v2 corpus bundles; F0004 suites (`test_content_consumer_versions.py`, `test_content_restore_v2.py`) | The authorized content reader and the restore drill were not run over *corpus* v2 bundles. Graph dense never completed on a v2 bundle. |
| S0005-AC5 writer switch | Not reachable (correctly) | gated on acceptance | |
| S0005-AC6 audit | Partly proven | as S0001-AC6 | |
| Cross-cutting: thresholds measured | Met | `report.json`, `report-summary.md` | |
| Cross-cutting: verdicts before state change | Pending | STATUS | |
| Cross-cutting: ≥ 80% changed-scope coverage | Met | `artifacts/coverage/changed-line-coverage.md`: 921/1123 = 82.0% | |

## Retries And Reruns

The retried tests and the proxy are untracked files, so `git diff` has no history for them. I compared the old test source that pytest printed in the failure logs with the current files and checked their mtimes.

1. **Graph-dense ambiguous timeout.** First run 00:36 (`live-timeout-faults.log`); rerun 01:30 (`live-timeout-graph-dense-rerun.log`). **Legitimate instrument fix; no relaxation.**
   - The first failure was `assert proxy.max_concurrency() <= 1` with a value of 2.
   - The log shows an upstream request dying with `RemoteProtocolError: Server disconnected` during the confirmed provider restart. The old proxy never closed that record (`finished=None`, counted as open forever), and it measured the proxy's reply interval, which includes the 30 s timeout hold. That makes a phantom overlap with the post-restart request.
   - The fixed `fault_proxy.py` (mtime 00:42) measures the upstream interval and closes errored records with status 599.
   - The rerun timeline shows record 1 upstream at 10387.7–10458.0 s, ended 599 by the quiescence kill, then records 2 and 3 strictly after. The provider never held two requests.
   - The assertion threshold `<= 1` is unchanged. The test source shown in the failure log matches the current file up to the assertion; the only visible change is printing the evidence, including the proxy timeline, *before* asserting.
   - The rerun happened after the measured run and touches nothing the measurement uses.
2. **Decision branches.** First run 00:56 (`live-decision-branches.log`); rerun 01:32–01:35 (`live-decision-branches-rerun.*`). **Legitimate test fix that tightened the assertion.**
   - The failure was `KeyError: 'v2_writer_enabled'` on the legacy summary row.
   - The old check was `assert case.get("bundle_contract") in (1, None)` for v1 branches. It is now `assert contract == 1`, with the contract read from the published artifact even when the later interpretation fails. That is stricter.
   - The final `any(...)` check is semantically unchanged (`r.get`).
   - No product code changed: all product sources date ≤ 00:24, and the test file mtime is 01:32.
3. **Engine `publication` fixture** (pinned at schema 0008, now `head`). This is a test-fixture correction for the new 0009 column. It is disclosed, it is not part of the qualification, and it relaxes nothing.
4. **gl-q-013 `pypdf` failure, fixed in product code.** This happened in an earlier session, before the measurement. It is a genuine product fix (an empty or unreadable page becomes a failed page) and is consistent with S0001-AC4 and the "page that converts empty is a failed page" edge case.
5. **Re-executions at 06:06–06:14** of the conversion and provider/storage/auth lanes, to retain raw logs. Both ran on the final code and passed. The kill-point and competing-worker lane was **not** re-executed although product code changed after it (F-06).
6. **The diagnostic subset** (`diagnostic-dense-subset-NOT-MEASURED.json`, 00:36) ran before the measurement, did not change the corpus (the hashes are identical), and did not alter any budget. The measured run is a single full run per engine, `void=false`, with no rerun. **S0004-AC3's ban on re-running with relaxed budgets is respected.**

## Findings

| ID | Severity | Location | Finding | Recommendation |
|---|---|---|---|---|
| F-01 | High | `neuron/tests/integration/test_live_reinterpretation_qualification.py:170`; `neuron/packages/brain-extraction/src/brain_extraction/graph_interpretation.py:86-94,203-206`; `test-execution-report.md` ("relationship output fails closed") | The S0003-AC4 probe accepts a model failure as a pass. The live run ended `model_malformed_output` ×3, so the fail-closed path was never executed live or offline (0 coverage hits). The execution report states the AC was demonstrated. | Correct the report; mark S0003-AC4 not proven; add a deterministic test that feeds `GraphInterpretationService` an output with edges, a foreign type or a nested entity and asserts `unsupported_output`, 0 assertions and 0 reviews. Do not tick S0003-AC4 until then. |
| F-02 | Medium | `neuron/tests/integration/test_live_conversion_qualification.py:73-100` | S0001-AC2 is partly proven. Parser configuration, document-level OCR engine name and version, OCR page count and warnings are not asserted, and the v1 manifest cannot carry the OCR page count or engine. | Architect decides the contract gap; until then S0001-AC2 stays partly proven in STATUS. |
| F-03 | Medium | `neuron/benchmarks/f0005_qualification.py:534`; `artifacts/qualification/report-summary.md` (Review workload row) | Review workload "MET" comes from 18 failed runs contributing 0 items; like for like it is 1.64–1.67×, above the 1.25× limit. Latency (line 592) similarly excludes failed runs. | Annotate the summary row as "not demonstrated / artifact of failures"; in future reports compute both on completed runs, with failed runs reported separately. |
| F-04 | Medium | `neuron/benchmarks/f0005_qualification.py:463-480,208` | Per-case rows keep only booleans. Predicted values and selectors are discarded and the isolated schemas and content roots are dropped, so accuracy cannot be re-audited or re-scored (for example gl-q-004). | Retain the predicted value, normalized form and selectors per field in the report (synthetic data, under the run folder). |
| F-05 | Medium | `neuron/fixtures/qualification/` (untracked); `commands.log` | The corpus and its hashes are not committed and corpus generation is not in `commands.log`. "Recorded before the first measured run" rests on mtimes (23:38) and the author's statement. Also, `commands.log` entries are batch-stamped (00:36:21, 01:36:22), not contemporaneous. | Commit the corpus and `CORPUS-HASHES.txt` in a commit that precedes the report commit; log corpus generation; stamp `commands.log` at execution time. |
| F-06 | Medium | `artifacts/test-results/live-kill-points-and-competing-workers.log` (receipt 00:21:50) vs mtimes of `engine/packages/brain-jobs/src/brain_jobs/queue.py`, `brain_content/config.py`, `brain_ingestion/worker_cli.py`, `brain_ingestion/submission.py` (00:23–00:24) | The S0002-AC2/AC4 kill-point and competing-worker evidence predates the final product code and has no JUnit XML. | Re-execute `pytest test_fault_injection_qualification.py -k 'killed or second_worker'` on the final tree with `--junitxml` before ticking S0002-AC2/AC4. This lane restarts the provider, so the operator must schedule it. |
| F-07 | Low | `neuron/benchmarks/f0005_qualification.py:433` | Calls, tokens and the context-budget metric cover completed runs only; the calls of the 54 failed dense attempts are not reported. | Record per-attempt call diagnostics (or count rejected calls) so the context-budget 0 covers every call. |
| F-08 | Low | `neuron/fixtures/qualification/build_corpus.py:437-438` | The gl-q-004 expectation `$ 500,000` encodes the join rule, not the printed reading; split values can never resolve to exact evidence under the current mapper. Engine-neutral; at most 3.4 pp. | For any future re-plan, author split currency values as printed (`$500,000`) or accept both forms explicitly in the PRD, then re-hash and re-measure both engines. |
| F-09 | Low | `neuron/tests/integration/test_live_reinterpretation_qualification.py:131`; `neuron/tests/integration/test_fault_injection_qualification.py:88,307`; `neuron/tests/integration/test_pipeline_selection.py:156` | Several assertions are conditional or loose: identities only if both profiles completed; `assertion_runs <= 1`; cancellation `<= 2` requests; the accepted branch's engine is asserted only if the job completed. Observed values were stricter than the assertions. | Tighten to `== 1`, `== 1` and unconditional identity checks. |
| F-10 | Low | `report-summary.md` ("every scored value was grounded"; Recovery "1 conversion") | The wording overstates: 11 of 20 dense values were unresolved, and the storage ×1 case had 2 pre-publication conversions. | Correct the wording. |
| F-11 | Info | `neuron/packages/brain-extraction/src/brain_extraction/graph_interpretation.py:60,214` | The baseline sees no tables, which loosens the relative thresholds in Graph's favour. Any non-complete call fails the dense attempt, which disables Graph's internal fallback and repair. Both are disclosed and defensible, and neither changes the outcome. | Record both in ADR-0060's failed-gate note so a re-plan does not mistake them for model-quality limits. |

Recommendations, in the consumer-contract format:

- [high] S0003-AC4 is not proven and the execution report claims it is (F-01) — owner: Quality Engineer; follow-up: correct `test-execution-report.md` and add a deterministic fail-closed test before S0003-AC4 is ticked. PM mitigation is required.
- [medium] The kill-point and competing-worker lane is stale relative to the final code (F-06) — owner: Quality Engineer with the operator; follow-up: re-execute with JUnit XML in a scheduled provider window.
- [medium] Review workload and latency exclude failed runs (F-03) — owner: Quality Engineer; follow-up: annotate the summary now and fix the harness before any re-measurement.
- [medium] The report is not re-scorable (F-04) and the corpus is not committed (F-05) — owner: Quality Engineer; follow-up: retain predictions; commit the corpus ahead of the report.
- [medium] The S0001-AC2 manifest gap (F-02) — owner: Architect; follow-up: decide whether a v1 or v2 manifest field is needed.
- [low] F-07 to F-10 — owner: Quality Engineer; follow-up: next harness revision.

## S0004-AC4 QA Verdict

- **Report validity.** The measured report is complete, `void=false`, and taken with recorded pins and isolated configurations on the final product code. Its aggregates recompute exactly from the per-case data. The corpus is hash-intact, reproducible and authored independently. The scoring is PRD-conformant and engine-neutral.
- **Thresholds.** Graph dense **misses field accuracy (27.6%), abstention (0%), evidence resolution (50.0%) and relative latency (6.65× the baseline p95)**. Review workload passes only as an artifact of its failures. No caveat in this review could reverse any of these misses.
- **Reruns.** Neither disclosed rerun relaxed a threshold, budget or assertion. Neither touched the measurement.
- **Permitted outcome.** The evidence supports the operator **recording rejection**. Under S0004-AC3, a missed threshold blocks activation. Under S0004-AC7, the only permitted closure is:
  - `extraction.pipeline: direct-baseline` stays the default;
  - `content.v2_writer_enabled: false` stays;
  - ADR-0060 records the failed gates (Proposed or Rejected, per the operator);
  - no partial activation remains.
  
  The committed `config/local.yaml` already has these values. Activation under S0004-AC5 and S0005-AC5 is not permitted.
- **ACs that must not be ticked yet.** These gaps do not affect the rejection decision, but they bear on closing F0005's other ACs. STATUS must not record the following as verified:
  - S0003-AC4 (not proven);
  - S0003-AC3 (not proven live);
  - S0002-AC2/AC4 (stale lane);
  - the partly-proven ACs listed above.

  In particular, the high-severity recommendation (F-01) needs PM mitigation before closeout.

Result: PASS WITH RECOMMENDATIONS
