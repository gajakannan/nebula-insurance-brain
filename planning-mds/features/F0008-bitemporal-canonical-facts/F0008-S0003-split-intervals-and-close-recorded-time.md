# Split intervals and close recorded time

**Story ID:** F0008-S0003
**Feature:** F0008 — Bitemporal canonical facts
**Title:** Split intervals and close recorded time
**Priority:** Critical
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Ingrid the Persistence Engineer
**I want** a retroactive change to split only the valid-time intervals it affects, close the recorded visibility of what it supersedes, and never rewrite anything else in an earlier version
**So that** every earlier belief stays readable exactly as it was accepted, and no client can quietly rewrite what the Brain knew at an earlier time.

## Context & Background

Master blueprint §109.2 steps 3–7 and its explicit open question: is closing a recorded interval the only permitted update to a historical version, or should an append-only event representation derive the intervals? F0008 adopts the first rule, enforced by the database. Phase B may still choose the event representation if it proves the same ACs. The F0001-S0005 proof is the baseline. The pilot gives split remainders the new proposal's receipt timestamps; this story corrects that. Master blueprint §115.4 lists retroactive change, interval splitting and distinct received and accepted times as proof cases.

## Acceptance Criteria

- [ ] **AC1:** §115.4 retroactive change. Start from $2,000,000 valid from 2026-01-01 (`DAY`, `America/Chicago`) and accepted 2026-01-10. An endorsement effective 2026-06-01, received 2026-06-12 and accepted 2026-06-14 sets $5,000,000. The commit closes the recorded interval of the $2M version at the acceptance instant and inserts a $2M remainder valid [2026-01-01, 2026-06-01) plus the $5M version valid from 2026-06-01. All three rows exist afterwards.
- [ ] **AC2:** §115.4 correction. A later commit moves the effective date from 2026-06-01 to 2026-06-03. The affected intervals are split again. Every prior version stays readable at its original recorded coordinates, and each closed version links to its successor through a change row.
- [ ] **AC3:** A split remainder carries its predecessor's value, evidence references, review linkage and `source_received_at`, `artifact_created_at` and `assertion_created_at`, unchanged. Its own recorded interval starts at the new acceptance instant. A test fails if a remainder takes the new proposal's timestamps.
- [ ] **AC4:** Valid-time intervals that the change does not overlap are not touched: no recorded close, no new row.
- [ ] **AC5:** Any UPDATE to a version row other than setting the upper bound of a currently open recorded interval. This includes payload, valid time, attestation, basis, ownership and timestamps. is rejected by the database, whatever the client role. A recorded interval that is already closed cannot be reopened or moved. A DELETE is rejected.
- [ ] **AC6:** §115.4 distinct times. `source_received_at`, `artifact_created_at`, `assertion_created_at` and `canonical_accepted_at` are stored separately, and the recorded interval starts at `canonical_accepted_at`. For the AC1 endorsement, receipt is 2026-06-12 and recorded time starts 2026-06-14.
- [ ] **AC7:** The fact rows, change rows, review linkage, commit row, audit event and outbox event of one commit are written in one transaction. A fault injected after the fact rows and before the outbox leaves zero rows from that commit.

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Existing canonical commit boundary | Commit a retroactive change or correction | Only the open recorded upper bound of an affected version | Recorded close, remainders and the new version in one transaction; commit id and version ids returned | Reads at each (valid, known) coordinate return the expected version; direct SQL UPDATE or DELETE is refused | Existing commit authority; F0010 supplies the change-reason vocabulary |

No new screen or route.

## Data Requirements

The recorded interval, the four timestamps, change rows linking from→to for each closed version, and a reason. F0010 extends the vocabulary; F0008 keeps the existing `ChangeReason` values.

## Role-Based Visibility

No new visibility. Superseded versions are readable under the same read authorization as current ones, evaluated against current grants (S0006). Commits require the caller's existing canonical-commit authorization over the slot's knowledge base, evaluated in the F0002 unit of work before any validation result is returned. An unauthorized caller is denied without learning whether the slot exists.

## Non-Functional Expectations

All or nothing per commit. The database enforces immutability whatever the client role.

## Dependencies

S0001 and S0002 fields; the F0001 commit service; F0002 unit-of-work authorization and audit.

## Out of Scope

Change-reason meaning (F0010), correction lineage and the Golden Corpus (F0009), and endorsement-specific orchestration (F0019).

## Questions & Assumptions

Assumption A3: a commit always writes a full version, and changing only an end closes and replaces. Phase B confirms the close-only rule against the event-derived alternative and records the choice in the assembly plan.

## Definition of Done

- [ ] Seven ACs pass on PostgreSQL, including the immutability negatives and the fault injection.
- [ ] The feature action records tests, coverage and the required signoffs.
