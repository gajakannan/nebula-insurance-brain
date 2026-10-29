# F0005 Delta Review: G4 Round-2 Fix Set (Code Reviewer + Security)

- Run: `2026-10-25-4020923b`
- Date: 2026-10-28
- Reviewer: independent; Code Reviewer and Security roles combined. I did not author this code.
- Baseline: the pre-change snapshot `g3r-snapshot/` in the session scratchpad.
- Current tree: `feature/f0005-live-qualification` , uncommitted.

## Summary

- **Delta scope.** I diffed every snapshot file against the current tree, file by file.
  - 21 files changed: 9 product modules, 7 test files, `neuron/uv.lock` and 3 ADRs.
  - One new product file: `neuron/packages/brain-extraction/src/brain_extraction/pins.py`
  - One test file outside the snapshot changed against HEAD: `neuron/packages/brain-ingestion/tests/test_docling_adapter.py`
  - No reviewed file under `engine/` or `docker/` changed.
- **Tests run (offline only; no live lanes, benchmark or `provider_supervisor`).**
  - Full neuron suite: 252 passed, 29 skipped and 1 failed. The one failure is `test_content_worker_v2.py::test_publication_import_and_second_profile_reuse[False]` . It is the same failure recorded at HEAD in `artifacts/test-results/head-baseline-neuron-content-worker-v2.log` and in `artifacts/test-results/g2r3-neuron-full.log`
  - The 22 new or changed delta tests pass when run on their own.
  - `uv lock --check --offline` is consistent, and the venv has `litellm-1.100.4`
- **Closure.**
  - Closed: N1, L5, L-N1 to L-N4, L3 (`boot_id`), the four Architect Lows, the four QA Lows, the `# WHY:` tags, litellm, and the ADR text fixes.
  - Partly closed: L4. Listener ownership and the 0600 log are closed. The program check is still basename-based, so `/tmp/x/vllm` or a `python` and `vllm` pair in any shared directory is accepted (probe below).
- **New findings.** No Critical, High or Medium. There are five Lows, described below.
- **ADR-0074.** N1 and L5 are both verified, so the ADR is ready for acceptance. One ADR sentence needs narrowing (D-1).

## Ordered Item Closure

| Item | Status | Code evidence | Proving test |
|---|---|---|---|
| Code Review **N1**: no third conversion after silent crashes | **Closed** | `neuron/packages/brain-ingestion/src/brain_ingestion/document_worker.py:245-250` — `_start_conversion` checks `conversion_launches >= 2` and raises `ConversionError("conversion_budget_exhausted")` before `conversion_started`. It is wired as `before_conversion` at `document_worker.py:288` . That callback runs before `supervisor.convert` and before the in-process path (`content_workflow.py:186-187` , `:201-202`), so nothing launches. `classify` maps it to `conversion_failed`, and `_record_failure` makes it terminal because launches ≥ 2. | `test_document_worker_reasons.py:357` (launch counts 0 to 3; nothing is launched at 2 or 3) and `:372` (terminal `fail conversion_failed`) |
| Security **L5**: a refused restart stops the server it started | **Closed** (Low residual D-2) | `neuron/packages/brain-ingestion/src/brain_ingestion/provider_supervisor.py:140-160` — `wait_ready`, `capture`, the pin check and the listener check all run inside `try`. `except BaseException` calls `terminate_group` (TERM, then KILL), waits, and re-raises. The marker is never cleared on this path. | `test_worker_guard.py:446` . It runs through `quiesce_and_restart` with an unauthenticated restart, then asserts `group_members(started[0]) == []`, that the marker is still dirty, and that the log mode is 0600. |
| Security **L4**: real vLLM entry point | **Partly** | `worker_guard.py:431-446` — `_serving_program` accepts argv[0] with basename `vllm`, or a `python*` argv[0] in the same directory as an argv[1] named `vllm`. My probe, using sentinel argv only, found: `['/tmp/evil','vllm']` refused, `['/bin/sh','/tmp/x/vllm']` refused, but `['/tmp/x/vllm']` , `['/tmp/x/python','/tmp/x/vllm']` and `['/tmp/x/python3','/tmp/x/vllm']` **accepted**. Neither `/proc/<pid>/exe` nor an operator allowlist binds the program. | `test_worker_guard.py:403` (the 7 tamper cases, including `vllm_named_argument` and `foreign_interpreter`) |
| Security **L4**: listener-socket ownership | **Closed** | `worker_guard.py:420-425` (`owns_listener`: LISTEN inodes in `/proc/net/tcp*` that also appear in the fds of a group member). It is enforced at record time (`worker_guard.py:383-385` ), before any signal (`provider_supervisor.py:93-96` ) and after a restart (`:151-152`, which `capture` already makes unreachable). | `test_worker_guard.py:492` (negative case). The positive path is exercised by every fake-provider capture in `test_worker_guard.py` . |
| Security **L4**: provider log 0600 | **Closed** | `provider_supervisor.py:124-126` (`os.open(..., 0o600)` followed by `chmod`, inside the 0700 control directory) | `test_worker_guard.py:446` (asserts mode 0600) |
| Code Review **L-N1**: pypdf error types | **Closed** | `docling_adapter.py:10,70-75,108-120,129-133` . `PyPdfError` is caught. An unreadable structure falls back to Docling's page count with a `pdf_structure_unreadable` warning. Rotations become empty, so v2 layout honestly records `geometry_state: unavailable` (`content_projection.py:172-176` ). | `test_docling_adapter.py:80` (v1 and v2) |
| Code Review **L-N2**: token-counter rejection | **Closed** | `vllm_graph_client.py:302-307` — any counter exception becomes `InferenceRejected("token_count_failed")`, recorded as `invalid_request`, which maps to `interpretation_failed`. The exception text is never recorded. | `tests/integration/test_vllm_graph_client.py:453` (also asserts that "private source" does not appear in the diagnostics) |
| Code Review **L-N3**: a marker-clear failure stops the worker | **Closed** (Low residual D-1) | `worker_guard.py:307-310` (a leftover marker sets `uncertain`) and `:329-334` (an `OSError` on unlink or fsync sets `uncertain`). `document_worker.py:241-242` then raises `WorkerStopped`. | `test_worker_guard.py:504` , `:522` |
| Code Review **L-N4**: `usage_exceeds_reservation` stops the worker | **Closed** | `document_worker.py:71` . `guard_fault` runs before any result classification (`:364-365`), so the worker raises `WorkerStopped` and records no reason. | `test_document_worker_reasons.py:380` (function level only; there is no `run_one` case) |
| Round-1 **L3**: `boot_id` in receipts | **Closed** (Low residual D-3) | `conversion_process.py:480` (written) and `:627-639`: a receipt from another boot never probes or signals its PID; only its staging is removed. Receipts without a boot id keep the start-ticks check. | `test_conversion_process.py:246` (a live unrelated process with mismatched ticks is never signalled) |
| Architect Low: legacy pipeline metadata | **Closed** (no test) | `graph_interpretation.py:300-301` — `"pipeline": pipeline or "graph-direct"` plus `pipeline_source` set to `pinned` or `legacy_default`. These are not part of `configuration_sha256`. | None. A grep finds no test that references `pipeline_source` (see Recommendations). |
| Architect Low: hard-coded stage-guard literal | **Closed** | `conversion_process.py:251,353,573,655-663` derive the guard from `brain_extraction/pins.py` , which has no dependencies. `docling_graph_pipeline.py:22-27,107` uses the same pin for its installed-version check. No `"1.9.1"` literal remains in code, only in comments. | Covered by the full suite and `g2r3-live-conversion.log` (stage-guard mismatch case) |
| Architect Low: RapidOCR import guard | **Closed** | `item_provenance.py:32-43` — `ImportError` or `AttributeError` returns without patching. With no tag, `resolve_ocr_assets` returns `None`, so `identify_ocr_engine` returns `(None, ())`: the engine is unidentified, never guessed (`:85-104`). | `test_ocr_quality.py:131` (asserts only that nothing is raised, not the null engine) |
| Architect Low: competing-worker recovery bound | **Closed in code**; live evidence pending | `test_fault_injection_qualification.py:504-510,540-567` assert `held_recovery <= elapsed + LEASE_SECONDS + 300` for the job A held (see D-5) | Live lane only; there is no `g2r3` log yet |
| QA R2-06: loose assertions | **Closed** | `test_fault_injection_qualification.py:88-90` (`assertion_runs == min(1, assertions)`). Cancellation keeps `<= 2` but adds a stronger timing bound: no request starts more than 1.5 s after the cancel (`:311-329`). Reinterpretation is now unconditional (`test_live_reinterpretation_qualification.py:132-140` ). | Live lanes; the change itself does not weaken anything |
| QA R2-04: harness `report_version` | **Closed** (Low residual) | `neuron/benchmarks/f0005_qualification.py:738-740` sets v2 with a comment. `metric_definitions` (`:746-748`) still does not state each metric's population, which R2-04 also asked for. | Not applicable |
| QA R2-05: timeout timeline | **Closed** | `test_fault_injection_qualification.py:152-160` records the client timeout, the quiescence start and the busy-request start, each relative to the fault. Quiescence end is start plus `quiescence_seconds`. The upstream statuses come from `proxy_timeline`. | Live lane |
| QA R2-09: neuron HEAD baseline | **Closed** | `artifacts/test-results/head-baseline-neuron-content-worker-v2.log` shows the same `[False]` failure at HEAD (1 failed, 4 passed) | My full-suite rerun matches |
| `# WHY:` tags | **Closed** | 7 tags in `document_worker.py` , `vllm_graph_client.py` and `conversion_process.py` | Not applicable |
| litellm 1.100.0 to 1.100.4 | **Closed** | `neuron/uv.lock` around line 1840 (sdist and all wheel hashes updated). The lock check passes and the venv has 1.100.4. | `uv lock --check --offline` |
| ADR-0073 §6 text | **Closed** | It now states the "pages OCR ran on" semantic, the add-only but *incompatible* class, the deploy-together, no-rollback and orphan-marker-drain rules, and the restore-drill proof gate. | Not applicable |
| ADR-0060 text | **Closed** | The header, the amendment title, "What becomes simpler" marked **Not in force**, the p95 "report v1" population, and the context-budget caveat are fixed. The report SHA-256 `55ce3484…aede`, corpus hash and expectation hash all match `artifacts/qualification/report.json` , which I recomputed. | `sha256sum` |
| ADR-0074 text | **Closed** (wording residual D-1, D-4) | It adds the boot id, the program and listener rules, refused-restart cleanup, the host/provider fault list, the pre-launch budget, the `conversion_started` contract, an Alternatives section, and the open items (M1 and the restart environment). | Not applicable |

## New Findings

### Critical

None.

### High

None.

### Medium

None.

### Low

- **D-1: a marker-clear failure in the middle of a run still records a model reason against the in-flight job, which contradicts ADR-0074 §2.**
  - Locations:
    - `neuron/packages/brain-ingestion/src/brain_ingestion/document_worker.py:71`
    - `neuron/packages/brain-ingestion/src/brain_ingestion/document_worker.py:225-242`
    - `neuron/packages/brain-ingestion/src/brain_ingestion/worker_guard.py:307-334`
    - `neuron/packages/brain-extraction/src/brain_extraction/vllm_graph_client.py:72`
    - `planning-mds/architecture/decisions/ADR-0074-local-document-job-execution-controls.md:42`
  - Scenario:
    1. Call 1 of a multi-call run is confirmed, then `marker_path.unlink()` fails. `uncertain` is set and the run continues.
    2. Call 2's dispatch raises `GuardError("provider_quiescence_required")`. This is recorded as a rejection of class `unavailable`.
    3. `model_failure_reason` returns `model_unavailable`, and `_record_failure` calls `queue.retry(...)` before `run_one` raises `WorkerStopped`.
    4. On the job's last attempt (`max_attempts`, `queue.py:496` ), that job ends **failed** with `model_unavailable`, although the provider answered correctly.
  - Contradiction: ADR-0074 says these faults leave queued jobs "for reclaim rather than failed". The worker does stop, so the queue is not drained; that was the L-N3 risk. Only the current job is charged.
  - Fix: add `provider_quiescence_required` to `_GUARD_FAULTS`, or check `guard.uncertain` before `_record_failure`.
- **D-2: the L5 cleanup does not confirm the group exit and can mask the refusal reason.**
  - Location: `neuron/packages/brain-ingestion/src/brain_ingestion/provider_supervisor.py:153-160`
  - The return value of `terminate_group` is ignored. If a member survives SIGKILL within 10 s (for example, uninterruptible GPU I/O), the operator sees only `provider_restart_unauthenticated` and is not told that an unauthenticated server may still be up.
  - `process.wait(timeout=5)` can raise `TimeoutExpired`, which replaces the `GuardError`. `main()` then exits with a traceback instead of the code. This still fails closed, because the marker stays dirty.
  - Security's remediation asked to "confirm the group is gone before re-raising".
  - Fix: on `False`, raise or log `provider_restart_cleanup_unconfirmed`, and suppress `TimeoutExpired`.
- **D-3: the boot-id comparison fails open when the current boot id cannot be read.**
  - Location: `neuron/packages/brain-ingestion/src/brain_ingestion/conversion_process.py:629-639`
  - `data.get("boot_id") not in (None, boot_id())` is True when `boot_id()` returns `None` and the receipt carries an id.
  - Every receipt is then treated as stale: the live converter group from this boot is neither checked nor terminated, and its staging is deleted underneath it.
  - This is unlikely on Linux, where `/proc/sys/kernel/random/boot_id` is always readable, but the direction is wrong for a fail-closed reaper.
  - Fix: treat an unknown current boot id as "same boot".
- **D-4: ADR-0074 overstates the program binding.**
  - Locations:
    - `planning-mds/architecture/decisions/ADR-0074-local-document-job-execution-controls.md:38`
    - `neuron/packages/brain-ingestion/src/brain_ingestion/worker_guard.py:431-446`
  - The ADR says the program must be "the `vllm` entry point itself (the console script, or the interpreter of the same virtual environment running its `bin/vllm` )". The code checks only basenames and a shared parent directory, so any directory with files named `python` and `vllm` passes (see the probe in the L4 row).
  - The exposure is the same UID and the 0700 control directory, so it stays Low, as in SEC-F5-L4.
  - Either bind `/proc/<pid>/exe` and the `vllm` realpath to an operator-owned allowlist, or narrow the ADR wording to "basename and co-located interpreter".
  - Related: `wait_ready` sends the API key to whatever answers on the port before listener ownership is checked (`provider_supervisor.py:141-152` ). A foreign same-host listener could capture the key. This ordering predates the delta, but the new ownership check could run first.
- **D-5: the recovery bound and some delta tests prove less than their names say.**
  - Recovery bound: `neuron/tests/integration/test_fault_injection_qualification.py:504-567`
    - `held_recovery` is measured from A's **claim**, not from the kill or the start of quiescence.
    - It is compared against a sum of monotonic `elapsed`, the lease and a 300 s slack, using the database clock.
    - The 300 s slack absorbs A's pre-kill conversion and dispatch time, so the assertion is loose.
  - Function-level tests:
    - `test_ocr_quality.py:131` checks only that nothing raises, not that the engine is null.
    - `test_document_worker_reasons.py:380` checks only `guard_fault`, not that `run_one` records no outcome.
  - When a PDF is unreadable, `_count_pages_needing_ocr` returns `0` (`docling_adapter.py:113-114` ). This is a declared count that understates, although the warning is present.

### Security and secrets check

- No secret or source text is added to logs or diagnostics.
- Token-counter exceptions are dropped (`from None`), and a test asserts they are absent.
- Receipts add only `boot_id`.
- The provider log is now owner-only.
- No test assertion was weakened.
  - `_fake_vllm` now runs through a co-located `python` symlink. The new rule requires this, and it does not relax any check.
  - The fault-injection and reinterpretation assertions are stricter than before.

### ADR text against code

- ADR-0074 §1 (boot id), §3 (pre-launch budget, `conversion_started` contract) and Alternatives match the code.
- §2 matches except for D-1 (the in-flight job is charged) and D-4 (the program-binding wording).
- ADR-0060 and ADR-0073 §6 match the code and the evidence; the report hashes were recomputed.

## ADR-0074 Acceptance Readiness

- **N1 verified: yes.**
  - The budget is enforced before every launch, through the only conversion entry points.
  - An exhausted budget is terminal `conversion_failed` with nothing launched.
  - Tests: `test_document_worker_reasons.py:357` , `:372`
- **L5 verified: yes.**
  - A refused restart terminates the group it started and leaves the marker dirty.
  - Proven through `quiesce_and_restart` in `test_worker_guard.py:446`
  - Residual D-2 is a confirmation and reporting gap, not a reopened orphan.
- **Overall: ready for the operator to accept.**
  - Recommended: narrow the §2 wording for D-1 and D-4, or fix the code, before or at acceptance.
  - SEC-F5-M1 and the restart environment stay recorded activation preconditions (ADR-0074 line 94).

## Recommendations

- [low] D-1: add `provider_quiescence_required` to `_GUARD_FAULTS` (or check `guard.uncertain` before `_record_failure`) so a marker-clear failure never charges the in-flight job, and add a `run_one` test — owner: Backend Developer; follow-up: before or at ADR-0074 acceptance
- [low] D-2: act on the `terminate_group` result in the refused-restart path, report `provider_restart_cleanup_unconfirmed`, and keep the original refusal code if `process.wait` times out — owner: DevOps; follow-up: before activation
- [low] D-3: treat an unreadable current boot id as the same boot in `reap_orphans` so the reaper stays fail-closed — owner: DevOps; follow-up: F0026 hardening
- [low] D-4 / SEC-F5-L4 residual: bind `/proc/<pid>/exe` and the `vllm` realpath to an operator-owned allowlist and check listener ownership before `wait_ready` sends the key, or narrow ADR-0074 §2 wording to the basename rule — owner: DevOps with Architect; follow-up: before activation, together with SEC-F5-M1
- [low] D-5: measure the competing-worker recovery bound from the kill or quiescence end, assert a null engine in the RapidOCR-guard test, add a `run_one` test for `usage_exceeds_reservation`, and add a test for the legacy `pipeline_source` metadata — owner: Quality Engineer; follow-up: next test revision, before any re-measurement
- [low] QA R2-04 residual: state each metric's population in the harness `metric_definitions` for `report_version` 2 — owner: Quality Engineer; follow-up: before any re-measurement
- [low] Attach `g2r3` live evidence for the competing-worker, cancellation, timeout-timeline and reinterpretation lanes changed by this delta — owner: Quality Engineer; follow-up: when the in-progress live run completes, before the G4 record

Result: APPROVED WITH RECOMMENDATIONS
