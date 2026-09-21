# Docling-Graph candidate evidence — 2026-09-17

This is partial compatibility evidence, not release acceptance. ADR-0060 remains Proposed.

## Candidate identity

- `docling-graph==1.9.1`, resolved and installed from the local uv cache; no floating Git branch.
- Wheel SHA-256 recorded in `neuron/uv.lock`: `04538ef0f35517f22c77641eb7dca5a35ee8d54d6e818b0341e479dc4280a62f`.
- Docling remains `2.126.0`; the lock records the complete dependency set. The adapter returns Docling, docling-core, and Graph versions separately, plus input and template-schema hashes.
- Python 3.14.4. Offline `uv lock` and `uv sync --locked` succeeded. This resolves an existing cache, not a clean network installation.

## Implemented boundary

`brain_extraction.docling_graph_pipeline.DoclingGraphPipelineAdapter` composes a Nebula checkpoint stage into `PipelineOrchestrator.stages`, immediately before its `ExtractionStage`. This is a version-pinned stage integration, not an upstream built-in checkpoint guarantee. A stage-layout check rejects an incompatible layout.

The injected Docling converter returns the shared `brain_interpretation.parsed_content.ParseResult`. A synchronous publication callback receives that document and its parse quality; extraction cannot proceed until publication returns successfully. The stage then uses the same native-document handoff as upstream's JSON input normalizer. API exports remain disabled. Graph, provenance, and effective configuration are returned separately from the content bundle; the later delivery increment below adds run persistence.

The direct client is explicitly named `OpenAICompatibleExtractionAdapter`; the old `DoclingGraphAdapter` name remains only as a compatibility import. F0001's archived records and measured results are unchanged.

## Observed checks

`neuron/tests/integration/test_graph_pipeline_contract.py`: **6 passed**.

| Check | Actual dependencies | What it establishes |
|---|---|---|
| Native PDF and scanned PDF, each followed by saved-JSON reuse | Real Docling conversion/OCR and pinned Graph stages; recorded model responses | Each initial pipeline invokes conversion once; a later profile succeeds with `DocumentConverter.convert` forbidden; saved JSON is unchanged |
| Two templates over synthetic native JSON | Real Graph input/extraction stages; recorded model responses | JSON input skips conversion and supports successive template runs |
| Checkpoint success and injected extraction timeout | Real Graph stages, bundle writer, manifest-last filesystem store; synthetic partial parse | Publication precedes extraction; failed-page warnings survive; a new store object reads the bundle after extraction failure |
| Publication failure | Real Graph stage ordering, injected publication error | No model call after publication fails |

`neuron/packages/brain-ingestion/tests/test_docling_adapter.py`: **3 passed**, covering native parsing, scanned OCR classification, and expected native text. These are parser checks, not Graph extraction-quality measurements.

The filesystem test runs the store's I/O callbacks inline: this execution sandbox hangs even a minimal `asyncio.to_thread` completion because thread wakeups use sockets. The test does not establish thread scheduling, process restart, fsync durability, or concurrent publication. The scanned test checks the parser's OCR-page classification; it does not instrument every OCR implementation entry point.

Initial combined neuron validation: **24 passed, 2 skipped** (the two existing live-vLLM baseline tests require the unavailable service/credential). Ruff and mypy passed for that candidate.

## Follow-up: bounded inference transport

`VllmGraphClient` now supplies the real OpenAI-compatible SDK transport to Graph with a shared in-process concurrency semaphore, per-attempt request/token budgets, context/output reservations, queue cancellation, transport timeouts, and a run deadline. SDK retries are disabled; Graph repairs must cross the same budget boundary. Source-bearing redirects are refused. Invalid schemas with external references, incomplete JSON, duplicate keys, non-finite values, schema-invalid responses, and truncated completions are rejected. Diagnostics retain only hashes, model revision, usage, and reason codes.

`test_vllm_graph_client.py`: **23 passed** using the real SDK with a deterministic HTTP transport; one test runs the actual Graph pipeline through this client. The combined suite passed 46 tests with 3 live tests skipped; after adding the final Graph repair-budget case, the focused client suite passed all 23 tests. Ruff, mypy, and planning gates pass. Tests include concurrency across two clients, cancellation while queued, timeout/500 handling without hidden retries, schema/output failures, token-budget exhaustion, and rejection of serving-tokenizer drift. The cached Phi tokenizer at revision `cfbefacb99257ffa30c83adab238a50856ac3083` was exercised. Transformers returned a mapping by default; the implementation now explicitly requests token IDs and tests that longer prompts increase the count.

`test_graph_live_inference.py` provides an opt-in two-profile real-model smoke test. It has not run against a live server in this session. Its recorded-response counterpart does not establish extraction accuracy. Cross-process worker limits, production wiring, durable diagnostics, and active-request termination remain outside this transport proof.

The result corrects an overly broad active-document claim: this pinned 1.9.1 build **does have a native-JSON reuse branch**. The earlier F0001 unsuccessful invocation does not prove that the whole package lacks reuse. The exact difference in the historical invocation/environment has not been reconstructed.

## Acceptance remains open

The dated increments below are historical observations. [STATUS](STATUS.md) is the current implementation and acceptance inventory. The local model credentials are absent, localhost service sockets are denied, and shell GitHub DNS resolution fails. These restrictions prevent live-service qualification and remote delivery; they do not establish architectural acceptance. Temporal remains F0050/v0.3.

## Follow-up: checkpoint, queue, and result path — 2026-09-20

The next increment adds verified synchronous checkpoint publication, atomic filesystem object publication, scoped run outputs, generation-fenced artifact leases and jobs, retry/cancel/heartbeat operations, a transactional completion outbox, and the blocking document-worker composition. Interpretation returns the existing Nebula result contract and independently grounds each supported scalar property using Graph's native-item refs. It never promotes a node's chunk-relative span to a property selector.

The combined command below passed **68 tests**, with **3 live tests skipped**:

```bash
LITELLM_LOCAL_MODEL_COST_MAP=True HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2 \
  neuron/.venv/bin/python -m pytest \
  neuron/packages/brain-ingestion/tests neuron/packages/brain-interpretation/tests neuron/tests \
  engine/packages/brain-jobs/tests engine/packages/brain-content/tests/test_object_store.py \
  -q --disable-warnings
```

The focused new suite passed 21 cases. A test found and fixed ambiguity handling when an additional textual occurrence lacks usable geometry. Queue tests exercise idempotency conflicts, cross-tenant artifact rejection, profile jobs sharing an artifact lease, stale-generation fencing, cancellation, retry exhaustion, and an exactly-once completion row. The worker test reconstructs the worker/store after model failure and forbids another conversion; it does not kill an operating-system process or run against PostgreSQL.

The new queue dependency resolves in both lockfiles. Neuron sync succeeds offline. Engine sync could not rebuild its worker in this cache because the required build dependencies were unavailable under its resolver constraints; no successful engine installation is claimed. Production authorization binding, assertion/review import, targeted content, relationships, retention, and the external-service proof remain unfinished; see STATUS for the complete list.

## Follow-up: authorized delivery and process recovery — 2026-09-20

This increment supersedes the earlier engine-installation and missing-composition limitations. Both workspaces now resolve and sync offline. The candidate worker is runnable explicitly; jobs bind a current principal/grant check and pin the extraction profile schema. A neutral `brain-contracts` package carries the unchanged result shape without making engine code import the AI runtime.

The worker registers source/artifact metadata before extraction inside its publication fence; a model timeout leaves the artifact discoverable through the engine. The engine importer verifies that metadata and commits runs, assertions, all evidence bindings, review items, and its outbox acknowledgement in one transaction. An injected failure during review insertion leaves no partial run or assertion; a retry imports exactly once. The importer does not commit canonical facts and refuses unsupported entity/relationship output. Missing constituent files in an accepted artifact/run are corruption, not a reason to reconvert. Text/table occurrences without geometry still count toward ambiguity.

The combined runtime command, adding `engine/packages/brain-security/tests/test_casbin_adapter.py` to the preceding command, passed **80 tests, 5 skipped**. New coverage includes real child-process exit after artifact/run publication, recovery with both converter and model forbidden, live-grant revocation, audited denial, table headers/cells, missing run files, and atomic import rollback/retry. The process test uses SQLite and preconstructed output; it does not measure live model accuracy or PostgreSQL crash behavior. Two isolated-schema PostgreSQL tests are opt-in and were skipped; the three model-service tests were also skipped.

Migration 0004 generates PostgreSQL SQL successfully (`cd engine/migrations && ../.venv/bin/alembic upgrade 0003:0004 --sql`). This is a DDL check, not a real database migration. Localhost ports 5432 and 8000 return `PermissionError: Operation not permitted`; `BRAIN_TEST_POSTGRES_URL`, `BRAIN_INFERENCE_API_KEY`, and `BRAIN_INFERENCE_MODEL_REVISION` are unset in this session.

Remaining acceptance covers actual PostgreSQL/model runs, direct-versus-chunked corpus measurements, unsupported relationship and multi-region evidence cases, deployment resource/retention qualification, and reviewer decisions. The full profile compiler and affected-content scheduler remain in their owning future features. No switch-wide or production completion claim is made.

The engine-owned checkpoint test suite adds **7 passing tests**, with **93% coverage** of `brain_content.checkpoints` under its own coverage command. This keeps the existing engine package coverage gate meaningful when neuron tests are not included. The full engine mypy invocation, including the new jobs/contracts packages, passes for 52 source files.

```bash
engine/.venv/bin/python -m pytest engine/packages/brain-content/tests/test_checkpoints.py \
  --cov=brain_content.checkpoints --cov-report=term-missing --cov-fail-under=80 -q
```

## Remote PostgreSQL and complete CI result — 2026-09-20

[CI run 35534966011](https://github.com/gajakannan/nebula-insurance-brain/actions/runs/35534966011), source commit `3151e5eff82eb6f8aa6d1c0c2dd8611fd85790d5`, passed all five jobs: product gates, framework validators, runtime suites, runtime stack, and experience. Git delivery succeeded despite the local API/DNS restrictions described in earlier observations; the candidate and article are now on their repositories' main branches.

- Engine suite: **126 passed, 19 skipped**. All configured per-package coverage gates passed; `brain_content` reached **96.21%** and `brain_jobs` **88.64%**.
- Neuron suite: **58 passed, 4 skipped**. This includes real native/scanned conversion with recorded extraction responses, not live-model quality.
- Disposable PostgreSQL stack: migrations **0001 through 0004 applied successfully**. The dedicated document-job concurrency/fencing tests ran against PostgreSQL: **2 passed in 0.45 seconds**. General-suite database skips do not count as this proof.
- Planning regression tests, readiness, KG freshness/reproducibility, framework validation, frontend checks, and both runtime lint/type checks passed.

This closes the initial PostgreSQL migration, competing-claim, and expired-worker-fencing checks. It does not establish process-kill recovery against PostgreSQL, live vLLM quality, serving-tokenizer parity, corpus thresholds, multi-region/relationship correctness, retention/deletion, or reviewer acceptance. The same live-model restrictions remain locally; ADR-0060 stays Proposed.

## PostgreSQL process-exit and lock-wait proof — 2026-09-20

[CI run 35535414661](https://github.com/gajakannan/nebula-insurance-brain/actions/runs/35535414661), source commit `a64f0ebc6a87602ccf1463c3998902f0e983a1a6`, applied migrations 0001–0004 and passed **all four PostgreSQL document-job tests in 3.06 seconds**. The two additional tests establish:

- A separate worker process publishes an atomic filesystem checkpoint through its PostgreSQL lease and exits with `os._exit(23)`. After lease expiry, a new claim recovers the checkpoint, rejects publication from the old generation, and commits one completion/outbox row.
- Publication waiting for a locked job row rechecks the current database clock after obtaining the lock. A lease that expires during that wait cannot publish, even though it was valid when the transaction began.

These extend the earlier competing-claim and expired-generation tests. The process-exit case exercises the queue and object store, not the complete Graph/model/engine-import composition, a database restart, or machine/storage failure.

The run passed runtime suites, product gates, framework validators, and experience, but its runtime-stack job subsequently failed while waiting for OIDC discovery. No Authentik failure logs were retained, so the cause is unconfirmed. Commit `9379e84` adds bounded HTTP attempts, a 180-second application-readiness window, and stack diagnostics before teardown. This failed full run still supplies the four observed PostgreSQL results; it is not recorded as complete CI acceptance.

## Complete CI with four PostgreSQL cases — 2026-09-20

[CI run 35552348580](https://github.com/gajakannan/nebula-insurance-brain/actions/runs/35552348580), source commit `9379e8466ad310b1630295992d21e6a6eeddc10f`, passed **all five jobs**. Engine: **126 passed / 21 skipped**; neuron: **58 passed / 4 skipped**; dedicated PostgreSQL qualification: **4 passed in 3.18 seconds**, after migrations 0001–0004 applied. All configured coverage, lint/type, product, framework, and frontend gates passed.

OIDC discovery returned 404 on the first attempt and 200 on the next attempt five seconds later; all three seeded principals authenticated. This confirms application readiness can lag server health in this run. It does not reconstruct the earlier failure or establish that every startup failure is a timing issue. The workflow now retains diagnostics for future failures.

Queue recovery is qualified for the four named cases. Full worker/model/import recovery on PostgreSQL, deployment/storage failure recovery, the live model/corpus comparison, operational controls, and reviewer acceptance remain open. ADR-0060 remains Proposed and runtime activation remains opt-in.

## Worker/importer process recovery on PostgreSQL — 2026-09-21

[CI run 35589532922](https://github.com/gajakannan/nebula-insurance-brain/actions/runs/35589532922), source `47128116747b0c09bb739d12993280ee5c2f473e`, passed all five jobs. The stack applied migrations 0001–0004, passed the four queue tests in **3.43 seconds**, and passed five new worker/importer recovery cases in **75.96 seconds**. Engine: **126 passed / 21 skipped**; neuron: **63 passed / 9 skipped**. The PostgreSQL variants skipped in the general neuron suite execute separately in the stack job.

`test_document_process_recovery.py` exits real child processes with `os._exit(29)` after bundle publication, run publication, job completion, midway through result import, and after import commits. It runs the real pinned Graph stages, bounded SDK client, current authorization checks/audits, fenced worker, artifact registration, and transactional importer. A synthetic converter supplies native content and an HTTP transport returns recorded model output. Recovery preserves one conversion and one successful model request across processes, creates exactly one assertion/evidence/review set, and acknowledges one outbox completion. Abrupt exit during review insertion rolls back the run/assertion rows and leaves the outbox unacknowledged for retry.

Each PostgreSQL case creates and drops its own schema without a `public` search-path fallback. Its tables come from application metadata; migration execution remains a separate CI check. The initial CI attempt exposed shared-table fixture collisions and missing test type annotations; both were corrected before this passing run. Locally, the same five cases passed against SQLite in **36.08 seconds**; PostgreSQL was unavailable locally and was not counted as passing there.

This closes the candidate's bounded worker/importer process-exit proof for these five boundaries. It does not establish live model behavior or extraction quality, physical parsing under process failure, database/machine restart, storage loss, retention/deletion, multi-region/relationship precision, or reviewer acceptance. The approved comparison corpus and thresholds, model credential/revision, and local service access remain unavailable in this session. ADR-0060 stays Proposed.
