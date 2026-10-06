## Story Header

**Story ID:** F0003-S0004  
**Feature:** F0003 — PostgreSQL persistence  
**Title:** Evolve the schema without losing accepted state  
**Priority:** High  
**Phase:** v0.1A  
**Status:** Not Started

## User Story

**As a** persistence engineer  
**I want** versioned and reviewable PostgreSQL schema migrations  
**So that** the Brain can add feature-owned records without losing established identifiers, ownership, evidence, or history.

## Context & Background

F0001 established migrations 0001–0004; F0002 extended them through 0007 for structural ownership and safeguards. F0003 extends this history; it must not replace it or conceal unresolved backfill decisions.

## Acceptance Criteria

**Happy Path:**

- **Given** a database at the accepted F0002 migration head, **when** the F0003 migration sequence is applied, **then** the schema reaches its declared revision and existing identifiers, ownership, provenance, and history remain intact.
- **Given** a new feature-owned table, **when** it is added, **then** its Alembic revision, owner keys, constraints, indexes, and inventory entry are traceable to the approved source contract.
- **Given** an upgrade from a clean PostgreSQL 18 database, **when** the supported migration sequence is applied, **then** the resulting schema matches the declared model and revision head.
- **Given** an authorized migration run, **when** it succeeds or fails, **then** the migration audit log records the revision, operator, timestamp, and outcome without logging secrets or source text.

**Alternative Flows / Edge Cases:**

- A migration finds an ambiguous owner or invalid legacy value → stop and report the row; do not silently coerce, delete, or widen access.
- A migration fails partway through data transformation → preserve a valid prior state or fail closed with an explicit recovery procedure; never report success with a partially reconciled schema.
- A migration is not safely reversible after data is written → document the forward-repair path; do not claim a data-losing downgrade is supported.

## Interaction Contract

N/A — migration operator workflow; no end-user mutation.

## Data Requirements

- Use the existing Alembic revision chain and PostgreSQL 18 baseline.
- Preserve UUIDs and durable evidence/history.
- Record explicit expand, reconcile/backfill, and constraint-enforcement steps where a change needs them.
- Keep secrets and source text out of migration logs.

## Role-Based Visibility

- **Roles that can execute:** Approved migration operator in a controlled environment.
- **Data Visibility:** Migration access is operational privilege and does not grant application users access.
- **Authorization:** Only the approved operator and deployment process may apply a migration; application principals cannot invoke schema changes.
- **Audit/timeline:** Each migration run records the revision, operator, timestamp, and outcome in the deployment/migration log. No business event is emitted solely for a schema revision.

## Non-Functional Expectations

- Clean-install and upgrade paths produce the same declared schema head.
- Migration behavior is verified on PostgreSQL 18; no extension or major-version downgrade is implicit.
- Changed persistence code meets at least 80% coverage during implementation.

## Dependencies

**Depends On:**

- F0001-S0002 — pinned PostgreSQL 18/extension baseline.
- F0002-S0001 and F0002-S0006 — ownership migration and consumer compatibility.

**Related Stories:**

- F0003-S0001 — inventory and owner assignments.
- F0003-S0002 — database reference constraints.
- F0003-S0003 — temporal and transaction constraints.

## Out of Scope

- Changing the selected PostgreSQL major version or extension build.
- Implementing a production deployment or backup/restore system.
- Silent data cleanup or inferred ownership backfills.

## Questions & Assumptions

**Assumptions:**

- Existing accepted migrations remain the compatibility baseline.
- Any data transformation requires an explicit mapping and a failure path for ambiguous rows.

## Definition of Done

- [ ] Upgrade from the accepted F0002 head succeeds on PostgreSQL 18.
- [ ] Existing IDs, owners, and history are preserved.
- [ ] Ambiguous backfills stop with actionable reconciliation output.
- [ ] Clean-install and upgrade paths reach the same revision head.
- [ ] Story index regenerated after story changes.
