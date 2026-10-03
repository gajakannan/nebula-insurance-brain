## Story Header

**Story ID:** F0003-S0001  
**Feature:** F0003 — PostgreSQL persistence  
**Title:** Inventory core persistence ownership and phase boundaries  
**Priority:** Critical  
**Phase:** v0.1A  
**Status:** Not Started

## User Story

**As a** persistence engineer  
**I want** one complete inventory of the core PostgreSQL tables with an owning feature and delivery phase  
**So that** later feature teams can add durable records without duplicating the system of record or pulling future behavior into v0.1.

## Context & Background

Master-blueprint §78 lists the core relational tables across multiple release phases. F0001 already created the first persistence baseline and F0002 extended ownership and identity. The inventory must preserve that history and make later feature ownership explicit.

## Acceptance Criteria

**Happy Path:**

- **Given** the §78 table list and the v0.1 roadmap, **when** the persistence inventory is reviewed, **then** every table has exactly one owning feature, delivery phase, source requirement, and migration boundary.
- **Given** a table already present from F0001 or F0002, **when** it appears in the inventory, **then** its existing schema and migration provenance are linked and are not silently reassigned.
- **Given** a table owned by a later-phase feature, **when** F0003 is implemented, **then** its inventory entry remains explicit but the table’s domain behavior is not activated early.
- **Given** content bytes or immutable artifact bundles, **when** their storage boundary is documented, **then** PostgreSQL holds metadata and references while bytes remain behind ADR-0059 storage ports.

**Alternative Flows / Edge Cases:**

- An inventory row has no clear owner or phase → record the unresolved mapping and block migration planning for that row; do not invent an owner.
- Two features claim the same table → resolve ownership in planning artifacts before a migration is authored.

## Interaction Contract

N/A — planning and persistence inventory; no user-facing mutation.

## Data Requirements

- Table identity, owning feature, delivery phase, source contract, existing migration/revision, ownership keys, and dependency notes.
- JSONB may represent only contract-approved flexible data; it does not replace normalized authoritative fields.

## Role-Based Visibility

- **Roles that can execute:** Persistence engineer and Architect maintain the inventory.
- **Data Visibility:** No direct user data access is introduced by this story.
- **Authorization:** No runtime data read/write is part of an inventory edit; repository changes require normal review, and database access remains governed by F0002.

## Non-Functional Expectations

- The inventory is complete against §78 and remains reviewable alongside the schema/migration sources.
- No table owner or release phase is inferred from a KG mapping alone; raw planning artifacts decide conflicts.

## Dependencies

**Depends On:**

- F0001 persistence baseline and accepted schema proofs.
- F0002 structural ownership and identity contracts.

**Related Stories:**

- F0004-S* — content-artifact schema owner.
- F0005-S0002 — production job and persistence consumer.
- F0008-S* — bitemporal canonical-fact behavior.

## Out of Scope

- Creating future-phase table behavior without its owning feature’s requirements.
- Replacing or rewriting F0001/F0002 migration history.
- Implementing business rules, services, APIs, or projections.

## Questions & Assumptions

**Assumptions:**

- The full §78 list is an inventory and ownership obligation; each row’s delivery phase remains authoritative for implementation timing.
- F0003 owns the shared persistence boundary, while domain-specific fields and behavior remain with the owning feature.

## Definition of Done

- [ ] Every §78 row has an owner, phase, source, and migration boundary.
- [ ] Existing tables link to their accepted F0001/F0002 migration provenance.
- [ ] Future-phase entries remain deferred.
- [ ] Inventory changes have reviewable acceptance evidence.
- [ ] Story index regenerated after story changes.
