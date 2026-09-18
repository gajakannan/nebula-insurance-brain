## Story Header

**Story ID:** F0005-S0001
**Feature:** F0005 — One-time document ingestion
**Title:** Pin and process source documents
**Priority:** High
**Phase:** v0.1A
**Status:** In Progress

## User Story

**As a** document intelligence engineer
**I want** a reproducible Docling-Graph pipeline candidate for native and scanned sources
**So that** I can establish compatibility before changing the running extraction path.

## Context & Background

Implements the [PRD](PRD.md) and [assembly plan](feature-assembly-plan.md) under proposed [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). F0001 measured Docling plus a direct full-document vLLM request; it did not prove the Graph pipeline.

## Acceptance Criteria

Edge cases covered below include partial conversion, unsupported checkpoint API, and model timeout or invalid extraction before final export.

- **Given** the proposed upstream candidate, **when** a clean environment resolves it, **then** record the immutable release/commit, package digest, Docling/docling-core versions, and dependency lock; explain the difference from the F0001 tested build using observed results.
- **Given** the native and scanned GL fixtures, **when** each enters the actual Graph pipeline, **then** Docling performs the initial conversion and the adapter exposes the native document, schema/version, parse status, failed pages, OCR counts, warnings, and source hash; mocks cannot satisfy this criterion.
- **Given** conversion completes before a model timeout or invalid extraction, **when** the pipeline crosses the proposed checkpoint seam, **then** the native document and quality details are available to Nebula before the model failure; document and test a supported pinned integration seam rather than relying on final exports.
- **Given** the callback fails or the selected build cannot expose the checkpoint, **when** processing is attempted, **then** stop before continuing extraction, record the integration limitation, and leave ADR-0060 Proposed.
- **Given** a partial conversion, **when** the result is returned, **then** preserve supported content and failed-page diagnostics; never label the document complete or discard its quality status.

- **Given** a job, artifact, run, or activation state changes, **when** the operation succeeds or fails, **then** append an audit event with actor/job identity, correlation and attempt IDs, relevant artifact/run references, outcome, and timestamp; omit secrets and source text.

## Data Requirements

Source/version and tenant/KB identity; native document/schema and file hashes; parser/conversion recipe separate from pipeline/template/model/run metadata; parse quality; declared evidence precision; attempts and outcomes. Preserve accepted six-file bundles and strict schema versioning.

## Role-Based Visibility

Only authorized principals/jobs can read source or run outputs. Model calls receive authorized content, never user credentials or authorization authority. Review and canonical acceptance remain engine responsibilities.

## Non-Functional Expectations

Enforce explicit concurrency/context budgets and durable job recovery. Keep source text and secrets out of routine logs; retain evidence outputs under tenant access and retention controls. Report costs and failures without claiming unmeasured quality.

## Dependencies

F0004 artifact/manifest contract; F0001 fixtures and recorded direct-client baseline; ADR-0060. This prototype uses fixed templates and does not depend on the future F0015 compiler.

## Out of Scope

Full profile workbench, enterprise entity resolution, canonical commits, AGE projection, and Temporal business workflows retain their owning features. This story cannot bypass those services.

## Questions & Assumptions

Prototype the proposed brain-extraction pipeline adapter and neutral parse-result handoff described in the assembly plan. Production activation waits for S0004.

## Definition of Done

- [ ] Acceptance and failure cases have observed evidence against the pinned package.
- [ ] Applicable runtime tests, authorization checks, and contract validation pass.
- [ ] STATUS, metadata, documentation, and trackers describe the actual implementation.
- [ ] Required reviewer verdicts are recorded; planning checks are not runtime proof.

## Review Provenance

Pending in [STATUS.md](STATUS.md). No implementation or lifecycle approval is claimed.
