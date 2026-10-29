# ADR-0060: Docling-Graph Document Pipeline Orchestration

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-15
**Direction authorized by:** Operator; formal ADR acceptance awaits the proof gates below.
**Implementation:** Synthetic development proof complete for the current scope. Docling-Graph 1.9.1 is locked; conversion/reuse, PostgreSQL recovery, dense extraction with recorded responses, and multi-region review mapping have bounded proof. Production acceptance and activation remain future work; see [compatibility evidence](../../features/archive/F0005-one-time-docling-ingestion/compatibility-evidence.md). Plan run `2026-10-23-9a04b327` (2026-10-23) defines the acceptance procedure: local live qualification on a synthetic corpus against operator-approved thresholds, independent QA/Architect/Security verdicts and operator acceptance, then activation through committed configuration with a direct-baseline rollback. See the F0005 [PRD](../../features/archive/F0005-one-time-docling-ingestion/PRD.md) and [assembly plan](../../features/archive/F0005-one-time-docling-ingestion/feature-assembly-plan.md).
**Approved Phase B design rework (2026-10-25):** plan run `2026-10-25-50fcf658`, Phase B existing feature, addresses PM-1/ARCH-1/BLD-1 from [plan review `2026-10-24-0fbc1de1`](../../operations/evidence/runs/2026-10-24-0fbc1de1/plan-review-report.md). The requirements and thresholds above remain approved; the operator approved these control-design amendments on 2026-10-25 with the response `approve`. They were implemented and qualified live in F0005 run `2026-10-25-4020923b`. They now ship for every pipeline under [ADR-0074](ADR-0074-local-document-job-execution-controls.md). They do not make this ADR accepted (see "F0005 qualification outcome" below).
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

F0005 implements and tests a version-pinned checkpoint stage immediately before upstream extraction, with a stage-layout guard. This is a Nebula integration seam, not an upstream durability guarantee. The inspected upstream orchestrator runs extraction before its optional export stages, and API mode does not dump artifacts by default. A single `run_pipeline()` call with an output directory is therefore insufficient evidence of crash-safe parse reuse. Dependency upgrades must revalidate the seam and publication ordering; do not silently relax the invariant or reach into unpinned internals.

There is one accepted artifact per scoped document version and parser configuration. A crash before durable publication may require a conversion retry; after publication, downstream failures must never repeat conversion or OCR. Record attempts separately from accepted artifacts. Nebula owns leases, heartbeats, cancellation, idempotent publication, and job/outbox recovery under section 114.1; upstream in-process stage execution does not supply those guarantees.

### Extraction, provenance, and authority

- F0015 compiles versioned Nebula profiles to trusted Pydantic templates and explicit pipeline configuration. Templates are application-controlled; user profile fields cannot select arbitrary Python imports. The compiler retains Nebula's ontology annotations, qualifiers, units, and schema hash.
- F0016 records the artifact hash, profile/template and schema hashes, pipeline revision/configuration, model/prompt identity, selected blocks, attempt, token usage, and outcome. Extraction graph, provenance ledger, and effective configuration are immutable run outputs, stored separately from the content bundle. Reinterpretation never mutates the parse artifact.
- F0005 proves a mapping from upstream chunks and native item references into Nebula block/table locators. A node identifier's text match does not ground every property or relationship. Preserve upstream precision and merge/derived lineage; unresolved or document-level grounding cannot become a fabricated span. ADR-0058 continues to govern evidence resolution and review.
- Upstream graph IDs and deduplication are local to extraction. F0017 owns tenant-scoped enterprise identity; F0018 owns canonical commits. Graph exports cannot write directly to canonical tables or the AGE projection. Assertions and relationship candidates enter the existing review and commit path.
- Keep the self-hosted vLLM policy from ADR-0055. Enforce input plus schema/prompt plus output token budgets before every model call, including repair, fill, and reconciliation calls. Revalidate the 4,096-token profile; upstream templates do not establish model adequacy. Keep source-bearing exports access-controlled and outside routine logs.

### Runtime ownership and handoff

The candidate `DoclingGraphPipelineAdapter` in `brain-extraction` owns calls into the upstream package. `brain-ingestion` supplies the conversion checkpoint callback and keeps `build_bundle()` / `ContentArtifactStore` publication. The shared parse-result DTO now lives in a neutral contract rather than the concrete `docling_adapter.py` module; neither package imports the other to construct that DTO. The adapter provides the native document and parse quality (status, failed pages, OCR counts, warnings) to the callback before semantic extraction, through the tested, pinned stage integration. The callback finishes publication before processing continues. Later interpretation enters the same adapter with the persisted native JSON and performs no conversion. `PipelineContext` and upstream export paths remain private adapter details.

F0005's candidate includes the checkpoint seam, package declarations, `neuron/uv.lock`, build/run metadata, and opt-in composition wiring. The direct client is now named `OpenAICompatibleExtractionAdapter` and remains the comparison baseline; its old name is a compatibility import. S0004 has recorded-response direct/dense comparison evidence, while production qualification and activation remain future work. A class rename alone is not migration evidence.

### Local control design amendments — Phase B approved 2026-10-25; implemented in F0005, now governed by ADR-0074

The [assembly plan Steps 0a and 2](../../features/archive/F0005-one-time-docling-ingestion/feature-assembly-plan.md) place physical conversion in a supervised conversion-only process group. The parent starts a monotonic 300-second deadline before launch, durably records child ownership before acknowledging conversion start, and alone accepts the validated native-JSON/quality/provenance handoff and publishes ready through the existing current-authority/generation fence. The child runs the same pinned Graph conversion/stage guard, with a serialization callback and no inference/publication capability. Timeout latches failure at 300 seconds before bounded termination/cleanup; late results cannot publish or start extraction. This replaces the prior design's reliance on the model client's cooperative deadline; it does not weaken parse-once, checkpoint ordering or F0004's bundle contract.

The local processing topology is one host-enforced worker per canonical dedicated serving endpoint, with a process-lifetime OS advisory lock in a fixed shared host control directory and a common in-process model semaphore of one. Aliases, model profiles, tenants, workspaces and temporary configs cannot allocate separate locks. The converter never inherits the descriptor. A durable in-flight marker precedes HTTP dispatch; ambiguous outcomes and SIGKILL keep replacement claims/requests stopped until the controlled-host harness/DevOps supervisor observes the dedicated provider group exit and restarts the pinned server under the same guard. Provider health alone is not quiescence. This fail-closed local recovery is measured against the existing recovery bound and is not a distributed quota or a new provider endpoint.

Steps 6–7 explicitly start ordinary new jobs on `direct-baseline` with the v2 writer disabled. Isolated qualification configs select Graph direct/dense without changing that default. Rejection verifies/restores direct-baseline/v1 after restart; acceptance selects Graph dense/v2. Extraction rollback after acceptance selects direct while retaining the qualified v2 writer. New job idempotency includes the pipeline; historical jobs retain their existing keys/pinned meaning. Negative tests cover every branch, deadline races, child/orphan cleanup and competing-worker/provider-crash recovery before activation. None of these proposed controls changes this ADR's status or approves runtime activation.

### What becomes simpler

> **Not in force.** Graph dense was rejected in F0005 (see below). The direct client stays the runtime default and is not retired. This section describes the design only if a future re-plan is accepted.

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

These are production-acceptance requirements. The current early-development scope uses synthetic fixtures and is complete without claiming these release gates. The [synthetic comparison](../../features/archive/F0005-one-time-docling-ingestion/synthetic-comparison.json) proves dense skeleton/fill orchestration with recorded responses; its estimated tokens and local timing are not model-quality or serving-cost measurements. On its longer fixtures, Graph direct lacks usable item refs and remains unresolved; dense preserves the refs. Multi-region grounding requires complete character coverage and retains separate selectors through review. Unsupported relationship output still fails closed.

- Exact release/commit and digest plus locked dependencies; native and scanned processing, durable parse publication, worker restart, and two saved-JSON profiles with instrumented zero conversion/OCR on reuse.
- Ground limit amount, currency, basis, effective date, table headers, and values supported by multiple regions; preserve the provenance ledger and unresolved precision.
- Compare the current single-request baseline with Graph chunking on an agreed corpus: schema validity, accuracy, abstention, tokens/calls, latency, and review workload. Cover timeouts, partial conversion, invalid extraction, retries, and worker restart.
- Verify local vLLM configuration, secret redaction, bounded worker/model concurrency (including upstream internal fan-out), and tenant access/retention for source-bearing outputs.

**Acceptance scope (2026-10-23).** Under the operator's F0005 scope decision, acceptance on F0005's local qualification governs the local Docker Compose runtime only. Production host qualification and frozen-corpus acceptance remain F0026 obligations, and they may reopen this decision. A rejection keeps the direct client as the runtime default and records the failed gates here.

Evidence and reviewer verdicts belong in [F0005 STATUS](../../features/archive/F0005-one-time-docling-ingestion/STATUS.md). The pin, native/scanned conversion, publication ordering, native-JSON reuse, scalar/table evidence, and durable recovery have bounded test evidence, including PostgreSQL queue and worker/importer process-exit recovery with recorded model responses. The synthetic comparison also proves dense extraction orchestration and multi-region grounding through import and review. Production gates remain open: live comparative extraction and property/multi-region evidence qualification, unsupported relationship semantics, full deployment recovery, operational qualification, and reviewer acceptance. Structural planning checks cannot change this ADR to Accepted.

## F0005 qualification outcome (2026-10-27): Graph dense rejected; ADR stays Proposed

**Decision recorded by the operator at F0005 G4, run `2026-10-25-4020923b` (2026-10-27).** Graph dense is rejected for activation. The direct client (`direct-baseline`) stays the runtime default with the v2 writer disabled. This ADR stays **Proposed** with the failed gates recorded here.

**Reopen condition:** if no re-plan of this candidate is approved by the start of F0014/F0015 planning, the operator marks this ADR Rejected. A re-plan (a larger output reservation, another serving model, or Graph direct as the candidate) is a new plan with full re-measurement, never a re-score of the recorded report.

**Measured gates.** Local live qualification on the synthetic corpus `f0005-gl-qualification-v1` (13 documents, 26 document-profiles per engine). Phi-4-mini-instruct @ `cfbefacb…`, vLLM 0.25.1, context 4,096, output reservation 512, Docling-Graph 1.9.1. Report `artifacts/qualification/report.json`, `void: false`; QA recomputed every value independently.

| PRD threshold | Direct baseline | Graph dense | Gate |
|---|---|---|---|
| Field accuracy ≥ 90% and ≤ 5 pp below baseline | 41.4% | 27.6% | **Failed** |
| Abstention ≥ 95% | 42.9% | 0% | **Failed** |
| Evidence resolution ≥ 80% and ≥ baseline | 66.7% | 50.0% | **Failed** |
| Latency p95 ≤ 120 s and ≤ 3× baseline | 1.48 s | 9.84 s (6.6×), completed runs only (report v1) | **Failed** |
| Review workload ≤ 1.25× baseline | 2.92 per document | 1.54 per document; 1.42–1.64× (1.64× per completed run; 1.42× on the 7 cases both engines completed — corrected after G3 round 2) per completed run | **Failed** like for like (met only because failed runs add no items) |
| Schema validity, fabricated evidence, context budget, recovery | met | met | Passed. Context budget counts only dispatched calls: this measurement predates H1, so pre-dispatch rejections could not be recorded. The run log shows none. |

Report `artifacts/qualification/report.json`, SHA-256 `55ce348489e253bc2a053adbaf7591d4e678d83470792ab0bf26b0207aabaede`, `report_version` 1. Corpus hash `fbc5e263c861c401dea07e3deac4023a0f660d35bb2edc891f8297ee0a5e2dc9`; expectation-set hash `16a29d67dddddea4e18136465567f67cd63c790fa9eb68018c35e4636933390c`.

**Root cause (model adequacy on this profile, not the orchestration seam).** 18 of 26 Graph-dense runs failed explicitly in the first-stage skeleton call. The response was either cut off at the 512-token output reservation or contained duplicate JSON keys, and repeated identically at temperature 0. The seam itself passed live:
- checkpoint-before-model ordering;
- native and scanned conversion;
- zero reconversion on reuse;
- bounded concurrency;
- isolation from canonical tables.

ADR-0055 §4 anticipates proposing an alternative backend in this situation.

**Measured limitations to carry into any re-plan:**
- **Graph direct** (reported, not a candidate) reached 84.5% accuracy but 0% evidence resolution, because its ledger lacks item references.
- **The baseline excludes tables,** which flatters the relative thresholds.
- **84.6% of documents fall back** from v2 to v1, because table cells have no attributable origin.
- **Docling-Graph 1.9.1 swallows per-call exceptions** and falls back from dense to one direct call. Nebula now fails both cases explicitly (Code Review H1).
- **The F0005 dense measurement predates that fix,** although its runs show no budget rejections.

**Controls moved.** The Phase B control amendments above (supervised conversion, the host guard and quiescence, failure reasons, the submission bound, pipeline selection) ship for every pipeline. They now have their own record: [ADR-0074](ADR-0074-local-document-job-execution-controls.md). They no longer depend on this ADR's status. The F0005 manifest OCR fields are recorded in the [ADR-0073](ADR-0073-versioned-content-contracts-and-document-metadata.md) amendment of 2026-10-27.

## References

Upstream references inspected 2026-09-15; `main` links describe the research baseline, not an approved runtime pin:

- [Input formats and native JSON reuse](https://github.com/docling-project/docling-graph/blob/main/docs/fundamentals/pipeline-configuration/input-formats.md)
- [Pipeline stage order and API export defaults](https://github.com/docling-project/docling-graph/blob/main/docling_graph/pipeline/orchestrator.py)
- [Provenance ledger and grounding semantics](https://github.com/docling-project/docling-graph/blob/main/docs/fundamentals/graph-management/provenance.md)
- [Docling dependency declaration](https://github.com/docling-project/docling-graph/blob/main/pyproject.toml)
- [Releases](https://github.com/docling-project/docling-graph/releases)
