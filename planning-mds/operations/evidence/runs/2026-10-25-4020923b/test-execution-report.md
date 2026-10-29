# Test Execution Report — F0005-one-time-docling-ingestion run 2026-10-25-4020923b

> QE-owned. Runtime is the development host:
> - RTX 5070, CUDA visible;
> - vLLM 0.25.1 serving Phi-4-mini-instruct @ `cfbefacb99257ffa30c83adab238a50856ac3083` on authenticated loopback, max length 4,096;
> - PostgreSQL 18 (`brain-postgres`);
> - real Docling 2.126.0 / Docling-Graph 1.9.1 / RapidOCR 3.9.2.
>
> Live lanes are opt-in (`BRAIN_RUN_LIVE_QUALIFICATION=1`). Containerized build and smoke checks are in `deployability-check.md`. Every command is in `commands.log`; that log was written in batches after execution, not at run time.
>
> This run has three evidence rounds:
> - **Round 3** (2026-10-28) is the current evidence, prefixed `g2r3-`. It follows the G4 round-2 order: N1, SEC-F5-L4/L5/L6, the Code Review/Architect/QA Lows, the delta-review Lows D-1–D-5, litellm 1.100.4 and the post-decision check.
> - **Round 2** (2026-10-27, after the G3 rework of C1, H1, M1–M6, SEC-F5-L1–L3, S0003-AC3/AC4 and pypdf), prefixed `g2r-`. It passed G2/G3 round 2.
> - **Round 1** (2026-10-26) is history. G3 found it insufficient.

## Round 3 (current)

| Lane | Passed | Failed | Skipped | Notes |
|---|---|---|---|---|
| Neuron offline | 260 | 1 | 29 | The failure is the pre-existing `test_content_worker_v2[False]`; it fails identically on clean HEAD (`head-baseline-neuron-content-worker-v2.log`). |
| Engine offline | 424 | 11 | 0 | The 11 authx failures are pre-existing and identical on HEAD. |
| Live conversion | 2 | 0 | 0 | `g2r3-live-conversion` |
| Live provider/storage/auth faults | 12 | 0 | 0 | `g2r3-live-provider-storage-auth-faults` (final re-run). Storage ×2: 2 conversions, `failed`. |
| Live ambiguous timeout | 2 | 0 | 0 | `g2r3-live-timeout-faults` (final re-run). Both engines record `model_timeout`. The busy request started 13–16 s after the fault, the client timed out 30 s later, and vLLM was still generating at quiescence (89 s). Recovered in 134 s and 144 s. |
| Live kill points + competing workers | 5 | 0 | 0 | `g2r3-live-kill-points-and-competing-workers` (final re-run). The held job recovered in 270 s from the kill, within quiescence 39 s + lease 120 s + 300 s. Provider busy at quiescence. |
| Live reinterpretation | 3 | 0 | 0 | `g2r3-live-reinterpretation`. Distinct profile identities are asserted unconditionally. |
| Live decision branches | 11 | 0 | 0 | `g2r3-live-decision-branches` |
| Live 300 s deadline | 1 | 0 | 0 | `g2r3-live-production-deadline` |
| **Post-decision check (S0004-AC7)** | 1 | 0 | 0 | `post-decision-check.log`. Committed config (SHA `e80cb506…`, `direct-baseline`, v2 off) in a fresh composition: `gl-q-001` completes on `direct-baseline` with a v1 bundle; the only call is the baseline's. |
| Lint / type | clean | | | `g2r3-lint-typecheck.log` |

**Round-3 retries:**

1. **Attempt 1** (03:27–03:41, `g2r3-attempt1/`). Conversion and the deadline passed.
   - The provider/storage/auth lane failed at its eighth case: a Graph-dense call ran past the 30 s timeout while vLLM generated at about 13 tokens/s. The cause was GPU contention from the concurrent independent delta reviewer's offline Docling/RapidOCR tests.
   - The guard correctly went uncertain, and the later lanes were refused.
   - Recovered by supervised quiescence (receipt `…/1793173355312796008.json`), which also exercised the round-3 program and listener checks on a real restart. The reviewer's background work was then stopped, so that the GPU ran nothing else.
2. **Attempt 2** (03:55–04:45, `g2r3-attempt2/`). Six lanes passed. The Graph-dense timeout case recorded **no** failure reason.
   - This was a real regression from fix D-1: the call after the timeout was refused with `provider_quiescence_required`, which was then treated as a host fault, hiding the `model_timeout`.
   - Fixed: host-fault outcomes no longer mask a genuine model failure in the same run. The worker still stops on the uncertain guard. Unit tests were added.
   - The three fault lanes were re-run (04:47–05:09) and all passed.



## Commands Executed

| Lane | Command (abridged; full form in `commands.log`) | Round-2 artifact |
|---|---|---|
| Neuron offline full | `cd neuron && pytest --cov --cov-config=<run>/artifacts/coverage/neuron.coveragerc` | `g2r-neuron-full.log/.xml` |
| Engine offline full | `cd engine && pytest --cov=brain_jobs --cov=brain_content` | `g2r-engine-full.log/.xml` |
| Engine HEAD baseline | the same suite on a clean `HEAD` worktree (round 1) | `head-baseline-engine-full.log` |
| Live conversion (S0001) | `pytest test_live_conversion_qualification.py -k 'not production'` | `g2r-live-conversion.log/.xml` |
| Live 300 s deadline | `pytest test_live_conversion_qualification.py -k production` | `g2r-live-production-deadline.log/.xml` |
| Live provider/storage/auth faults (S0002) | `pytest test_fault_injection_qualification.py -k 'not timeout and not second_worker and not killed'` | `g2r-live-provider-storage-auth-faults.log/.xml` |
| Live ambiguous timeout, both engines | `pytest test_fault_injection_qualification.py -k timeout` | `g2r-live-timeout-faults.log/.xml` |
| Live kill points + competing workers | `pytest test_fault_injection_qualification.py -k 'killed or second_worker'` | `g2r-live-kill-points-and-competing-workers.log/.xml` |
| Live reinterpretation (S0003) | `pytest test_live_reinterpretation_qualification.py` | `g2r-live-reinterpretation.log/.xml` |
| Live decision branches (S0004-AC5–AC7) | `pytest test_pipeline_selection.py` | `g2r-live-decision-branches.log/.xml` |
| Measured comparison (S0004-AC2/AC3) | `python neuron/benchmarks/f0005_qualification.py …` (round 1 only; immutable, never re-run) | `../qualification/report.json` |
| Lint / type | ruff check/format + mypy on all changed files | `g2r-lint-typecheck.log` |

## Pass/Fail Counts

Round 2, current:

| Lane | Passed | Failed | Skipped | Notes |
|---|---|---|---|---|
| Neuron offline | 235 | 1 | 29 | 48 new tests (OCR quality, H1 client/service, reasons, guard record validation, S0003-AC4, baseline prompt identity). The failure is pre-existing (below). Skips are live-only lanes. |
| Engine offline | 424 | 11 | 0 | All 11 failures are pre-existing and fail identically on clean HEAD. New: migration 0010 and config loader tests. |
| Live conversion | 2 | 0 | 0 | All 13 documents publish before the first model request. Every manifest (v1 and v2) records the OCR page count, the observed pages and the pinned RapidOCR 3.9.2 engine, plus 3 asset digests. Scanned documents OCR every page. Native documents with image regions show observed OCR pages (for example gl-q-002 [1, 2]). Slowest attempt 13.7 s. |
| Live 300 s deadline | 1 | 0 | 0 | |
| Live provider/storage/auth faults | 12 | 0 | 0 | Five provider modes × two engines, storage ×1/×2, revocation, cancellation. **Storage ×2 ends `failed` after exactly 2 conversions** (reconvert at most once; M2). |
| Live ambiguous timeout | 2 | 0 | 0 | **The provider was busy when the client timed out and still busy at quiescence (M4).** direct-baseline: quiescence 110 s, recovered 153 s. graph-dense: quiescence 38 s, recovered 104 s. Provider concurrency 1 throughout. |
| Live kill points + competing workers | 5 | 0 | 0 | Re-run on current code (QA had found round 1 stale). Each of the 4 kill points ends with single effects. Second worker refused; the killed holder's request was still running in the provider at the kill and at quiescence (91 s); no claim before confirmed quiescence. |
| Live reinterpretation | 3 | 0 | 0 | Zero conversion; bundles unchanged; ≤ 4,096 tokens; fabricated 0; targeting rejected. **S0003-AC3:** on all 8 completed runs, the provenance ledger and graph are retained as run outputs, and every ledger reference resolves to an item in the saved DoclingDocument. |
| Live decision branches | 11 | 0 | 0 | Engine identity asserted whatever the job outcome; no Graph call on any direct-baseline branch; the accepted and rollback branches publish and read back v2 bundles (M5). |

S0003-AC4 is now proven offline and deterministically: `test_interpretation_rejections.py::test_relationship_output_fails_closed_with_no_assertions[direct-baseline|graph-direct]`. The live relationship probe still runs, but it usually ends with a model failure before reaching the check.

## Skipped Tests And Rationale

The 29 neuron skips are the live lanes (`BRAIN_RUN_LIVE_QUALIFICATION` unset in the offline run). They are executed separately above against the real provider. Nothing else is skipped.

## Raw Test Artifact Paths

All under `artifacts/test-results/` .

- **Round 2:**
  - offline: `g2r-neuron-full.{log,xml}`, `g2r-engine-full.{log,xml}`;
  - live: `g2r-live-conversion.*`, `g2r-live-production-deadline.*`, `g2r-live-provider-storage-auth-faults.*`, `g2r-live-timeout-faults.*`, `g2r-live-kill-points-and-competing-workers.*`, `g2r-live-reinterpretation.*`, `g2r-live-decision-branches.*`;
  - lint: `g2r-lint-typecheck.log`.
- **Round 2, first attempt** (`g2r-attempt1/`, see history below). Its conversion log was overwritten by the re-run before it was copied; the summary is in `g2r-attempt1/summary.log`.
- **Round 1:** `g2-neuron-full.*`, `g2-engine-full.*`, `live-*`, `head-baseline-engine-full.log`, `g1-regression-baseline.xml`.
- **Measurement:** `artifacts/qualification/`.

## Failed / Retried Command History

Round 2:

1. **First live attempt (22:45–22:55), 1 lane passed and 6 failed** (`g2r-attempt1/`).
   - The conversion lane failed on a wrong test assumption: native documents never OCR. Docling also OCRs image regions on text-layer pages. The test was corrected to check that observed pages are valid; scanned documents must OCR every page.
   - In the provider-fault lane, the round-1 per-request timeout of 10 s (production 60 s) was shorter than one full-reservation Graph-dense call on this GPU (about 11 s, visible in the vLLM log). The client timed out, the guard correctly marked the request uncertain, and every later case and lane was correctly refused with `provider_quiescence_required`.
   - The fault cases now use a 30 s request timeout. The `timeout` mode's forwarded busy generation still lasts about 60 s, measured with `max_tokens` 3,800 and `ignore_eos`.
   - The dirty marker was cleared only through supervised quiescence, which exercised the new provider-record and unauthenticated-restart checks live (receipt `…/receipts/1793156237639102048.json`).
   - All six lanes were then re-run and passed (22:57–23:41). The 300 s deadline lane passed in the first attempt and was not repeated.
2. **Offline, during the rework:**
   - Two guard tests used a fake provider that is not a `vllm serve` group leader. They were updated, and five tampering cases were added.
   - A Graph node-ID collision affected the relationship probe template defined inside the test module. The probe now lives in `tests/support/relationship_probe.py`, loaded by path.

Round 1 (history):

1. **Ambiguous timeout, Graph dense, 1 failed.** The proxy measured its own reply interval rather than the provider's. Fixed in the proxy; the rerun passed. G3 (M4) then found the provider was idle during held requests; round 2 fixes that.
2. **Decision branches, first run, 1 failed.** Test bugs (a `KeyError` on the legacy row; the contract read only from completed jobs); fixed. G3 (M5) then found engine identity unchecked on failed jobs; round 2 fixes that.
3. **Engine offline, 29 errors.** F0004's `publication` fixture pinned the schema at `0008`; it now uses `head`. Disclosed in `g2-self-review.md`.
4. **gl-q-013 conversion failure** from a damaged page. Product fix: such pages are recorded as failed and the document as `partial`.
5. **Evidence re-executions** (06:06–06:14) to retain raw logs.

**Pre-existing failures (not F0005), identical on clean HEAD:**
- 11 engine authx tests: `reconcile_authx.py` runs at the 0005–0007 schema against ORM models that already include F0004's `content_artifact.artifact_contract_version`.
- Neuron `test_content_worker_v2.py::test_publication_import_and_second_profile_reuse[False]`: Docling on this host merges two fixture lines.

Both are logged as follow-ups.

## AC Coverage Result

Every F0005 AC maps to an executed test or review step (`test-plan.md`).

- **Newly proven in round 2:**
  - S0001-AC2: OCR page count and engine on every bundle;
  - S0003-AC3: ledger retained live;
  - S0003-AC4: deterministic fail-closed test;
  - S0002-AC2/AC4: re-run on current code, with the provider busy;
  - S0002-AC3: two conversions at most.
- **Partly proven, carried to G3 review:**
  - the five audit ACs: job events carry job, generation, reason and time; authorization decisions are in `audit_event`; no single record asserts every listed field;
  - S0002-AC4: duplicate submissions are idempotent by request key, but Graph's internal fan-out is bounded only by the shared single model slot;
  - S0005-AC3/AC4: the fallback rate is reported; the content reader and restore drill are covered by the F0004 suites rather than corpus v2 bundles.
- **The measured comparison blocks activation** (S0004-AC3).
- **Pending G4:** S0004-AC4 verdicts and S0004-AC7 rejection.
- **Unreachable** because thresholds were missed: S0004-AC5 and S0005-AC5.

## Result

PASS WITH RECOMMENDATIONS
