## Story Header

**Story ID:** F0005-S0002

**Feature:** F0005 — One-time document ingestion

**Title:** Persist artifacts and recover jobs

**Priority:** High

**Phase:** MVP — v0.1A

**Status:** In Progress

## User Story

**As a** platform engineer

**I want** document jobs to recover from live provider, storage and process failures without reconverting or duplicating effects

**So that** retries preserve published evidence and never produce two accepted results.

## Context & Background

Implements the [PRD](PRD.md) under proposed [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). Delivered 2026-09-21: the PostgreSQL queue (migration 0004) and nine database recovery cases with recorded model responses. Not yet proven: live-provider failures, storage write failures, and recovery through the F0004 publication boundary.

## Acceptance Criteria

- [ ] **F0005-S0002-AC1:** Given a published bundle, when the live vLLM endpoint is stopped, times out, returns HTTP 5xx, returns malformed JSON or returns schema-invalid output, then the attempt fails with a distinct recorded reason, finite retries resume from the saved native JSON, and converter/OCR call counters stay at zero after publication.
- [ ] **F0005-S0002-AC2:** Given a worker process killed after bundle publication, after result publication, mid-import and after import commit, when a new worker claims the job, then it completes with exactly one accepted artifact, one run per profile, one assertion/evidence/review set and one acknowledged completion.
- [ ] **F0005-S0002-AC3:** Given a storage write failure or crash before the manifest completion marker, when recovery runs, then the incomplete publication is never exposed as ready, is cleaned or resumed under the F0004 store contract, and the job reconverts at most once.
- [ ] **F0005-S0002-AC4:** Given duplicate submissions, competing workers, expired leases or cancellation during model calls, when jobs execute, then stale attempts are fenced, cancellation stops further model scheduling within one in-flight call, and the configured model concurrency limit (default 1 for the host GPU) is never exceeded, including Graph-internal fan-out.
- [ ] **F0005-S0002-AC5:** Given a different tenant, a revoked grant or an inactive principal, when a job or reader accesses source, bundle, run output or temporary export, then access is denied and audited; the job does not continue under stale authority.
- [ ] **F0005-S0002-AC6:** Given run outputs, chunks, provenance ledgers and temporary exports holding source text, when a run completes, fails or is cancelled, then temporary files are removed and retained outputs sit under the owning tenant/KB scope with the same retention as the source.
- [ ] **F0005-S0002-AC7:** Given a job, artifact or run state change, when the operation succeeds or fails, then an audit event records actor and job identity, correlation and attempt IDs, artifact/run references, outcome and timestamp, without secrets or source text.

**Edge Cases & Error Scenarios:** Retry budget exhausted → job ends `failed` with the bundle retained and readable. Provider recovers mid-retry → no duplicate assertion set. Disk full during result publication → result not registered; bundle untouched.

## Interaction Contract

No UI. Entry points: worker loop, importer and the CLI `cancel` command; failures are injected by the qualification harness.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Worker/importer under injected failure | Submit, kill, cancel or resubmit a job | Job state transitions only; accepted artifacts and results immutable | One accepted outcome per scoped version, recipe and profile, or an explicit terminal failure | Database row counts, counters and audit history after restart | ServicePrincipal `ingest`/`interpret` grants; revocation takes effect at the next boundary |

**Validation and audit:** every terminal failure carries a reason code; no failure path records a successful mutation.

## Data Requirements

Job, attempt, lease generation, idempotency key, failure reason, counters (conversion, OCR, model calls), artifact and run references, retention scope.

## Role-Based Visibility

Run outputs and temporary exports require the same current authorization as the source, rechecked after every restart; operators read failure reasons, not source text, from logs.

## Non-Functional Expectations

- Recovery after a worker kill completes within one lease period plus one attempt.
- Queue depth beyond the configured bound rejects new submissions explicitly rather than growing without limit.

## Dependencies

S0001 checkpoint; F0004 store contract and v1 fallback; F0002/F0003 authorization and persistence; ADR-0059.

## Out of Scope

Multi-host deployment, distributed GPU quotas, Temporal workflows (F0050), retention-period policy changes.

## Questions & Assumptions

PostgreSQL durable jobs and outbox stay the v0.1 mechanism. Failure before publication may reconvert once; failure after publication may not.

## Definition of Done

- [ ] Every acceptance criterion has observed evidence with the live provider and real storage.
- [ ] Applicable runtime tests, authorization checks and contract validation pass.
- [ ] STATUS, compatibility evidence and trackers describe the actual implementation.
- [ ] Required reviewer verdicts are recorded in STATUS; planning checks are not runtime proof.

## Review Provenance

Implementation signoff belongs in [STATUS.md](STATUS.md). This planning update is not runtime completion or reviewer approval.
