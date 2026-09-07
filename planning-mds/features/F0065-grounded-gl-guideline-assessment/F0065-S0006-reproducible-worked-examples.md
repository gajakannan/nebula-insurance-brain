## Story Header

**Story ID:** F0065-S0006
**Feature:** F0065 — Grounded GL guideline assessment
**Title:** Reproducible worked examples
**Priority:** High
**Phase:** v0.1B
**Status:** Not Started

## User Story

**As a** new contributor reviewing the semantic architecture
**I want** one linked example through every stage and its boundary cases
**So that** I can understand the concepts and check the expected behavior.

## Context & Background

The v0.1 workflow combines model interpretation with governed facts and a bounded rule. This story implements part of the [PRD](PRD.md) under the proposed [assessment contract](assessment-contract.md). The [worked example](../../examples/neurosymbolic-gl/README.md) supplies a fictional guideline and independently authored expected outcomes; no runtime execution is claimed by those examples.

## Acceptance Criteria

- **Given** EX-GL-001, **when** the walkthrough is read, **then** stable identifiers connect the source excerpt, illustrative model assertion, review, canonical fact, rule, assessment, and late endorsement; every concept links to its definition and owning feature.
- **Given** the structured example bundle, **when** the planning validator runs, **then** schema, reference, and feature/story links pass. A dangling fact/rule/evidence ID or malformed record is rejected; this check does not claim the runtime comparison has executed.
- **Given** the challenge table, **when** reviewed, **then** it includes wrong high-confidence extraction, missing versus explicit negative, conflicts, basis/currency mismatch, temporal change, and access revocation with expected outcomes and story owners.
- **Given** implemented F0024/F0025 integration, **when** the documented reproduction command runs, **then** actual model interpretation flows through governed acceptance into the evaluator and observed results are compared with independently authored expected cases; audit and runtime evidence links are recorded.
- **Given** vector retrieval, scenarios, obligations, or learned-rule examples, **when** displayed, **then** their later release phase and conceptual-only status are explicit. All source and model outputs in this documentation are labeled synthetic/illustrative, and their fixtures are excluded from the frozen evaluation holdout.

## Data Requirements

Synthetic source text, educational example-schema and JSON records, case IDs, feature/story mapping, expected outcomes, and future actual run evidence.

## Role-Based Visibility

Use verified principals and current tenant/knowledge-base/resource permissions. Underwriters/reviewers may inspect only authorized assessments and complete relevant evidence lineage. Rule installation requires separately authorized administrative authority; a model assertion or ordinary read permission never grants it. Documentation examples contain synthetic data only.

## Non-Functional Expectations

Exact decimal values, versioned inputs, and a consistent snapshot are required. Keep source text out of operational logs. Record audit events through existing kernel contracts. Measure latency and cost at F0026 without inventing performance thresholds in this story. Runtime assessment uses no neural call for the deterministic comparison; extraction is evaluated separately.

## Dependencies

Example authoring can start now against the draft contract. Runtime reproduction depends on S0001–S0005 and F0024/F0025; F0026 owns the independent holdout.

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
