# F0005 assembly plan

**Status:** Draft delivery plan; candidate adapter and contract tests implemented. See [compatibility evidence](compatibility-evidence.md). The opt-in worker, authorization binding, and transactional result import are implemented; live qualification and activation remain pending. ADR-0060 is Proposed.

## Ownership and package boundary

AI engineering owns the proposed `DoclingGraphPipelineAdapter` in `brain-extraction`, the only adapter calling upstream Graph. It handles raw input and saved-native-JSON entry points, templates, and InterpretationResult/evidence translation. Ingestion owns `build_bundle()` and ContentArtifactStore publication. The parse-result DTO is shared through `brain_interpretation.parsed_content`; engine and neuron share the result DTO from `brain-contracts`. Neither engine persistence nor review imports the AI implementation.

The job supplies a synchronous publication boundary to the pipeline adapter. After conversion, the adapter passes the native DoclingDocument plus status, failed pages, OCR counts, page count, and warnings into this boundary. Ingestion builds/hashes the six-file bundle, retains the source, publishes the completion marker, and records the checkpoint. Extraction can proceed only after that succeeds. Prove the selected package exposes a supported seam for this ordering. End-of-pipeline exports or a PipelineContext available only on successful return do not establish the checkpoint.

Backend owns jobs, leases/heartbeats, fencing of stale attempts, cancellation, scoped idempotency, authorized reads, and outbox effects. QA owns independently expected corpus results and failure injection. Security review covers credential handling, data egress, tenant isolation, concurrency exhaustion, and provenance retention. These are ownership assignments, not reviewer signoffs.

## Build order

| Step | Story | Exit condition |
|---|---|---|
| 1 | S0001 | Exact candidate resolved; real native/scanned conversion and supported checkpoint handoff demonstrated. |
| 2 | S0002 | F0004 storage contract integrated; model failure/restart, incomplete publication, duplicate jobs, and scoped recovery proven. |
| 3 | S0003 | Two profiles over saved JSON after restart; no conversion/OCR; honest property/relationship evidence; scoped input and per-call budget guards. |
| 4 | S0004 | Comparative corpus and all failure/security/resource gates measured, reviewers recorded, then ADR acceptance and runtime activation. |

Use fixed proof templates for steps 1–3. F0015 compiles production templates; F0016 persists full production runs; F0032 schedules affected-content evolution. Do not make those later features prerequisites for the fixed-template compatibility test. Production ingestion also needs F0002/F0003 authorization and durable persistence, while isolated proof setup may reuse F0001 fixtures.

## Runtime migration inventory

- Add the proven Graph dependency to the owning `neuron/packages/brain-extraction/pyproject.toml`, align Docling/docling-core consumers, and regenerate `neuron/uv.lock` reproducibly. Do not install a floating `main` dependency.
- Preserve `build_bundle()` semantics while extracting its concrete ParseResult import into the shared contract. Wire the pipeline adapter/publication callback in the application composition boundary.
- Rename the current misleading `DoclingGraphAdapter` / module to an explicitly direct OpenAI-compatible baseline and update imports/tests. Retain benchmark comparability; remove duplicate production coordination only after acceptance.
- Record parser version/conversion recipe separately from pipeline revision, template/schema/chunk settings, model revision, and run provenance. Version strict schema additions and retain compatible readers.
- Update build/run metadata, dependency matrix, actual C4 runtime description, and runnable instructions when activation occurs. No graph output bypasses engine assertion/review/commit services.

## Proof and resource controls

Instrument converter/OCR entry points during saved-JSON tests; do not trust self-reported counters alone. Preserve parse-quality diagnostics on timeout, invalid extraction, and partial conversion. Compare the existing full-document single-call path with Graph chunking and report calls/tokens, schema validity, accuracy, abstention, evidence fidelity, latency, and review workload.

Set explicit worker/model concurrency and queue/backpressure limits, including Graph-internal fan-out and retries; cancellation must stop further model scheduling. Enforce context budgets before every model call. Verify secrets never enter prompts or ordinary logs. Apply tenant access and retention/deletion to graph exports, chunks, provenance, temporary files, and retained run outputs.

## Open decisions before acceptance

| Decision | Owner | Required by |
|---|---|---|
| Exact release/commit/digest and supported conversion checkpoint API | AI engineer + architect | S0001 |
| Versioned artifact/run metadata DTOs and durable publication transaction | Backend + architect | S0002 |
| Licensed corpus, independent expected values, reviewers, and quality/cost/latency thresholds | QA + product owner | Before S0004 comparison |
| Concurrency caps, secret injection, source-output retention and cleanup configuration | Backend + security | S0002/S0004 |

## Rollout

Keep the current F0001 runtime until the proof gates pass. Record actual results and reviewer verdicts in STATUS and the feature evidence run. Only then accept ADR-0060 and enable the new implementation. Failure leaves the proposed integration pending; do not silently relax parse reuse or relabel direct-client results as Graph proof.
