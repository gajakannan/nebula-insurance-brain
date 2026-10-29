## Story Header

**Story ID:** F0005-S0003

**Feature:** F0005 — One-time document ingestion

**Title:** Reinterpret saved JSON and map evidence

**Priority:** High

**Phase:** MVP — v0.1A

**Status:** In Progress

## User Story

**As a** document intelligence engineer

**I want** live interpretations over saved native content with evidence grounded in actual source regions

**So that** a profile change enriches knowledge without reparsing or inventing locations.

## Context & Background

Implements the [PRD](PRD.md) under proposed [ADR-0060](../../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) and accepted ADR-0058. Delivered 2026-09-22: evidence mapper v2, multi-region grounding and recorded-response dense extraction. This plan proves the same behavior with live model output on the qualification corpus.

## Acceptance Criteria

- [ ] **F0005-S0003-AC1:** Given each published corpus bundle after a worker restart, when `gl-limits-a` and `gl-limits-b` run through the live dense contract, then saved DoclingDocument JSON is the only input, converter/OCR entry points are instrumented and called zero times, bundle hashes are unchanged, and each run records distinct template, schema, chunking, model and tokenizer identities.
- [ ] **F0005-S0003-AC2:** Given live output for limits, dates and the named insured, when evidence is resolved, then every resolved selector's source text supports its value (Unicode offsets and table cells checked against the bundle), repeated or ambiguous values stay unresolved, and multi-region values need complete character coverage.
- [ ] **F0005-S0003-AC3:** Given Graph chunks, nodes and properties, when the adapter builds InterpretationResult, then the provenance ledger and native item references are retained as run outputs; graph IDs and local merges never become enterprise identity or canonical facts.
- [ ] **F0005-S0003-AC4:** Given output containing relationships or entity types without a downstream mapping, when it is imported, then the import fails closed with an explicit unsupported-output reason and no partial assertions.
- [ ] **F0005-S0003-AC5:** Given any model call (skeleton, fill, repair or reconciliation), when it is scheduled, then input + schema + output reservations measured with the serving tokenizer fit the 4,096-token context; an oversized request fails before sending.
- [ ] **F0005-S0003-AC6:** Given a selected-block or targeted request, when interpretation begins, then it fails explicitly as unsupported rather than broadening to the full document; F0032 owns targeted evolution.
- [ ] **F0005-S0003-AC7:** Given a job, artifact or run state change, when the operation succeeds or fails, then an audit event records actor and job identity, correlation and attempt IDs, artifact/run references, outcome and timestamp, without secrets or source text.

**Edge Cases & Error Scenarios:** Value printed differently from the expectation (e.g. `$1M`) → reported as an accuracy miss, not normalized into a match. Model returns a value absent from the document → unresolved evidence and an accuracy miss, never a fabricated span. A chunk boundary splitting a value → multi-region resolution or unresolved, never truncation.

## Interaction Contract

No UI. Entry points: worker interpretation stage and the importer; review items appear in the existing Review Panel unchanged.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Interpretation over a published bundle → importer | Run a profile against an artifact | New run only; bundle and prior runs immutable | Run outputs plus assertions, evidence and review items in one transaction, or explicit failure | Reload run, assertions and evidence selectors; recheck selectors against bundle text | ServicePrincipal `interpret` grant; canonical acceptance excluded |

**Validation and audit:** unresolved evidence enters provenance review per ADR-0058; nothing is committed canonically.

## Data Requirements

Run identity and configuration hashes, chunk inventory, provenance ledger, per-call token reservations and usage, evidence precision per value.

## Role-Based Visibility

Run outputs require current `interpret` authorization in the source's tenant/KB, rechecked after restart. Model context contains chunk text only.

## Non-Functional Expectations

- Every call's reservation is checked before sending; budgets cover repairs.
- Per-document-profile latency is reported for S0004's threshold.

## Dependencies

S0001/S0002; fixed proof profiles; ADR-0040/ADR-0058; F0015/F0016 for production profiles and run lifecycle.

## Out of Scope

Relationship semantics, new profiles, targeted evolution, canonical commits.

## Questions & Assumptions

Two fixed profiles remain sufficient for qualification; F0015 compiles production templates against the qualified adapter.

## Definition of Done

- [ ] Every acceptance criterion has observed live-model evidence.
- [ ] Applicable runtime tests, authorization checks and contract validation pass.
- [ ] STATUS, compatibility evidence and trackers describe the actual implementation.
- [ ] Required reviewer verdicts are recorded in STATUS; planning checks are not runtime proof.

## Review Provenance

Implementation signoff belongs in [STATUS.md](STATUS.md). This planning update is not runtime completion or reviewer approval.
