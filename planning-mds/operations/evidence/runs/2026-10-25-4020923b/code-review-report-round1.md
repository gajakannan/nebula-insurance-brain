# Feature Code Review Report

Feature: F0005 — One-time document ingestion (feature action run `2026-10-25-4020923b`, gate G3)

Reviewer: independent Code Reviewer session (fresh context; did not author code, corpus, expectations or evidence). Reviewed 2026-10-26 against the uncommitted working tree on `feature/f0005-live-qualification` (`git diff` plus untracked files), the approved assembly plan (Steps 0a–7), the PRD, the five stories, BLUEPRINT and SOLUTION-PATTERNS.

## Summary

Result: REJECTED

- Assessment: REJECTED. One acceptance criterion is not met (S0001-AC2), and one High correctness defect exists: a failed model call can still produce a successful Graph-dense run. Most of the work is sound and well tested: the deadline and latch, the host guard and in-flight marker, the reason taxonomy, pipeline pinning and queue admission. The rework is narrow. See Recommendation.
- Files reviewed: 36. That is 17 runtime modules, the migration, `config/local.yaml`, 14 test modules, the harness and the fault proxy.
- Issues found: Critical 1, High 1, Medium 6, Low 6.

### Per-story verdicts (for STATUS)

| Story | Verdict | Basis / evidence |
|---|---|---|
| F0005-S0001 | **FAIL** | AC2 not met (C1): bundles record no OCR page count, and no OCR engine name/version on the ordinary v1 path. AC1, AC3, AC4, AC5 and AC6 pass: `artifacts/test-results/live-conversion.log`, `live-production-deadline.log`, `neuron/packages/brain-ingestion/tests/test_conversion_process.py`. |
| F0005-S0002 | **PASS** (with recommendations M1–M4) | `live-provider-storage-auth-faults.xml` (12/12), `live-timeout-faults.log` plus the Graph-dense rerun, `live-kill-points-and-competing-workers.log`, `engine/packages/brain-jobs/tests/test_postgres.py` (depth bound, re-run by me), `test_document_worker_reasons.py` |
| F0005-S0003 | **PASS**. H1 must be fixed before any Graph-dense re-measurement. | `live-reinterpretation.xml` (3/3). The defect in H1 was not triggered in the recorded runs: all 54 dense-to-direct fallbacks in `qualification/report-run.log` follow a recorded call failure, and the log shows no budget or context rejection. |
| F0005-S0004 | **PASS** for code scope (harness, selection, rollback, pinning). AC4 and AC7 still need reviewer verdicts and the operator decision; AC5 cannot be reached. | `qualification/report.json` (`void: false`; committed config hash `e80cb506…` equals the working tree), `live-decision-branches-rerun.xml` (11/11), `test_pipeline_selection.py`. See M5 and M6. |
| F0005-S0005 | **PASS** (AC1–AC4; AC5 not applicable before acceptance) | `test_ocr_asset_provenance.py`, `live-conversion.log` rows (fallback 11/13 reported), `report-summary.md`. See L1. |

### Independent verification performed

- Offline neuron: `packages/brain-ingestion/tests`, `test_pipeline_selection.py`, `test_worker_cli_enqueue.py`, `test_vllm_graph_client.py` and `test_fault_injection_qualification.py`. Result: **142 passed, 20 skipped** (the skips are live-only), using the PostgreSQL URLs.
- Offline engine: `packages/brain-jobs/tests` (including the PostgreSQL concurrent-depth test), `brain-content/tests/test_config.py` and `test_job_event_reason_migration.py`. Result: **47 passed**.
- Probe (scratch script, no product edits): `VllmGraphClient` rejections raised before dispatch leave no call record. `call_budget_exceeded` leaves the recorded outcomes as `['complete']`; `context_limit_exceeded` leaves them as `[]`. This confirms H1.
- I read the upstream Docling-Graph 1.9.1 code. `llm_backend.py:1159-1161` and the dense orchestrator (`orchestrator.py:2501`, `:2866`) swallow per-call exceptions. `many_to_one.py:522-527` falls back to one direct call whenever dense returns no model.
- KG: `validate.py --check-symbols` passes (read-only). The new modules have no symbol entries yet; that regeneration belongs to G7 (feature.md Step 7), so it is not a G3 finding. `risk.py` gives `document_worker.py` and `queue.py` 6 and `graph_interpretation.py` 4. All are below the band that needs a second reviewer.

## Vertical Slice Completeness

- [x] Backend complete: queue reasons, migration 0009, depth bound, worker, guard, supervisor. F0005 has no API endpoint.
- [x] Frontend: not in scope (PRD: no UI).
- [ ] AI layer complete. Supervised conversion, provenance and the direct-baseline path are done, but dense result acceptance is unsound (H1).
- [x] Tests complete: unit, PostgreSQL and live lanes are recorded. Strength gaps are listed in M4–M6.
- [x] Can be deployed independently. The committed config is `direct-baseline` with v2 off, so activation is blocked.

## Findings

### Critical

**C1 — S0001-AC2 not met: the bundle does not record OCR page count or OCR engine name/version.**
- Location: `neuron/packages/brain-ingestion/src/brain_ingestion/bundle_writer.py:152-164`, `content_projection.py:246-248`, `content_workflow.py:180-193`.
- What: `ParseResult.ocr_page_count` is computed (`docling_adapter.py:45`) and carried through the child handoff (`conversion_process.py:124`). Neither the v1 nor the v2 manifest persists it. On the ordinary committed path (v1, `capture_provenance=False` at `content_workflow.py:188`), no OCR engine identity is recorded at all. v2 records it only per item. The v1 fallback records asset digests, but not engine name/version or OCR page count.
- Evidence: `live-conversion.log`. The scanned documents gl-q-007, 008 and 010 publish contract 1 with `ocr_producers: []`. The authors disclose this in `g2-self-review.md` (S0001-AC2 "Partly met").
- Why it matters: the AC lists these fields explicitly, and the severity framework treats an unmet AC as Critical. The plan (Step 3) required the work to stop and return to the Architect when the contract cannot express what is observed. Implementation continued instead.
- Fix: either (a) the Architect approves a contract change that persists `ocr_page_count` and the document-level OCR engine identity in the extraction-quality block, which needs F0004 contract and consumer re-qualification; or (b) the PM/Architect record an AC amendment with rationale. S0001 cannot pass until one of these is recorded.

### High

**H1 — A Graph-dense run can complete successfully after failed model calls, or with a direct-contract answer labelled dense.**
- Location: `neuron/packages/brain-extraction/src/brain_extraction/graph_interpretation.py:214` (the acceptance rule) and `:245`; `vllm_graph_client.py:221-263`.
- What: the worker accepts a run unless a recorded call has an outcome other than `complete`. Several rejections are raised before a call record is appended: `context_limit_exceeded` (line 252), `call_budget_exceeded` and `token_budget_exceeded` (lines 260-263), and `run_deadline_exceeded`, `cancelled` and `usage_exceeds_reservation` (via `_check_active`, lines 221/255/258). Graph 1.9.1 swallows per-batch and per-fill exceptions, and falls back to one direct call when dense returns no model.
- Failure scenarios:
  1. **Over budget:** a corpus document has more skeleton and fill jobs than `max_calls=16`, or one fill batch exceeds 4,096 tokens. Those requests are rejected before dispatch and leave no record. Graph keeps the other chunks and the run finishes `complete` or `partial`. The missing fields are imported as absent, which scores as abstention, and the job is `complete`.
  2. **Empty skeleton:** a skeleton call returns valid but empty JSON, so all calls are `complete`. Graph falls back to `extract_from_markdown` (`many_to_one.py:522-527`), and the run is published with dense pipeline identity and a direct-contract answer. That breaks S0004-AC6 ("no run mixes engines") and S0003-AC1 run identity.
- The harness has the same blind spot: `f0005_qualification.py:446` counts `context_rejections` from call records that can never contain that outcome, so the reported "Context budget: 0" is true by construction.
- Evidence: my probe above. The authors' claim that "any failed model call fails the attempt" (`g2-self-review.md`, Step 4) holds only for calls that were dispatched.
- Fix: record every rejection in `_calls` with a `failure_class`, before raising (budget and deadline rejections become their own non-complete outcomes). Detect Graph's dense-to-direct fallback, for example from the number of dense skeleton/fill phases or the trace event `structured_output_fallback_triggered` / "Dense extraction returned no model", and fail it as `model_malformed_output` or a new explicit reason. Add offline tests with a recorded transport for both scenarios.

### Medium

**M1 — Unexpected post-publication errors are recorded as `conversion_failed` and use up the reconversion budget.**
- Location: `neuron/packages/brain-ingestion/src/brain_ingestion/document_worker.py:121` and `:203-211`. The test `test_document_worker_reasons.py:41` locks this behaviour in.
- Scenario: attempt 1 fails conversion (`conversion_failed`, retried). Attempt 2 publishes the bundle, then hits a transient DB `OperationalError` in `queue.publish`, or a `ValueError` in mapping. `classify()` falls through to `conversion_failed`, which counts as a second pre-publication failure, so the job ends terminally `failed`. No reconversion was needed, and the recorded reason says conversion failed when it succeeded.
- Related: `document_worker.py:315` labels `run_deadline_exceeded`, `usage_exceeds_reservation` and template `ValidationError` as `model_malformed_output`. This weakens S0002-AC1's "distinct recorded reason".
- Fix: record whether the attempt passed ready publication, and only treat failures before that point as pre-publication. Map unknown post-publication errors to a non-conversion reason, which needs an expand-only CHECK addition if a new code is required.

**M2 — The reconvert-at-most-once rule does not hold across a crash followed by a storage failure.**
- Location: `document_worker.py:203-211`.
- Scenario: the worker is SIGKILLed during publication, before the manifest marker, so no reason is recorded and the lease expires. Attempt 2 reconverts and hits `storage_write_failed`; there is no prior pre-publication reason, so the job retries. Attempt 3 reconverts again. That is two reconversions, which S0002-AC3 forbids ("storage write failure or crash before the manifest completion marker … reconverts at most once"). The total is bounded only by `max_attempts=3`.
- Fix: count prior conversion launches, for example from durable launch receipts or a `conversion_started` job event, instead of only recorded failure reasons.

**M3 — A guard infrastructure fault drains the queue into permanently failed jobs.**
- Location: `vllm_graph_client.py:278-283` and `worker_guard.py:307-312`, `:115-126`.
- Scenario: `/tmp` fills up or loses permissions. Every `inflight` call raises `inflight_marker_not_durable` and nothing is sent (correct). But `guard.uncertain` is never set, so the worker keeps claiming, and each job fails `model_unavailable` three times and ends `failed`. A failed `_atomic_write` also leaves `.<marker>.<pid>.tmp` behind, so later `O_EXCL` opens in the same process keep failing after the disk recovers. Resubmitting the same source returns the existing failed job, because `queue.py:318-322` is idempotent on the request key. The jobs therefore cannot be recovered without a new identity.
- Fix: treat guard and marker infrastructure errors as `WorkerStopped` (stop claiming), and clean up the temporary file when an atomic write fails.

**M4 — The fault proxy never puts an uncertain request on the provider, so overlap and quiescence are only proven against an idle provider.**
- Location: `neuron/tests/support/fault_proxy.py:96-112`; `test_fault_injection_qualification.py:473-483`.
- What: `timeout` mode forwards the request, waits for the upstream response, and then holds the reply ("the provider did the work"). The "kill A during a held provider request" case and the ambiguous-timeout case therefore never have GPU work in flight. The plan (Step 4) requires "an ambiguous client timeout while the provider still works". `max_concurrency() <= 1` and "no overlapping old/new provider work" pass trivially. The proxy fix after the 01:36 failure (measuring the upstream interval) is legitimate, but it shows the provider interval had already closed.
- The control logic itself (dirty marker blocks claims, receipt-gated clear) is proven.
- Fix: add a proxy mode that holds before or while forwarding, or a slow-generation request (large `max_tokens`), so the provider is busy at kill or timeout. Then assert that quiescence observes and stops it.

**M5 — The decision-branch test passes without checking the engine when a job fails.**
- Location: `neuron/tests/integration/test_pipeline_selection.py:151-156`.
- What: engine identity is asserted only when `job_state == "complete"`. In the recorded rerun the "accepted" (graph-dense) branch failed, so its engine/no-mix identity was never checked. The plan's required assertion "no Graph call on new rejection/default jobs" is not made in any branch, for example by checking for no `dense_skeleton` or Graph-stage call. A rollback test that checks v2 readability is also missing: the rollback row published contract 1.
- Fix: assert pinned engine identity from the job and run metadata whatever the outcome, assert that direct-baseline jobs make no Graph calls, and add an explicit v2-readability check for the rollback branch.

**M6 — Harness latency measures only the surviving attempt of completed runs.**
- Location: `neuron/benchmarks/f0005_qualification.py:584-592`.
- What: `timings` keeps the last attempt per job, and p95 is computed only over completed jobs. For Graph dense, that is 8 of 26 document-profiles. Failed and retried attempts' wall time is excluded. The PRD defines latency as "p95 wall time per document-profile interpretation". This did not change the outcome (dense missed anyway), but the harness is the gate for any re-measurement.
- Fix: report p95 over all document-profiles, summing attempt time per job, with completed-only p95 as a secondary figure. The `context_rejections` metric in H1 needs the same correction.

### Low

- **L1** — `item_provenance.py:73`: the asset "revision" is the RapidOCR package version (`@rapidocr==3.9.2`), not a model-asset revision. That is acceptable only because the pin file ties assets to that package version. State this in the manifest documentation or ADR so S0005-AC2's "revision" is interpreted consistently.
- **L2** — `graph_interpretation.py:52-64`: the direct baseline copies the F0001 prompt text instead of reusing `OpenAICompatibleExtractionAdapter`, as the plan (Step 6) describes ("wrap"), so the two can drift. It also repeats an item's text once per `prov` entry (`for _prov in item.prov`), which differs from F0001's per-block join when an item has several provenance entries. Add a test that pins the prompt hash against the F0001 adapter.
- **L3** — `conversion_process.py:600-605`: if `/tmp` survives a host reboot (as on WSL/ext4), a leftover launch receipt whose PID has been reused makes every startup fail `converter_ownership_unconfirmed` until someone cleans up by hand. Record `/proc/sys/kernel/random/boot_id` in the receipt and treat a receipt from a different boot as gone. Separately, the runbook should exclude `/tmp/nebula-brain-inference-*` from systemd-tmpfiles aging. Aging could unlink a long-held lock inode or a dirty marker.
- **L4** — `worker_cli.py:227-238` and `document_worker.py:184-187`: after `converter_cleanup_unconfirmed`, the process exits and the OS releases the guard. The plan (Step 2.5) says to "retain the guard". Safety now depends on the startup reaper failing closed, which it does. Record this deviation in the runbook, or block in the foreground until DevOps acts.
- **L5** — `submission.py:150-163` (disclosed): with the queue-full pre-check race, the losing submitter has already stored source bytes and provisioned access rows. The bound itself holds: the PostgreSQL test shows 3 admitted and 5 rejected. Consider adding an orphan sweep, or moving the store step after admission.
- **L6** — Dimension 12: non-obvious decisions (latch re-check at acceptance, refused-connect confirmation, legacy `graph-direct` meaning, terminal-reason sets) have good rationale comments but no `# WHY:` tags, so `decisions-index.yaml` will not pick them up at G7. Tag the key ones.

### Disclosed risks, verified

| Author disclosure | My finding |
|---|---|
| Queue bound race leaves orphan source objects | Confirmed. The bound holds under concurrency (PostgreSQL test re-run). See L5. |
| OCR page-count contract gap | Confirmed, and it is an unmet AC → C1 |
| 84.6% v2 fallback | Confirmed in `live-conversion.log`; reported as S0005-AC3 requires |
| Weak baseline (tables excluded) | Confirmed. The prompt matches F0001 (L2); Graph dense misses the absolute thresholds anyway |
| Live timeout failure and proxy fix | Fix is legitimate. It also shows the provider was never busy during "held" requests → M4 |
| Graph dense fallback is failed by the worker | True only when the skeleton call fails after dispatch → H1 |

## Pattern Compliance

- [x] Clean architecture respected. Engine `brain_content.config` does not import the AI runtime (it duplicates the pipeline enumeration on purpose). Neuron-to-neuron imports stay inside ADR-0060 ownership.
- [x] SOLID principles followed. The guard, supervisor, converter and worker have narrow responsibilities. `DocumentWorker.__init__` is growing, but that is acceptable.
- [x] SOLUTION-PATTERNS.md applied: jobs with idempotency keys, leases, fencing and outbox; append-only reason codes with no source text; expand-only migration with a guarded downgrade.
- [x] Test coverage ≥80% for feature logic: changed-line coverage is 82.0% (921/1,123) in `artifacts/coverage/changed-line-coverage.md`. `content_workflow.py` is at 40.9% offline; the supervised publication branch is covered only by the live lanes.

## Acceptance Criteria

- [ ] All feature ACs met. S0001-AC2 is not (C1). S0004-AC4, AC5 and AC7 wait on verdicts and the operator decision, which is outside code scope.
- [x] Edge cases handled: empty/unreadable pages become failed pages (`docling_adapter.py:57-69`), encrypted or corrupt input gives explicit `conversion_failed`, unpinned assets fall back to v1, `queue_depth_exceeded`.
- [ ] Error scenarios covered. Provider, storage, kill, cancel and revocation are covered, but H1 (silent success), M1/M2 (reason and reconversion accounting) and M3 (guard I/O fault) remain.

Focus-area conclusions:
- **300 s deadline, latch, cleanup, orphans:** correct. The deadline is set before staging/launch. The watchdog never holds the latch while waiting. `accept()` re-checks the monotonic clock, so a late or blocked handoff cannot win. Group TERM→KILL→reap checks every group member, not just the leader. Receipts are written before the start ack, and a parent dying before the ack makes the child exit unconverted. The reaper refuses reused PIDs (but see L3).
- **Host lock and in-flight marker:** correct. The lock key is a canonical loopback identity, the directory is fixed by UID with 0700/owner/symlink checks, `flock` is held on a non-inheritable FD, and the inode is never unlinked. The marker is fsynced before dispatch and cleared only on a terminal response or a refused connect. `max_retries=0` prevents hidden SDK retries. A dirty marker blocks startup and every later dispatch; the semaphore serialises Graph's fan-out. Infrastructure error handling is M3.
- **Reconvert-at-most-once and terminal reasons:** correct for single faults. Gaps are M1 and M2.
- **Queue-depth admission:** correct under concurrency on PostgreSQL. The advisory transaction lock is taken before the count under READ COMMITTED, and duplicates stay idempotent.
- **Pipeline pinning and legacy meaning:** correct. The pipeline is part of the request key and payload, and retries use the pinned value. A legacy payload with no pipeline maps to `graph-direct` with the exact pre-change `requested_configuration`, and its payload is not rewritten.
- **Can a failed model call be reported as success?** Yes, for Graph dense (H1). No for direct-baseline and graph-direct, which make a single call, so any rejection produces `output=None`.
- **Do tests prove their claims?** Mostly. M4 and M5 are the exceptions.
- **Is activation truly blocked?** Yes. `config/local.yaml` sets `extraction.pipeline: direct-baseline` and `content.v2_writer_enabled: false`, and the pipeline must be set explicitly. There is no environment override (`load_extraction_config`), the isolated config cannot move the guard, and the report's `committed_config_sha256` matches the working tree. These are uncommitted working-tree values, so the eventual commit must carry them.

## Recommendation

REJECT (fix critical first). The rework is narrow:
1. Resolve C1 through an Architect/PM disposition: a contract extension, or a recorded AC amendment.
2. Fix H1 in `vllm_graph_client.py` and `graph_interpretation.py`, with offline tests for pre-dispatch rejection and the dense-to-direct fallback. Correct the harness's `context_rejections` metric.
3. Address M1–M3 in `document_worker.py` and `worker_guard.py`, and strengthen M4–M5 before any re-measurement.

The measured rejection outcome in `report-summary.md` does not depend on H1 or M6. Nothing I found would change the operator's G4 choice to reject Graph dense, and the rejection settings are already in place.
