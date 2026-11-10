# Distinguish single, multi-valued and relationship slots

**Story ID:** F0007-S0002
**Feature:** F0007 — FactSlot model
**Title:** Distinguish single, multi-valued and relationship slots
**Priority:** Critical
**Phase:** MVP
**Status:** Done

## User Story

**As a** Ingrid the Persistence Engineer
**I want** each slot to declare whether it holds one answer, a set of members, or a relationship to another entity
**So that** two additional insureds coexist and removing one can close only that membership.

## Context & Background

Master blueprint §109.1: the single-valued overlap constraint (§15) must not be applied unchanged to a set of legitimate insureds or locations, and relationships need explicit identity. F0008 owns temporal versions and the close operation. F0007 defines the identity unit those versions attach to.

## Acceptance Criteria

- [ ] **AC1:** Every slot has a cardinality of `SINGLE`, `MULTI` or `RELATIONSHIP`, fixed at creation from the predicate contract. Resolving an existing identity with a different cardinality is rejected with `CARDINALITY_CONFLICT` and writes no rows.
- [ ] **AC2:** For a `SINGLE` slot, a second fact version that overlaps an existing version in both valid and recorded time is rejected by the existing ADR-0008 exclusion constraint (pilot regression).
- [ ] **AC3:** For a `MULTI` slot, each member has its own member identity derived from its normalized value or member entity identity. Two different additional insureds give two members under one slot. Asserting the same insured twice resolves to the one existing member. Overlap is enforced per member, so the second insured is not rejected.
- [ ] **AC4:** A `RELATIONSHIP` slot's identity is subject, predicate key, object entity identity and qualifiers, so two relationships that differ only in object are distinct. An object outside the slot's tenant, or not associated with the slot's KB, is rejected with `RELATIONSHIP_OBJECT_OUT_OF_SCOPE`.
- [ ] **AC5:** §109.1 identity fixture: with members A and B in one `MULTI` slot, a version change addressed to member A references no row of member B. F0008 proves the temporal close.
- [ ] **AC6:** An unknown cardinality, a `MULTI` member with no member key, or a `RELATIONSHIP` without an object is rejected with a named reason and zero rows. Creating a member writes an audit event with actor, slot and member identity, and unauthorized member creation is denied.

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Internal slot-resolution service | Resolve a slot, member or relationship | New identities only; cardinality immutable | Returns slot/member identity; audit event on create | Reload shows one member per distinct insured and per-member overlap scope | Existing KB write authority |

No screen. Member identity is storage and contract only; F0008 owns temporal behaviour.

## Data Requirements

Cardinality enum, member key and member entity reference, relationship object entity identity, and tenant/KB ownership on each member and relationship row.

## Role-Based Visibility

Members and relationship objects are visible only through the parent slot's KB authorization. An object entity outside the reader's grants is not disclosed.

## Non-Functional Expectations

Deterministic member identity with no model call. Per-member uniqueness is enforced by the database, not only by application code.

## Dependencies

S0001 slot identity, F0002 entity identity and KB associations, and the existing ADR-0008 constraint from the F0001 pilot. F0008 consumes member identity for temporal versions.

## Out of Scope

Temporal close and supersession (F0008, F0019), relationship ontology (F0012/F0013), relationship resolution from documents (F0016/F0017), and graph projection (F0034).

## Questions & Assumptions

The Architect decides whether member identity is a child row of the slot or a slot-level key, provided the ADR-0008 constraint applies per member. Predicate cardinality comes from the predicate contract (S0001) or the F0007 system-predicate set (S0005).

## Definition of Done

- [ ] Six ACs pass against PostgreSQL, including the two-insureds fixture and the cardinality conflict.
- [ ] Feature action records tests, coverage and required signoffs.
