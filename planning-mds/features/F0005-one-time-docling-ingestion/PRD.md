# F0005 — One-time document ingestion — PRD

## Feature Header

**Feature ID:** F0005\
**Feature Name:** One-time document ingestion\
**Priority:** High\
**Phase:** MVP — v0.1A\
**Status:** Requirements re-planned in plan run `2026-10-23-9a04b327` (Phase A approved by the operator with `approve-phase-a` on 2026-10-23, including the qualification thresholds; Phase B approved with `approve-phase-b` the same day). The synthetic development scope delivered 2026-09-20 to 2026-09-22 remains complete; this plan defines the remaining local qualification and gated activation. See [STATUS](STATUS.md).

## Feature Statement

**As a** document intelligence engineer
**I want** durable one-time ingestion and repeatable interpretation of saved native content, qualified against a live local model
**So that** model failures and profile changes never repeat published parsing or lose source evidence, and the Docling-Graph pipeline replaces the direct client only on measured evidence.

## Business Objective

Decide ADR-0060 on observed local evidence. The candidate pipeline (Docling-Graph 1.9.1 over Docling 2.126.0) is implemented and opt-in, with synthetic, recorded-response proof only. F0005 finishes when the pipeline is either qualified and activated as the local default, or rejected with the F0001 direct client retained. Both outcomes are complete if recorded with evidence.

## Problem Statement

The current proof never ran a live model through Graph, never measured quality or cost against the direct baseline, and never injected live-provider or storage failures. Since it was written, F0002–F0004 shipped verified principals, persistence discipline, versioned content contracts, text-origin records and a disabled v2 writer. F0004 handed F0005 two obligations: exact OCR model-asset provenance and fixed Docling/hook qualification before broader v2 activation. Without this plan, the candidate stays opt-in indefinitely and downstream features (F0014–F0016, F0024) plan against an unqualified extraction path.

## Scope & Boundaries

**Operator scope decisions (G1, 2026-10-23):**

1. Local qualification plus gated activation: live `microsoft/Phi-4-mini-instruct` on vLLM on the development host GPU, real failure injection, a direct-versus-Graph comparison with thresholds fixed in this PRD. If every gate passes, ADR-0060 is accepted and Graph becomes the default extraction path in local Docker Compose. The production host remains F0026.
2. Synthetic qualification corpus with independent expectations and independent agent-role reviewers; the operator accepts the result. No licensed real documents are used or claimed.
3. F0005 qualifies text origin and exact OCR asset provenance, then enables `content.v2_writer_enabled` for new sources as an activation step, keeping F0004's per-document v1 fallback.
4. F0016 owns producing CONTENT and SOURCE_METADATA document-date candidates. F0005 produces none.

**In scope:**

- Live native, scanned and mixed-page conversion on the pinned package with exact parser, OCR engine and OCR model-asset identity.
- Live two-profile interpretation over saved native JSON with zero conversion/OCR, through the dense (chunked) Graph contract and the direct baseline.
- Live failure injection: provider unavailable, timeout, malformed and schema-invalid output, worker kill after publication, storage write failure, cancellation and duplicate submission.
- Evidence qualification for amounts, dates, names, table cells, repeated values and multi-region values; unsupported relationship output fails closed.
- A synthetic qualification corpus, a recorded comparison against the thresholds below, and independent QA, Architect and Security verdicts.
- Activation: Graph dense as the worker default, v2 writer enabled for new sources, metadata/dependency-matrix/C4 updates, and a tested rollback switch to the direct baseline.

**Out of scope:** production host or multi-replica deployment (F0026); licensed or frozen-holdout corpora (F0026); F0015 profile compiler and profiles beyond `gl-limits-a`/`gl-limits-b`; F0016 production run lifecycle and date-candidate production; F0032 targeted evolution; F0017 entity resolution; canonical acceptance (F0018); AGE loading; review UI changes (F0022); Temporal (F0050); new OCR engines or input formats beyond PDF. Archived F0001 records remain unchanged.

## Acceptance Criteria Overview

- [ ] S0001: live native, scanned and mixed-page conversion on the pinned package publishes a bundle before any model call, records exact parser/OCR identities and preserves partial-conversion diagnostics.
- [ ] S0002: live provider and storage failures, worker kills, cancellation and duplicates recover with zero reconversion after publication and no duplicate accepted effects; run outputs follow tenant access and retention.
- [ ] S0003: live two-profile reinterpretation over saved JSON grounds every resolved value in its actual source regions, keeps the rest unresolved, keeps every call within budget and fails closed on relationship output.
- [ ] S0004: the corpus comparison meets every threshold below with recorded reviewer verdicts; only then are ADR-0060 accepted and Graph activated, with a tested rollback.
- [ ] S0005: per-item text origin and exact OCR asset provenance pass on the live corpus, and consumers read v2 bundles before the v2 writer is enabled.

## Qualification Thresholds (operator-approved 2026-10-23)

Measured on the full qualification corpus, both profiles, one recorded run configuration per engine. A threshold miss blocks activation; it is never waived by reinterpretation.

| Metric | Definition | Graph dense must achieve |
|---|---|---|
| Schema validity | Completed runs whose result validates against the profile schema; invalid output must surface as an explicit failure | 100% (no silently invalid result) |
| Field accuracy | Fields whose normalized value equals the independent expectation, over present expected fields | ≥ 90% overall, and no more than 5 percentage points below the direct baseline |
| Abstention | Expected-absent fields returned as null | ≥ 95% |
| Fabricated evidence | Resolved selectors whose source text does not support the value | 0 |
| Evidence resolution | Correct values resolved to an exact span/cell (the rest unresolved or coarse, never fabricated) | ≥ 80%, and not below the direct baseline |
| Context budget | Model calls whose input + schema + output reservation exceeds the 4,096-token serving context | 0 |
| Latency | p95 wall time per document-profile interpretation on the development host | ≤ 120 s and ≤ 3× the direct baseline p95 |
| Review workload | Review items per document | ≤ 1.25× the direct baseline |
| Recovery | Reconversions after publication, or duplicate accepted artifacts/runs/assertions, across all injected failures | 0 |

Calls, prompt/completion tokens (serving tokenizer) and GPU memory are reported, not thresholded. Thresholds apply to synthetic development data only and do not transfer to F0026 production acceptance.

## UX / Screens

**Key workflows:** authorized submission → conversion → bundle publication (checkpoint) → per-profile interpretation over saved JSON → transactional import → review items; failure → retry from checkpoint; operator activation and rollback through committed configuration.

Existing job status and evidence consumers must keep distinguishing pending, partial, failed and completed work, and must not treat a failed extraction as missing source evidence. Native review stays F0022; its Review Panel consumes imported evidence unchanged.

## Screen Layouts (ASCII)

No UI. F0005 changes worker, ingestion and configuration behavior only; no screen is introduced or materially modified, so desktop and narrow layouts are not applicable.

## Data Requirements

Keep separate source, content-artifact and interpretation identities (ADR-0004). Conversion identity: parser name/version/configuration, OCR engine name/version and exact OCR model-asset identity (name, revision, file digest). Interpretation identity: Graph revision, extraction contract (direct or dense), template/schema hash, chunking settings, serving model id and revision, tokenizer revision. Graph chunks, extraction graph and provenance ledger are run-owned outputs, never bundle content.

**Qualification corpus:** at least 12 synthetic GL declarations documents outside the frozen holdout — at least 6 native, 4 scanned and 2 mixed-page — covering unique values, repeated values, table-borne limits, values split across regions, absent fields and one partial conversion. Expected values and evidence locations for all five profile fields are authored from the document source, before and independently of any extraction output, and committed with their hashes.

**Validation rules:** missing values stay missing; unknown origin stays `ORIGIN_UNAVAILABLE` and triggers v1 fallback; a node-identifier match cannot ground all of its properties; unsupported targeting or relationship output is an explicit failure.

## Role-Based Access

Reuse F0002 principals and the existing `ServicePrincipal` `ingest`/`interpret` grants; no new role, permission or endpoint. Authorization is rechecked at each sensitive boundary, including after restart. Model requests carry authorized chunk text only, never principal, tenant or credential data (ADR-0055 data policy). Run outputs, temporary exports and qualification artifacts holding source text are readable only under the owning tenant/KB scope. The CLI remains a trusted-operator interface.

## Success Criteria

- Each story passes with observed live evidence; recorded-response tests remain regression coverage, not qualification.
- Every threshold above is measured and recorded with commands, pins, corpus hashes and per-case results.
- QA, Architect and Security verdicts and the operator's acceptance are recorded before ADR-0060 or activation changes state.
- A rejection is a valid outcome: the direct client stays default, ADR-0060 records the failed gates, and no partial activation remains.
- The feature action records at least 80% coverage for changed runtime scope.

## Risks & Assumptions

- **Model adequacy:** Phi-4-mini's 4,096-token context may force small chunks and many calls; thresholds may fail. That outcome is recorded, not tuned away by weakening budgets.
- **Synthetic bias:** the corpus is authored by agents, so results show pipeline fitness on representative layouts, not real-world accuracy. F0026 owns frozen-corpus acceptance.
- **Reviewer independence:** agent reviewers must not author the corpus expectations they judge; the assembly plan assigns separate roles.
- **Upstream seam:** the checkpoint stage relies on the pinned stage layout. Any dependency change revalidates the seam before reuse.
- **GPU contention:** one 12 GB host GPU serves one model; concurrency is qualified at one worker replica with an explicit model semaphore.

No business question remains open; Phase B fixes the failure-injection mechanics, corpus format and switch names.

## Dependencies

| Feature | Relationship / boundary |
|---|---|
| F0001 (archived) | Direct-client baseline, fixtures and inference profile (ADR-0055). |
| F0002 (archived) | Verified principals, grants, audited authorization decisions. |
| F0003 (archived) | PostgreSQL persistence, migration and restore discipline. |
| F0004 (archived) | Versioned bundle contracts, verifier, text-origin records, v2 writer switch, per-document v1 fallback; hands F0005 OCR asset provenance and hook qualification. |
| F0014/F0015/F0016 | Downstream: production profiles, compiler and run lifecycle consume the qualified adapter. F0016 owns date candidates. |
| F0022 | Downstream review display of imported evidence; no change required. |
| F0026 | Production host, frozen corpus and release qualification reuse these cases. |

## Related Stories

- [S0001 — Pin and process source documents](F0005-S0001-pin-and-process-source-documents.md)
- [S0002 — Persist artifacts and recover jobs](F0005-S0002-persist-artifacts-and-recover-jobs.md)
- [S0003 — Reinterpret saved JSON and map evidence](F0005-S0003-reinterpret-saved-json-and-map-evidence.md)
- [S0004 — Evaluate and activate the proven pipeline](F0005-S0004-evaluate-and-activate-proven-pipeline.md)
- [S0005 — Qualify text origin and enable v2 publication](F0005-S0005-qualify-text-origin-and-enable-v2-publication.md)

## Example Library

No new semantic concept is introduced. The qualification corpus specializes the continuing EX-GL-001 case and reuses F0004's EX-CONTENT examples for bundle, origin and fallback behavior. Its documents are synthetic development data, outside the frozen holdout.
