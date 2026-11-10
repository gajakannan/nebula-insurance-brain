# Preserve pilot slots and ownership

**Story ID:** F0007-S0006
**Feature:** F0007 — FactSlot model
**Title:** Preserve pilot slots and ownership
**Priority:** Critical
**Phase:** MVP
**Status:** Done

## User Story

**As a** Ingrid the Persistence Engineer
**I want** the existing pilot slots, commit path and fact reads to keep working while every new slot identity row is owned by its tenant and knowledge base
**So that** adopting the full model loses no existing fact or history and opens no cross-tenant path.

## Context & Background

The F0001 pilot `fact_slot` (migration 0003) holds `entity_id` and a free-text `slot_type`, with a tenant ownership key to `entity_identity` added in 0006 and immutable ownership columns from 0007. The F0003 ownership table assigns `fact_slot` and `fact_slot_qualifier` to F0007 and requires preserving the 0003 rows. G1 (2026-11-09): F0007 binds ownership; F0018 designs and enables row-level security on every tenant-owned table.

## Acceptance Criteria

- [ ] **AC1:** Every pre-existing `fact_slot` row and its fact versions read back through `GET /facts/{factSlotId}` with identical values, ranges and evidence after the upgrade. No fact version is rewritten.
- [ ] **AC2:** Pilot slots that have no predicate key or qualifiers keep their `slot_type` and are labelled legacy. No predicate key or qualifier is fabricated for them. Identity-based resolution never matches a legacy slot implicitly; any mapping is explicit, recorded and reversible.
- [ ] **AC3:** The existing pilot commit, review and assertion-consumer test suites pass unchanged (regression).
- [ ] **AC4:** Every new F0007 row (qualifier, member, relationship) carries `tenant_id` and `knowledge_base_id` bound to its slot through composite foreign keys. A child row pointing at another tenant's or KB's slot is rejected by PostgreSQL. Updates to identity or ownership columns are rejected by trigger (the 0007 pattern).
- [ ] **AC5:** The F0007 tables are listed in an RLS inventory handed to F0018. F0007 does not enable row-level security and introduces no superuser, `BYPASSRLS` or table-owner shortcut that would stop F0018 enabling it.
- [ ] **AC6:** The migration is additive with a documented rollback. Upgrade, downgrade and upgrade again on a database seeded with pilot data leave pilot rows identical.
- [ ] **AC7:** Unauthorized or cross-tenant/KB slot reads are denied with zero disclosure. Existing authorization-decision audit is unchanged, and new slot creation is audited (S0001).

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Schema upgrade; existing `GET /facts/{factSlotId}` and pilot commit | Upgrade, read and commit on pilot slots | Pilot rows read-only to the migration | Additive structures only | Before/after snapshots equal; up/down/up cycle passes | Existing read/commit authority; operator runs migrations |

No screen or new route.

## Data Requirements

Legacy marker, preserved `slot_type`, composite ownership keys on every new child table, immutability triggers, and the RLS inventory list.

## Role-Based Visibility

Visibility is unchanged for pilot slots. New rows follow the parent slot's KB authorization.

## Non-Functional Expectations

Zero data loss and zero rewritten fact versions. The migration completes on the pilot dataset with no manual step.

## Dependencies

F0001 pilot migrations 0003/0006/0007, F0002 ownership pattern and F0003 safe schema evolution. F0018 receives the RLS inventory.

## Out of Scope

RLS policy design and enablement (F0018), isolation proof (F0026), and mapping pilot facts to ontology predicates (F0012/F0013).

## Questions & Assumptions

The Architect decides whether the pilot `slot_type` values get an explicit predicate-key mapping or remain legacy-only, under AC2's no-fabrication rule.

## Definition of Done

- [ ] Seven ACs pass with snapshot comparison, the migration cycle and ownership negative tests against PostgreSQL.
- [ ] Feature action records tests, coverage and required signoffs.
