# Distinguish open, bounded and unknown ends

**Story ID:** F0008-S0002
**Feature:** F0008 — Bitemporal canonical facts
**Title:** Distinguish open, bounded and unknown ends
**Priority:** Critical
**Phase:** MVP
**Status:** Done

## User Story

**As a** Rosa the Business Reviewer
**I want** a fact whose end date is unknown to be stored as unknown, with the date of the document that says it ended, and a fact whose start is unknown never to reach back to "since always"
**So that** "the prior carrier is no longer on the account" is never shown as either still current or ended on a date nobody stated.

## Context & Background

ADR-0064 §5 and EX-SEM-004. `valid_to_state` is `OPEN` (still holds), `BOUNDED` (ends at a known instant) or `UNKNOWN` (ended, date not known). `attested_from` is the earliest dated evidence document, and `attested_to` is the date of the document that says the fact ended. G1 decision 3: an unknown start with no dated evidence is refused. Assumption A4: an unknown start with dated evidence is floored at `attested_from`. F0008 settles the physical representation inside the ADR-0008 constraint in Phase B. ADR-0064 recommends closing the integrity range at `attested_to`.

## Acceptance Criteria

- [x] **AC1:** Every identity-v1 version carries `valid_to_state` ∈ {`OPEN`, `BOUNDED`, `UNKNOWN`}. `OPEN` has no end instant. `BOUNDED` has an end instant with its granularity and zone (S0001). `UNKNOWN` has no end instant and requires `attested_to`. Any other combination is refused with `END_STATE_INVALID` and writes nothing.
- [x] **AC2:** EX-SEM-004: the prior-carrier fact is attested positively by a document dated 2026-06-01 and then ended by a broker note dated 2026-08-02 (`UNKNOWN`, `attested_to` = 2026-08-02). It reads `UNKNOWN` at valid time 2026-07-15, never as the carrier and never as absence. It reads as the carrier at valid time 2026-05-15.
- [x] **AC3:** An `UNKNOWN` end still takes part in the ADR-0008 exclusion. A second version for the same slot, overlapping the integrity range up to `attested_to` at the same recorded time, is rejected by the database.
- [x] **AC4:** A commit whose start is unknown and whose evidence includes at least one dated document is stored with its start floored at `attested_from` (the earliest selected document date) and marked as an attestation floor. A read before `attested_from` returns validity-unknown with no value (EX-PC-014-B). It never returns a version reaching back to minus infinity. *(Amended at Phase B 2026-11-16 with operator approval; previously "returns no version".)*
- [x] **AC5:** A commit whose start is unknown and whose evidence has no selected document date is refused with `START_UNATTESTED` and writes nothing. Upload, receipt and acceptance times are never used as a substitute (ADR-0064 §8).
- [x] **AC6:** `attested_from` and `attested_to` come from F0004 document-date selections on the evidence, not from the caller. A caller-supplied value that disagrees with the selected dates is refused with `ATTESTATION_MISMATCH`.
- [x] **AC7:** The commit response and the fact read return `valid_to_state`, `attested_from`, `attested_to` and the start marker, so `OPEN`, `BOUNDED` and `UNKNOWN` are distinguishable without inspecting null bounds.

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Existing canonical commit boundary | Submit a version with an end state, or with an unknown start | New versions only | Version stored with its end state and attestation bounds; `END_STATE_INVALID`, `START_UNATTESTED` or `ATTESTATION_MISMATCH` write nothing | Fact read at the EX-SEM-004 coordinates returns carrier, `UNKNOWN` or nothing as specified | Existing commit and read authority; attestation documents must be readable by the committing principal |

No new screen or route.

## Data Requirements

`valid_to_state`, `attested_from`, `attested_to`, the latest positive attestation needed for the unknown-end window, and a start marker (resolved start or attestation floor). Document dates come from the F0004 append-only selection on each evidence document version.

## Role-Based Visibility

Attestation dates come from evidence documents. A principal without read authorization for an attesting document must not learn its date through the read. Phase B applies the F0007 T-08 pattern. Commits require the caller's existing canonical-commit authorization over the slot's knowledge base, evaluated in the F0002 unit of work before any validation result is returned. An unauthorized caller is denied without learning whether the slot exists.

## Non-Functional Expectations

End-state validation is deterministic and happens before any write.

## Dependencies

S0001 bounds; F0004 document-date selection; F0002 authorization; F0007 slots.

## Out of Scope

Producing document dates (F0016 candidates, F0022 human selection), grade-`C` re-resolution when an anchor arrives (F0016), and display (F0020/F0023).

## Questions & Assumptions

Assumption A4 (attestation floor) is labelled for G3 review. Phase B decides the unknown-end integrity representation and where the latest positive attestation is stored.

## Definition of Done

- [x] Seven ACs pass, with the EX-SEM-004 sequence and negative fixtures for each refusal code.
- [x] The feature action records tests, coverage and the required signoffs.
