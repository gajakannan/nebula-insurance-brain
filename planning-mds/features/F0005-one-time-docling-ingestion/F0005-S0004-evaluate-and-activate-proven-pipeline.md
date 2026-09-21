## Story Header

**Story ID:** F0005-S0004
**Feature:** F0005 — One-time document ingestion
**Title:** Evaluate and activate the proven pipeline
**Priority:** High
**Phase:** v0.1A
**Status:** Not Started

## User Story

**As a** platform owner
**I want** measured migration results and reproducible runtime wiring
**So that** we adopt Graph only after it satisfies our artifact, evidence, and operational contracts.

## Context & Background

Implements the [PRD](PRD.md) and [assembly plan](feature-assembly-plan.md) under proposed [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). F0001 measured Docling plus a direct full-document vLLM request; it did not prove the Graph pipeline.

## Acceptance Criteria

Edge cases covered below include benchmark failure, missing reviewer evidence, leaked secrets, exceeded concurrency, and rollback after activation.

- **Given** an agreed licensed corpus slice with independently authored expectations, **when** Graph and the current direct adapter run under recorded configurations, **then** compare schema validity, field accuracy, abstention, evidence precision, model calls/tokens, latency, and review workload; explicitly measure the change from one full-document request per profile to chunked extraction.
- **Given** local vLLM credentials and bounded resources, **when** all extraction paths including retries execute, **then** verify compatible settings, secret redaction, no identity credentials in model context, per-call context limits, configured aggregate concurrency, and authorized retention of source-bearing exports.
- **Given** S0001–S0003 and timeout/partial-conversion/invalid-output/retry/restart cases, **when** acceptance is reviewed, **then** record commands, exact pins, fixtures, outputs, agreed thresholds, failures, and actual reviewer verdicts in the evidence package; leave the ADR Proposed while any mandatory gate is unmet.
- **Given** all ADR-0060 proof gates pass and reviewers accept the evidence, **when** the runtime migration is enabled, **then** update owning pyproject declarations, neuron/uv.lock, build/run version metadata, composition wiring, dependency matrix, and runtime diagrams together; rename the old direct client and update imports/tests so its name identifies what it does.
- **Given** the candidate fails or later needs rollback, **when** activation is considered or reversed, **then** retain the explicitly identified F0001 baseline and existing artifacts; never silently switch engines within a run or present baseline results as Graph proof.

- **Given** a job, artifact, run, or activation state changes, **when** the operation succeeds or fails, **then** append an audit event with actor/job identity, correlation and attempt IDs, relevant artifact/run references, outcome, and timestamp; omit secrets and source text.

## Data Requirements

Source/version and tenant/KB identity; native document/schema and file hashes; parser/conversion recipe separate from pipeline/template/model/run metadata; parse quality; declared evidence precision; attempts and outcomes. Preserve accepted six-file bundles and strict schema versioning.

## Role-Based Visibility

Only authorized principals/jobs can read source or run outputs. Model calls receive authorized content, never user credentials or authorization authority. Review and canonical acceptance remain engine responsibilities.

## Non-Functional Expectations

Enforce explicit concurrency/context budgets and durable job recovery. Keep source text and secrets out of routine logs; retain evidence outputs under tenant access and retention controls. Report costs and failures without claiming unmeasured quality.

## Dependencies

S0001–S0003; named quality/architecture/security reviewers and agreed corpus/thresholds; production F0026 reuses these regression cases.

## Out of Scope

Full profile workbench, enterprise entity resolution, canonical commits, AGE projection, and Temporal business workflows retain their owning features. This story cannot bypass those services.

## Questions & Assumptions

The candidate pin, lockfiles, implementation, and contract results are recorded in [compatibility evidence](compatibility-evidence.md). Comparative live benchmarks, activation, and reviewer verdicts remain open. Record limitations before approval; do not invent quality thresholds.

## Definition of Done

- [ ] Acceptance and failure cases have observed evidence against the pinned package.
- [ ] Applicable runtime tests, authorization checks, and contract validation pass.
- [ ] STATUS, metadata, documentation, and trackers describe the actual implementation.
- [ ] Required reviewer verdicts are recorded; planning checks are not runtime proof.

## Review Provenance

Pending in [STATUS.md](STATUS.md). No implementation or lifecycle approval is claimed.
