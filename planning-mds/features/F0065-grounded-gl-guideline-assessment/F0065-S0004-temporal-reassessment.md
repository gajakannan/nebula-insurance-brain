## Story Header

**Story ID:** F0065-S0004
**Feature:** F0065 — Grounded GL guideline assessment
**Title:** Temporal reassessment
**Priority:** High
**Phase:** v0.1B
**Status:** Not Started

## User Story

**As a** GL underwriter reviewing a late endorsement
**I want** assessments at explicit effective and known times
**So that** I can distinguish the current interpretation of a period from what was known earlier.

## Context & Background

The v0.1 workflow combines model interpretation with governed facts and a bounded rule. This story implements part of the [PRD](PRD.md) under the proposed [assessment contract](assessment-contract.md). The [worked example](../../examples/neurosymbolic-gl/README.md) supplies a fictional guideline and independently authored expected outcomes; no runtime execution is claimed by those examples.

## Acceptance Criteria

- **Given** the EX-GL-001 500000.00 limit and a 2000000.00 endorsement effective July 1 but accepted July 10, **when** July 5 is assessed as known July 8 and July 11, **then** outcomes are BELOW_GUIDELINE and MEETS_GUIDELINE, respectively, with the corresponding fact versions.
- **Given** a request for June 30 as known July 11, **when** evaluated, **then** the original limit still applies; the endorsement does not alter an earlier valid interval.
- **Given** a correction, retraction, or changed rule release, **when** a new current assessment is requested, **then** the newly resolved snapshot and selected applicable rule are evaluated and recorded in the audit timeline; earlier assessment records remain unchanged and labeled historical.
- **Given** a concurrent commit during evaluation, **when** the result is saved, **then** every input belongs to the same resolved snapshot; no mixed old/new fact set or unqualified current label is returned.
- **Given** a historical result and revoked current access, **when** history is requested, **then** access is denied; historical grants are not restored. A future rule release is rejected for an earlier known-time request.

## Data Requirements

Explicit valid/known coordinates, snapshot, endorsement/correction change links, exact fact/rule versions, immutable prior assessments.

## Role-Based Visibility

Use verified principals and current tenant/knowledge-base/resource permissions. Underwriters/reviewers may inspect only authorized assessments and complete relevant evidence lineage. Rule installation requires separately authorized administrative authority; a model assertion or ordinary read permission never grants it. Documentation examples contain synthetic data only.

## Non-Functional Expectations

Exact decimal values, versioned inputs, and a consistent snapshot are required. Keep source text out of operational logs. Record audit events through existing kernel contracts. Measure latency and cost at F0026 without inventing performance thresholds in this story. Runtime assessment uses no neural call for the deterministic comparison; extraction is evaluated separately.

## Dependencies

S0003; F0008/F0010/F0019/F0020 bitemporal and change semantics. F0025 consumes this story as integration acceptance.

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
