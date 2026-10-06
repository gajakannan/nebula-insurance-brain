## Story Header

**Story ID:** F0003-S0003  
**Feature:** F0003 — PostgreSQL persistence  
**Title:** Preserve temporal and transactional integrity  
**Priority:** Critical  
**Phase:** v0.1A  
**Status:** Not Started

## User Story

**As a** persistence engineer  
**I want** PostgreSQL to enforce temporal and transaction invariants for authoritative records  
**So that** concurrent writes cannot produce ambiguous history or detached audit and projection events.

## Context & Background

ADR-0007 requires separate valid and recorded periods. ADR-0008 requires database-level exclusion of overlapping canonical intervals. F0001-S0005 provides the measured bitemporal proof; F0008 and F0018 retain ownership of feature-level temporal semantics and canonical commit behavior.

## Acceptance Criteria

**Happy Path:**

- **Given** a canonical fact version with a non-empty valid range and a non-empty recorded range, **when** the row is stored, **then** each period remains independently queryable.
- **Given** a successful authoritative commit, **when** it completes, **then** the fact state, required audit record, and outbox event commit in the declared transaction.
- **Given** a process restart after commit, **when** a new session reads the record, **then** the committed state and outbox identity are present.

**Alternative Flows / Edge Cases:**

- An empty or missing required range → reject the write without a partial row.
- Two concurrent writes produce overlapping valid and recorded ranges for the same slot → PostgreSQL permits at most one conflicting write; no ambiguous accepted state remains.
- Audit or outbox persistence fails during an atomic operation → roll back the authoritative fact change as required by the owning operation.
- A worker retries an already published outbox event → processing remains idempotent and does not duplicate accepted effects.

## Interaction Contract

N/A — internal persistence and worker transaction behavior; no user-facing mutation.

## Data Requirements

- Valid and recorded periods use PostgreSQL range types.
- The same-slot two-range exclusion rule follows ADR-0008 and the accepted F0001-S0005 proof.
- Evidence references and change reasons remain addressable from persisted canonical versions.
- Outbox and audit records retain stable operation/commit references.

## Role-Based Visibility

- **Roles that can execute:** The owning authorized service or worker initiates the transaction.
- **Data Visibility:** Authorization is enforced by the owning service per F0002; database access does not expand visibility.

## Non-Functional Expectations

- Database constraints, not application-only checks, protect non-overlap.
- Concurrency and PostgreSQL range behavior are verified against PostgreSQL 18.
- Changed persistence code meets at least 80% coverage during implementation.

## Dependencies

**Depends On:**

- F0001-S0005 — bitemporal commit proof and PostgreSQL range/GiST baseline.
- F0002-S0006 — durable audit behavior through existing consumers.

**Related Stories:**

- F0008 — bitemporal canonical fact semantics.
- F0018 — authorized canonical commit service and policy-version audit.
- F0020 — temporal query behavior.

## Business Rules

1. Valid time and recorded time describe different axes and are not interchangeable.
2. PostgreSQL is authoritative for accepted semantic state; a projection or outbox consumer cannot replace the source transaction.
3. Evidence or derivation lineage remains mandatory for authoritative facts under ADR-0010.

## Out of Scope

- Replacing the F0001 bitemporal algorithm or expanding F0008/F0018 business behavior.
- Graph/vector projection delivery.
- General Temporal workflow orchestration.

## Questions & Assumptions

**Assumptions:**

- The database implements the accepted F0001/ADR constraints; feature owners specify which operation writes each record.
- The F0001 proof is a baseline contract, not evidence that the full F0003 production scope is complete.

## Definition of Done

- [ ] Range validation and exclusion behavior pass PostgreSQL integration cases.
- [ ] Concurrent conflicting writes cannot create ambiguous state.
- [ ] Failure injection proves required fact/audit/outbox atomicity.
- [ ] Retry behavior does not duplicate accepted effects.
- [ ] Story index regenerated after story changes.
