# F0005 assembly plan

**Status:** Phase B rework in plan run `2026-10-25-50fcf658`, approved by the operator on 2026-10-25 with the response `approve` at the architecture gate. Addresses PM-1, ARCH-1 and BLD-1 from [plan review 2026-10-24-0fbc1de1](../../../operations/evidence/runs/2026-10-24-0fbc1de1/plan-review-report.md). The preceding design was approved in plan run `2026-10-23-9a04b327`; its approval is historical; approval of this amendment is recorded separately in the current run. Approved PRD/stories/thresholds are unchanged. The 2026-09-15 draft's first three steps remain delivered synthetic development scope (see [compatibility evidence](compatibility-evidence.md)). ADR-0060 and ADR-0073 remain Proposed. Every new control below is a future feature-action deliverable, not implemented proof.

## Review repair decisions

| Finding | Phase B correction | Implementation owner / required proof |
|---|---|---|
| PM-1 — rejected qualification retained Graph direct | Step 6 starts at `direct-baseline` with v2 disabled; Step 7 gives explicit acceptance, rejection and rollback settings | Backend + AI; restart/new-submission tests for all three decisions, with historical jobs unchanged |
| ARCH-1 — conversion bound delegated to a cooperative model deadline | Step 2 supervises conversion in a child process; parent alone owns the 300-second decision and ready publication | AI + Backend; hung/late converter and process cleanup/fence tests |
| BLD-1 — two workers could each use a process-local model slot | Step 0a enforces a host singleton before claims/model work, plus fail-closed recovery of uncertain provider requests; Step 4 proves second-process refusal | Backend + AI + DevOps; shared-inode lock, SIGKILL, provider quiescence and negative startup proofs |

## Reconciliation with the 2026-09-15 plan and shipped F0002–F0004

The previous plan is not silently overwritten. Its status per item:

| 2026-09-15 plan item | As built (main) | This plan |
|---|---|---|
| Pin Graph, align Docling, regenerate `neuron/uv.lock` | Delivered: Graph 1.9.1, Docling 2.126.0, wheel digest locked | Re-verify against the lock at preflight (S0001-AC1); no upgrade planned |
| Shared ParseResult DTO, `build_bundle()` publication callback | Delivered; F0004 replaced the publication path with the versioned v1/v2 boundary, `ContentWorkflow` and the shared verifier | Use the F0004 boundary unchanged |
| Rename the direct client | Delivered: `OpenAICompatibleExtractionAdapter`, old name kept as an import alias | Add a worker path for it so it can be the rollback engine (Step 6) |
| Job leases, fencing, outbox, recovery | Delivered: `DocumentJobQueue`, migration 0004, nine PostgreSQL cases with recorded responses; job events carry no failure reason | Add live-provider and storage failure injection (Step 4) and a reason column (migration 0009) |
| Evidence translation | Delivered: mapper v2, multi-region, unresolved fallback | Prove with live output (Step 5) |
| Corpus comparison, thresholds, reviewers | Only a synthetic recorded-response comparison | Corpus, live harness, thresholds and reviews (Steps 1, 7) |
| Activation | Not done; the worker uses Graph's `direct` contract while opt-in | Pipeline selection in committed configuration; gated switch (Step 7) |
| — | F0004 shipped a disabled v2 writer and handed off OCR asset provenance | Step 3 (S0005) |

The open decisions table of the old plan is closed: the pin and checkpoint seam (S0001), the metadata DTOs and publication transaction (F0004), and the corpus, reviewers and thresholds (operator, 2026-10-23 PRD). Concurrency is fixed at one worker replica and model semaphore 1 for qualification.

## Ownership and package boundary

Unchanged from ADR-0060: `brain-extraction` (AI engineer) is the only package calling upstream Graph; `brain-ingestion` owns conversion, item provenance and publication through the F0004 `ContentWorkflow`; the engine owns jobs, authorization, import and audit. Neither engine persistence nor review imports AI implementation modules. New code stays inside these packages plus a qualification harness under `neuron/benchmarks/` and corpus fixtures under `neuron/fixtures/qualification/`.

| Role | Owns in this plan |
|---|---|
| Quality Engineer (corpus author session) | Corpus generator, documents, expectations, hashes. Never runs or reviews extraction. |
| AI Engineer | Supervised conversion child and typed handoff, origin/OCR provenance, evidence proof, comparison harness and runs, direct-baseline worker path, provider in-flight tracking around every model call |
| Backend Developer | Parent deadline/publication fence, pipeline selection config and job pinning, singleton worker guard, failure-injection composition, cleanup/retention of temporary exports |
| DevOps | Preflight: shared lock mount, dedicated vLLM process ownership/quiescence, GPU, model and OCR asset cache, database; deadline/guard crash qualification, dependency matrix, C4 runtime update at activation |
| Quality Engineer (independent review session) | QA verdict over all stories and the report |
| Code Reviewer (independent review session) | Code verdict over all stories, including deadline, guard and configuration decision branches |
| Architect (independent review session) | Architecture verdict; ADR-0060 status change |
| Security (independent review session) | Security verdict: data egress, credentials, logs, tenant access, retention |

Review sessions start from fresh context and do not author code, corpus or expectations they judge.

## Build order

| Step | Story | Exit condition |
|---|---|---|
| 0 | all | Preflight green: exact model/tokenizer/assets/database pins; Step 0a's shared singleton guard and provider recovery preconditions verified. |
| 1 | S0004-AC1 | Corpus committed with corpus and expectation hashes recorded in the feature evidence package before any measured run. |
| 2 | S0001 | Every corpus document converts live through the supervised handoff; the 300-second timeout/late-publication tests pass; bundles published before the first model call; partial and stage-guard cases pass. |
| 3 | S0005 AC1–AC4 | Per-item origin and OCR asset identity on every converted document; fallback rate reported; consumer compatibility passes. The switch is not flipped here. |
| 4 | S0002 | Every injected failure recovers or terminates explicitly with zero post-publication reconversion and no duplicate effects. |
| 5 | S0003 | Live two-profile runs over saved JSON: zero conversion, grounded evidence, budgets enforced, relationship output fails closed. |
| 6 | S0004-AC6/AC7 support | `direct-baseline` is the committed initial setting; pipeline job pinning and direct-baseline worker path pass recovery/evidence suites and rejection/rollback restart tests. |
| 7 | S0004, S0005-AC5 | Measured report; thresholds marked; three verdicts and operator decision; then activation or recorded rejection. |

Steps 2–5 may interleave once Step 1 is committed, but no measured comparison run (Step 7) starts before Steps 2–6 pass.

## Step 0 — Preflight (DevOps)

Use `docker/local-inference-runbook.md` (F0005 candidate revision section). Record GPU model and memory, driver, CUDA, vLLM image digest, model revision, tokenizer revision, max model length 4,096, and the Docling/RapidOCR asset cache paths. Run the existing offline suites (`test_graph_pipeline_contract.py`, `test_vllm_graph_client.py`, `test_document_process_recovery.py` on PostgreSQL) as a regression baseline. Fail preflight on any lock mismatch (S0001-AC1).

## Step 0a — Host singleton and provider recovery (Backend, AI, DevOps)

This is a local one-worker deployment control, not a distributed quota. Add `brain_ingestion/worker_guard.py`; the processing CLI acquires its guard before the first queue claim, conversion, import coupled to processing, or inference call. Submission-only and import-only commands do not invoke a model and retain their existing authorization boundaries.

1. Resolve the allowed serving endpoint to the preflight-recorded canonical service identity: scheme, numeric loopback address, effective port and normalized API base path. Only the dedicated local Brain provider is supported. Resolve configured hostname aliases to that identity; reject ambiguous/mismatching addresses and nonallowlisted origins. Do not key by the model, tenant, profile, PID or a raw alias string. The key is SHA-256 of this identity, never the credential.
2. The host control directory is the fixed `/tmp/nebula-brain-inference-<host-uid>/`, private (0700) to the dedicated worker OS account and independent of checkout, content root, model, tenant and temporary configuration. The worker derives it from the host account UID, never `TMPDIR`, a per-repository default or a config/env override. Every processing process/replica uses this **same host directory and lock inode**. For a container, preflight requires the mapped host UID and an explicit bind mount of that directory at the same path; a private container `/tmp` is invalid. Preflight records the resolved host path/owner and proves exclusion with two independent processes through the actual mounts and two different working/content directories. It rejects a filesystem without working advisory locks, wrong owner/symlink roots, mismatched UID or unshared mounts. Provider preflight permits only this worker account to use the dedicated service; multi-account and multi-host processing remain unsupported. Never delete this control directory while the provider is live: `/tmp` cleanup/reboot provisioning requires the provider stopped and the same quiescence procedure below.
3. Open `<key>.lock` with restrictive permissions and acquire `fcntl.flock(LOCK_EX | LOCK_NB)`. Hold the open descriptor for the processing worker lifetime. A loser exits `inference_guard_busy` before a queue claim, conversion or model request. Never unlink, replace or truncate the lock inode; owner metadata is a separate file and PID presence never overrides the lock. Crash release is performed by the OS, not by a PID-file cleanup heuristic.
4. Use spawn/exec for the converter and other helper processes, `close_fds=True`, and non-inheritable descriptors. Pass only the named conversion IPC descriptors; never pass the guard descriptor. No forked child may prolong or explicitly unlock the parent's guard. The two-process proof checks both accidental inheritance and a child exiting after the parent has acquired a replacement lock.
5. Keep one shared `BoundedSemaphore(1)` inside the owner for all direct/dense calls, including Graph skeleton/fill/repair/reconciliation. Every path must pass the same host guard and client boundary. A fault proxy forwards owner requests and is not a second model client. Other host workloads using this dedicated provider are stopped at preflight; an external client that bypasses this composition is not silently counted as governed.

**In-flight requests after timeout or worker death.** Releasing an OS lock does not cancel GPU work. Before dispatching each HTTP request, while holding the guard and semaphore, atomically write and fsync `<key>.inflight.json` plus its directory. It contains an opaque request/attempt correlation hash and provider-instance fingerprint, never prompt text or credentials. If durability fails, send nothing. Clear and fsync it only after a terminal provider response proves the request finished; an HTTP timeout, disconnected transport, cancellation without confirmed completion or process crash leaves it dirty. No next request is sent while dirty. Once the client has an uncertain outcome, stop claiming jobs; record the ordinary job failure (`model_timeout`, `model_unavailable` or `cancelled` as applicable) without assuming the provider stopped.

A replacement may acquire the singleton lock after a crash but must inspect the marker **before claiming a job**. A dirty marker fails startup with `provider_quiescence_required`; lock acquisition or `/health` alone is insufficient. DevOps/the qualification harness, retaining the same guard, stops the dedicated vLLM process group, waits for the server and its model workers to exit, then restarts the exact recorded serving command/model/tokenizer revision. If process ownership or exit cannot be established, remain stopped; never clear the marker on a timeout guess. Record a source-free receipt with old/new provider-instance identities, confirmed exit, pins and timestamps; clear the marker under the guard only after that receipt is durable. Release the maintenance guard and start the replacement processing worker. Credentials remain in the existing local secret mechanism, not the receipt. This is the only uncertain-request recovery path for the bounded local scope; no new public endpoint or provider API is assumed.

For abrupt-exit cases after already completed requests, the absent marker permits ordinary lease recovery without restarting the provider. For an in-flight kill or ambiguous timeout, the harness/DevOps supervisor **automates** the stop/confirm/restart sequence on the controlled qualification host, with no approval prompt for each injected fault; include that elapsed time when checking S0002's existing recovery bound (one lease period plus one attempt). A slow restart fails qualification against that bound; it does not authorize overlapping requests or an unbounded claim of successful recovery. The future DevOps runbook must name the dedicated provider process-group owner and exact stop/restart procedure. No production host or distributed scheduler is introduced.

## Step 1 — Qualification corpus (QE corpus author)

```
neuron/fixtures/qualification/
  build_corpus.py          # deterministic generator; seeds and layout specs in-file
  corpus.yaml              # document list: id, kind (native|scanned|mixed|partial), case tags, sha256
  expectations/<doc>.json  # per profile field: value | null (absent), evidence: [{page, text, region?}]
  CORPUS-HASHES.txt        # sha256 of every PDF and expectation file
```

- At least 12 GL declarations documents: 6 native, 4 scanned (rasterized pages), 2 mixed (native text plus an image region), plus the partial-conversion case among them (one deliberately damaged page). Case tags must cover unique, repeated, table-borne, split-across-regions and absent values for all five fields of `gl-limits-a` and `gl-limits-b`.
- Expectations are generated from the generator's input data, not from any conversion or extraction output, so they are independent by construction. Values are verbatim as printed; evidence lists the printed region(s).
- Insured names, addresses and policy numbers are synthetic. The corpus sits outside `golden-corpus/` and the frozen holdout and is labelled synthetic development data in `corpus.yaml`.
- The two existing `neuron/fixtures/gl-policy-declarations*.pdf` files stay as regression fixtures and are not counted.

## Step 2 — Live conversion (S0001)

Reuse `DocumentWorker` and the F0004 `ContentWorkflow` publication contract with physical conversion and OCR enabled, replacing the blocking in-process conversion invocation with the supervised boundary below. Add `brain_ingestion/conversion_process.py` and `neuron/tests/integration/test_live_conversion_qualification.py`, skipped unless `BRAIN_RUN_LIVE_QUALIFICATION=1`, that submits every corpus document and asserts S0001-AC2–AC5 from the persisted bundle after a process restart.

- **Checkpoint before model (AC3):** run with the fault proxy (Step 4) in `stopped` mode; assert the bundle is ready and the job recorded `model_unavailable` with conversion count 1.
- **Stage guard (AC5):** monkeypatch the installed stage list in a subprocess; the existing guard must raise before extraction and register nothing.
- **Bounds:** the parent sets a monotonic deadline of start + 300 s immediately before preparing/launching physical conversion. The model client's cooperative deadline is not the conversion control. The parent alone accepts a completed conversion result or selects `conversion_timeout` under the protocol below.

### Supervised conversion and checkpoint handshake

1. The authorized parent owns the queue lease/heartbeat, guard, content-store handle and ready-publication callback. It creates an attempt-private staging directory outside the accepted bundle namespace. Spawn/exec a new conversion process group with only the authorized source file, pinned parser settings, staging location and IPC endpoint. The child initially blocks without converting. Under the guard, the parent atomically writes/fsyncs a private launch receipt containing attempt nonce, staging path and child process-group/leader-start identity, then sends the start acknowledgement. Parent IPC closure before that acknowledgement makes the child exit without conversion; after acknowledgement every executing child is durably discoverable if the parent dies. Strip DB, inference and application credentials/object-store configuration from its environment. The child has no job/ready-publication capability or inference transport; its model-client stub raises if called. It never creates a manifest completion marker or contacts vLLM.
2. The child runs the **same pinned Graph stage-layout guard and conversion-only path**, with real Docling/OCR, and replaces the checkpoint callback with a serializer. The callback emits a bounded JSON completion frame after atomically staging the native DoclingDocument JSON, required native assets, parse quality (including failed pages/OCR counts/warnings), per-item producer/origin observations and OCR asset identities. The frame contains attempt nonce, file inventory/hashes and the pinned guard result. It uses JSON and relative declared files, never pickle or arbitrary paths. The child exits the conversion-only adapter after the callback; extraction must not run. Failure before the callback emits a stable conversion/stage error instead.
3. Before the 300-second deadline, the parent requires both a successful child exit and a complete frame whose nonce, source identity, hashes, native schema/asset closure, quality and provenance validate. At the deadline a missing, partial, still-running or invalid handoff cannot be accepted as success. A dedicated parent watchdog selects timeout independently of converter, IPC and staging/receipt I/O; none of those operations may hold its attempt-latch lock while waiting. The parent serializes completion/timeout/cancellation decisions through that one latch, checking the monotonic clock again at acceptance; queued/late IPC never wins over an expired deadline. Fenced durable event persistence follows the selected outcome and cannot extend the decision deadline. Malformed handoffs fail `conversion_failed`, and a mismatched pinned stage layout fails `stage_guard_mismatch`.
4. On a valid result accepted before the bound, reconstruct the existing neutral `ParseResult` in the parent. Invoke F0004's current-authority/generation-fenced `ContentWorkflow` publication callback **once**, then verify/reload the bundle. Only after that callback commits ready may the parent start saved-native-JSON interpretation through the selected pipeline. No second physical conversion is used to enter Graph extraction. The 300-second metric ends at accepted conversion handoff; subsequent verified publication is a separate recorded phase with existing database/storage bounds, not additional allowed converter time. Stage-list mismatch and callback/publication failure still prevent any model call.
5. At 300 s select failure immediately, disable this attempt's publication capability, and record `conversion_timeout` with the deadline/outcome in the job's fenced failure path. Do not wait for child cleanup to choose the outcome. Send SIGTERM to the **whole child process group**, allow at most 2 s for exit, then SIGKILL and bounded reap (at most 3 s). Check that parser/OCR helper descendants are gone, not just that `waitpid` returned for the group leader; preflight rejects a pinned converter/helper that escapes this group. These ≤5 s are cleanup overhead after a failed conversion; they never extend the 300-second decision or permit late ready/model activity. Cancellation, authority/fence loss and parent exceptions use the same revoked-publication/cleanup path with their own reason. If the group cannot be confirmed gone, stop the worker, retain the guard and private staging for explicit DevOps recovery; do not start another conversion or release its ownership as if clean.
6. Remove the attempt staging tree only after the child group is confirmed gone; never delete another generation's staging. A parent crash leaves no child-accessible ready path. On restart, under the singleton guard and database generation fence, reap any recorded orphan child group (record PID plus process-start identity to avoid PID reuse), then remove its staging before retry. A host restart already terminates the old group. A reaper unable to establish ownership fails closed for DevOps; it never kills an unrelated PID. Accepted bundle bytes and registered ready rows remain untouched. Retry before publication follows S0002-AC3's existing at-most-one-reconversion rule; exhausted budgets end explicitly.

**Required deadline proof (AI/Backend; independently checked by QE/DevOps):** a child that never returns, a child/helper that ignores SIGTERM, a completion arriving at/after the deadline, and a child staging callback blocked across deadline selection must produce one timed-out outcome, no ready artifact/outbox/model call from that attempt, bounded group kill/reap and private-tree cleanup. A completion accepted before the deadline may subsequently publish only through the current parent's live generation fence; that separate storage phase does not retrospectively time out successful conversion. The child is forbidden to inherit the singleton descriptor or publish ready. Unit tests use an injected monotonic clock for boundary races; a real subprocess test verifies the production 300-second setting and records decision time separately from cleanup time. Kill the parent before and after the durable launch receipt/start acknowledgement to prove no undiscoverable converter executes or overlaps a retry; include orphan cleanup and retry-exhaustion cases. Do not substitute a measured fast corpus for this negative control proof.

## Step 3 — Text origin and OCR asset provenance (S0005)

`item_provenance.py` currently records `ProducerIdentity(engine_class, version("rapidocr"), None, None)` for RapidOCR items, with the model fields null.

- Resolve the RapidOCR detection, recognition and classification model files actually loaded by the configured pipeline (read from the engine instance's configured model paths, not from defaults or documentation). Hash each file's bytes at conversion time.
- Write the result into slots that already exist and are always written empty today:
  - The v2 manifest's `execution.model_artifact_digests` (array of strings), as `<asset-name>@<revision>:sha256:<hex>`; `content_workflow.py` and `bundle_writer.py` currently write `[]`.
  - The per-item `ProducerIdentity.model` and `model_version` fields, which are currently `None` for OCR items.
- No schema change is needed. If the contract cannot express what is observed, stop and return to the architect.
- An asset path that cannot be resolved, or a digest that differs from the value recorded at preflight, makes the document `ORIGIN_UNAVAILABLE` for its OCR items, so the per-document v1 fallback applies (S0005-AC2/AC3). No guessed identity is written.
- Run the F0004 consumer-compatibility suites (`test_content_consumer_versions.py`, `test_content_worker_v2.py`, `test_content_restore_v2.py`, the evidence resolver and the importer) against v2 bundles of the corpus with `content.v2_writer_enabled=true` in an isolated config (`BRAIN_LOCAL_CONFIG_PATH`). The committed switch stays `false` until Step 7.

## Step 4 — Failure injection (S0002)

Test-only composition, never shipped in the production worker path:

- **Model fault proxy** `neuron/tests/support/fault_proxy.py`: an HTTP proxy between the worker and vLLM with modes `pass`, `stopped` (connection refused), `timeout` (hold beyond the client timeout), `http_5xx`, `malformed_json` and `schema_invalid` (valid JSON violating the template). Mode is selected per request number so a retry can succeed.
- **Storage fault** wrapper over the filesystem object store that raises on the Nth write or before the manifest marker.
- **Process kills:** extend `test_document_process_recovery.py` to run with the live model through the proxy in `pass` mode at the four kill points (after bundle publication, after result publication, mid-import, after import commit).
- **Assertions:** conversion and OCR counters are instrumented at the converter and RapidOCR entry points (not self-reported). Database row counts prove one accepted artifact, one run per profile and one assertion/evidence/review set. Reason codes are distinct per fault mode.
- **Concurrency (AC4):** enqueue 5 jobs and start processing worker A through Step 0a; start worker B against the same canonical endpoint/shared lock mount. B must fail `inference_guard_busy` before any queue claim, converter entry or model request. A drains work with at most one provider request, including Graph fan-out; prove this with proxy timestamps. Run the existing PostgreSQL competing-claim/fencing tests separately at queue level; they do not authorize two live model workers. Kill A during a held provider request: B may acquire the released OS lock but must fail `provider_quiescence_required` with zero claims/requests until the confirmed provider stop/restart receipt clears the marker. Repeat with an ambiguous client timeout while the provider still works; assert a healthy `/health` response does not clear/bypass the marker. Inject marker file/directory fsync failure and assert zero outbound requests. Then verify recovery, no overlapping old/new provider work, no duplicate accepted effects, descriptor noninheritance and cancellation scheduling no further request. A graceful exit clears/releases only after model work is confirmed finished; uncertain cancellation takes the same quiescence path.
- **Authorization (AC5):** revoke the ServicePrincipal grant or deactivate the principal between attempts; the next boundary denies and audits, and the job does not continue.
- **Temporary exports (AC6):** after completed, failed and cancelled runs, assert the attempt's temporary directory is removed and retained run outputs carry the source's tenant/KB scope. Retention period and deletion follow the source (F0004); F0005 adds no retention policy.

## Step 5 — Live interpretation and evidence (S0003)

Extend `test_graph_live_inference.py` (opt-in) to run both profiles with `extraction_contract="dense"` over every corpus bundle after a worker restart, with converter/OCR entry points patched to raise.

- **Evidence (AC2):** for every resolved selector, re-read the span or cell from the bundle (`blocks.jsonl`, `tables.jsonl`) and compare it to the value. Unicode code-point offsets follow the F0004 convention.
- **Unsupported output (AC4):** a dedicated template variant that elicits a relationship asserts the import fails closed with no rows.
- **Budgets (AC5):** `VllmGraphClient` already reserves input, schema and output tokens with the serving tokenizer; add per-call reservation records to run diagnostics and assert none exceeds 4,096.
- **Targeting (AC6):** a selected-block request raises `unsupported_targeting` before any call.

## Step 6 — Pipeline selection and rollback path

Add a committed, non-secret section to `config/local.yaml`, loaded beside `ContentWriterConfig`. This changes the planned initial worker selection to the direct baseline; Graph's current opt-in `direct` path is neither the accepted baseline nor the rejection outcome:

```yaml
extraction:
  # direct-baseline | graph-dense | graph-direct (qualification only)
  pipeline: direct-baseline
```

- **Job pinning and identity:** new submissions derive their idempotency key from the existing scoped source/version/recipe/actor/profile identity **plus the selected pipeline**, and write that pipeline in `payload`. Same pipeline + same identity stays idempotent; a different pipeline is a different job/run over the same immutable artifact, not a conflicting payload for the old key. Retries and recovery use the pinned value. A configuration change affects new submissions only, so no run mixes engines (S0004-AC6). Existing pinned jobs/results are immutable. Historical jobs lacking the new field retain their existing keys and known pre-change `graph-direct` meaning on recovery, never acquire the current default; record that effective legacy identity without rewriting their payload/history. Drain or cancel historical candidate jobs before decision smoke tests. New submissions always contain an explicit pipeline. No migration is needed: `payload` and idempotency keys are existing carriers.
- **Run identity:** the interpretation run records the pipeline value, Graph revision and contract, or the direct adapter's identity.
- **Direct baseline in the worker:** wrap `OpenAICompatibleExtractionAdapter` behind the same interpretation interface as `GraphInterpretationService`, with the same `VllmGraphClient` budget and semaphore policy, evidence mapper and importer. It must pass the Step 4 recovery suite and the Step 5 evidence checks before it can serve as a rollback.
- An unknown value fails worker startup with a configuration error; there is no environment-variable override.
- **Qualification isolation:** each measured engine uses a separate temporary config, queue namespace/database schema and content root, recording its hash; those worker compositions still share Step 0a's fixed host guard directory for the same provider. Only one runs at a time. `BRAIN_LOCAL_CONFIG_PATH` selects this existing isolated-config facility. Graph direct/dense are explicitly selected there; running the harness never edits the committed baseline setting or leaves candidate jobs in the ordinary queue. The guard directory cannot be changed by an isolated config; reject an attempted override.
- **Required branch tests:** `test_pipeline_selection.py` restarts from committed `direct-baseline`/v2 false, submits a fresh source and proves direct adapter identity/v1. Exercise acceptance, rejection after each threshold/reviewer failure, operator rejection and rollback using the settings table below; restart and submit a new source after each branch. Assert the expected engine/writer, hashes/config identity, unchanged historical runs/bundles/pinned jobs, no live temporary override, and no Graph call on new rejection/default jobs. A rollback test also checks v2 artifacts remain readable. A legacy queued candidate remains identifiable without changing its pinned interpretation.

## Step 7 — Comparison, review and decision (S0004, S0005-AC5)

**Harness:** `neuron/benchmarks/f0005_qualification.py --corpus neuron/fixtures/qualification --pipelines direct-baseline graph-dense graph-direct --output <run>/artifacts/qualification/report.json`. It reuses the scoring of `docling_graph_comparison.py`, runs through the worker composition against live vLLM, and records configuration hashes, pins, corpus and expectation hashes, and per-case rows. Graph direct is reported but is not a candidate.

**Metrics,** exactly as the PRD defines them:

- Accuracy: normalized exact match. Normalization is limited to whitespace collapse and Unicode NFC; no currency or date reformatting.
- Abstention: computed over expected-null fields.
- Fabricated evidence: resolved selectors whose re-read text fails the value comparison.
- Evidence resolution: exact span or cell over correct values.
- Latency: wall time from interpretation start to result publication per document-profile; p95 by nearest rank.
- Review workload: review items created per document.

**Void runs:** if the provider fails mid-measurement, the whole report is void and rerun. Reports are immutable; reruns get a new file.

**Decision sequence:**

1. Mark each threshold met or missed in `report-summary.md`.
2. The three independent review sessions write verdicts with evidence references into STATUS's append-only provenance table.
3. The operator records acceptance or rejection.
4. **On acceptance:** in one change, set `extraction.pipeline: graph-dense` and `content.v2_writer_enabled: true`; mark ADR-0060 Accepted with the evidence links; update `docker/DEPENDENCY-MATRIX.md`, build/run metadata, the C4 container description and BLUEPRINT §2.1/§4.8. Restart, submit a new corpus document and verify engine/run/v2 identity. These remain future runtime/operator decisions, not this plan's approval.
5. **On rejection:** verify or restore `extraction.pipeline: direct-baseline` and `content.v2_writer_enabled: false`, remove isolated qualification overrides and drain/cancel their queue namespaces. Restart the ordinary worker and submit a new source; it must use the direct client and v1. ADR-0060 records failed gates and remains Proposed, or becomes Rejected if the operator says so. Do not infer either setting from the phrase "stay as they are".

| State / decision | Ordinary `extraction.pipeline` | `content.v2_writer_enabled` | Evidence required after restart |
|---|---|---|---|
| Initial implementation / before qualification | `direct-baseline` | `false` | New ordinary source uses direct adapter/v1 |
| Isolated measured qualification | Ordinary default stays `direct-baseline`; isolated engine config explicitly selects each of the three pipelines | Ordinary stays `false`; isolated v2 compatibility config may use `true` | Hashed temporary config, isolated queues/content, shared host guard, no ordinary-default mutation |
| All thresholds/verdicts pass and operator accepts | `graph-dense` | `true` | New ordinary source uses dense/v2, with the retained per-document origin fallback |
| Any threshold miss, failed verdict or operator rejection | `direct-baseline` | `false` | New ordinary source uses direct/v1; no candidate override or partial activation remains |
| Rollback after an accepted activation | `direct-baseline` | `true` | Only extraction selection changes; new run uses direct, and accepted v2 publication/read compatibility remains qualified |

The approved rollback criterion switches extraction engines; it does not revoke an already qualified content writer. If writer integrity itself fails, stop new ingestion for targeted repair rather than silently rewriting accepted bundles or treating it as the extraction rollback. Rejection before acceptance always leaves the writer disabled. Every branch preserves existing accepted bytes and prior run identities.

## Contracts, data and authorization

- No new endpoint, schema file, role or permission. Existing `ServicePrincipal` `ingest`/`interpret` grants cover all qualification jobs; Casbin policy is unchanged.
- S0005 fills existing, currently empty fields of `schema:content-artifact-manifest-v2`; no shape change.
- **Failure reasons (migration 0009, expand-only).** `document_job_event` records only `event` (state); `DocumentJobQueue.retry()` has no reason. Add a nullable `reason VARCHAR(64)` column with a CHECK constraint over this enumeration:
  - `model_unavailable`, `model_timeout`, `model_http_error`, `model_malformed_output`, `model_schema_invalid`
  - `storage_write_failed`, `conversion_failed`, `conversion_timeout`, `stage_guard_mismatch`
  - `unsupported_targeting`, `unsupported_output`, `authorization_denied`, `cancelled`

  `retry()` and the terminal-failure path take a required reason. Existing rows keep `NULL`, with no backfill and no edit to migrations 0001–0008. This is F0003's expand-only discipline; the restore drill covers the new column.
- Audit: authorization decisions stay in `audit_event` with policy version. Job state changes are the append-only `document_job_event` rows, each carrying job, generation (attempt), event, the new reason and time. Correlation and artifact/run references come from the job row and outbox.
- Data egress: model requests carry chunk text only (ADR-0055). Diagnostics and reports carry hashes, usage and reason codes, never prompts, responses, source text or keys.

## Test inventory and coverage

| Story | Tests (new or extended) | Mode |
|---|---|---|
| S0001 | `test_live_conversion_qualification.py`; new `neuron/packages/brain-ingestion/tests/test_conversion_process.py` (hung child, deadline/result race, SIGTERM/SIGKILL, child guard-fd exclusion, late callback and orphan cleanup) | live, opt-in; real subprocess and injected-clock unit |
| S0002 | `test_document_process_recovery.py` (live variant), `test_fault_injection_qualification.py`, new `neuron/packages/brain-ingestion/tests/test_worker_guard.py` (actual shared-mount two-process refusal and uncertain-provider recovery), storage-fault unit tests, migration 0009 upgrade/restore test (`engine/tests/integration/test_job_event_reason_migration.py`) | live and PostgreSQL; real process/lock |
| S0003 | `test_graph_live_inference.py` (dense, corpus), evidence re-read checks | live, opt-in |
| S0004 | `f0005_qualification.py` harness, `test_pipeline_selection.py` (initial direct default, isolated configs, explicit decision branches, restart/new-submission rejection, pinning/legacy recovery, unknown value, rollback) | live; unit/integration |
| S0005 | `test_ocr_asset_provenance.py`, F0004 consumer suites under v2 config | live; existing |

Live suites run on the development host and are recorded in the feature evidence package; CI keeps running the offline and PostgreSQL suites. The feature action records at least 80% coverage for changed runtime scope. Required signoff roles for every story: Quality Engineer, Code Reviewer, Security, DevOps and Architect.

## Non-functional limits

- One host-enforced processing worker per canonical serving endpoint and shared in-process model semaphore 1, during qualification and local activation. A competing worker is refused before work; uncertain provider activity requires confirmed quiescence before replacement.
- Per-call context ≤ 4,096 tokens by the serving tokenizer.
- Conversion decision deadline 300 s per document, enforced by a supervised subprocess and parent publication latch; ≤5 s bounded failure cleanup does not extend that decision or allow late publication.
- Latency and accuracy thresholds as in the PRD.
- GPU memory and tokens are reported, not thresholded.

## Rollout

Implement the direct-baseline/v2-disabled initial setting and isolated qualification controls at Step 6. Only Step 7's recorded acceptance activates Graph dense/v2 for new ordinary jobs. Rejection explicitly restores the baseline settings; extraction rollback after acceptance is one pipeline setting, as tabulated above. Historical jobs, bundles and run records remain unchanged. Archived F0001 records stay unchanged. The production host (F0026) is out of scope; this Phase B planning approval is not a release approval.
