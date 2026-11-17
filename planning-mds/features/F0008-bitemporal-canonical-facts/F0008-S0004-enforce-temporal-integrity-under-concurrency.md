# Enforce temporal integrity under concurrency

**Story ID:** F0008-S0004
**Feature:** F0008 — Bitemporal canonical facts
**Title:** Enforce temporal integrity under concurrency
**Priority:** Critical
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Ingrid the Persistence Engineer
**I want** any second accepted state at the same slot, valid time and recorded time, and any answer whose state and value disagree, to be rejected even when commits race or a client bypasses the service
**So that** the Brain can never hold two answers to one question.

## Context & Background

ADR-0008 and master blueprint §15: exclusion over slot × valid × recorded. §115.4 lists concurrent changes as a proof case. F0007 (ADR-0077) made MULTI members child slots, so the exclusion applies per member without changing this table, and handed F0008 the database backstop for the `fact-answer/v1` envelope. The service enforces that envelope rule today.

## Acceptance Criteria

- [ ] **AC1:** §115.4 concurrency. N ≥ 8 concurrent commits target one SINGLE slot with overlapping valid ranges. Afterwards every (valid, known) coordinate on a dense grid over the affected range resolves to at most one version. Each losing commit returns a retryable conflict (`STALE_VERSION` or `TEMPORAL_CONFLICT`) and writes zero rows, including no audit or outbox row. Each winning commit writes exactly one commit audit event and one outbox event.
- [ ] **AC2:** A direct insert that bypasses the service and overlaps an existing version on slot, valid and recorded time is rejected by the exclusion constraint.
- [ ] **AC3:** MULTI members: concurrent commits to members M1 and M2 of one MULTI slot both succeed with overlapping times. Closing M1 writes no row for M2 and does not change any M2 row (F0007 EX-SLOT-003 handoff).
- [ ] **AC4:** A RELATIONSHIP slot's versions obey the same exclusion and close behaviour as a SINGLE slot, without a separate relationship version table unless Phase B records why one is needed.
- [ ] **AC5:** For identity-v1 slots, the database rejects a version whose `fact-answer/v1` envelope has a value with a non-`PRESENT` state, or `PRESENT` without a value (F0007 S0003 AC2 backstop). A direct insert that bypasses the service is rejected. Legacy pilot versions are not subject to this check.
- [ ] **AC6:** A version, change row or commit row whose tenant or knowledge base differs from its slot's is rejected by composite-key constraints, with zero rows written.

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Existing canonical commit boundary and direct database insert (negative tests) | Commit concurrently; attempt an invalid insert | New versions only | One winner per contested coordinate; database rejects overlap, envelope mismatch and cross-scope rows | Grid read after the race; constraint violation codes captured in evidence | Existing commit authority; the database enforces rules regardless of role |

No new screen or route.

## Data Requirements

The exclusion constraint over slot, valid time and recorded time, incorporating the S0002 unknown-end representation. An envelope check constraint (or equivalent trigger) scoped to identity-v1 slots. Composite ownership keys from the F0002/0007 pattern.

## Role-Based Visibility

No new visibility. Commits require the caller's existing canonical-commit authorization over the slot's knowledge base, evaluated in the F0002 unit of work before any validation result is returned. An unauthorized caller is denied without learning whether the slot exists. The database constraints apply to every role, including the migration owner.

## Non-Functional Expectations

Conflicts are deterministic and retryable. No deadlock is left unresolved past the database's own detection. Lock strategy and isolation level are recorded in Phase B.

## Dependencies

S0002 (unknown-end representation inside the constraint); S0003; F0007 member slots and envelope; F0003 btree_gist.

## Out of Scope

RLS enablement (F0018), isolation proof (F0026), and projection consistency (F0018, F0034).

## Questions & Assumptions

The canonical relationship version table named in master blueprint §78 is reconciled in Phase B against F0007 RELATIONSHIP slots.

## Definition of Done

- [ ] Six ACs pass on PostgreSQL, including the concurrent race and the direct-insert negatives.
- [ ] The feature action records tests, coverage and the required signoffs.
