# Define name FactSlots

**Story ID:** F0007-S0005
**Feature:** F0007 — FactSlot model
**Title:** Define name FactSlots
**Priority:** High
**Phase:** MVP
**Status:** In Progress

## User Story

**As a** Rosa the Business Reviewer
**I want** an entity's legal, trade, former and informal names held as evidenced name facts on fixed slots
**So that** a named-insured change by endorsement keeps the same entity and both names remain answerable.

## Context & Background

ADR-0066 (Proposed, direction authorized 2026-09-25) has F0007 define the name FactSlots, F0013 declare the name properties and their kinds, F0017 resolve on them, and F0023 list them. The v0.1 P-2 scope guard admits storage, contract checks and hooks only. G1 (2026-11-09) deferred the display-name precedence rule to F0017/F0023.

## Acceptance Criteria

- [ ] **AC1:** The F0007 system-predicate set contains `hasLegalName` (`SINGLE`), `hasTradeName` (`MULTI`), `hasFormerName` (`MULTI`) and `knownAs` (`MULTI`). Resolving any of them with another cardinality is rejected with `CARDINALITY_CONFLICT`.
- [ ] **AC2:** EX-SEM-008: "Acme Roofing Inc." and "Acme Roofing & Restoration Inc." for the same entity resolve to the same `hasLegalName` slot. No new entity or slot is created. F0008/F0019 own the valid-time split.
- [ ] **AC3:** A name value carries the verbatim text, a normalized comparison form, an optional name-kind qualifier and a reference to its admitted F0006 name claim and quote. A name with no admitted evidence reference is rejected with `NAME_EVIDENCE_REQUIRED`.
- [ ] **AC4:** A trade name admitted only in KB A for a tenant entity associated with KBs A and B cannot be resolved, read or returned by the display-name hook in KB B. A KB B-only principal is denied, and the denial is indistinguishable from not found.
- [ ] **AC5:** The display-name hook returns the current accepted name facts of the reader's KB, each with its kind and slot. It applies no precedence (an open decision owned by F0017/F0023) and creates no `entity_alias` rows. Creating a name slot or member is authorized and audited like any slot (S0001).

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Slot resolution; display-name hook (internal read) | Resolve a name slot; list an entity's names in a KB | New name members only | Name slot/member with evidence reference; audit on create | Reload shows the same slot for both legal names; the KB B listing excludes KB A names | Existing KB read/write authority |

No screen. F0023 lists names later.

## Data Requirements

Name predicate keys and cardinalities, verbatim and normalized name text, name kind, and the F0006 name-claim/quote reference, all KB-owned.

## Role-Based Visibility

Names are visible only within their owning KB, even when the entity identity is shared across KBs. Shared identity never shares vocabulary.

## Non-Functional Expectations

No similarity matching or model call in F0007. Name normalization is deterministic and reversible to the stored verbatim text.

## Dependencies

S0001/S0002 identity and cardinality, and F0006 name-claim admission. F0013 adds name kinds, F0017 adds resolution and the alias projection, and F0023 adds display.

## Out of Scope

Display-name precedence, `entity_alias` projection, shared-name review pairs, similarity proposals (F0017/F0027), name ontology kinds (F0013) and temporal splitting (F0008/F0019).

## Questions & Assumptions

Open decision (G1, deferred): the order of preference across legal, trade and informal names for display. Recorded so no implementation invents one. Roles such as "the named insured" are F0006/F0017 role references, not name values.

## Definition of Done

- [ ] Five ACs pass, including the EX-SEM-008 identity fixture and the cross-KB negative case.
- [ ] Feature action records tests, coverage and required signoffs.
