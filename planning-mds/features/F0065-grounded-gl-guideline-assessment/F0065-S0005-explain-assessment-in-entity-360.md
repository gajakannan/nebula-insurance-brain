## Story Header

**Story ID:** F0065-S0005
**Feature:** F0065 — Grounded GL guideline assessment
**Title:** Explain assessment in Entity 360
**Priority:** High
**Phase:** v0.1B
**Status:** Not Started

## User Story

**As a** GL underwriter using Entity 360
**I want** the comparison and evidence displayed alongside the policy facts
**So that** I can review the result without reconstructing internal records.

## Context & Background

The v0.1 workflow combines model interpretation with governed facts and a bounded rule. This story implements part of the [PRD](PRD.md) under the proposed [assessment contract](assessment-contract.md). The [worked example](../../examples/neurosymbolic-gl/README.md) supplies a fictional guideline and independently authored expected outcomes; no runtime execution is claimed by those examples.

## Acceptance Criteria

- **Given** an authorized evaluated assessment, **when** the Entity 360 panel opens, **then** it displays the plain-language outcome, guideline/version, time basis, coverage basis, currency, compared values, and links to supporting Document 360 evidence.
- **Given** a historical record, **when** opened, **then** its original valid/known coordinates are visible and it is not labeled as a new current evaluation.
- **Given** UNKNOWN, CONFLICT, or NOT_APPLICABLE, **when** displayed, **then** the panel shows its authorized reason and any permitted existing review link; it does not render a successful comparison or a policy approval action.
- **Given** loading, service failure, or invalid rule request, **when** displayed, **then** these states remain distinct from business outcomes and a failed save is not shown as a persisted result.
- **Given** access revocation while the panel is open, **when** data is refreshed or an evidence/history request is made, **then** permission checks deny protected fields and clear stale displayed results through the existing session/revocation contract; result, title, counts, explanation, and citations are included in the negative tests.
- **Given** an assessment creation, **when** shown in the timeline, **then** its audit link identifies the acting principal and snapshot without displaying source text in operational logs.

## Data Requirements

Authorized assessment DTO, existing evidence/review links, display labels, explicit loading/error/outcome states and time context.

## Role-Based Visibility

Use verified principals and current tenant/knowledge-base/resource permissions. Underwriters/reviewers may inspect only authorized assessments and complete relevant evidence lineage. Rule installation requires separately authorized administrative authority; a model assertion or ordinary read permission never grants it. Documentation examples contain synthetic data only.

## Non-Functional Expectations

Exact decimal values, versioned inputs, and a consistent snapshot are required. Keep source text out of operational logs. Record audit events through existing kernel contracts. Measure latency and cost at F0026 without inventing performance thresholds in this story. Runtime assessment uses no neural call for the deterministic comparison; extraction is evaluated separately.

## Dependencies

S0003/S0004; F0021 shell/session, F0022 evidence/review, F0023 Entity 360. Backend/API behavior precedes frontend integration.

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
