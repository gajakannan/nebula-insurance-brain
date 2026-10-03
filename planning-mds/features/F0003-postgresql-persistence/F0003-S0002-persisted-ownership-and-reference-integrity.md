## Story Header

**Story ID:** F0003-S0002  
**Feature:** F0003 — PostgreSQL persistence  
**Title:** Enforce persisted ownership and reference integrity  
**Priority:** Critical  
**Phase:** v0.1A  
**Status:** Not Started

## User Story

**As a** persistence engineer  
**I want** PostgreSQL to enforce declared ownership and parent-reference constraints  
**So that** invalid cross-tenant or cross-knowledge-base records cannot become authoritative state.

## Context & Background

F0002 defines and implements structural Tenant → Workspace → KnowledgeBase ownership, explicit access, and composite keys. F0003 must preserve those contracts as the §78 inventory is completed. This story does not redesign F0002 authorization or grant rules.

## Acceptance Criteria

**Happy Path:**

- **Given** a record with valid tenant, workspace, knowledge-base, and parent keys, **when** it is persisted, **then** PostgreSQL accepts the reference and the record remains readable after a new process/session.
- **Given** a child or link row with owner keys, **when** its parent belongs to a different owner, **then** a database constraint rejects the write even if application validation is bypassed.
- **Given** an existing F0001/F0002 record with a stable identifier, **when** an additive schema migration is applied, **then** that identifier and its valid history are retained.

**Alternative Flows / Edge Cases:**

- Required parent or owner data is missing → the write fails before any dependent record is committed.
- A backfill encounters ambiguous historical ownership → migration reports the unresolved row and stops; it does not guess an owner or grant access.
- A link table has no owner columns → its parent foreign key must unambiguously establish ownership; multi-parent links carry the owner keys needed for composite references.

## Interaction Contract

N/A — internal persistence boundary; no user-facing mutation.

## Data Requirements

- Preserve F0002’s tenant, workspace, knowledge-base, principal, membership, and identity references.
- Use composite keys/foreign keys where required to prevent cross-owner parent associations.
- Maintain append-only behavior for audit rows as specified by F0002.

## Role-Based Visibility

- **Roles that can execute:** Authorized application services and workers use the persistence contract; migration operators apply schema changes.
- **Data Visibility:** This story does not grant application or end-user access. F0002 remains the authority for authorization.

## Non-Functional Expectations

- Ownership failures are atomic and do not leave dependent partial records.
- PostgreSQL integration checks cover constraints that SQLite fixtures cannot enforce.
- Changed persistence code meets at least 80% coverage during implementation.

## Dependencies

**Depends On:**

- F0002-S0001 — structural tenancy and entity identity.
- F0002-S0006 — audit and consumer contract proof.

**Related Stories:**

- F0003-S0001 — table owner and migration inventory.
- F0003-S0004 — compatible schema changes.

## Out of Scope

- Defining tenant or knowledge-base access policy.
- Creating new principal kinds, roles, or grants.
- Cross-tenant sharing or entity matching.

## Questions & Assumptions

**Assumptions:**

- A verified identity or database connection alone does not grant protected data access.
- Existing F0002 constraints are preserved; remaining table references follow the same owner contract where applicable.

## Definition of Done

- [ ] Valid owner and parent references persist.
- [ ] Cross-owner and incomplete references fail at PostgreSQL.
- [ ] Failed writes leave no partial dependent state.
- [ ] Stable IDs and existing history survive migration.
- [ ] Applicable migration and PostgreSQL integration cases pass.
- [ ] Story index regenerated after story changes.
