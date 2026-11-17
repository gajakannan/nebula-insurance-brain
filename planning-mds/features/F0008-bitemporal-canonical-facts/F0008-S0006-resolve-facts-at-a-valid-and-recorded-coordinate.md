# Resolve facts at a valid and recorded coordinate

**Story ID:** F0008-S0006
**Feature:** F0008 — Bitemporal canonical facts
**Title:** Resolve facts at a valid and recorded coordinate
**Priority:** Critical
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Priya the GL Underwriter
**I want** to ask what a fact was at a valid time, as the Brain knew it at a recorded time, and get exactly one answer
**So that** "the limit as of July 1" and "what the Brain knew on June 5" are both answerable, and an answer is never silently replaced by today's knowledge.

## Context & Background

Master blueprint §14 and §87, and the F0001-S0005 pilot read `GET /facts/{factSlotId}?validAsOf&knownAsOf`. F0020 owns the full temporal and graph query API. F0008 owns the resolution rule and keeps the existing route, adding the S0001/S0002 fields. ADR-0053: historical reads are authorized against current grants.

## Acceptance Criteria

- [ ] **AC1:** §87 grid: after the S0003 AC1 commits, reads return $2,000,000 at (valid 2026-05-15, known now), $5,000,000 at (valid 2026-07-01, known now), $2,000,000 at (valid 2026-06-05, known 2026-06-05) and $5,000,000 at (valid 2026-06-05, known 2026-06-15).
- [ ] **AC2:** Any (valid, known) coordinate resolves to at most one version. For identity-v1 slots, the internal reader returns `NOT_PROCESSED` for a coordinate with no recorded version, never null or an empty body, unless S0002 AC4 or AC3 below applies. The existing GET keeps its pilot 404 for that case, and HTTP exposure of information states remains with F0020. *(Clarified at Phase B 2026-11-16 with operator approval.)*
- [ ] **AC3:** A coordinate inside an unknown-end window (S0002 AC2), or before an attestation-floor start with no earlier covering version (S0002 AC4), returns a validity-unknown result with no value. It never returns the predecessor's value and never `NOT_PROCESSED`. The internal reader and, for identity-v1 slots, the existing GET (as an additive 200 variant) both return it.
- [ ] **AC4:** Range boundaries are half-open. A read exactly at a version's valid start returns that version, and a read exactly at its valid end returns its successor or the next applicable result.
- [ ] **AC5:** The read returns the version id, the value or answer envelope, the valid bounds with granularity and zone, `valid_to_state`, attestation bounds, start basis, the recorded interval and the four timestamps. Pilot response fields keep their names and meaning.
- [ ] **AC6:** Omitting `validAsOf` or `knownAsOf` keeps the pilot default behaviour. A malformed coordinate is refused with a validation error and writes nothing.
- [ ] **AC7:** A principal whose read grant on the slot's knowledge base has been revoked is denied at every historical coordinate, including coordinates before the revocation. The denial does not reveal whether a version exists.

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Existing `GET /facts/{factSlotId}?validAsOf&knownAsOf` and the internal reader | Read a slot at a coordinate | Read-only | No mutation | Repeated reads at the same coordinate return identical results after later commits | Existing read authority under current grants; denial before existence |

Read-only; no mutation path. F0020 adds list, range and graph queries.

## Data Requirements

Read result shape as listed in AC5. Validity-unknown is a read result, not an ADR-0039 information state.

## Role-Based Visibility

Read authorization under the current grant decides visibility at every coordinate (ADR-0053). Attestation dates follow S0002's visibility rule.

## Non-Functional Expectations

Deterministic. A historical coordinate's answer never changes after later commits (immutability, S0003).

## Dependencies

S0001–S0003; F0002 authorization; F0007 `NOT_PROCESSED` read default.

## Out of Scope

Range queries, lists, graph traversal and performance budgets (F0020, §114.2), and user display (F0023).

## Questions & Assumptions

Phase B specifies the additive response contract and the representation of validity-unknown on the existing route.

## Definition of Done

- [ ] Seven ACs pass on PostgreSQL, including the coordinate grid and the revocation case.
- [ ] The feature action records tests, coverage and the required signoffs.
