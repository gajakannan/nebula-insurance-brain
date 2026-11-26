# F0012-S0002 — Assign stable term identities

**Story ID:** F0012-S0002
**Feature:** F0012 — Foundation ontology
**Title:** Assign stable term identities
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Not Started

## User Story

**As a** domain steward (Sameer)
**I want** each term to receive a deterministic IRI that is never reassigned, with every change in meaning recorded explicitly
**So that** a fact or rule pinned to a term today still means the same thing when it is read later.

## Context & Background

Master blueprint §112 and ADR-0045 require a stable namespace, deterministic ID-to-IRI mapping, collision handling and tenant-extension rules before vocabulary authoring. Operator decisions D4 and D5 (G1, 2026-11-25) select `urn:nebula:ont:<dotted-id>` and reserve `urn:nebula:tenant:<tenant_id>:ont:` without an install path. EX-ONT-001 is the worked case.

## Acceptance Criteria

- [ ] **AC1:** A term ID that matches the documented ID grammar maps to exactly `urn:nebula:ont:<id>`, and repeated runs on any machine produce the same IRI. An ID that violates the grammar is rejected with the offending ID.
- [ ] **AC2:** Given the identity history of all previously published releases, a candidate that gives an existing or retired IRI a different definition without a declared change record is rejected as identity reuse. An IRI is never reassigned to a different concept.
- [ ] **AC3:** Two terms whose IRIs are equal, including after Unicode NFC normalization and case folding, within one module or across modules in one release are rejected as a collision naming both terms.
- [ ] **AC4:** Changing a preferred label or adding or removing an alias keeps the IRI unchanged and is classified as rename/alias. The release records both the old and new labels with their release IDs (EX-ONT-001).
- [ ] **AC5:** A semantic change, split, merge or retirement requires an explicit change record naming the change class, the source IRIs, the replacement IRIs (none for retirement) and a rationale. The prior definition stays in its prior release. A term that disappears from a candidate without a retirement record is rejected.
- [ ] **AC6:** A shared module that declares a term in the `urn:nebula:tenant:` namespace, or any module term that redefines or overrides a shared IRI, is rejected. A request to install a tenant extension is rejected as unsupported, makes no database change, and is audited like any other install denial.

## Edge Cases & Error Scenarios

A split's replacement terms receive new IRIs; the split term keeps its old IRI and definition in its old release (AC5). A merge names two or more source IRIs and one replacement. A first release has no identity history, so AC2 passes trivially and the history begins with it.

## Interaction Contract

Entry points: the offline validation/compile command (identity checks) and the install command (tenant-extension refusal). Identity history is read from published releases; nothing is edited in place. A tenant-extension refusal returns a typed error and writes no row. Persisted proof for AC4/AC5 is the published release record queried in a fresh session.

## Data Requirements

Term ID, derived IRI, prior identity history across releases, change records (class, source IRIs, replacement IRIs, rationale, author) and label history. Physical storage of change records and the ID grammar are Phase B decisions.

## Role-Based Visibility

Offline identity checks need no runtime principal and make no authorization decision. Tenant-extension installation is rejected for every principal, whatever its authorization. See the [PRD role matrix](PRD.md#role-based-access).

## Non-Functional Expectations

Deterministic mapping and error ordering. Zero parses or model calls. At least 80% changed executable-code coverage in the later feature run.

## Dependencies

S0001 validation pass; S0004 published releases provide the identity history.

## Out of Scope

Tenant-extension installation and composition (deferred by D5); external vocabulary crosswalks (F0030/F0062); dereferenceable IRIs.

## Questions & Assumptions

No open business-rule question. Operator decisions D4 and D5 are in the [PRD](PRD.md#risks--assumptions). The ID grammar, case policy and change-record format are Phase B decisions.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] Fixtures for grammar, reuse, collision (including normalization/case), rename, each change class and tenant-namespace rejection.
- [ ] Error scenarios and refusal-without-write checks pass.
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.

## Review Provenance

Planning only. No runtime signoff is claimed. The Architect sets the required role matrix in [STATUS.md](STATUS.md) during Phase B; the feature action supplies actual evidence.
