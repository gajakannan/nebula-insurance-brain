# Docling-Graph candidate evidence — 2026-09-17

This is partial compatibility evidence, not release acceptance. ADR-0060 remains Proposed.

## Candidate identity

- `docling-graph==1.9.1`, resolved and installed from the local uv cache; no floating Git branch.
- Wheel SHA-256 recorded in `neuron/uv.lock`: `04538ef0f35517f22c77641eb7dca5a35ee8d54d6e818b0341e479dc4280a62f`.
- Docling remains `2.126.0`; the lock records the complete dependency set. The adapter returns Docling, docling-core, and Graph versions separately, plus input and template-schema hashes.
- Python 3.14.4. Offline `uv lock` and `uv sync --locked` succeeded. This resolves an existing cache, not a clean network installation.

## Implemented boundary

`brain_extraction.docling_graph_pipeline.DoclingGraphPipelineAdapter` composes a Nebula checkpoint stage into `PipelineOrchestrator.stages`, immediately before its `ExtractionStage`. This is a version-pinned stage integration, not an upstream built-in checkpoint guarantee. A stage-layout check rejects an incompatible layout.

The injected Docling converter returns the shared `brain_interpretation.parsed_content.ParseResult`. A synchronous publication callback receives that document and its parse quality; extraction cannot proceed until publication returns successfully. The stage then uses the same native-document handoff as upstream's JSON input normalizer. API exports remain disabled. Graph, provenance, and effective configuration are returned separately from the content bundle; production run persistence is still required.

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

## Remaining work and environmental limits

| Gate | Remaining implementation or proof |
|---|---|
| Durable ingestion | Production composition with F0004 metadata and F0002/F0003 services; PostgreSQL jobs, leases/fencing, scoped idempotency, cancellation, retries, interrupted publication, real process restart |
| Evidence and interpretation | Translate property/relationship provenance into immutable block/table selectors; unresolved evidence stays unresolved; persist run outputs under tenant access and retention; return Nebula InterpretationResult |
| Profiles and scope | Production profile compiler, durable model revision/run metadata, affected-content-only input with original references; the new per-call controls still require serving-tokenizer parity and live qualification |
| Extraction quality | Live vLLM and chunked-versus-direct comparison: schema validity, accuracy, abstention, tokens, latency, review effort; timeout/invalid-output/partial-result behavior |
| Operations and activation | Cross-process worker/model concurrency beyond the tested shared in-process semaphore, production credential injection and log review, retention/deletion, independent reviewer verdicts, accepted ADR and application activation |

The local inference API key is absent in this session, socket access to the local endpoint is denied, and shell GitHub DNS resolution fails. No live Graph/model comparison or external-service recovery proof is claimed. These restrictions do not explain away the remaining implementation work above.

The related future features have updated requirements; this candidate does not claim to implement their complete production scope. PostgreSQL durable jobs remain the v0.1 plan; Temporal remains F0050/v0.3.

Reproduction commands are in [GETTING-STARTED](GETTING-STARTED.md); completion and reviewer tracking are in [STATUS](STATUS.md).
