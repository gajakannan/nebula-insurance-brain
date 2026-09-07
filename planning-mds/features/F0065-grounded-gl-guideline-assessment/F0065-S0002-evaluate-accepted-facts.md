## Story Header

**Story ID:** F0065-S0002
**Feature:** F0065 — Grounded GL guideline assessment
**Title:** Evaluate accepted facts
**Priority:** High
**Phase:** v0.1B
**Status:** Not Started

## User Story

**As a** GL underwriter inspecting a coverage limit
**I want** a scoped comparison with explicit incomplete and conflict outcomes
**So that** I can distinguish a supported result from an unanswered question.

## Context & Background

The v0.1 workflow combines model interpretation with governed facts and a bounded rule. This story implements part of the [PRD](PRD.md) under the proposed [assessment contract](assessment-contract.md). The [worked example](../../examples/neurosymbolic-gl/README.md) supplies a fictional guideline and independently authored expected outcomes; no runtime execution is claimed by those examples.

## Acceptance Criteria

- **Given** accepted USD each-occurrence limits of 500000.00, 1000000.00, and 2000000.00 with matching scope and a 1000000.00 minimum, **when** evaluated independently, **then** the outcomes are BELOW_GUIDELINE, MEETS_GUIDELINE, and MEETS_GUIDELINE using exact decimals and zero model calls during comparison.
- **Given** an unknown amount, missing accepted input, failed-page evidence gap, or retracted value with no replacement, **when** evaluated, **then** the result is UNKNOWN without substituting zero or a model guess.
- **Given** an unresolved relevant source conflict, **when** evaluated, **then** the result is CONFLICT and the service does not choose the higher-confidence assertion.
- **Given** an aggregate limit, different currency, or known out-of-scope coverage, **when** evaluated, **then** the result is NOT_APPLICABLE with a permitted reason; unknown applicability remains UNKNOWN.
- **Given** a high-confidence unaccepted assertion, **when** a comparison is requested, **then** it is not used as a canonical input. A missing rule or unsupported operation is a typed error, not an assessment outcome.
- **Given** a principal without permission to the subject or complete relevant lineage, **when** assessment is requested, **then** access is denied before any outcome or revealing reason is returned.

## Data Requirements

Subject and typed qualifiers, selected rule release, valid/known coordinates, accepted fact versions, authorized gap/conflict references; outcome and typed comparison only when evaluated.

## Role-Based Visibility

Use verified principals and current tenant/knowledge-base/resource permissions. Underwriters/reviewers may inspect only authorized assessments and complete relevant evidence lineage. Rule installation requires separately authorized administrative authority; a model assertion or ordinary read permission never grants it. Documentation examples contain synthetic data only.

## Non-Functional Expectations

Exact decimal values, versioned inputs, and a consistent snapshot are required. Keep source text out of operational logs. Record audit events through existing kernel contracts. Measure latency and cost at F0026 without inventing performance thresholds in this story. Runtime assessment uses no neural call for the deterministic comparison; extraction is evaluated separately.

## Dependencies

S0001; F0006–F0013 facts/provenance/completeness and F0018/F0020 canonical snapshot reads.

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
