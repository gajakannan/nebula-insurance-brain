# F0012-S0005 — Register predicates and activate temporal kinds

**Story ID:** F0012-S0005
**Feature:** F0012 — Foundation ontology
**Title:** Register predicates and activate temporal kinds
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Not Started

## User Story

**As a** document intelligence engineer (Mateo)
**I want** foundation predicates served by the existing predicate registry from the installed release, with their declared temporal kinds honored at commit
**So that** future typed assertions can use real foundation predicates with exact contracts instead of being refused as unregistered.

## Context & Background

ADR-0077 D2 defines the predicate key `<namespace>:<localName>@v<major>` and a pinned release reference that is not identity; every non-`sys` namespace is `PREDICATE_UNREGISTERED` until F0012/F0013 register predicates. ADR-0078 D10 reserves the `EVENT` and `ETERNAL` shapes and says F0012/F0013 predicate contracts activate them without DDL. Operator decision D6 (G1, 2026-11-25) activates them for registered predicates.

## Acceptance Criteria

- [ ] **AC1:** Each foundation property that implies a FactSlot yields a predicate contract with key, release reference (the installed release ID), cardinality, value type, declared qualifiers, member-key source, basis requirement and `temporal_kind`. The term-IRI-to-key mapping is deterministic and recorded in the release.
- [ ] **AC2:** The production registry serves the four `sys` predicates unchanged plus the predicates of releases installed for the slot's tenant/KB. A key absent from every installed release, or a release reference that is not installed for that tenant/KB, is refused as `PREDICATE_UNREGISTERED`; the registry never falls back to another release.
- [ ] **AC3:** A new release that keeps a predicate's major version keeps existing slot identity. A changed major version is a new predicate with new slots and requires a semantic-change record (S0002).
- [ ] **AC4:** A commit for a registered `ETERNAL` predicate is accepted only with valid time `(,)` and NULL bound columns; a commit for a registered `EVENT` predicate only as one bounded granularity period. A `STATE` commit behaves as before. A temporal shape that does not match the predicate's kind is rejected with a typed reason and writes nothing. No DDL is added.
- [ ] **AC5:** An inventory lists every legacy pilot slot type and maps each to a foundation predicate key or marks it unmapped with its future owner. No legacy row is backfilled or rewritten.
- [ ] **AC6:** Resolving a contract for an existing slot or version uses its recorded release reference, never the currently active release. Predicate resolution runs under the existing current authorization checks and audit.

## Edge Cases & Error Scenarios

A redeclared `sys` predicate with another cardinality stays `CARDINALITY_CONFLICT` (existing behavior). An `ETERNAL` commit that supplies bounds is refused. An `EVENT` span collapses to its start only where ADR-0064 normalization already applies; otherwise a multi-period span is refused.

## Interaction Contract

Entry point: the existing canonical commit and FactSlot resolution boundaries, which already consult the registry; no new route. A commit is allowed only for a registered predicate with a matching temporal shape under the existing `fact_slot:commit` grant. A refusal writes no version row. Proof of persistence is a fresh-session read of the committed version with its `temporal_kind`. Commits and refusals use the existing audit.

## Data Requirements

Predicate contracts derived from the release, tenant/KB-to-installed-release lookup, legacy slot-type inventory. The predicate namespace prefix, registry composition and cache invalidation are Phase B decisions.

## Role-Based Visibility

No new grant or authorization rule. Commits keep the existing ServicePrincipal `fact_slot:commit` grant; reads keep existing scoped read. See the [PRD role matrix](PRD.md#role-based-access).

## Non-Functional Expectations

Existing F0007/F0008 test suites pass unchanged. PostgreSQL proves `ETERNAL` and `EVENT` writes against the D10 CHECK shapes. At least 80% changed executable-code coverage in the later feature run.

## Dependencies

S0004 installed releases; F0007 registry port; F0008 temporal contract. F0013 registers GL predicates later.

## Out of Scope

GL predicates (F0013); source-authority policy by predicate (F0018); time-mention resolution replacing template fields (v0.2+ scope guard).

## Questions & Assumptions

No open business-rule question. Operator decision D6 is in the [PRD](PRD.md#risks--assumptions). Whether every foundation property implies a FactSlot, and which are relationship slots, is a Phase B decision.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] Registry tests for registered, unregistered and uninstalled-release keys; `ETERNAL`/`EVENT`/`STATE` commits and mismatches on PostgreSQL; legacy inventory review.
- [ ] Error scenarios, permission checks and persistence expectations pass.
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.

## Review Provenance

Planning only. No runtime signoff is claimed. The Architect sets the required role matrix in [STATUS.md](STATUS.md) during Phase B; the feature action supplies actual evidence.
