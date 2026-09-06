## Story Header

**Story ID:** F0001-S0003
**Feature:** F0001 — Repository and engineering foundation
**Title:** Proof: parse once, reinterpret twice, evidence resolves
**Priority:** High
**Phase:** Infrastructure

## User Story

**As a** Mateo the Document Intelligence Engineer
**I want** one GL policy package parsed once by Docling into a persisted content artifact and interpreted by two extraction profiles through Docling-Graph
**So that** reinterpretation is proven to reuse the artifact with zero conversion or OCR calls and every extracted value carries an evidence locator that resolves to an immutable block with declared precision

## Context & Background

Parse once is the foundational rule (master blueprint section 5, ADR-0003). Section 108 turns it into a contract: retain the native DoclingDocument JSON (108.1), make evidence precision explicit (108.2), define a provider-neutral InterpretationResult (108.3), and treat the accepted artifact as immutable while retries and replacements are recorded separately (108.4). Section 115.4 names this proof as a prerequisite for freezing F0004 and F0005. Proposed ADR-0040 is settled by the outcome.

## Acceptance Criteria

**Happy Path:**
- **Given** one GL policy package as a native PDF and as a scanned variant
- **When** each is ingested
- **Then** the content artifact bundle persists `docling-document.json`, `normalized.md`, `blocks.jsonl`, `tables.jsonl`, `layout.jsonl`, and `manifest.json`, and the manifest records parser package version, configuration hash, environment digest, extraction quality status, and a sha256 per file

- **Given** the persisted artifact
- **When** the worker restarts and extraction profile A then extraction profile B interpret the same document
- **Then** the instrumented conversion and OCR counters read 0 for the second interpretation and the artifact hash is unchanged

- **Given** an extracted EachOccurrence limit from profile A
- **When** its evidence binding is resolved
- **Then** the locator resolves to page, block id, and bounding box in the persisted artifact and declares its precision as one of span, table cell, block, page, document, or unresolved

- **Given** the Docling-Graph adapter configured for the OpenAI-compatible backend at the local vLLM endpoint serving `microsoft/Phi-4-mini-instruct`
- **When** each chunk is submitted
- **Then** the request is rejected client-side before the call if it would exceed the 4,096-token context (no truncated output is accepted as a result), and the run records prompt and completion tokens per chunk

- **Given** both interpretations
- **When** their InterpretationResult records are inspected
- **Then** each contains candidate entities, assertions, relationships, evidence bindings, quality signals, warnings, and the exact run configuration, and the external provenance ledger is stored with the run

**Alternative Flows / Edge Cases:**
- A page fails to parse → the run records status partial with the failed page numbers and creates a review item; no explicit negative assertion is produced for that page
- Docling-Graph returns invalid output or times out → the run is recorded as failed with the error, and no previously accepted artifact or fact is replaced
- The scanned variant yields page-level grounding only → the binding records precision `page`; no bounding box is fabricated
- Phi-4-mini-instruct returns schema-invalid output for a chunk → the run records the failure per chunk and stays partial; the finding is recorded for ADR-0040, and if the model cannot produce a schema-valid InterpretationResult for the fixture at all, the Architect proposes an alternative backend at Phase B rather than the proof silently widening

## Interaction Contract

N/A — proof harness driven by tests and a CLI; no user-facing mutation.

## Data Requirements

**Required Fields:**
- Content artifact bundle per section 80 plus `docling-document.json` (section 108.1) and manifest fields `artifact_contract_version`, `docling_document.schema_version`, `extraction_quality`, `execution`
- InterpretationResult: candidate entities, assertions, relationships, evidence bindings with precision, quality signals, warnings, run configuration
- Counters: conversion calls, OCR calls, model calls per run

**Optional Fields:**
- Page rotation and crop transforms when present (section 108.2)

**Validation Rules:**
- Character offsets use one declared encoding (Unicode code points) recorded in the manifest
- Evidence for amount, currency, limit basis, and effective date is stored separately when they occur in different regions

## Role-Based Visibility

**Roles that can execute:**
- Document intelligence engineer — runs the harness locally and in CI
- Service principal — the worker identity that writes artifacts under the fixture tenant and knowledge base

**Data Visibility:**
- InternalOnly content: the fixture package; stored under the tenant and knowledge-base path
- ExternalVisible content: none

## Non-Functional Expectations

- Performance: parse duration, page count, block count, and model tokens are recorded as the baseline for section 114.2; no threshold is asserted at this proof
- Security: the extraction model is `microsoft/Phi-4-mini-instruct` on the local vLLM service, the same profile the CRM validated in its ADR-035; no fixture text leaves the machine, no user token or PII is sent to the model server, the server does not persist prompts, and no fixture text enters routine telemetry
- Reliability: the harness is repeatable; a second full run against the same source version reuses the accepted artifact

## Dependencies

**Depends On:**
- F0001-S0001 — `neuron/` workspace
- F0001-S0002 — object store and PostgreSQL

**Related Stories:**
- F0001-S0004 — consumes a low-confidence assertion from this proof
- F0001-S0007 — records the outcome in ADR-0040

## Business Rules

1. Parse once: expensive physical parsing happens once per document version; reinterpretation reads the persisted artifact (ADR-0003, ADR-0016).
2. An empty extraction from a failed page cannot count as an explicit negative (section 108.3).
3. Model self-reported confidence is a signal, not a calibrated probability or an authorization to commit (section 108.3).

## Out of Scope

- Entity resolution and canonical commit of the extracted values (F0017, F0018)
- Document classification and profile selection beyond two hand-selected profiles (F0014, F0015)
- Extraction quality thresholds (F0026)

## UI/UX Notes

- N/A

## Questions & Assumptions

**Open Questions:**
- [x] Model provider — decided at the F0001 clarification gate (2026-09-06): `microsoft/Phi-4-mini-instruct` served by vLLM as an OpenAI-compatible endpoint, aligned with the CRM's validated local profile (nebula-insurance-crm ADR-035 and its WSL2 runbook); no data policy dependency for the proof
- [ ] Context adequacy — the CRM uses this model for short structured intent calls; document chunks are longer. The proof measures whether 4,096 tokens holds Docling-Graph chunks plus the extraction schema; the result goes to ADR-0040
- [ ] Docling-Graph release or commit — Architect to decide at Phase B and pin in the dependency matrix (section 117.1 item 4)
- [ ] GL policy package source — operator to supply a licensed package; if none is available before S0003 starts, the Architect selects a synthetic package and records it (section 117.1 item 5)

**Assumptions (to be validated):**
- The Docling-Graph JSON input path accepts the persisted DoclingDocument without conversion (reference R1)
- Docling-Graph's OpenAI-compatible backend can target the local vLLM endpoint with a bearer key
- Two profiles suffice to prove reuse; profile composition rules belong to F0015

## Definition of Done

- [ ] Acceptance criteria met
- [ ] Edge cases handled
- [ ] Permissions enforced (service principal scoped to the fixture tenant)
- [ ] Audit/timeline logged (interpretation runs recorded with configuration and status)
- [ ] Tests pass
- [ ] Documentation updated (harness README, ADR-0040 input for S0007)
- [ ] Story filename matches `Story ID` prefix
- [ ] Story index regenerated

## Review Provenance

Recorded in `STATUS.md` (Required Signoff Roles, Story Signoff Provenance).
