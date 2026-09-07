## Story Header

**Story ID:** F0065-S0001
**Feature:** F0065 — Grounded GL guideline assessment
**Title:** Versioned guideline rule
**Priority:** High
**Phase:** v0.1B
**Status:** Not Started

## User Story

**As a** domain steward responsible for GL guidelines
**I want** a reviewed version of the minimum-limit guideline with explicit scope
**So that** the comparison uses a known authority and a stable business meaning.

## Context & Background

The v0.1 workflow combines model interpretation with governed facts and a bounded rule. This story implements part of the [PRD](PRD.md) under the proposed [assessment contract](assessment-contract.md). The [worked example](../../examples/neurosymbolic-gl/README.md) supplies a fictional guideline and independently authored expected outcomes; no runtime execution is claimed by those examples.

## Acceptance Criteria

- **Given** the fictional EX-GL-001 rule, **when** its reviewed asset is installed by an authorized administrator, **then** its immutable version records authority/source references, ontology release, effective interval, tenant/KB scope, coverage type, limit basis, currency, operation, and exact decimal minimum; installation is audited.
- **Given** an installed version, **when** its minimum changes, **then** a new release is created and the original remains readable under current permissions.
- **Given** a malformed amount, empty interval, unsupported operator, or free-form logic string, **when** validation runs, **then** the definition is rejected before evaluation. A claim of authority inside model output grants no installation permission.
- **Given** a selected rule released after the requested known time, **when** historical assessment is requested, **then** a rule-unavailable error is returned rather than applying hindsight.

## Data Requirements

Rule identity/version, approved source/authority references, typed scope and amount, release/effective times, ontology release, installer and audit ID.

## Role-Based Visibility

Use verified principals and current tenant/knowledge-base/resource permissions. Underwriters/reviewers may inspect only authorized assessments and complete relevant evidence lineage. Rule installation requires separately authorized administrative authority; a model assertion or ordinary read permission never grants it. Documentation examples contain synthetic data only.

## Non-Functional Expectations

Exact decimal values, versioned inputs, and a consistent snapshot are required. Keep source text out of operational logs. Record audit events through existing kernel contracts. Measure latency and cost at F0026 without inventing performance thresholds in this story. Runtime assessment uses no neural call for the deterministic comparison; extraction is evaluated separately.

## Dependencies

F0011/F0013 typed ontology contracts, F0002/F0018 principal and authorized-write contracts.

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
