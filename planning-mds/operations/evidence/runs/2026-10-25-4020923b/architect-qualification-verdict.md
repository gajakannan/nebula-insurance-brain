# Architect Qualification Verdict (G3 round 2): F0005 run 2026-10-25-4020923b

> Independent Architect review session for F0005-S0004-AC4, G3 round 2, written 2026-10-28. This reviewer did not write the implementation, the corpus, the expectations or the round-2 architecture records (ADR-0073 §6, ADR-0074, ADR-0060 outcome section). The review covers the uncommitted working tree on `feature/f0005-live-qualification` (`git diff` plus untracked files). Everything was read-only. No ADR, STATUS or knowledge-graph file was changed. ADR status changes are the operator's G4 decision. The round-1 verdict is kept as `architect-qualification-verdict-round1.md` in this folder.

Result: PASS WITH RECOMMENDATIONS

This result covers architecture conformance, the round-2 records and the quality of the evidence. It is not a pass for Graph dense. Graph dense failed qualification, and the rejection branch (S0004-AC7) is the only permitted outcome.

## Summary

- **No Critical or High finding.**
  - The round-1 High finding (shipped controls without an architectural home) is closed in design by ADR-0074. It closes fully once the operator accepts ADR-0074 at G4.
  - Code Review C1 (OCR fields) and H1 (silent dense acceptance) are fixed in code and covered by tests. The architecture conforms on both.
- **ADR-0074 is ready for operator acceptance.**
  - It is pipeline-neutral, matches the shipped code clause by clause, and records its known limits: SEC-F5-M1 as an activation precondition, the host-wide queue bound, and the submission orphan race.
  - Its live proof was re-run on current code.
  - Two small additions are recommended but do not block: name the `conversion_started` job event as part of the contract, and add a short Alternatives section.
- **ADR-0073 §6 (optional `extraction_quality.ocr` in v1 and v2) is acceptable, but its compatibility reasoning is inaccurate (Medium).**
  - It is add-only and optional, `null`/absent means "not observed", and hashing is unchanged. It does not imply historical provenance, which is the real concern in the "Alternatives" text against mandatory v1 fields.
  - However, it is *not* "a compatible clarification like `source.pdf`". That clarification admitted bytes the writer already emitted and readers already accepted. This change adds new data that pre-amendment readers reject inside the same contract version. It gives up the staged deployment that §1's version dispatch exists to provide.
  - The amendment needs an explicit **code-rollback floor**: once a bundle carries the block, no build older than this amendment may read or sweep the store. It also needs a drain-before-deploy rule for unadvertised orphan markers. `deployability-check.md` covers neither.
- **ADR-0060's new outcome section is accurate against `report.json` .** I recomputed every figure. However, the ADR now contradicts itself (Medium):
  - the header still says the Phase B controls "remain unimplemented";
  - the "Local control design amendments" section is still headed "runtime proof pending" and has no pointer to ADR-0074;
  - "What becomes simpler" (retiring the direct client) is not marked as not in force.
- **Schema copies match.** I compared both changed manifest schemas with `cmp`. The read schema needs no change, because it is `oneOf` two `$ref`s to the changed files.
- **Several round-1 Lows remain open:** legacy run metadata, the guard literal, the SIGKILL recovery bound, the RapidOCR import-time patch, STATUS role marks, and KG/patterns drift. G7 carries most of them.

## Records Review

### ADR-0073 §6: observed OCR quality in both manifest versions

`planning-mds/architecture/decisions/ADR-0073-versioned-content-contracts-and-document-metadata.md` lines 90–101.

Note on status: ADR-0073 (and ADR-0065) are **Proposed**, not Accepted. The brief described them as accepted. Even so, the F0004 content contract is in force at runtime (F0004 is archived as done), so this amendment is judged as a change to a live contract.

| Question | Judgement |
|---|---|
| Is the optional v1 field consistent with §1? | **Partly.** §1 says "Keep v1 readable with its current hashing algorithm" and "dispatch solely on the declared contract version". Hashing is unchanged (verified: `inventory_hash` and the manifest is excluded from the bundle hash). Historical bytes stay valid, and parsing a manifest without the field yields `ocr=None` (`manifest.py:75` ; `test_ocr_quality.py:110-114` ). However, the same `artifact_contract_version: 1` now names two shapes, and only post-amendment readers accept the newer one. |
| Is it consistent with §5? | **Yes.** §5 says "a page OCR count is not a block's origin". The block is document-level quality only. Per-item origin, `ORIGIN_UNAVAILABLE` and the per-document v1 fallback are unchanged. The engine identity reuses the item `ProducerIdentity` rule (`identify_ocr_engine`, `item_provenance.py:85-106` ), which consistently strengthens ADR-0065's "engine, model and version". |
| Is it consistent with the Alternatives text that rejects mandatory v1 fields? | **Yes on substance, no on the stated rationale.** That text names two harms: breaking strict readers, and implying never-captured provenance. The optional field avoids the second. It avoids the first only for *historical* bundles. Pre-amendment strict readers reject *new* v1 bundles, so this is a forward-incompatible change within v1, mitigated by deploying readers and writers together. Calling it "like the earlier `source.pdf` clarification" (line 98) is inaccurate. **I still accept the design.** The ordinary path writes v1 (v2 is off), S0001-AC2 requires the fields there, a v3 contract for one optional block would be disproportionate, and every reader is in this repository. The record should state the trade-off honestly. |
| Deploy-together: readers | All readers go through `brain_content.manifest.parse_manifest` → JSON Schema + Pydantic (`manifest.py:156-174` ). The engine API, the worker, the sync `CheckpointStore` and the async store share it. The local Compose images are built from one tree. Handled. |
| Deploy-together: restore drill | Restore restores bytes and rows and reads them with the same build, so it is unaffected. The **code rollback** case is not handled: a pre-amendment build would fail to parse OCR-bearing manifests ("invalid manifest" → 409 `ARTIFACT_INTEGRITY`), and its operator integrity sweep would treat that as a definitive failure and **quarantine valid bundles**. The F0004 restore suites (`test_content_restore_v2.py`) were not run with OCR-bearing bundles. The live lane covers v1/v2 round trips only. |
| Deploy-together: orphan markers | Adoption compares the parsed manifests (`verified_store.py:69-75` ). An unadvertised v1 orphan marker written before the amendment, then retried by the new writer (which adds `ocr` and the digests), raises `ArtifactConflict` → `PublicationFailed` → `storage_write_failed` (`content_workflow.py:179` ). The job ends terminally after two conversions. The local scope is narrow, but the deploy note should say: drain jobs and resolve orphan markers before deploying. |
| Read schema `planning-mds/schemas/content-artifact-manifest-read.schema.json` | No change needed. It is `oneOf` `$ref` to the v1 and v2 files, so it inherits the block, and the `artifact_contract_version` constants keep the two branches exclusive. It has no package copy (that predates this run). |
| Schema copies | `cmp` reports `planning-mds/schemas/content-artifact-manifest.schema.json` identical to `engine/packages/brain-content/src/brain_content/schemas/content-artifact-manifest.schema.json` , and the same for the v2 pair. The v1 and v2 `ocr` subschemas are identical. |
| Schema vs model | The JSON Schema cannot express `page_count == len(pages)` or sorted pages. Pydantic `OcrQuality.consistent` enforces both (`manifest.py:59-64` ), and every Python reader runs both layers. The schema description does not state these invariants, although the `planning-mds` copy is the shared contract (Low). Neither layer bounds `pages` by the manifest `page_count` (Low). |
| `engine: null` semantics | The record defines `null` as "configured but not the approved, pinned engine/assets". The code also writes `{page_count: 0, pages: [], engine: null}` when the pipeline has no OCR stage at all (`item_provenance.py:117-121` ). That makes "OCR disabled" indistinguishable from "unidentified engine" (Low). The writer never emits `ocr: null`, so "absent or null" now only appears in historical bundles. That is consistent. |
| Asset "revision" (Code Review L1) | Recorded (line 101). Closed. |

### ADR-0074: local document-job execution controls (Proposed)

`planning-mds/architecture/decisions/ADR-0074-local-document-job-execution-controls.md`

| Aspect | Judgement |
|---|---|
| Vehicle and scope | This is what round 1 recommended: a new pipeline-neutral record, no in-place edits to Accepted ADRs, and refining ADR-0003/0004/0055. It respects ADR-0003's supersession-only rule, because it refines in a separate record and does not change the parse-once decision. Scope is local Compose on a single host, and F0026 may reopen it. Correct. |
| §1 Supervised conversion | It matches the code reviewed in round 1 and unchanged since: 300 s parent deadline, launch receipt before acknowledgement, latch, TERM→2 s→KILL→bounded reap, `converter_cleanup_unconfirmed` stops the worker, orphan reaper fails closed, child has no inference or publication capability. SEC-F5-M1 is correctly recorded as an activation precondition. The ADR could also note Code Review L3: a reused PID across a reboot with a surviving `/tmp`. |
| §2 Host guard / marker / quiescence | Matches the code. Provider record validation runs on write (`record_provider`) and on use (`load_provider`). It accepts only a `vllm serve` group leader with the guarded `--host`/`--port` and no `--api-key` (`worker_guard.py:378-400` ). The liveness check covers start ticks, process group and argv before any signal (`provider_supervisor.py:84-99` ). Quiescence refuses a restart that accepts unauthenticated requests (`wait_ready`). A marker fault stops the worker without failing jobs (`document_worker.py:68,121-126` ; `run_one` raises `WorkerStopped`). Precision note: when the leader is gone but group members remain, members are signalled without an argv check. That is safe, because a process group ID cannot be reused while members exist, but the absolute wording "before any signal" overstates it slightly. |
| §3 Reasons and retry | Matches the code. The vocabulary is 13 + 4, with a frozen-enumeration test linking migration 0010 to `FAILURE_REASONS` (`test_job_event_reason_migration.py:56-59`). The 0010 downgrade refuses while added reasons exist. The retry budget counts durable `conversion_started` events (`queue.py:509-525`). Post-ready errors become `interpretation_failed` (`document_worker.py:279` plus the `_published` remap). The terminal set matches line 48. **Gap:** `conversion_started` is now load-bearing for the retry budget, but `document_job_event.event` is an unconstrained `VARCHAR(64)`, and the ADR does not name the event as part of the contract (Low). |
| §4 Submission bound | Designed and limited as round 1 asked: host-wide, advisory transaction lock, idempotent duplicates, exit 4, orphan race recorded, F0026 owns fairness. Closed. |
| §5 Pipeline selection | Matches `brain_content.config.load_extraction_config` (explicit, unknown values fail, no environment variable names a pipeline, `BRAIN_LOCAL_CONFIG_PATH` only selects a file) and the job pinning. The enumeration is duplicated in `brain_content/config.py` (`EXTRACTION_PIPELINES`) and `brain_extraction/graph_interpretation.py:35` (`PIPELINES`) with no parity test. Engine code must not import the AI runtime, so the duplication is deliberate, but it can drift (Low). |
| Proof | Cites run lanes that were re-run on current code (`g2r-live-*`, 7 lanes passed, kill lane re-run with the provider busy). Adequate. |
| Format | No Alternatives section. Round 1's rationale (amend ADR-0055/0003; keep it in ADR-0060) is only implied in Context (Low). |
| **Acceptance readiness** | **Ready for operator acceptance at the rerun G4.** No blocking defect. Accepting it does not activate Graph and does not lift SEC-F5-M1. |

### ADR-0060: "F0005 qualification outcome (2026-10-27)"

`planning-mds/architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md` lines 102–135.

- **Decision text matches the G4 row** in `gate-decisions.md` (2026-10-27T22:12:58):
  - Graph dense rejected;
  - the ADR stays Proposed;
  - reopen deadline "start of F0014/F0015 planning", otherwise Rejected;
  - a re-plan means a new plan with full re-measurement, never a re-score.
- **Figures** were verified against `report.json` (sha256 `55ce3484…aaede` , `void: false`):
  - accuracy 41.4 / 27.6 (16/58);
  - abstention 3/7 vs 0/7;
  - evidence resolution 66.7 / 50.0;
  - p95 1.48 s / 9.84 s (6.65×);
  - review items per document 2.92 / 1.54, and per completed run 1.52 vs 2.50 (1.64×);
  - 18/26 dense failures, all `model_malformed_output`;
  - Graph direct 84.5% accuracy with 0% evidence resolution;
  - 11/13 documents published v1 (84.6%).

  The committed `config/local.yaml` sha256 still equals the report's `committed_config_sha256` (`e80cb506…`).
- **Root cause and limitations** match `report-summary.md` and the round-1 analysis. The section adds the H1 caveat.
- **Inaccuracies (Low):**
  - The "context budget: met" row (line 117) and "its runs show no budget rejections" (line 133) rest on a measurement that could not record pre-dispatch rejections. That was H1's point: the measurement was true by construction. They should read "not observable in this measurement".
  - The 9.84 s p95 is the pre-M6 completed-run, last-attempt figure. Any correction only makes dense worse.
  - The report sha256 and the corpus and expectation hashes that round 1 asked for are missing.
  - None of this changes the outcome.
- **Internal inconsistency (Medium):**
  - Line 13 still says the Phase B controls "remain unimplemented".
  - Line 56 still says "runtime proof pending", and line 62 says "None of these proposed controls … approves runtime activation". Neither points to ADR-0074.
  - "What becomes simpler" (line 66, retiring the direct-vLLM adapter) is not marked as not in force.
  - "They no longer depend on this ADR's status" (line 135) is true only after ADR-0074 is accepted.

## Design Conformance

| Area | Verdict | Evidence |
|---|---|---|
| OCR observer on both writer paths | Conforms | `DoclingAdapter._new_converter` installs an `OcrObserver` on every converter, whether or not provenance is captured (`docling_adapter.py:40-61`). Pages are cleared on each parse. The observer wraps the running engine's `post_process_cells` and records a page only when a cell is `from_ocr` (`item_provenance.py:109-132`). In v2 capture mode, `ItemProvenance` wraps the same engine again; both hooks chain. The v1 `build_bundle` (`bundle_writer.py:30-47,185`) and v2 `build_bundle_v2` (`content_projection.py:251`) both call the one `ocr_quality()`. The observation crosses the child handoff (`conversion_process.py:140-144,187`; `test_ocr_quality.py:95-107`). Live: every v1 and v2 manifest records pages and the pinned RapidOCR 3.9.2 engine (`g2r-live-conversion.log`). Engine identity is hashed at converter construction, not per conversion. Under supervised conversion each child is a new process, so this is effectively per conversion. |
| Shared OCR identity rule | Conforms | `identify_ocr_engine` is the single rule for the bundle block, the item producers and `model_artifact_digests`. An unknown engine, unresolvable assets or a pin mismatch gives no identity, `ORIGIN_UNAVAILABLE` and the v1 fallback (`item_provenance.py:85-106`). Test: `test_unpinned_assets_record_ocr_pages_but_no_engine_identity`. |
| Client rejection rules (H1) | Conforms | Every `InferenceRejected` that is not already recorded becomes a `rejections` entry with a `failure_class`, and does not consume the call budget (`vllm_graph_client.py:240-266`). Calls that were dispatched get a `failure_class` per error type. A dispatch-guard failure sends nothing (`:336-338`). The marker is cleared only on a response, an HTTP status or a refused connection (`:356-371`). |
| Service acceptance (H1) | Conforms | Any rejection or non-complete call voids the output (`graph_interpretation.py:209-216`). A dense run with any non-`dense_` call phase is voided with `dense_contract_fallback` (`:217-225`). Tests: `test_interpretation_rejections.py:132,143,157`. |
| Worker reason rules | Conforms | `model_failure_reason` takes the first failed call or rejection and maps it to the frozen vocabulary (`document_worker.py:107-118`). Result-level mapping order: unsupported → cancelled → model reason → contract fallback → `interpretation_failed` → malformed (`:355-365`). Guard faults raise `WorkerStopped`. A non-`GuardError` exception inside the dispatch guard maps to `dispatch_guard_failed` → `interpretation_failed` (a retry), not to a worker stop. That is acceptable because `inflight()` converts every `OSError` into the coded fault. Residual: `classify` maps `ParserMigrationRequired` to `conversion_failed` (`:146-147`). That is a governance refusal that reconversion cannot cure, recorded under a misleading reason (Low). |
| Provider-record validation | Conforms | See ADR-0074 §2 above. Five tampering tests were added (`test_worker_guard.py`). The live quiescence ran the new checks (`g2r-attempt1` receipt). |
| Package boundaries | Conforms | `brain_extraction` and `brain_interpretation` import nothing from `brain_ingestion` (grep: none). The DTO `OcrObservation` and `ParseResult.model_artifact_digests`/`ocr` live in the neutral `brain_interpretation.parsed_content`. The shared F0001 prompt builder `baseline_prompt` and the public `strict_json_schema` live in `brain_extraction.openai_compatible_adapter`, used by the F0001 adapter and by `_direct_baseline`. `test_direct_baseline_sends_exactly_the_f0001_prompt` pins them as equal. The `brain_ingestion` → `brain_extraction` direction already existed for composition. The engine's `brain_content` does not import the AI runtime. |
| Harness metrics (M6/H1) | Conforms for future measurement | `f0005_qualification.py`: p95 sums every attempt per document-profile, failed attempts included (`:650-669`). The completed-only figure is secondary (`:600`). `rejections`, `context_rejections` and `budget_rejections` come from the new rejection records (`:491-507`), and review items are also reported per completed run (`:605`). Context and budget counts use the last attempt's metadata only, while calls are aggregated across attempts (`:418-428`). This is minor, and nothing has been re-measured. The recorded `report.json` is round 1 and predates these fixes. ADR-0060 says so. |
| Migration 0010 | Conforms | Expand-only CHECK widening. The downgrade is guarded and offline SQL mode is refused. 0009 is unedited. Head is `0010` in the smoke run. |
| Committed configuration | Conforms | `extraction.pipeline: direct-baseline`, `content.v2_writer_enabled: false`, `jobs.max_queue_depth: 100`. The committed config hash is unchanged since measurement. |

## Round-1 Finding Closure

| Round-1 finding | Status | Evidence / remainder |
|---|---|---|
| **High:** controls with no architectural home | **Closed by record, pending acceptance** | ADR-0074 written and conforming. It is fully closed when the operator accepts it at G4. ADR-0060's leftover text still needs the pointer (see Findings). |
| Medium: direct baseline duplicates F0001's prompt | **Closed** | Shared `baseline_prompt` and `strict_json_schema`, plus a prompt-equality test. The engine identity is `direct-baseline` / `prompt-v1` in run metadata. |
| Medium: unknown exceptions → `conversion_failed` | **Closed** | `_published` → `interpretation_failed` (migration 0010). Budget counted from `conversion_started` (M2). The residual `ParserMigrationRequired` mapping is a new Low. |
| Medium: queue bound not designed | **Closed** | ADR-0074 §4. |
| Medium: S0001-AC2 contract gap | **Closed, with a different design** | ADR-0073 §6 adds the block to v1 as well as v2 (round 1 had recommended v2 only and v1 frozen). Accepted with the Medium below. |
| Low: legacy run metadata `"pipeline": None` | **Open** | `graph_interpretation.py:298`. No `effective_pipeline` is recorded in run metadata. |
| Low: hardcoded child guard literal | **Open** | `conversion_process.py:249,351,570`. |
| Low: SIGKILL competing-worker recovery bound | **Open** | The kill-point case asserts the bound (`test_fault_injection_qualification.py:460`). The competing-worker case still asserts only states and concurrency (`:532-533`). |
| Low: RapidOCR import-time monkeypatch | **Open, higher stakes** | `docling_adapter.py:18` → `item_provenance.py:26-46` are unguarded. An upstream move now breaks the v1 writer path at import time, rather than recording `engine: null`. It fails loudly, not silently, but this should be listed in the DEPENDENCY-MATRIX upgrade revalidation. |
| Low: provider log under the control directory | **Partly** | Security found no prompt or credential content. The file is still opened with the default umask (`provider_supervisor.py:118`). Security owns this. |
| Low: STATUS marks QA/DevOps `done` before G3 | **Open** | `STATUS.md` Story × Role still shows QA `done` for S0001–S0003 and S0005. |
| Low: KG and patterns drift | **Open, G7** | SOLUTION-PATTERNS lines 335–339, `feature-mappings.yaml:479-481`, missing bindings. See below. |
| Recommended ADR-0060 record items 1–7 | **Mostly done** | Outcome, gates, root cause, limitations and reopen condition are recorded. Still missing: header update, the "not in force" note on retirement, the report and corpus hashes, and the DEPENDENCY-MATRIX entry. |

## Qualification Outcome

- **Permitted outcome:** S0004-AC3 blocks activation, because Graph dense misses accuracy, abstention, evidence resolution and latency, and also misses review workload when compared like for like. **Only the S0004-AC7 rejection branch is permitted.** S0004-AC5 and S0005-AC5 are unreachable. Graph direct is not a candidate under the approved PRD.
- **Already in place:**
  - `direct-baseline` with the v2 writer off is committed and unchanged;
  - the harness drops its isolated schemas.
- **Still outstanding before closeout:**
  - S0004-AC7's after-decision check: a restart plus one new ordinary source shown on `direct-baseline` / v1. The decision-branch lane proves the branch in isolation, not the post-G4 state.
- **ADR-0060's new section records this accurately against `report.json` ,** with the wording corrections listed under Findings. None of them changes the outcome.

## ADR Recommendations

- **ADR-0060:** keep it **Proposed**. It must not be Accepted. Keep the dated reopen condition: it becomes Rejected if no re-plan is approved by the start of F0014/F0015 planning. Before G7 closes, make the text consistent:
  - header line 13: implemented, governed by ADR-0074, and Graph dense failed qualification on 2026-10-26;
  - line 56: point to ADR-0074 and mark the section as superseded there;
  - "What becomes simpler": not in force;
  - add the report sha256 and the corpus and expectation hashes;
  - reword the context-budget row as not observable in this measurement.
- **ADR-0074:** **ready for operator acceptance** at the rerun G4. Optional additions before or at acceptance:
  - name `conversion_started` as a contract event;
  - add an Alternatives section;
  - note the reboot/PID-reuse limit (Code Review L3).

  The STATUS and KG must then show it as Accepted at G7.
- **ADR-0073 §6:** keep it, but correct line 98. It is an add-only, forward-incompatible change within v1, accepted because readers and writers ship together. It is not a `source.pdf`-style clarification. Add:
  - a **code-rollback floor** (no pre-amendment build may read the store, or run the integrity sweep on it, once any OCR-bearing bundle exists; forward-fix only);
  - a drain/no-orphan-marker precondition for deployment;
  - an "OCR quality block round trip v1/v2 and rollback floor" item in its Proof Gates.

  Mirror the floor in `deployability-check.md` . ADR-0073 itself stays Proposed: this amendment does not change its acceptance gates.

## G7 Reconciliation Notes

Read-only scan. Commands: `python3 scripts/kg/hint.py <path>` and `python3 scripts/kg/blast.py --file <path>` in the product root.

| Path | hint / blast result |
|---|---|
| `engine/migrations/versions/0010_f0005_job_event_reason_expand.py` | No binding |
| `neuron/packages/brain-ingestion/tests/test_ocr_quality.py` | → `capability:parse-once-content-artifact`, with neighbours `capability:versioned-content-contracts` and `entity:content-artifact` (bound via the package tests glob) |
| `neuron/tests/integration/test_interpretation_rejections.py` | No binding |
| `neuron/tests/support/relationship_probe.py` | No binding |
| ADR-0074 | No binding and no node |
| ADR-0073 | Exists as node `adr:0073`, with no code binding, which is expected for an ADR |
| `engine/packages/brain-content/src/brain_content/manifest.py` | → `capability:parse-once-content-artifact`, `capability:versioned-content-contracts`, `entity:content-artifact`, and endpoints `content-artifact-get` / `content-artifact-file-get` |

What G7 must add or change:

1. **`canonical-nodes.yaml`**
   - Add node `adr:0074` ("Local Document-Job Execution Controls", with its status as decided at G4). Relate it to `adr:0003`, `adr:0004`, `adr:0055`, `adr:0060`, `capability:parse-once-content-artifact`, `capability:semantic-interpretation-run` and `workflow:ingestion-interpretation`.
   - Update the `adr:0073` related nodes or notes for the §6 OCR block, and keep "(Proposed)" in its label.
   - Annotate `adr:0060` with the qualification outcome and reopen deadline, without implying Accepted.
   - Replace the stale "Target: Docling-Graph coordinates…" notes on `capability:parse-once-content-artifact` (`canonical-nodes.yaml:599`) with the real state: direct-baseline default, supervised conversion, host guard, the OCR quality block, and Graph dense rejected.
2. **`feature-mappings.yaml` `feature:F0005`**
   - Add `adr:0074` to `governed_by`.
   - Replace "No implementation or runtime proof claimed" (`:479-481`) with the run id, the G4 outcome and the round-2 G3 result.
   - `uses_schema` already lists both manifest schemas. Add `schema:content-artifact-manifest-read`, which F0004 already maps at `:437`.
3. **`code-index.yaml` bindings** (the existing `neuron/tests/integration/test_content_*` / `test_document_*` globs miss these):
   - `engine/migrations/versions/0009_f0005_job_event_reason.py`
   - `engine/migrations/versions/0010_f0005_job_event_reason_expand.py`
   - `engine/tests/integration/test_job_event_reason_migration.py`
   - `neuron/tests/integration/test_interpretation_rejections.py`
   - `neuron/tests/integration/test_{fault_injection,live_*,pipeline_selection}*.py`
   - `neuron/tests/support/**`
   - `neuron/benchmarks/f0005_qualification.py`
   - `neuron/fixtures/qualification/**`
   - `neuron/packages/brain-ingestion/src/brain_ingestion/ocr_asset_pins.json`
   - `config/local.yaml`
   - `docker/local-inference-runbook.md`

   Bind the migrations and the job-reason test to the jobs/workflow node that owns `document_job_event`. Bind the interpretation tests and the probe to `capability:semantic-interpretation-run`.
4. **`coverage-report.yaml`:** source hashes change for `adr:0060`, `adr:0073`, the new `adr:0074` entry, `schema:content-artifact-manifest` and `schema:content-artifact-manifest-v2` (both the `planning-mds` and package source sets). `schema:content-artifact-manifest-read` is unchanged.
5. **SOLUTION-PATTERNS.md** "F0005 candidate composition" (`:335-339`) is stale. Replace it under the change process, citing ADR-0074 and the ADR-0073 amendment, and add a Change Log line.
6. **DEPENDENCY-MATRIX:**
   - record the Docling-Graph 1.9.1 qualification result and limitations;
   - record the RapidOCR private-loader patch as an upgrade revalidation item;
   - record pypdf ≥ 6.21.2.
7. **Regenerate and validate:**
   - run `validate.py` and expect exit 0;
   - `decisions.py` finds only the existing `WHY:` tag in `docling_adapter.py` and no new `KG-DECISION` markers.
8. **Trackers:**
   - STATUS: round-2 verdict rows, story statuses after G4, and the corrected QA/DevOps role marks;
   - C4 and BLUEPRINT §2.1/§4.8 stay unchanged, because nothing was activated.

## Findings

- [medium] ADR-0073 §6 misstates its compatibility class. It calls the change "a compatible clarification … like `source.pdf`", but pre-amendment readers reject new v1 bundles carrying `ocr`. The record also gives no code-rollback floor: a pre-amendment build would return 409 on valid bundles, and its integrity sweep would quarantine them. It gives no drain rule either: a pre-amendment orphan marker fails adoption with `ArtifactConflict` → `storage_write_failed`. Locations: `planning-mds/architecture/decisions/ADR-0073-versioned-content-contracts-and-document-metadata.md:98-99` ; `engine/packages/brain-content/src/brain_content/verified_store.py:69-75` ; `neuron/packages/brain-ingestion/src/brain_ingestion/content_workflow.py:179` ; `planning-mds/operations/evidence/runs/2026-10-25-4020923b/deployability-check.md:24-31` . Owner: Architect, DevOps. Follow-up: correct the wording, add the rollback floor and the drain precondition to ADR-0073 and the deployability check, and add the OCR block to ADR-0073's Proof Gates.
- [medium] ADR-0060 contradicts its new outcome section. The header says the controls "remain unimplemented", the amendments section says "runtime proof pending" with no pointer to ADR-0074, and the direct-client retirement in "What becomes simpler" is not marked as not in force. Locations: `planning-mds/architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md:13,56,62,66,135` . Owner: Architect. Follow-up: fix at G7, after ADR-0074 is accepted.
- [low] The ADR-0060 outcome table says "context budget: met" and that the dense runs "show no budget rejections", but the measurement could not record pre-dispatch rejections (H1). The p95 is the pre-M6 completed-run figure. The report and corpus hashes are missing. The outcome is unaffected. Locations: `planning-mds/architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md:108,115,117,133` . Owner: Architect.
- [low] ADR-0074's retry budget depends on the `conversion_started` job event, but the event vocabulary is unconstrained and the ADR does not name it. The ADR has no Alternatives section and does not mention reboot/PID reuse (Code Review L3). Locations: `planning-mds/architecture/decisions/ADR-0074-local-document-job-execution-controls.md:43-49` ; `engine/packages/brain-jobs/src/brain_jobs/queue.py:509-525` . Owner: Architect. Follow-up: add before or at acceptance; this does not block acceptance.
- [low] The `ocr` JSON Schema does not document `page_count == len(pages)` or the sorted, unique invariant, which only Pydantic enforces. No layer bounds `pages` by the manifest `page_count`. "OCR stage absent" and "unidentified engine" both serialize as `engine: null`. Locations: `planning-mds/schemas/content-artifact-manifest.schema.json:167-236` ; `planning-mds/schemas/content-artifact-manifest-v2.schema.json:260-329` ; `engine/packages/brain-content/src/brain_content/manifest.py:46-64` ; `neuron/packages/brain-ingestion/src/brain_ingestion/item_provenance.py:117-121` . Owner: Architect, AI Engineer.
- [low] `classify` maps `ParserMigrationRequired` to `conversion_failed`. This is a deterministic governance refusal, but it is retried as a conversion failure under a misleading reason. Location: `neuron/packages/brain-ingestion/src/brain_ingestion/document_worker.py:146-147` . Owner: Backend. Follow-up: make it terminal, with a distinct reason through a future expand-only migration under ADR-0074.
- [low] The pipeline enumeration is duplicated in engine and neuron with no parity test. Locations: `engine/packages/brain-content/src/brain_content/config.py:39` ; `neuron/packages/brain-extraction/src/brain_extraction/graph_interpretation.py:35` . Owner: Backend/QE.
- [low] Round-1 Lows that remain open:
  - legacy run metadata `"pipeline": None` (`neuron/packages/brain-extraction/src/brain_extraction/graph_interpretation.py:298` );
  - hardcoded child guard literal (`neuron/packages/brain-ingestion/src/brain_ingestion/conversion_process.py:249` );
  - the competing-worker SIGKILL case does not assert a recovery bound (`neuron/tests/integration/test_fault_injection_qualification.py:532-533` );
  - unguarded import-time RapidOCR patch, now on the v1 writer path (`neuron/packages/brain-ingestion/src/brain_ingestion/docling_adapter.py:18` );
  - provider log opened with the default umask (`neuron/packages/brain-ingestion/src/brain_ingestion/provider_supervisor.py:118` );
  - STATUS role marks (`planning-mds/features/F0005-one-time-docling-ingestion/STATUS.md` ).

  Owners: as in round 1.
- [low] The S0004-AC7 after-decision check is still outstanding before closeout: a restart plus one ordinary source on `direct-baseline` / v1. Owner: DevOps/QE after G4.
- [low] KG and patterns drift: see G7 Reconciliation Notes items 1–8. Owner: Architect at G7.
