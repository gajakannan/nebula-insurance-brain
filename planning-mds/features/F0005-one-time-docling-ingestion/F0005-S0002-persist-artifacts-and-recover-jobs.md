## Story Header

**Story ID:** F0005-S0002
**Feature:** F0005 — One-time document ingestion
**Title:** Persist artifacts and recover jobs
**Priority:** High
**Phase:** v0.1A
**Status:** In Progress

## User Story

**As a** platform engineer
**I want** a durable artifact checkpoint and idempotent document jobs
**So that** retries preserve source evidence without repeating published conversion work.

## Context & Background

Implements the [PRD](PRD.md) and [assembly plan](feature-assembly-plan.md) under proposed [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). F0001 measured Docling plus a direct full-document vLLM request; it did not prove the Graph pipeline.

## Acceptance Criteria

Edge cases covered below include incomplete publication, expired leases, duplicate/competing jobs, cancelled attempts, and denied cross-tenant reads.

- **Given** a native parse result, **when** the ingestion callback publishes it, **then** retain the original source and six-file bundle through ContentArtifactStore, with hashes and parse quality; publish the completion marker last and verify it before extraction resumes.
- **Given** a published bundle followed by model failure or worker termination, **when** a new worker retries the job, **then** load the existing native JSON, preserve its hash and identity, and perform zero converter/OCR calls; exercise both timeouts and invalid model output.
- **Given** a crash before bundle completion or a partially converted source, **when** recovery runs, **then** distinguish incomplete publication from a complete bundle with partial parse quality; clean or resume incomplete writes under the store contract and never expose them as accepted artifacts.
- **Given** duplicate notifications, expired leases, competing workers, or cancellation, **when** jobs execute or retry, **then** respect configured worker/model concurrency limits and internal fan-out, fence stale attempts, and create at most one accepted artifact per scoped version/recipe with no duplicate accepted effects.
- **Given** a different tenant or a revoked grant, **when** a job or reader accesses source, bundle, or provenance, **then** deny access; apply the same retention/deletion policy to source-bearing run outputs, temporary exports, and their store references.

- **Given** a job, artifact, run, or activation state changes, **when** the operation succeeds or fails, **then** append an audit event with actor/job identity, correlation and attempt IDs, relevant artifact/run references, outcome, and timestamp; omit secrets and source text.

## Data Requirements

Source/version and tenant/KB identity; native document/schema and file hashes; parser/conversion recipe separate from pipeline/template/model/run metadata; parse quality; declared evidence precision; attempts and outcomes. Preserve accepted six-file bundles and strict schema versioning.

## Role-Based Visibility

Only authorized principals/jobs can read source or run outputs. Model calls receive authorized content, never user credentials or authorization authority. Review and canonical acceptance remain engine responsibilities.

## Non-Functional Expectations

Enforce explicit concurrency/context budgets and durable job recovery. Keep source text and secrets out of routine logs; retain evidence outputs under tenant access and retention controls. Report costs and failures without claiming unmeasured quality.

## Dependencies

S0001 conversion/checkpoint seam; F0004 storage contract; F0002/F0003 scope and persistence contracts for production wiring; ADR-0059.

## Out of Scope

Full profile workbench, enterprise entity resolution, canonical commits, AGE projection, and Temporal business workflows retain their owning features. This story cannot bypass those services.

## Questions & Assumptions

Use PostgreSQL durable jobs/outbox in v0.1. Failure before publication can require a conversion retry; failure after publication cannot. Temporal is not a prerequisite.

## Definition of Done

- [ ] Acceptance and failure cases have observed evidence against the pinned package.
- [ ] Applicable runtime tests, authorization checks, and contract validation pass.
- [ ] STATUS, metadata, documentation, and trackers describe the actual implementation.
- [ ] Required reviewer verdicts are recorded; planning checks are not runtime proof.

## Review Provenance

Pending in [STATUS.md](STATUS.md). No implementation or lifecycle approval is claimed.
