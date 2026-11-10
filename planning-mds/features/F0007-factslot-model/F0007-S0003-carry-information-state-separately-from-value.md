# Carry information state separately from value

**Story ID:** F0007-S0003
**Feature:** F0007 — FactSlot model
**Title:** Carry information state separately from value
**Priority:** Critical
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Rosa the Business Reviewer
**I want** each FactSlot answer to state whether the information is present, not processed, not found in a named scope, not stated, illegible, ambiguous, conflicting, explicitly negative or not applicable
**So that** "not found on pages 1–3" is never read as "the policy has no aggregate limit".

## Context & Background

ADR-0039 decisions 1–3 and master blueprint §107.4. F0007 is the carrier. F0008 versions it bitemporally, F0016 records the scope its runs searched, and F0020/F0023 return and display it. EX-OWN-003 is the worked example.

## Acceptance Criteria

- [ ] **AC1:** The answer carrier accepts exactly `PRESENT` and the eight ADR-0039 states (`NOT_PROCESSED`, `NOT_FOUND`, `NOT_STATED`, `ILLEGIBLE`, `AMBIGUOUS`, `CONFLICTING`, `EXPLICIT_NEGATIVE`, `NOT_APPLICABLE`). Any other state is rejected with `INFORMATION_STATE_INVALID`. No access-denied or restricted state exists.
- [ ] **AC2:** Only `PRESENT` carries a value. A value on any other state, or `PRESENT` with no value, is rejected with `STATE_VALUE_MISMATCH` and no fact version is written.
- [ ] **AC3:** `NOT_FOUND` and `NOT_STATED` require a scope naming the content artifact version, the profile release reference and the pages or blocks covered. A missing or empty scope is rejected with `ABSENCE_SCOPE_REQUIRED`. A scope reference outside the slot's tenant/KB is rejected.
- [ ] **AC4:** Reading a slot, or a resolvable slot key, that has no recorded answer returns `NOT_PROCESSED`. It never returns null or an empty body.
- [ ] **AC5:** EX-OWN-003: `NOT_PROCESSED`, `NOT_FOUND` (pages 1–3) and `NOT_STATED` (reviewed scope), each committed through the existing pilot commit path, reload as three distinguishable answers with their scopes intact. F0008 owns how a later answer supersedes an earlier one.
- [ ] **AC6:** A principal without read authority over a scope's content receives an authorization denial before any missingness explanation. No state answer exposes block IDs, page numbers or excerpts from a scope the principal is not authorized to read (threat T-08).
- [ ] **AC7:** Each accepted state answer is recorded under the existing commit audit. A rejected carrier produces no fact version, and the rejection reason is returned to the caller.

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Existing canonical commit boundary (pilot) and slot read | Submit a state answer; read a slot | New answers only; prior answers untouched | Fact version with state, value or scope; audit via commit | `GET /facts/{factSlotId}` reload returns the state and scope; an unread slot reads `NOT_PROCESSED` | Existing commit and read authority; denial before explanation |

No new screen or route. Reviewer display is F0022/F0023.

## Data Requirements

State enum, optional typed value (S0004), and absence scope (content artifact version ID, profile release reference, page/block list) bound to the slot's tenant/KB.

## Role-Based Visibility

Scope details are visible only to principals authorized for that content. Access denial is decided by authorization and never encoded as an information state.

## Non-Functional Expectations

Validation is deterministic and runs at the boundary before any write. An invalid carrier causes zero partial writes.

## Dependencies

S0001 slot identity, S0004 typed values, the F0001 pilot commit path and F0004 content artifact identities. F0008, F0016, F0020 and F0023 consume the carrier.

## Out of Scope

Producing `NOT_FOUND` scopes from runs (F0016), bitemporal supersession of states (F0008), package completeness (F0014), and user-facing display (F0020/F0023).

## Questions & Assumptions

Assumption: an unread slot answers `NOT_PROCESSED` at read time, with no stored row per possible slot. The Architect decides where the carrier is persisted on the F0008-owned version row without breaking pilot reads.

## Definition of Done

- [ ] Seven ACs pass with positive and negative carrier fixtures and the EX-OWN-003 sequence.
- [ ] Feature action records tests, coverage and required signoffs.
