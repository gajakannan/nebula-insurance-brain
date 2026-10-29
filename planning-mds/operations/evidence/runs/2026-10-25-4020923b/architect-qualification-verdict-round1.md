# Architect Qualification Verdict — F0005 run 2026-10-25-4020923b

> Independent Architect review session for F0005-S0004-AC4, written 2026-10-26. This reviewer did not write the code, the corpus or the expectations under review. The review covers the uncommitted working tree on `feature/f0005-live-qualification` (`git diff` plus untracked files). It is judged against ADR-0060 (including the Phase B control amendments, proof gates and the "Acceptance scope (2026-10-23)" paragraph), the approved assembly plan (Steps 0a–7), the PRD, the five stories, SOLUTION-PATTERNS and F0004's content contract. Everything was read-only. No ADR, STATUS or knowledge-graph file was changed. Changing ADR-0060's status is the operator's G4 decision.

Result: PASS WITH RECOMMENDATIONS

This result covers architecture conformance and the quality of the evidence. It is not a pass for Graph dense, which failed qualification (see Qualification Outcome).

## Summary

- **The implementation conforms to the approved Phase B design on every control the plan required:**
  - the parent owns the 300 s outcome and the publication fence;
  - conversion runs in a process group that is cleaned up as a whole, with an orphan reaper that checks process start time;
  - one host-guarded worker runs per canonical endpoint, with a durable in-flight marker and confirmed quiescence;
  - the checkpoint is published before any model call, and content is parsed once;
  - jobs are pinned to a pipeline, legacy jobs keep their meaning, and the default/rollback settings are explicit;
  - package boundaries are neutral, and graph output is kept out of canonical tables.

  Live evidence backs each point. Examples: the deadline decision at 300.002 s with 2.03 s cleanup, one conversion per job across all fault modes, a refused second worker, and quiescence enforced after SIGKILL.
- **The measured comparison is valid** (`void: false`; corpus and expectation hashes recorded before measurement). Graph dense misses four PRD thresholds: accuracy, abstention, evidence resolution and latency. S0004-AC3 therefore blocks activation, and only the S0004-AC7 rejection branch is permitted.
- **ADR-0060 recommendation: it stays Proposed.** It must not be Accepted. Its text must record the failed gates, and a dated reopen condition must apply; if no re-plan is approved by then, the operator should mark it Rejected.
- **Main architectural issue (High):** the Phase B controls now ship as the runtime of the *direct baseline*, but their only design authority is a Proposed ADR. They include a frozen database enumeration (migration 0009). They need their own accepted ADR before G7 closes. See Home For Shipped Controls.
- **Other recommendations (Medium/Low):**
  - The direct baseline duplicates F0001's prompt instead of wrapping the adapter.
  - Unrecognised exceptions are recorded as `conversion_failed`.
  - The queue bound was approved in the story but never designed in the plan.
  - S0001-AC2 has a gap in the content contract.
  - Several smaller items are listed under Findings.

## Design Conformance

| Plan step / ADR-0060 amendment | Verdict | Evidence |
|---|---|---|
| Step 0 preflight / S0001-AC1 pins | Conforms | G1 PASS (`gate-decisions.md`): `uv sync --locked`, 40/40 regression baseline. The report `pins` block records Graph 1.9.1 wheel sha256 `04538ef0…`, Docling 2.126.0, docling-core 2.95.0, RapidOCR 3.9.2 and model/tokenizer `cfbefacb…`. The lock is unchanged from HEAD (`deployability-check.md`). |
| **0a — canonical endpoint key** | Conforms | `worker_guard.py:62-90`: scheme, numeric loopback address, effective port and normalized path. Rejects multiple addresses, non-loopback hosts and credentials in the URL. The key is SHA-256 of the canonical string (`:57-59`), never the credential, model or tenant. |
| **0a — fixed host directory, flock, no inheritance** | Conforms | `control_directory()` is derived from the UID only (`:102-104`). The directory must be 0700, owned by the account and not a symlink (`:225-236`). `flock(LOCK_EX\|LOCK_NB)` returns `inference_guard_busy` (`:253-259`). The descriptor is `O_CLOEXEC` and non-inheritable, and the lock inode is never unlinked (`:244-279`). The worker CLI acquires the guard before composing or claiming (`worker_cli.py:207-219`). The isolated-config override is rejected (`worker_cli.py:88-93`). Evidence: `test_worker_guard.py:115,135` and live `inference_guard_busy` (`test_fault_injection_qualification.py:469-471`). |
| **0a — one model semaphore across all paths** | Conforms | One `BoundedSemaphore(1)` per owner is shared by every client the factory creates (`worker_cli.py:121-134`). Dispatch happens inside the slot (`vllm_graph_client.py:252-276`). Live proxy `max_concurrency ≤ 1` on both engines, including Graph fan-out. |
| **0a — durable in-flight marker before dispatch** | Conforms | `inflight()` writes atomically and fsyncs the file and its directory. If durability fails it sends nothing (`worker_guard.py:294-322`; the client maps that to `InferenceRejected` before the HTTP call, `vllm_graph_client.py:276-283`). The marker is cleared only on a terminal response, an HTTP status error or a refused connection (`:295-316`). A dirty marker makes the worker stop claiming (`document_worker.py:156-161,199-200`). |
| **0a — confirmed quiescence before replacement** | Conforms | Startup calls `require_quiescent()` before any claim (`worker_cli.py:116`). `provider_supervisor.quiesce_and_restart` holds the guard, verifies start ticks, terminates the whole group, restarts the recorded argv, checks the pins, writes the receipt and only then clears the marker (`provider_supervisor.py:95-153`). Live evidence: after SIGKILL the replacement exits `provider_quiescence_required` with zero claims and zero requests, and `/health` does not clear the marker (`test_fault_injection_qualification.py:137-147,488-497`). Quiescence took 84.6 s. |
| **Step 2 — parent-owned 300 s outcome** | Conforms | The deadline is set immediately before staging and launch (`conversion_process.py:402-404`). A watchdog thread decides independently of IPC and staging I/O (`:468-482`). `AttemptLatch.accept()` re-checks the monotonic clock under the latch, so a late completion cannot win (`:99-109`). Unit races use an injected clock (`test_conversion_process.py:87`). Live: `test_production_300_second_deadline_with_a_real_hung_child` decided at 300.002 s, with cleanup reported separately (2.03 s). |
| **Step 2 — publication fence** | Conforms | The child has no inference transport (`_NoInferenceClient`, `:174-181`) and an environment without credentials (`:50-64,346-349`). It cannot publish. The parent rebuilds `ParseResult` and calls F0004 `ContentWorkflow` publication once, through the leased publisher (`content_workflow.py:180-196`). A timeout or cancellation raises before `publish` runs. |
| **Step 2 — process-group isolation and cleanup** | Conforms | Launch uses `start_new_session=True`, `close_fds=True` and `pass_fds` (IPC only) (`:413-440`). The launch receipt is fsynced before the start acknowledgement (`:444-466`); if IPC closes before the acknowledgement, the child exits without converting (`:192-196`). Cleanup sends TERM, waits 2 s, sends KILL and reaps for 3 s, then checks the group members rather than the leader's `waitpid` (`worker_guard.py:144-174`). Unconfirmed cleanup stops the worker and keeps the guard and staging (`document_worker.py:184-187`). The orphan reaper refuses a reused PID (`:593-622`). Tests cover hang, ignored TERM, a helper that ignores TERM, blocked staging, descriptor inheritance, and the parent killed before and after the acknowledgement (`test_conversion_process.py:61-226`). |
| **Checkpoint before model (S0001-AC3)** | Conforms | The supervised branch returns the verified, published bundle before `client_factory` is ever called (`content_workflow.py:180-196`; `document_worker.py:278`). Live: ready bundle, `model_unavailable`, 1 conversion, 0 provider requests. |
| **Parse once / reinterpretation from saved JSON** | Conforms | Interpretation reads the bundle's native JSON (`graph_interpretation.py:184-200`). Pre-publication failures reconvert at most once, using the reason history (`document_worker.py:203-211`). Live: `converter.launches == 1` in every fault case and kill point. Three live reinterpretation tests ran with zero conversion and unchanged bundles. |
| **Step 3 — OCR asset provenance (S0005)** | Conforms, with a recorded gap | Assets are read from the loaded predictor's tagged path and hashed at conversion time (`item_provenance.py:24-73`). The producer identity is written only when the hashes equal the packaged pins (`:107-124`); otherwise items get no producer, become `ORIGIN_UNAVAILABLE` and fall back to v1. `model_artifact_digests` is filled in both writers. No schema shape changes. The v1 fallback rate is 84.6% (see Contract Gaps). |
| **Step 4 — failure reasons / migration 0009** | Conforms | The migration is expand-only and nullable, with a CHECK over exactly the 13 planned reasons (`0009_f0005_job_event_reason.py:20-48`). Downgrade refuses while reasons exist (`:51-65`). `retry()` and `fail()` require a reason (`queue.py:475-502`). Migrations 0001–0008 are unedited. Restore test 4/4 passed. |
| **Step 5 — budgets, targeting, relationship fail-closed** | Conforms | `_reject_unsupported` fails closed on edges, foreign types and nested entities (`graph_interpretation.py:86-94,203-206`). Any failed call voids the output (`:214-217`), so Graph's dense-to-direct fallback is never reported as dense. Live: every call stayed within 4,096 tokens, no evidence was fabricated, and targeting was rejected. |
| **Step 6 — pipeline pinning and request identity** | Conforms | The request key includes the pipeline (`submission.py:146-148`). `DocumentTask.pipeline` is pinned and written explicitly (`exclude_defaults` keeps it) (`document_worker.py:70-75`; `submission.py:142`). Retries use the pinned value. |
| **Step 6 — legacy meaning** | Conforms (Low deviation) | `pipeline=None` takes Graph's `direct` contract and keeps the prior `requested_configuration` shape (`graph_interpretation.py:126-130,350-375`). Test `test_historical_job_without_pipeline_keeps_its_pre_change_meaning` passed. Deviation: the run metadata records `"pipeline": None`, not the effective `graph-direct` that the plan asks to be recorded (`:290`). |
| **Step 6 — default and rollback settings** | Conforms | `config/local.yaml` has `extraction.pipeline: direct-baseline` and `content.v2_writer_enabled: false`. The value must be explicit, an unknown value fails startup, and no environment variable can override it (`brain_content/config.py:39-63`). Branch tests: 11/11 (`live-decision-branches-rerun.log`). |
| **Step 6 — direct-baseline worker path** | Deviates (Medium) | The plan said to *wrap* `OpenAICompatibleExtractionAdapter`. The implementation re-implements F0001's prompt inside `graph_interpretation._direct_baseline` and imports a private helper (`graph_interpretation.py:30,51-80`). Transport, budget, semaphore, guard and mapper are shared as the plan intended. The prompt text matches F0001 (`openai_compatible_adapter.py:113-124`), but the rollback engine is now a second copy of it. |
| **Step 7 — harness and report** | Conforms | The report uses the worker composition with isolated schemas, which are dropped afterwards (`f0005_qualification.py:144,208`), hashed configs and an unchanged committed config (`committed_config_sha256`). Report sha256 is `55ce3484…aaede`. |
| **Package boundaries** | Conforms | `brain-extraction` imports nothing from `brain_ingestion`. The DTO stays in the neutral `brain_interpretation.parsed_content`, and the only change is the additive `model_artifact_digests` field. `brain-ingestion` already depended on `brain-extraction` for composition. The conversion child uses the Graph adapter only for its pinned stage guard, as Step 2 requires. |
| **Graph output never reaches canonical tables** | Conforms | The importer (`brain_worker/document_delivery.py`) is unchanged. Graph exports stay in temporary directories, and relationship/entity output fails closed before import. |
| **Unapproved scope** | Deviates (Medium) | The queue-depth bound has a new committed key `jobs.max_queue_depth`, a global count across tenants, an advisory-locked admission check and a submission pre-check (`queue.py:132-212`; `submission.py:150-163`). S0002's non-functional line 60 requires a bound, but the assembly plan never designed one. Other additions are acceptable and disclosed: empty/unreadable page → failed page (an S0001 edge case), heartbeat interval ≤ 1 s (supports S0002-AC4), removal of the `BRAIN_ENABLE_GRAPH_CANDIDATE` gate (implied by Step 6), and the F0004 fixture pinned to `head`. |

## Contract Gaps And Owners

| Gap | Needs contract / ADR change? | Owner | Recommendation |
|---|---|---|---|
| **S0001-AC2: the v1 manifest has no OCR page count and no document-level OCR engine** | Yes for the page count; no for the engine | Architect (F0004 content contract, ADR-0073 Proposed) and PM (AC disposition) | `ExtractionQuality` is `extra="forbid"` in v1 and v2 (`brain_content/manifest.py:37-42`), so no field exists to hold the page count. Leave v1 frozen. The OCR engine name/version is already recorded on both contracts through `execution.model_artifact_digests` (`<asset>@rapidocr==3.9.2:sha256:…`) and, in v2, the per-item `ProducerIdentity`. The PM can accept that as the engine identity. The OCR page count is computed (`ParseResult.ocr_page_count`) and then discarded. Add it as an optional, expand-only v2 `extraction_quality` field through an ADR-0073 amendment, with an updated schema and verifier. Until then, S0001-AC2 stays partly met. Not blocking for the rejection branch. |
| **84.6% v2→v1 fallback (table cells lack origin)** | No ADR change now. One would be needed only to change the fallback granularity. | AI Engineer (provenance hook); Architect (ADR-0065/0073) only if the per-document fallback rule is reopened | The per-document fallback is F0004's approved fail-closed behaviour, and the rate was reported as S0005-AC3 requires. Fix first in the hook: derive a table cell's origin from the underlying `PdfTextCell` and OCR cells it covers, with no contract change. Allowing table cells to carry `ORIGIN_UNAVAILABLE` without a whole-document fallback would change the contract under ADR-0065/0073. Record the rate as a precondition for any future v2 activation in ADR-0060 and DEPENDENCY-MATRIX. |
| **Queue-bound residual race (pre-check before source storage)** | No ADR change for the race itself. The bound's design belongs in the controls ADR below. | Backend; Security judges the orphan records | The locked `_admit` check is authoritative, so the bound is never exceeded. When two submitters race, the loser keeps an immutable source object and the `resource_access` rows it provisioned (`submission.py:187,204`), and not just the source bytes as G2 stated. Acceptable for the local single-operator scope. Record it as a known limitation, and have Code Review/Security confirm whether a later resubmission reconciles the provisioned rows. The global, cross-tenant count is a fairness issue for F0026 (one tenant can fill the queue). |
| **Baseline prompt excludes tables** | No | PM/operator (threshold policy) with AI Engineer | This is faithful to F0001: ADR-0060 says "Keep the F0001 runtime as the measured baseline". It makes the relative thresholds easier, but Graph dense misses the absolute thresholds anyway, so the outcome does not change. It is a real limitation of the engine that stays default (41.4% accuracy, 42.9% abstention). Record it in ADR-0060 and DEPENDENCY-MATRIX. Any re-plan must decide explicitly whether a table-aware baseline becomes a *new* measured baseline. That would be a new candidate with its own evidence, never a silent change to the rollback engine. |

## Qualification Outcome

From `report.json` (`void: false`, sha256 `55ce348489e253bc2a053adbaf7591d4e678d83470792ab0bf26b0207aabaede`). Corpus `fbc5e263…`, expectation set `16a29d67…`, 13 documents × 2 profiles.

| PRD threshold | Graph dense | Direct baseline | Result |
|---|---|---|---|
| Schema validity 100% | 100% (8 completed, 18 explicit `model_malformed_output` failures) | 100% (25/1) | Met |
| Accuracy ≥ 90% and ≤ 5 pp below baseline | 27.6% (16/58) | 41.4% | **Missed** |
| Abstention ≥ 95% | 0/7 | 3/7 | **Missed** |
| Fabricated evidence 0 | 0 | 0 | Met |
| Evidence resolution ≥ 80% and ≥ baseline | 50.0% | 66.7% | **Missed** |
| Context budget 0 over | 0 | 0 | Met |
| p95 ≤ 120 s and ≤ 3× baseline | 9.84 s (limit 4.44 s) | 1.48 s | **Missed** |
| Review workload ≤ 1.25× | 1.54 vs 2.92 | — | Met, but meaningless: 18/26 runs produced nothing |
| Recovery 0 | 0 across S0002 lanes | — | Met |

**S0004-AC3:** four thresholds are missed, so activation is blocked. The PRD forbids re-running with relaxed budgets, including a larger 512-token output reservation. That is a new plan and a full re-measurement, never a re-score.
**S0004-AC5 / S0005-AC5:** unreachable.
**S0004-AC7:** this is the only permitted closure. It requires:

- `extraction.pipeline: direct-baseline` and `content.v2_writer_enabled: false`, which are already the committed values;
- no isolated overrides and no leftover candidate queue namespaces (the harness drops its schemas);
- after G4, a restart plus one new ordinary source shown to use the direct-baseline identity and v1;
- ADR-0060 recording the failed gates and staying Proposed, or becoming Rejected if the operator says so.

That post-decision smoke check is still outstanding and must be recorded before closeout. Graph direct (84.5% accuracy, 0% evidence resolution) is not a candidate under the approved PRD.

## ADR-0060 Recommendation

**Recommendation: the ADR stays Proposed.** It is not Accepted. Its text records the failed gates. A dated reopen condition applies: if the operator has not approved a re-plan by the time F0014/F0015 planning starts, mark it Rejected.

**Rationale.** ADR-0060 cannot be Accepted. The PRD makes acceptance conditional on every gate passing. ADR-0060 itself says "ADR acceptance and activation require observed tests" and that "Structural planning checks cannot change this ADR to Accepted". Proof gate 3 (the corpus comparison) failed on four PRD thresholds. The "Acceptance scope (2026-10-23)" paragraph covers this case directly: "A rejection keeps the direct client as the runtime default and records the failed gates here." That rejects the *qualification*, keeps the record in this ADR, and leaves the ADR's own status to the operator (S0004-AC7: "Proposed or Rejected per operator").

The evidence does not falsify the orchestration decision. The parts that are Nebula's own architectural invariants passed on live runs:

- the parse-once checkpoint seam on the pinned stage layout;
- native and scanned conversion;
- recovery with zero reconversion;
- run outputs owned by the run and kept out of canonical tables;
- bounded concurrency.

The failure is in model adequacy on the current inference profile. Phi-4-mini's dense skeleton call is cut off at the 512-token output reservation, or it emits duplicate JSON keys. ADR-0055 §4 anticipates exactly this ("If the model cannot produce schema-valid … output … the Architect proposes an alternative backend"), and the acceptance-scope paragraph says F0026 "may reopen this decision".

Rejecting the ADR now would throw away a proven seam and force a new ADR for any re-plan with a larger reservation or a different model. Leaving it Proposed indefinitely, however, would repeat the PRD's own problem statement: downstream features planning against an unqualified path. Hence the dated reopen condition. Graph dense also missed the latency-ratio threshold (6.6× vs ≤ 3×) as an intrinsic multi-call cost, which should weigh toward Rejected if no re-plan is likely.

**ADR-0060 must not keep governing runtime it does not own.** Move the Phase B control text to the new ADR below, and leave a pointer behind.

**Text to record in ADR-0060 for the failed gates** (Architect role, after the G4 decision):

1. **Header:** replace the "Implementation" line with: "Live local qualification run `2026-10-25-4020923b` (2026-10-26): Graph dense **failed** PRD thresholds; not activated. Operator decision <date/response>." Mark the "Approved Phase B design rework" note as implemented, governed by ADR-00NN.
2. **Proof-gate ledger:**
   - Gate 1: pin, conversion, publication, restart and saved-JSON reuse, met live.
   - Gate 2: evidence. Fabricated 0, but dense evidence resolution was 50% and multi-region grounding was not qualified at the threshold.
   - Gate 3: **failed**, with the four missed metrics and their values, the baseline values, the report path and sha256, and the corpus and expectation hashes.
   - Gate 4: concurrency and recovery met. Security and tenant retention are subject to the G3 Security verdict.
3. **Root cause:**
   - The skeleton call is truncated at the 512-token output reservation, or Phi-4-mini emits duplicate keys.
   - It fails the same way on every retry at temperature 0.
   - Graph then falls back to direct, and the worker deliberately fails that attempt rather than reporting it as dense.
4. **Measured limitations:**
   - The baseline excludes tables (41.4% accuracy).
   - The v1 fallback rate is 84.6%, because table cells lack origin.
   - The `$ 500,000` adjacent-cell expectation affects every engine.
   - S0001-AC2 has the OCR page-count gap.
   - Graph direct is accurate but never located (0% evidence resolution).
5. **Runtime state:**
   - The default is the `direct-baseline` engine, identified as `prompt-v1` through the bounded client, with the v2 writer off.
   - Historical candidate jobs keep `graph-direct`.
   - Sections "What becomes simpler" and the direct-client retirement are **not in force**.
6. **Reopen condition:** only through a newly approved plan that changes the model, serving profile or output reservation, re-measures both engines in full under the unchanged PRD thresholds, and replaces this report rather than re-scoring it; or through F0026.
7. **Cross-records:** a matching DEPENDENCY-MATRIX entry (results and limitations) and a link to STATUS's verdict table.

## Home For Shipped Controls

**Finding:** these controls now govern the ordinary runtime of the direct baseline, independent of Graph:

- the host inference guard with in-flight marker and quiescence;
- supervised conversion with a 300 s parent deadline and a publication fence;
- the failure-reason enumeration (migration 0009);
- the queue bound;
- pipeline selection and job pinning.

Their only design text is ADR-0060's "Local control design amendments" section. That section says they are "proposed controls" that do not approve runtime activation. If ADR-0060 stays Proposed or becomes Rejected, a persisted schema enumeration and a worker startup contract have no accepted decision record. That conflicts with SOLUTION-PATTERNS' own change rule ("Propose changes via ADR … Update this file") and with ADR-0003's rule that changes go through a linked ADR.

**Recommendation:** create a new ADR. Do not amend existing ones.

- **Suggested title:** "ADR-00NN: Local document-job execution controls — supervised conversion, host inference guard, failure reasons and admission bound".
- **Scope:** pipeline-neutral, covering every extraction pipeline.
- **Refines:** ADR-0003 (the parse-once checkpoint now has a parent-owned conversion deadline and publication fence), ADR-0055 (one worker per canonical endpoint, a model semaphore of 1, the in-flight marker, and confirmed provider quiescence as the only recovery from an uncertain request) and ADR-0004 (pipeline identity is part of job and run identity; historical jobs keep their legacy meaning).
- **Contents:**
  - the frozen reason enumeration;
  - the expand-only rule for adding reasons;
  - `extraction.pipeline` (no environment override, explicit, unknown values fail startup);
  - the `jobs.max_queue_depth` design, its global scope and the known race;
  - Local Docker Compose scope only, with F0026 reopening it for production.
- **Evidence:** cite this run's live lanes.
- **Approval:** the operator approves it at G4 together with the rejection decision. The Architect applies it at G7.

Amending accepted ADRs is the wrong vehicle. ADR-0003 is a baseline record that changes "only through a superseding ADR". ADR-0055 is about the inference profile, not conversion supervision or job admission. Splitting the controls across them would scatter one coherent mechanism.

**Fallback:** if the operator declines a new ADR, the minimum is to record dated, Accepted refinement sections in ADR-0055 (guard, marker, quiescence) and ADR-0003 (supervised conversion and fence), with the reason enumeration documented in ADR-0003's refinement. This is weaker and is not recommended.

## G7 Reconciliation Notes

Read-only scan. `scripts/kg/hint.py` resolves the changed runtime files to `capability:parse-once-content-artifact` / `capability:semantic-interpretation-run`. `engine/migrations/versions/0009_f0005_job_event_reason.py`, `neuron/benchmarks/f0005_qualification.py` and `config/local.yaml` resolve to nothing.

1. **`canonical-nodes.yaml`:**
   - Add the new controls ADR node, related to `adr:0003`, `adr:0004`, `adr:0055`, `adr:0060`, `capability:parse-once-content-artifact`, `capability:semantic-interpretation-run` and `workflow:ingestion-interpretation`.
   - Add `rationale` entries on those capabilities.
   - Update the `capability:parse-once-content-artifact` notes. The current text, "Target: Docling-Graph coordinates Docling conversion…; F0005 must prove ADR-0060", is now stale. The actual state is: direct-baseline default, supervised conversion with a parent fence, host guard, and Graph qualification failed 2026-10-26.
   - Annotate the `adr:0060` node with the qualification outcome. Do not imply Accepted.
2. **`feature-mappings.yaml` `feature:F0005`:**
   - Replace "No implementation or runtime proof claimed" (`:480-481`) with the actual outcome and run id.
   - Add the new ADR to `governed_by`.
   - Set status to match the G4 decision.
3. **`code-index.yaml` bindings:** add the following. The existing `neuron/tests/integration/test_content_*` / `test_document_*` globs miss the qualification tests.
   - `engine/migrations/versions/0009_f0005_job_event_reason.py`
   - `engine/tests/integration/test_job_event_reason_migration.py`
   - `neuron/benchmarks/f0005_qualification.py`
   - `neuron/fixtures/qualification/**`
   - `neuron/tests/support/**`
   - `neuron/tests/integration/test_{fault_injection,live_*,pipeline_selection}*.py`
   - `config/local.yaml` (the extraction and jobs sections)
   - `docker/local-inference-runbook.md`
4. **SOLUTION-PATTERNS.md** "F0005 candidate composition" (`:335-339`) is stale. It still says "opt-in `worker_cli`" and "the fixed-template candidate uses Graph direct extraction". Update it under the change process, citing the new ADR. Also add a Change Log line.
5. **Regenerate and validate:**
   - `coverage-report.yaml` source hashes change for ADR-0060, the new ADR and SOLUTION-PATTERNS.
   - Run `validate.py` and expect exit 0.
   - Run `decisions.py`. There are no `KG-DECISION` markers in the changed code, so it is a no-op.
6. **Trackers:**
   - STATUS proof gates and story statuses must reflect the rejection.
   - DEPENDENCY-MATRIX records the measured limitations.
   - C4 and BLUEPRINT §2.1/§4.8 remain *unchanged*, because nothing was activated. Confirm no activation text was added.

## Findings

- [high] The Phase B controls ship as the direct baseline's runtime with only a Proposed ADR as design authority. Migration 0009 freezes a reason enumeration in the database. Locations: `ADR-0060-docling-graph-document-pipeline-orchestration.md:56-62`; `engine/migrations/versions/0009_f0005_job_event_reason.py:20-48`; `neuron/packages/brain-ingestion/src/brain_ingestion/worker_cli.py:207-219` — owner: Architect + operator; follow-up: approve a pipeline-neutral controls ADR at G4, apply it and repoint ADR-0060 at G7 (PM mitigation: closeout is blocked until it is recorded).
- [medium] The direct-baseline rollback engine re-implements F0001's prompt and imports the private `_strict_json_schema` instead of wrapping `OpenAICompatibleExtractionAdapter` as Step 6 planned. Two copies of the prompt can drift. Location: `neuron/packages/brain-extraction/src/brain_extraction/graph_interpretation.py:30,51-80` — owner: AI Engineer; follow-up: build the prompt from one shared function, or add a test that checks prompt-hash equality with F0001; name the actual default engine identity (`direct-baseline`/`prompt-v1`) in ADR-0060.
- [medium] `classify()` maps every unrecognised exception to `conversion_failed`. That reason is in `_PRE_PUBLICATION`, so post-publication defects (integrity or hash mismatch, interpretation bugs) are recorded as conversion failures and become terminal under the reconversion rule. Reason codes then stop being diagnostic. Location: `neuron/packages/brain-ingestion/src/brain_ingestion/document_worker.py:40-42,102-121,203-211` — owner: Backend; follow-up: do not count unknown post-publication errors toward the reconversion budget; add an explicit reason through an expand-only migration under the controls ADR if needed.
- [medium] The queue-depth bound is approved only as S0002's non-functional line, not designed in the assembly plan. Undesigned choices: a global cross-tenant count, a new committed key, PostgreSQL-only serialization, and loser-side orphan source objects plus provisioned `resource_access` rows. Locations: `engine/packages/brain-jobs/src/brain_jobs/queue.py:132-212`; `neuron/packages/brain-ingestion/src/brain_ingestion/submission.py:150-163,187,204`; `config/local.yaml:13-16` — owner: Backend + Architect; follow-up: record the design and limitation in the controls ADR; Security/Code Review to judge the orphan rows; F0026 to decide on tenant fairness.
- [medium] S0001-AC2 content-contract gap: no OCR page count in either manifest version, and no document-level OCR engine in v1. Location: `engine/packages/brain-content/src/brain_content/manifest.py:37-42` — owner: Architect (ADR-0073/F0004 contract) + PM; follow-up: accept `model_artifact_digests`/`ProducerIdentity` as the engine identity, and add an optional expand-only v2 `ocr_page_count` through an ADR-0073 amendment, or formally amend the AC.
- [low] Legacy jobs record `"pipeline": None` in run metadata rather than the effective `graph-direct` identity that Step 6 requires. Location: `neuron/packages/brain-extraction/src/brain_extraction/graph_interpretation.py:290` — owner: AI Engineer; follow-up: add an `effective_pipeline` field without changing the legacy `requested_configuration` shape.
- [low] The child's handoff `guard` is a hardcoded literal (`docling-graph: 1.9.1`) rather than derived from the guard result or the installed version. The frame also carries only two files, with no native assets. Location: `neuron/packages/brain-ingestion/src/brain_ingestion/conversion_process.py:227,548,48` — owner: AI Engineer; follow-up: derive the value from `version("docling-graph")` and the guard, and add the asset closure to the dependency-upgrade checklist.
- [low] The SIGKILL competing-worker case records quiescence time (84.6 s) but does not assert S0002's recovery bound, unlike the timeout case. Location: `neuron/tests/integration/test_fault_injection_qualification.py:500-511` (compare `:184-186`) — owner: QE; follow-up: assert `recovered_seconds ≤ lease + attempt`.
- [low] An import-time monkeypatch of RapidOCR's private `ModelLoader._build_and_load_model` would make `docling_adapter` fail to import on an upstream change, instead of failing closed to `ORIGIN_UNAVAILABLE`. Locations: `neuron/packages/brain-ingestion/src/brain_ingestion/docling_adapter.py:14`; `item_provenance.py:24-45` — owner: AI Engineer; follow-up: guard the install and fail closed; list it in the DEPENDENCY-MATRIX upgrade revalidation.
- [low] The quiescence supervisor appends the restarted vLLM's stdout and stderr to the control directory. ADR-0055 requires that prompts are never persisted. Location: `neuron/packages/brain-ingestion/src/brain_ingestion/provider_supervisor.py:112-122` — owner: Security/DevOps; follow-up: confirm the recorded argv disables request logging, or send the output to `/dev/null`.
- [low] STATUS Story×Role marks QA and DevOps `done` before the independent G3 verdicts. Location: `planning-mds/features/F0005-one-time-docling-ingestion/STATUS.md:105-109` — owner: PM; follow-up: separate implementation-QE from independent QA status.
- [low] KG and patterns drift. Locations: `planning-mds/architecture/SOLUTION-PATTERNS.md:337-339`; `planning-mds/knowledge-graph/feature-mappings.yaml:480`; `code-index.yaml` missing bindings — owner: Architect; follow-up: G7 items 1–6 above.
