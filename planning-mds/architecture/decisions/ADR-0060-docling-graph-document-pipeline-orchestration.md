# ADR-0060: Docling-Graph Document Pipeline Orchestration

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-15
**Direction authorized by:** Operator; formal ADR acceptance awaits the proof gates below.
**Implementation:** Candidate in progress. Docling-Graph 1.9.1 is locked and its checkpoint/native-JSON path has contract tests. Production activation and all acceptance gates remain pending; see [compatibility evidence](../../features/F0005-one-time-docling-ingestion/compatibility-evidence.md).
**Would refine:** ADR-0003, ADR-0004, ADR-0028, ADR-0040, ADR-0055, ADR-0058, ADR-0059. Reconsiders the exclusion recorded after F0001; the current runtime decision, accepted content/evidence contracts, and F0001 measurements remain in force pending proof.

## Context

F0001 planned a Docling-Graph proof but recorded a substitution: Docling performed conversion and a Nebula adapter called vLLM directly for extraction. The [dependency matrix](../../../docker/DEPENDENCY-MATRIX.md) records F0001's unsuccessful reuse attempt and the later correction: the pinned 1.9.1 candidate does support a separate native-JSON input path. The archived [F0001 status](../../features/archive/F0001-repository-and-engineering-foundation/STATUS.md) records that deviation. The file name `docling_graph_adapter.py` does not establish use of the upstream package. That adapter joins the persisted document text into one request; `test_parse_once_reinterpret.py` expects one model call per profile. F0001 did not prove chunked extraction. The switch must measure the change in calls, cost, context behavior, and evidence fidelity.

Upstream's current input guide documents loading DoclingDocument JSON without conversion. This warrants a fresh integration proof; it does not invalidate the recorded F0001 run. Documentation on `main` and an installed release with the same version string need not contain the same code. F0005 must identify the tested release or immutable commit and its dependency lock before enabling the new path.

## Proposed Decision

Use `docling-project/docling-graph` as the document pipeline coordinator in `neuron/`. Docling remains its conversion engine and the source of the native document representation. The switch replaces Nebula's custom coordination of specialist extraction steps; it does not remove Docling from the dependency graph.

| Owner | Responsibility |
|---|---|
| Docling-Graph | Coordinate document conversion through Docling, template-driven extraction, chunking, model calls, output validation, and extraction graph/provenance production within a processing attempt |
| Nebula ingestion and artifact adapters | Authorize input; identify source/version; publish and reuse the immutable content bundle through `ContentArtifactStore`; map native items to stable evidence references |
| Nebula interpretation adapter | Compile released profiles into supported templates/configuration; map output to `InterpretationResult`; enforce context/cost limits and evidence fidelity |
| Nebula engine | Persist jobs and runs, authorize access, recover failed attempts, review assertions, resolve enterprise identities, and commit canonical facts with audit/outbox |
| Temporal, from F0050 | Durable business workflows, timers, external-system activities, and human waits; invoke the same bounded document operation when needed |

### Artifact checkpoint and reuse

The ingestion operation coordinates conversion through Docling-Graph and publishes a complete, hashed native DoclingDocument plus normalized bundle before fallible semantic extraction proceeds. A retry after this checkpoint loads the saved native JSON. Profile changes create new interpretation runs over that bundle; they never submit the original PDF or a Markdown export as a substitute for the native JSON reuse path.

F0005 must prove a supported integration seam for the conversion checkpoint. The inspected upstream orchestrator runs extraction before its optional export stages, and API mode does not dump artifacts by default. A single `run_pipeline()` call with an output directory is therefore insufficient evidence of crash-safe parse reuse. If the selected build cannot expose/persist the converted document before a model failure, resolve that integration gap explicitly before activation; do not silently relax the invariant or reach into unpinned internals.

There is one accepted artifact per scoped document version and parser configuration. A crash before durable publication may require a conversion retry; after publication, downstream failures must never repeat conversion or OCR. Record attempts separately from accepted artifacts. Nebula owns leases, heartbeats, cancellation, idempotent publication, and job/outbox recovery under section 114.1; upstream in-process stage execution does not supply those guarantees.

### Extraction, provenance, and authority

- F0015 compiles versioned Nebula profiles to trusted Pydantic templates and explicit pipeline configuration. Templates are application-controlled; user profile fields cannot select arbitrary Python imports. The compiler retains Nebula's ontology annotations, qualifiers, units, and schema hash.
- F0016 records the artifact hash, profile/template and schema hashes, pipeline revision/configuration, model/prompt identity, selected blocks, attempt, token usage, and outcome. Extraction graph, provenance ledger, and effective configuration are immutable run outputs, stored separately from the content bundle. Reinterpretation never mutates the parse artifact.
- F0005 proves a mapping from upstream chunks and native item references into Nebula block/table locators. A node identifier's text match does not ground every property or relationship. Preserve upstream precision and merge/derived lineage; unresolved or document-level grounding cannot become a fabricated span. ADR-0058 continues to govern evidence resolution and review.
- Upstream graph IDs and deduplication are local to extraction. F0017 owns tenant-scoped enterprise identity; F0018 owns canonical commits. Graph exports cannot write directly to canonical tables or the AGE projection. Assertions and relationship candidates enter the existing review and commit path.
- Keep the self-hosted vLLM policy from ADR-0055. Enforce input plus schema/prompt plus output token budgets before every model call, including repair, fill, and reconciliation calls. Revalidate the 4,096-token profile; upstream templates do not establish model adequacy. Keep source-bearing exports access-controlled and outside routine logs.

### Runtime ownership and handoff

The proposed `DoclingGraphPipelineAdapter` in `brain-extraction` owns calls into the upstream package. `brain-ingestion` supplies the conversion checkpoint callback and keeps `build_bundle()` / `ContentArtifactStore` publication. Move the shared parse-result DTO/port out of the concrete `docling_adapter.py` module into a neutral contract before wiring these packages; neither package imports the other to construct that DTO. The adapter must provide the native document and parse quality (status, failed pages, OCR counts, warnings) to the callback before semantic extraction, through a seam proven in the selected upstream build. The callback must finish publication before processing continues. Later interpretation enters the same adapter with the persisted native JSON and performs no conversion. `PipelineContext` and upstream export paths remain private adapter details.

F0005-S0001 prototypes this seam; S0004 updates package declarations, `neuron/uv.lock`, build/run metadata, and composition wiring only for the proven candidate. Rename the existing direct client to `OpenAICompatibleExtractionAdapter` and update imports/tests as part of that runtime migration, preserving it as an explicitly named comparison baseline until acceptance. A class rename alone is not migration evidence.

### What becomes simpler

Nebula delegates chunk/extract/validate/graph coordination to one specialist pipeline and one configured model backend. After acceptance, retire duplicated extraction control flow in the current direct-vLLM adapter. Retain thin adapters for artifact publication, profile compilation, scope enforcement, evidence translation, and the provider-neutral result contract. Do not duplicate these business contracts inside upstream templates.

Docling-Graph does not replace Temporal. v0.1 keeps PostgreSQL-backed durable jobs; F0050 remains v0.3. Temporal should schedule bounded document operations, not reproduce Docling-Graph's internal chunk loop. Both paths call the same authorized application service; neither owns canonical truth.

## Delivery and acceptance

| Feature | Required change / evidence |
|---|---|
| F0004 | Retain the native six-file bundle and parser identity; separately record pipeline identity and interpretation-output manifests. Preserve ADR-0059 storage and hash verification. |
| F0005 | Pin upstream and transitive dependencies; prove native and scanned conversion, durable checkpoint before model failure, zero conversion/OCR on two later profiles, restart reuse, duplicate-job isolation, and cancellation/retry without duplicate accepted effects. |
| F0014 / F0015 | Keep document-profile selection in Nebula; compile templates/configuration with stable hashes and bounded context; expose unsupported mappings as explicit failures. |
| F0016 | Persist run outputs and provenance; prove selected-block scope, partial/failure reporting, versioned reruns, and no conversion during interpretation. |
| F0017 / F0018 | Verify graph-local merging cannot resolve enterprise identity or bypass review, authorization, or commit idempotency. |
| F0022 / F0024 / F0026 | Resolve translated evidence in the native panel; prove the real pipeline through the GL acceptance/assessment slice; measure property/relationship grounding, extraction errors, review burden, latency/cost, authorization, and recovery on the frozen corpus. |
| F0031 | Preview and release the compiled template/configuration together with its profile hash; show unsupported mappings and context estimates before execution. |
| F0032 | Prove affected-content-only reinterpretation through F0016, with stable original references and zero conversion; explicitly reject unsupported targeting. |
| F0034 | Build AGE only from accepted canonical records/outbox; never import the extraction graph as enterprise truth. |
| F0050 | Retain durable business orchestration; call the same document service from activities and preserve run/job idempotency across retries. |

F0005's proof may use two small fixed templates before the production F0015 compiler exists. F0015/F0016 then deliver the production interpretation path against the accepted adapter. Do not create a circular dependency between the foundation proof and the full compiler.

ADR acceptance and activation require observed tests against the real upstream package and local model, not a renamed mock or the existing direct client. Failure injection must cover a crash after conversion publication and a model failure before graph export. Keep the F0001 runtime as the measured baseline until those gates pass; do not claim it validates Docling-Graph. Record the selected package/source digest, measured limitations, and results in the dependency matrix. Archived F0001 requirements, results, and Done status remain historical records.

## Proof gates before acceptance

- Exact release/commit and digest plus locked dependencies; native and scanned processing, durable parse publication, worker restart, and two saved-JSON profiles with instrumented zero conversion/OCR on reuse.
- Ground limit amount, currency, basis, effective date, table headers, and values supported by multiple regions; preserve the provenance ledger and unresolved precision.
- Compare the current single-request baseline with Graph chunking on an agreed corpus: schema validity, accuracy, abstention, tokens/calls, latency, and review workload. Cover timeouts, partial conversion, invalid extraction, retries, and worker restart.
- Verify local vLLM configuration, secret redaction, bounded worker/model concurrency (including upstream internal fan-out), and tenant access/retention for source-bearing outputs.

Evidence and reviewer verdicts belong in [F0005 STATUS](../../features/F0005-one-time-docling-ingestion/STATUS.md). The pin, native/scanned conversion, publication ordering, native-JSON reuse, scalar/table evidence, and durable recovery have bounded test evidence, including PostgreSQL queue and worker/importer process-exit recovery with recorded model responses. No complete gate is satisfied: live comparative extraction, multi-region/relationship evidence, full deployment recovery, operational qualification, and reviewer acceptance remain pending. Structural planning checks cannot change this ADR to Accepted.

## References

Upstream references inspected 2026-09-15; `main` links describe the research baseline, not an approved runtime pin:

- [Input formats and native JSON reuse](https://github.com/docling-project/docling-graph/blob/main/docs/fundamentals/pipeline-configuration/input-formats.md)
- [Pipeline stage order and API export defaults](https://github.com/docling-project/docling-graph/blob/main/docling_graph/pipeline/orchestrator.py)
- [Provenance ledger and grounding semantics](https://github.com/docling-project/docling-graph/blob/main/docs/fundamentals/graph-management/provenance.md)
- [Docling dependency declaration](https://github.com/docling-project/docling-graph/blob/main/pyproject.toml)
- [Releases](https://github.com/docling-project/docling-graph/releases)
