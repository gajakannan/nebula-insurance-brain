## Story Header

**Story ID:** F0005-S0004

**Feature:** F0005 — One-time document ingestion

**Title:** Evaluate and activate the proven pipeline

**Priority:** High

**Phase:** MVP — v0.1A

**Status:** In Progress

## User Story

**As a** platform owner

**I want** a measured direct-versus-Graph comparison against agreed thresholds, followed by activation or rejection

**So that** Graph replaces the direct client only on evidence, and either outcome is recorded and reversible.

## Context & Background

Implements the [PRD](PRD.md) under proposed [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). Delivered 2026-09-22: a recorded-response [synthetic comparison](synthetic-comparison.json), which is orchestration proof, not model quality. This plan adds the live corpus comparison, reviewer verdicts and the activation decision.

## Acceptance Criteria

- [ ] **F0005-S0004-AC1:** Given the qualification corpus (at least 12 synthetic documents: 6 native, 4 scanned, 2 mixed-page), when it is committed, then every expected value and evidence location was authored from the document source by a role that does not run or review the extraction, and the corpus and expectation hashes are recorded before the first measured run.
- [ ] **F0005-S0004-AC2:** Given the direct baseline and Graph dense under recorded configurations (pins, model and tokenizer revision, chunking, budgets), when both profiles run over the full corpus, then the report records per-case and aggregate schema validity, field accuracy, abstention, fabricated evidence, evidence resolution, calls, serving-tokenizer tokens, p95 latency and review items per document.
- [ ] **F0005-S0004-AC3:** Given the report, when it is compared with the PRD thresholds, then each threshold is marked met or missed with its measured value; a missed threshold blocks activation and is never re-run with relaxed budgets to pass.
- [ ] **F0005-S0004-AC4:** Given S0001–S0003 and S0005 evidence plus the report, when QA, Architect and Security review them, then each records a verdict with evidence references in STATUS, and the operator records acceptance or rejection.
- [ ] **F0005-S0004-AC5:** Given all thresholds met, every verdict passing and operator acceptance, when activation runs, then ADR-0060 becomes Accepted, the worker default extraction contract becomes Graph dense through committed non-secret configuration, the v2 writer is enabled per S0005, and the dependency matrix, build/run metadata and C4 runtime description are updated together.
- [ ] **F0005-S0004-AC6:** Given an activated configuration, when the rollback setting selects the direct baseline, then new runs use the direct client with its own identity, existing artifacts and runs stay readable and unchanged, and no run mixes engines.
- [ ] **F0005-S0004-AC7:** Given any threshold miss, failing verdict or operator rejection, when the feature closes, then the direct client stays default, the v2 writer stays disabled, ADR-0060 records the failed gates (Proposed or Rejected per operator), and no partial activation remains.
- [ ] **F0005-S0004-AC8:** Given a job, artifact, run or activation state change, when the operation succeeds or fails, then an audit event records actor and job identity, correlation and attempt IDs, artifact/run references, outcome and timestamp, without secrets or source text.

**Edge Cases & Error Scenarios:** Live model unavailable during measurement → the run is void and repeated in full, never partially merged. Baseline worse than Graph on every metric → still reported; the baseline remains the rollback path. Reviewer finds an expectation error → the corrected expectation is re-hashed and both engines are re-measured.

## Interaction Contract

No UI. Entry points: the comparison harness, the committed configuration file and the ADR/STATUS records.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Comparison harness → report | Run both engines over the corpus | Report immutable once recorded; a re-run creates a new report | Hashed report with per-case rows | Re-run reproduction command; compare corpus and configuration hashes | QA owns corpus; AI engineer runs; reviewers do not author expectations |
| Committed configuration | Activate or roll back | Default extraction contract and `content.v2_writer_enabled` | Next job uses the selected engine and writer | Restart worker; submit a document; inspect run and manifest identity | Activation only after AC4 acceptance |

**Validation and audit:** activation and rollback are recorded in STATUS and the feature evidence package with the operator's decision.

## Data Requirements

Corpus manifest and hashes, expectation files, run configurations, per-case results, aggregate metrics, verdicts, activation decision and configuration diff.

## Role-Based Visibility

Corpus and reports are synthetic and repository-committed; measured runs execute under the ServicePrincipal's current authorization like any job, and activation needs no new permission; reports exclude secrets and serving credentials.

## Non-Functional Expectations

Thresholds as listed in the PRD. Measurement uses one worker replica and the model semaphore at 1.

## Dependencies

S0001–S0003, S0005; agent-role QA, Architect and Security reviewers; operator acceptance; F0026 reuses the cases.

## Out of Scope

Production host activation, licensed or frozen-holdout corpora, retiring the direct client code (it stays as the rollback path).

## Questions & Assumptions

Thresholds are the operator-approved PRD defaults. Graph direct is reported for completeness but is not an activation candidate.

## Definition of Done

- [ ] Every acceptance criterion has observed evidence.
- [ ] Applicable runtime tests, authorization checks and contract validation pass.
- [ ] STATUS, ADR-0060, dependency matrix and trackers describe the actual outcome.
- [ ] Required reviewer verdicts and the operator decision are recorded; planning checks are not runtime proof.

## Review Provenance

Implementation signoff belongs in [STATUS.md](STATUS.md). This planning update is not runtime completion or reviewer approval.
