# Guard succession by start basis and state

**Story ID:** F0008-S0005
**Feature:** F0008 — Bitemporal canonical facts
**Title:** Guard succession by start basis and state
**Priority:** Critical
**Phase:** MVP
**Status:** Done

## User Story

**As a** Priya the GL Underwriter
**I want** a known limit to be replaced only by a successor whose start date was actually read or entered, and only by another value or an explicit statement of absence
**So that** a guessed date or a "not found on pages 1–3" never silently replaces the $5M each-occurrence limit I rely on.

## Context & Background

ADR-0064 §7: a successor closes a predecessor in a single-valued slot only when its start is grade `A` or `B`, never on model confidence. G1 decision 1 (2026-11-16): each version stores how its start was obtained. A template field or a human-entered date counts as grade `A`, and grade `C` cannot close. ADR-0039 and the 2026-11-08 amendment version the information state like a value: a later `NOT_STATED` or `EXPLICIT_NEGATIVE` supersedes `NOT_PROCESSED` without erasing it. G1 decision 2: a `PRESENT` value closes only to `PRESENT` or `EXPLICIT_NEGATIVE`. Routing a refused proposal to review is F0018's work.

## Acceptance Criteria

- [x] **AC1:** Every identity-v1 commit records a start basis in {`TEMPLATE_FIELD`, `HUMAN`, `MENTION_A`, `MENTION_B`, `MENTION_C`}, or the S0002 attestation-floor marker. A missing or unknown basis is rejected with `START_BASIS_INVALID`. The commit contract has no confidence input to the guard.
- [x] **AC2:** A proposal with basis `TEMPLATE_FIELD`, `HUMAN`, `MENTION_A` or `MENTION_B` whose valid time overlaps a current version closes and splits it (S0003).
- [x] **AC3:** A proposal with basis `MENTION_C`, or with an attestation-floor start, that would close or split any current version is rejected with `SUCCESSION_START_UNANCHORED`. It writes no version and no change row, and the refusal is audited. The same proposal with no overlap is accepted. An end revision, meaning the same answer, start bound, basis and `attested_from` with only the end changed (EX-PC-014 `OPEN` → `UNKNOWN`), is not a succession and is not refused by this guard (ADR-0078 D8). *(Phase B clarification, operator-approved at G5 on 2026-11-17.)*
- [x] **AC4:** EX-OWN-003 succession: a stored `NOT_PROCESSED` answer is superseded by a later `NOT_STATED`, and that by `EXPLICIT_NEGATIVE`. Each earlier state stays readable at its recorded coordinates.
- [x] **AC5:** Against a `PRESENT` predecessor ($5M), a proposal of `NOT_FOUND`, `NOT_STATED`, `ILLEGIBLE`, `AMBIGUOUS`, `CONFLICTING` or `NOT_APPLICABLE` over an overlapping valid interval is rejected with `STATE_SUPERSESSION_REFUSED`, and the $5M version is unchanged.
- [x] **AC6:** Against a `PRESENT` predecessor, a `PRESENT` successor or an `EXPLICIT_NEGATIVE` successor with an eligible start basis closes it. Any non-`PRESENT` predecessor can be closed by any answer with an eligible start basis.
- [x] **AC7:** For a MULTI slot the guards apply per member. A refused proposal for member M1 does not affect member M2.

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Existing canonical commit boundary | Commit a successor answer | New versions only | Eligible successors close the predecessor; ineligible ones are refused with `SUCCESSION_START_UNANCHORED` or `STATE_SUPERSESSION_REFUSED` and write nothing | Predecessor version unchanged after a refusal; refusal recorded in the audit | Existing commit authority; the guard runs after authorization and before any effect |

No new screen or route. A reviewer resolves refusals through later review features (F0018, F0022).

## Data Requirements

Start basis enum on each version. Information state from the F0007 envelope. Refusal reason codes: F0008 returns them as the 422 problem `code` and audits each refusal as a `failed` authorization decision; durable per-refusal reason persistence is deferred to F0018 (ADR-0078 D8 note).

## Role-Based Visibility

A refusal reveals nothing about versions the caller cannot read. Authorization runs first.

## Non-Functional Expectations

The guard is deterministic and evaluated inside the commit transaction after the slot lock.

## Dependencies

S0002 (attestation floor); S0003 (close and split); F0007 envelope and member slots; F0002 audit.

## Out of Scope

Computing time-mention grades (F0016), routing refusals to review (F0018), and removing a value through correction or retraction (F0010).

## Questions & Assumptions

Assumption A4 treats an attestation floor like grade `C` for succession. Section 54 source-authority checks join the guard in F0018.

## Definition of Done

- [x] Seven ACs pass, with a fixture for each basis, each state transition and each refusal code.
- [x] The feature action records tests, coverage and the required signoffs.
