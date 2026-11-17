# Preserve pilot versions through migration

**Story ID:** F0008-S0007
**Feature:** F0008 — Bitemporal canonical facts
**Title:** Preserve pilot versions through migration
**Priority:** High
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Ingrid the Persistence Engineer
**I want** the temporal additions to leave every fact the Brain already holds exactly as it was, with no invented precision, zone or basis, and to be safely reversible
**So that** the answers already stored keep their meaning, and a rollback never loses history.

## Context & Background

F0003 assigned `canonical_fact_version` to F0008 and requires safe schema evolution. F0007 followed the same pattern: legacy pilot slots stay legacy, with no fabricated identity. Pilot versions have instants but no granularity, zone, end state, attestation or basis.

## Acceptance Criteria

- [ ] **AC1:** After upgrade, every pre-existing version's id, slot, value, valid range, recorded range, evidence, review linkage and four timestamps are byte-for-byte equal to a pre-upgrade snapshot. Existing audit events and authorization decision rows are unchanged.
- [ ] **AC2:** Pre-existing versions are explicitly marked legacy. Their granularity, zone, attestation and basis are absent, never defaulted to invented values. A NULL valid upper bound on a legacy row reads as `OPEN`.
- [ ] **AC3:** Legacy pilot slots keep accepting the pilot commit request shape, with pilot behaviour and the S0003 immutability rule. Identity-v1 slots require the new fields (Assumption A1). A pilot-shaped request to an identity-v1 slot is rejected with `TEMPORAL_FIELDS_REQUIRED`, and nothing is written.
- [ ] **AC4:** Upgrade → downgrade → upgrade on a database seeded with pilot versions and F0007 identity-v1 versions preserves the AC1 snapshot. A downgrade refuses to run while any version uses a field the old schema cannot hold, and names the blocking rows.
- [ ] **AC5:** The existing F0001 bitemporal and F0007 answer test suites pass unchanged after the migration.
- [ ] **AC6:** The migration adds no grant, role or route. The API change is limited to additive commit-request and read-response fields.

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Alembic migration (operator) and the existing commit and read routes | Upgrade or downgrade the schema; commit to a legacy slot | Legacy slots keep the pilot commit shape | Additive DDL; legacy marker; guarded downgrade | Snapshot comparison before and after; existing suites pass | Operator runs migrations; existing commit and read authority |

No new screen or route.

## Data Requirements

A legacy marker on versions, nullable new columns constrained by identity version, and downgrade guards.

## Role-Based Visibility

No new visibility. The migration changes no permission and no grant. Commits require the caller's existing canonical-commit authorization over the slot's knowledge base, evaluated in the F0002 unit of work before any validation result is returned. An unauthorized caller is denied without learning whether the slot exists.

## Non-Functional Expectations

The migration completes on the seeded fixture without manual steps and is idempotent under re-run.

## Dependencies

F0003 migration conventions; F0007 migrations 0012/0013; S0001–S0005 fields.

## Out of Scope

Converting legacy pilot slots to identity-v1 (no feature owns this; it would need a new operator decision).

## Questions & Assumptions

Assumption A1 is labelled for G3 review. Phase B gives the migration number and the rollback steps.

## Definition of Done

- [ ] Six ACs pass, with snapshot evidence and up/down/up logs.
- [ ] The feature action records tests, coverage and the required signoffs.
