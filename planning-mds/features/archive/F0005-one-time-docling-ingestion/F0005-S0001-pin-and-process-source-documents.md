## Story Header

**Story ID:** F0005-S0001

**Feature:** F0005 — One-time document ingestion

**Title:** Pin and process source documents

**Priority:** High

**Phase:** MVP — v0.1A

**Status:** In Progress

## User Story

**As a** document intelligence engineer

**I want** the pinned Docling-Graph pipeline to convert real native, scanned and mixed-page sources and publish them before any model call

**So that** conversion is proven on the actual parser and OCR stack, not only on synthetic native content.

## Context & Background

Implements the [PRD](PRD.md) under proposed [ADR-0060](../../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). Delivered 2026-09-20: the 1.9.1 pin, wheel digest, lock, checkpoint stage and synthetic conversion tests ([compatibility evidence](compatibility-evidence.md)). This plan adds live conversion of the qualification corpus. F0004's v1/v2 publication boundary is the checkpoint target.

## Acceptance Criteria

- [ ] **F0005-S0001-AC1:** Given a clean checkout, when both workspaces sync from their locks, then the resolved Docling-Graph, Docling and docling-core versions and the Graph wheel digest equal the recorded pin, and any difference fails the qualification run before conversion.
- [ ] **F0005-S0001-AC2:** Given each native, scanned and mixed-page corpus document, when it enters the real pipeline with physical conversion and OCR enabled, then the published bundle records parser name/version/configuration, OCR engine name/version, page count, failed pages, OCR page count, warnings and source hash; mocks or recorded native JSON cannot satisfy this criterion.
- [ ] **F0005-S0001-AC3:** Given conversion completes and the model endpoint then fails or returns invalid output, when the checkpoint stage runs, then the bundle is verified and registered before the first model request, and the job records the model failure without discarding or reconverting the bundle.
- [ ] **F0005-S0001-AC4:** Given the corpus's partial-conversion document, when conversion returns, then supported content is published with its failed pages and partial status, and no later stage labels the document complete.
- [ ] **F0005-S0001-AC5:** Given the checkpoint callback fails or the installed stage layout differs from the pinned guard, when processing is attempted, then extraction does not start, the job fails with an explicit integration reason, and no artifact is registered ready.
- [ ] **F0005-S0001-AC6:** Given a job, artifact or run state change, when the operation succeeds or fails, then an audit event records actor and job identity, correlation and attempt IDs, artifact/run references, outcome and timestamp, without secrets or source text.

**Edge Cases & Error Scenarios:** Encrypted or corrupt PDF → explicit conversion failure with no bundle. OCR model assets missing offline → conversion fails before publication; no fallback to an unrecorded engine. A page that converts empty is a failed page, not silent success.

## Interaction Contract

No UI. Entry point: the worker CLI `submit` command and the worker loop under a provisioned ServicePrincipal.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Worker CLI submission → conversion → checkpoint publication | Submit a corpus PDF | New job only; published bundle immutable | Verified bundle registered ready, or explicit conversion/integration failure | Restart, reload the artifact through the authorized reader, compare hashes and identities | ServicePrincipal with current `ingest` grant in the target tenant/KB |

**Validation and audit:** a failed conversion or checkpoint never registers a ready artifact; every authorization decision and state change is audited with policy version.

## Data Requirements

Source/version, tenant/KB, native document and file hashes, parser and OCR identities, parse quality, attempts and outcomes; F0004 manifest contract version. Exact OCR model-asset identity is qualified in S0005.

## Role-Based Visibility

Only principals and jobs with current `ingest` authorization read source or bundle bytes; each decision is audited with its policy version. Model calls receive authorized content only, never credentials or authorization data.

## Non-Functional Expectations

- Conversion of each corpus document completes within 300 s on the development host, or fails explicitly at that bound.
- Source text and secrets stay out of routine logs.

## Dependencies

F0004 publication boundary and verifier; F0001 fixtures and inference runbook; ADR-0060.

## Out of Scope

New parser or OCR engines, non-PDF formats, production host deployment.

## Questions & Assumptions

The installed pin is not upgraded by this plan. If live conversion forces an upgrade, the checkpoint seam and every S0001–S0003 criterion are re-proven on the new pin.

## Definition of Done

- [ ] Every acceptance criterion has observed live evidence on the pinned package.
- [ ] Applicable runtime tests, authorization checks and contract validation pass.
- [ ] STATUS, compatibility evidence and trackers describe the actual implementation.
- [ ] Required reviewer verdicts are recorded in STATUS; planning checks are not runtime proof.

## Review Provenance

Implementation signoff belongs in [STATUS.md](STATUS.md). This planning update is not runtime completion or reviewer approval.
