# F0016 — Semantic interpretation runs

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

Semantic interpretation runs version every extraction over persisted content and are the unit of incremental reinterpretation (sections 28, 29). Each run records pipeline, profile and model identity and the exact scope it interpreted.

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0016](../../architecture/decisions/ADR-0016-semantic-reinterpretation-is-incremental.md), [ADR-0035](../../architecture/decisions/ADR-0035-interpretation-basis-is-first-class.md).

## Requirement-ownership amendment (2026-11-08)

The 2026-11-08 review of the master blueprint against the feature portfolio assigned these requirements to this feature (master blueprint section 106.3). Carry them into the PRD and stories when the feature is planned; the feature status is unchanged.

- **Dependencies:** F0004, F0005, F0006, F0015 (previously F0015, F0005, F0004, F0001).
- ADR-0060 was Rejected on 2026-11-08; runs use the direct-baseline pipeline and record pipeline identity for any future backend.
- Carry master blueprint 110.4 (untrusted inputs) - extracted text is evidence, never instruction. Acceptance - a PDF instructing a limit change or another account disclosure produces no tool action, cross-account retrieval or canonical mutation. Extraction workers hold no business-write credentials; run metadata stores secret references only.
- Carry 110.4 model routing - v0.1 inference is local only (ADR-0055); a timeout never falls back to another provider. Carry 114.2 - record stage latency, pages/blocks, tokens, retries and cost per run without sensitive text.
- Carry 107.4 - each run records the scope it interpreted so NOT_PROCESSED and NOT_FOUND are scoped. Carry the 88 embedding-abstraction hook as a port with no adapter (F0033 implements it).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0016.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15) — withdrawn 2026-11-08

> **Withdrawn 2026-11-08.** The operator Rejected [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). Requirements below that are specific to Docling-Graph (templates, compiled Graph configuration, run-owned extraction graphs, upstream chunk/item provenance, Graph quality gates) no longer apply. Pipeline-neutral requirements (checkpoint before model, zero-reconversion reuse, honest evidence precision, idempotent authorized commit, isolation from canonical tables) still apply to the direct-baseline pipeline. The text is kept as history.

> **F0005 outcome (2026-10-28) supersedes the scope amendment below.** Graph dense was qualified live and rejected (F0005 run `2026-10-25-4020923b`, PR #30).
> - **Defaults:** `direct-baseline` and the v1 writer stay the defaults.
> - **ADR-0060 status:** **Rejected** by the operator on 2026-11-08 (the reopen decision).
> - **Plan** against the direct baseline and the accepted execution controls in [ADR-0074](../../architecture/decisions/ADR-0074-local-document-job-execution-controls.md). The Docling-Graph-specific requirements below are withdrawn.

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governed this planned work until the operator Rejected it on 2026-11-08; see the withdrawal note above.

- Load only the published native artifact for initial interpretation and later reruns. Record artifact hash, selected blocks, profile/template/schema/config hashes, explicit chunking/extraction settings, upstream revision, model/prompt identity, attempt, counters, costs, and complete/partial/failed outcome.
- Persist graph/provenance/effective configuration separately from the parse bundle. Record upstream chunk/item-to-Nebula evidence mappings; preserve unresolved and coarse grounding.
- Prove targeted-block extraction retains original references and does not silently expand to the full document. Reject unsupported scope configurations explicitly.
- Keep authorization, job idempotency, cancellation, and acceptance in Nebula. No extraction graph export may publish canonical facts or write AGE directly.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md), [ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md), [ADR-0068](../../architecture/decisions/ADR-0068-decision-basis-fingerprints.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Record time mentions with their model interpretation, the code-computed interval, and the resolution grade, plus the document time context used by the run. Unanchored mentions date nothing and are re-resolved when an anchor arrives (ADR-0064).
- Persist interpretation drops by reason. A run with `BLOCK_UNINTERPRETED` or `TRUNCATED_OUTPUT` is `PARTIAL`; affected fields answer `NOT_PROCESSED` (ADR-0065).
- Store a `basis_hash` over everything the run considered (ADR-0068).
- **v0.1 scope guard (validate finding P-2):** this feature's Phase A admits only the storage fields, contract checks, and review/display hooks listed here. Alignment, automated deciders, fingerprint-driven scheduling, and time-mention resolution that replaces template fields stay in v0.2+ unless the operator amends the scope (BLUEPRINT §4.11).
- **Schema versioning (validate finding A-5):** time mentions, document time context, interpretation drops, run outcome counts, and `basis_hash` need a versioned addition to `schemas/interpretation-result.schema.json` (and to the run metadata contract) with compatible readers.

## Graph Observatory carry-in (2026-10-13)

[ADR-0072](../../architecture/decisions/ADR-0072-observatory-is-a-read-only-projection.md) (Proposed) governs this planned work. Carry these requirements into the PRD; the feature status is unchanged. Design: [design note section 10](../../architecture/graph-observatory-design.md#10-delivery-approach-carry-the-contract-in-now-land-the-observatory-in-v02b). The scoped Observatory is [F0067](../F0067-graph-observatory/README.md).

- Keep each run's outcome records queryable by run, with a terminal status, including outcomes that change nothing: reused content, drops, and `NONE` or `UNDECIDED` alignments. Learning traces are projected from these records (ADR-0072 section 2); this feature emits no Observatory-specific events.
- **No new v0.1 scope.** This is a property of records the feature already keeps (run outcome counts, drops, `basis_hash`).

## Document-date candidate producer (2026-10-23)

Operator decision at the F0005 plan G1 (run `2026-10-23-9a04b327`), closing the BLUEPRINT §4.8 open decision: F0016 owns producing CONTENT and SOURCE_METADATA document-date candidates through the F0004 append-only date service. F0005 produces none. Carry this into the PRD and stories when the feature is planned; selection stays a verified human decision (F0022).
