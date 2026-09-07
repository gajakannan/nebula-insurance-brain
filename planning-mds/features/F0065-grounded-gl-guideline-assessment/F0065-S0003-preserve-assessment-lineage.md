## Story Header

**Story ID:** F0065-S0003
**Feature:** F0065 — Grounded GL guideline assessment
**Title:** Preserve assessment lineage
**Priority:** High
**Phase:** v0.1B
**Status:** Not Started

## User Story

**As a** reviewer auditing a guideline assessment
**I want** a stable record of the exact comparison and its evidence
**So that** I can inspect why that result was produced.

## Context & Background

The v0.1 workflow combines model interpretation with governed facts and a bounded rule. This story implements part of the [PRD](PRD.md) under the proposed [assessment contract](assessment-contract.md). The [worked example](../../examples/neurosymbolic-gl/README.md) supplies a fictional guideline and independently authored expected outcomes; no runtime execution is claimed by those examples.

## Acceptance Criteria

- **Given** an evaluated result, **when** it is saved, **then** an immutable assessment records exact input fact versions, rule/source/ontology/evaluator versions, semantic snapshot, valid/known time, typed comparison, acting principal, derivation references, and an audit reference.
- **Given** an UNKNOWN or CONFLICT result, **when** saved, **then** its authorized gap/conflict references and snapshot are retained without fabricated input facts or comparison values.
- **Given** an assessment, **when** provenance is followed, **then** its fact points to supporting assertions, interpretation runs, and immutable evidence; extraction confidence remains on the assertion and is not relabeled as assessment confidence.
- **Given** a save failure or a repeated idempotency key, **when** the request is retried with the same snapshot/content, **then** there is at most one saved assessment and audit effect; a key reused for different content is rejected.
- **Given** revoked evidence permission, **when** an existing assessment is read, **then** its outcome and explanation are denied under current grants. Saving an assessment does not update policy approval state or canonical facts.

## Data Requirements

Assessment record fields in assessment-contract.md; links to fact versions and evidence, not duplicated mutable canonical payloads.

## Role-Based Visibility

Use verified principals and current tenant/knowledge-base/resource permissions. Underwriters/reviewers may inspect only authorized assessments and complete relevant evidence lineage. Rule installation requires separately authorized administrative authority; a model assertion or ordinary read permission never grants it. Documentation examples contain synthetic data only.

## Non-Functional Expectations

Exact decimal values, versioned inputs, and a consistent snapshot are required. Keep source text out of operational logs. Record audit events through existing kernel contracts. Measure latency and cost at F0026 without inventing performance thresholds in this story. Runtime assessment uses no neural call for the deterministic comparison; extraction is evaluated separately.

## Dependencies

S0002; F0003/F0009/F0018 audited persistence and lineage; ADR-0026.

## Out of Scope

General rule chaining, OWL/Datalog, vector retrieval, autonomous rule promotion, business approval, and automatic propagation of persisted derived canonical facts remain later features. This story does not bypass the canonical commit or authorization service.

## Questions & Assumptions

The example threshold is fictional. The [assembly plan](feature-assembly-plan.md) assigns production guideline authority and runtime contract binding before implementation, and evaluation thresholds before release. ADR-0056 remains Proposed until proof evidence is recorded.

## Definition of Done

- [ ] Acceptance and boundary cases pass with observed evidence.
- [ ] Permissions, audit, provenance, and temporal behavior meet the contract where applicable.
- [ ] Worked examples and owning concept links reflect the delivered behavior.
- [ ] Relevant runtime or planning checks pass; fixture validation is not claimed as runtime proof.
- [ ] Story status, blueprint links, KG mapping, and generated story index are synchronized.
- [ ] Required reviewers record actual verdicts and evidence in STATUS.md.

## Review Provenance

Pending in [STATUS.md](STATUS.md); no implementation or lifecycle approval is claimed.
