# F0005 acceptance criteria checklist

**Status:** Re-planned in plan run `2026-10-23-9a04b327`; no criterion verified. Synthetic development evidence delivered 2026-09-20 to 2026-09-22 is regression coverage and does not tick any live-qualification criterion.

## F0005-S0001 — Pin and process source documents

- [ ] [F0005-S0001-AC1](F0005-S0001-pin-and-process-source-documents.md) — Given a clean checkout, when both workspaces sync from their locks, then the resolved Docling-Graph, Docling and docling-core versions and the Graph wheel digest equal the recorded pin, and any difference fails the qualification run before conversion.

- [ ] [F0005-S0001-AC2](F0005-S0001-pin-and-process-source-documents.md) — Given each native, scanned and mixed-page corpus document, when it enters the real pipeline with physical conversion and OCR enabled, then the published bundle records parser name/version/configuration, OCR engine name/version, page count, failed pages, OCR page count, warnings and source hash; mocks or recorded native JSON cannot satisfy this criterion.

- [ ] [F0005-S0001-AC3](F0005-S0001-pin-and-process-source-documents.md) — Given conversion completes and the model endpoint then fails or returns invalid output, when the checkpoint stage runs, then the bundle is verified and registered before the first model request, and the job records the model failure without discarding or reconverting the bundle.

- [ ] [F0005-S0001-AC4](F0005-S0001-pin-and-process-source-documents.md) — Given the corpus's partial-conversion document, when conversion returns, then supported content is published with its failed pages and partial status, and no later stage labels the document complete.

- [ ] [F0005-S0001-AC5](F0005-S0001-pin-and-process-source-documents.md) — Given the checkpoint callback fails or the installed stage layout differs from the pinned guard, when processing is attempted, then extraction does not start, the job fails with an explicit integration reason, and no artifact is registered ready.

- [ ] [F0005-S0001-AC6](F0005-S0001-pin-and-process-source-documents.md) — Given a job, artifact or run state change, when the operation succeeds or fails, then an audit event records actor and job identity, correlation and attempt IDs, artifact/run references, outcome and timestamp, without secrets or source text.

## F0005-S0002 — Persist artifacts and recover jobs

- [ ] [F0005-S0002-AC1](F0005-S0002-persist-artifacts-and-recover-jobs.md) — Given a published bundle, when the live vLLM endpoint is stopped, times out, returns HTTP 5xx, returns malformed JSON or returns schema-invalid output, then the attempt fails with a distinct recorded reason, finite retries resume from the saved native JSON, and converter/OCR call counters stay at zero after publication.

- [ ] [F0005-S0002-AC2](F0005-S0002-persist-artifacts-and-recover-jobs.md) — Given a worker process killed after bundle publication, after result publication, mid-import and after import commit, when a new worker claims the job, then it completes with exactly one accepted artifact, one run per profile, one assertion/evidence/review set and one acknowledged completion.

- [ ] [F0005-S0002-AC3](F0005-S0002-persist-artifacts-and-recover-jobs.md) — Given a storage write failure or crash before the manifest completion marker, when recovery runs, then the incomplete publication is never exposed as ready, is cleaned or resumed under the F0004 store contract, and the job reconverts at most once.

- [ ] [F0005-S0002-AC4](F0005-S0002-persist-artifacts-and-recover-jobs.md) — Given duplicate submissions, competing workers, expired leases or cancellation during model calls, when jobs execute, then stale attempts are fenced, cancellation stops further model scheduling within one in-flight call, and the configured model concurrency limit (default 1 for the host GPU) is never exceeded, including Graph-internal fan-out.

- [ ] [F0005-S0002-AC5](F0005-S0002-persist-artifacts-and-recover-jobs.md) — Given a different tenant, a revoked grant or an inactive principal, when a job or reader accesses source, bundle, run output or temporary export, then access is denied and audited; the job does not continue under stale authority.

- [ ] [F0005-S0002-AC6](F0005-S0002-persist-artifacts-and-recover-jobs.md) — Given run outputs, chunks, provenance ledgers and temporary exports holding source text, when a run completes, fails or is cancelled, then temporary files are removed and retained outputs sit under the owning tenant/KB scope with the same retention as the source.

- [ ] [F0005-S0002-AC7](F0005-S0002-persist-artifacts-and-recover-jobs.md) — Given a job, artifact or run state change, when the operation succeeds or fails, then an audit event records actor and job identity, correlation and attempt IDs, artifact/run references, outcome and timestamp, without secrets or source text.

## F0005-S0003 — Reinterpret saved JSON and map evidence

- [ ] [F0005-S0003-AC1](F0005-S0003-reinterpret-saved-json-and-map-evidence.md) — Given each published corpus bundle after a worker restart, when `gl-limits-a` and `gl-limits-b` run through the live dense contract, then saved DoclingDocument JSON is the only input, converter/OCR entry points are instrumented and called zero times, bundle hashes are unchanged, and each run records distinct template, schema, chunking, model and tokenizer identities.

- [ ] [F0005-S0003-AC2](F0005-S0003-reinterpret-saved-json-and-map-evidence.md) — Given live output for limits, dates and the named insured, when evidence is resolved, then every resolved selector's source text supports its value (Unicode offsets and table cells checked against the bundle), repeated or ambiguous values stay unresolved, and multi-region values need complete character coverage.

- [ ] [F0005-S0003-AC3](F0005-S0003-reinterpret-saved-json-and-map-evidence.md) — Given Graph chunks, nodes and properties, when the adapter builds InterpretationResult, then the provenance ledger and native item references are retained as run outputs; graph IDs and local merges never become enterprise identity or canonical facts.

- [ ] [F0005-S0003-AC4](F0005-S0003-reinterpret-saved-json-and-map-evidence.md) — Given output containing relationships or entity types without a downstream mapping, when it is imported, then the import fails closed with an explicit unsupported-output reason and no partial assertions.

- [ ] [F0005-S0003-AC5](F0005-S0003-reinterpret-saved-json-and-map-evidence.md) — Given any model call (skeleton, fill, repair or reconciliation), when it is scheduled, then input + schema + output reservations measured with the serving tokenizer fit the 4,096-token context; an oversized request fails before sending.

- [ ] [F0005-S0003-AC6](F0005-S0003-reinterpret-saved-json-and-map-evidence.md) — Given a selected-block or targeted request, when interpretation begins, then it fails explicitly as unsupported rather than broadening to the full document; F0032 owns targeted evolution.

- [ ] [F0005-S0003-AC7](F0005-S0003-reinterpret-saved-json-and-map-evidence.md) — Given a job, artifact or run state change, when the operation succeeds or fails, then an audit event records actor and job identity, correlation and attempt IDs, artifact/run references, outcome and timestamp, without secrets or source text.

## F0005-S0004 — Evaluate and activate the proven pipeline

- [ ] [F0005-S0004-AC1](F0005-S0004-evaluate-and-activate-proven-pipeline.md) — Given the qualification corpus (at least 12 synthetic documents: 6 native, 4 scanned, 2 mixed-page), when it is committed, then every expected value and evidence location was authored from the document source by a role that does not run or review the extraction, and the corpus and expectation hashes are recorded before the first measured run.

- [ ] [F0005-S0004-AC2](F0005-S0004-evaluate-and-activate-proven-pipeline.md) — Given the direct baseline and Graph dense under recorded configurations (pins, model and tokenizer revision, chunking, budgets), when both profiles run over the full corpus, then the report records per-case and aggregate schema validity, field accuracy, abstention, fabricated evidence, evidence resolution, calls, serving-tokenizer tokens, p95 latency and review items per document.

- [ ] [F0005-S0004-AC3](F0005-S0004-evaluate-and-activate-proven-pipeline.md) — Given the report, when it is compared with the PRD thresholds, then each threshold is marked met or missed with its measured value; a missed threshold blocks activation and is never re-run with relaxed budgets to pass.

- [ ] [F0005-S0004-AC4](F0005-S0004-evaluate-and-activate-proven-pipeline.md) — Given S0001–S0003 and S0005 evidence plus the report, when QA, Architect and Security review them, then each records a verdict with evidence references in STATUS, and the operator records acceptance or rejection.

- [ ] [F0005-S0004-AC5](F0005-S0004-evaluate-and-activate-proven-pipeline.md) — Given all thresholds met, every verdict passing and operator acceptance, when activation runs, then ADR-0060 becomes Accepted, the worker default extraction contract becomes Graph dense through committed non-secret configuration, the v2 writer is enabled per S0005, and the dependency matrix, build/run metadata and C4 runtime description are updated together.

- [ ] [F0005-S0004-AC6](F0005-S0004-evaluate-and-activate-proven-pipeline.md) — Given an activated configuration, when the rollback setting selects the direct baseline, then new runs use the direct client with its own identity, existing artifacts and runs stay readable and unchanged, and no run mixes engines.

- [ ] [F0005-S0004-AC7](F0005-S0004-evaluate-and-activate-proven-pipeline.md) — Given any threshold miss, failing verdict or operator rejection, when the feature closes, then the direct client stays default, the v2 writer stays disabled, ADR-0060 records the failed gates (Proposed or Rejected per operator), and no partial activation remains.

- [ ] [F0005-S0004-AC8](F0005-S0004-evaluate-and-activate-proven-pipeline.md) — Given a job, artifact, run or activation state change, when the operation succeeds or fails, then an audit event records actor and job identity, correlation and attempt IDs, artifact/run references, outcome and timestamp, without secrets or source text.

## F0005-S0005 — Qualify text origin and enable v2 publication

- [ ] [F0005-S0005-AC1](F0005-S0005-qualify-text-origin-and-enable-v2-publication.md) — Given every qualification-corpus document converted live, when per-item origin is projected, then each native text item is `STATED` with its observed producer, each OCR item is `OCR` with engine name/version, and items that cannot be attributed return `ORIGIN_UNAVAILABLE`; no origin is derived from page OCR counts.

- [ ] [F0005-S0005-AC2](F0005-S0005-qualify-text-origin-and-enable-v2-publication.md) — Given OCR ran, when the bundle is published, then the OCR model assets used are identified by name, revision and file SHA-256 read from the installed asset files; an unidentifiable asset blocks v2 publication for that document instead of recording a guessed identity.

- [ ] [F0005-S0005-AC3](F0005-S0005-qualify-text-origin-and-enable-v2-publication.md) — Given a document with any `ORIGIN_UNAVAILABLE` item and the v2 writer enabled, when it is published, then it falls back to a v1 bundle with `writer_fallback_reason=ORIGIN_UNAVAILABLE` audited, and the per-corpus fallback rate is reported.

- [ ] [F0005-S0005-AC4](F0005-S0005-qualify-text-origin-and-enable-v2-publication.md) — Given v2 bundles from the corpus, when every existing consumer reads them (authorized content reader, evidence resolver, Graph adapter saved-JSON path, importer, restore drill), then they pass with unchanged behavior; v1 bundles stay readable.

- [ ] [F0005-S0005-AC5](F0005-S0005-qualify-text-origin-and-enable-v2-publication.md) — Given AC1–AC4 pass and S0004 activation is accepted, when `content.v2_writer_enabled` is set to `true` in committed configuration, then new sources publish v2 bundles and existing artifacts are not rewritten.

- [ ] [F0005-S0005-AC6](F0005-S0005-qualify-text-origin-and-enable-v2-publication.md) — Given a job, artifact or run state change, when the operation succeeds or fails, then an audit event records actor and job identity, correlation and attempt IDs, artifact/run references, outcome and timestamp, without secrets or source text.

## Cross-cutting exit checks

- [ ] Every PRD qualification threshold has a measured value marked met or missed in the S0004 report.

- [ ] QA, Architect and Security verdicts and the operator decision are recorded in STATUS before ADR-0060 or configuration changes state.

- [ ] Changed runtime scope has at least 80% coverage.
