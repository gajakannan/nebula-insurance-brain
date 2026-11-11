# Resolve stable FactSlot identity

**Story ID:** F0007-S0001
**Feature:** F0007 — FactSlot model
**Title:** Resolve stable FactSlot identity
**Priority:** Critical
**Phase:** MVP
**Status:** In Progress

## User Story

**As a** Ingrid the Persistence Engineer
**I want** every semantic question about a subject to resolve to exactly one FactSlot identity in its knowledge base
**So that** two limits that differ only by basis never share an answer and the same question never splits into two slots.

## Context & Background

ADR-0006 makes FactSlot first-class; master blueprint §13 gives the scalar example and §109.1 lists the identity rules still to specify. G1 (2026-11-09) chose an opaque, versioned predicate key: F0012/F0013 register real predicates later, and ADR-0038's SourceAuthorityPolicy keys on the same predicate key.

## Acceptance Criteria

- [ ] **AC1:** Given subject S, predicate key `hasLimitAmount` with pinned release R, and qualifiers `{basis: EachOccurrence, currency: USD}`, resolving twice, including from two concurrent sessions, returns the same slot ID and leaves exactly one slot with one set of qualifier rows.
- [ ] **AC2:** Changing only `basis` to `GeneralAggregate` resolves a different slot (ADR-0006 use case). Supplying the same qualifiers in a different input order resolves the original slot.
- [ ] **AC3:** Qualifier values are normalized by declared type before identity: Unicode NFC for text and one canonical decimal encoding (`1000000`, `1000000.00` and `1E+6` are equal). The normalized qualifier rows are stored and the fingerprint records its algorithm version. If two different normalized qualifier sets ever produce the same fingerprint, the second is rejected with `FINGERPRINT_COLLISION` and the slots are not merged.
- [ ] **AC4:** An omitted qualifier and a qualifier supplied as explicit null follow one documented rule (settled in Phase B). Fixtures prove the rule's outcome for both inputs, and neither input is silently coerced into the other.
- [ ] **AC5:** For a tenant entity associated with KB A and KB B, the same predicate key and qualifiers resolve to two distinct slots, one owned by each KB. A principal authorized only for KB B is denied resolution or reads of the KB A slot, and the denial is indistinguishable from not found.
- [ ] **AC6:** A malformed predicate key, or one with no pinned release reference, is rejected with `PREDICATE_KEY_INVALID` and no slot row is written. The resolved slot exposes its predicate key unchanged for SourceAuthorityPolicy lookup. F0007 does not check predicate semantics against an ontology.
- [ ] **AC7:** Creating a slot is authorized against the caller's existing KB write authority (F0002). Each creation writes one audit event naming actor, tenant, KB, slot ID and fingerprint version. Unauthorized or cross-tenant subject attempts are denied with zero slot rows. Updating identity fields after creation is rejected.

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Internal slot-resolution service (engine) | Resolve or create a slot from subject, predicate key and qualifiers | New slot only; identity immutable once created | Returns existing or newly created slot ID; audit event on create | PostgreSQL reload returns the same ID and normalized qualifiers; concurrent test shows one row | Existing KB write authority to create; read authority to resolve an existing slot |

No new screen or HTTP route. Tests must exercise the resolution service against PostgreSQL, not only the fingerprint function.

## Data Requirements

Tenant, KB, subject entity identity, predicate key and release reference, cardinality (S0002), normalized typed qualifier rows, fingerprint and algorithm version, creation actor and time.

## Role-Based Visibility

Only principals authorized for the slot's KB can resolve or read it. Denials do not reveal whether a slot exists in another KB or tenant.

## Non-Functional Expectations

Deterministic identity with no model call and no clock dependence. The resolve-or-create step is idempotent and safe under concurrent callers.

## Dependencies

F0002 tenant entity identity, authorization and audit. F0003 persistence conventions. The F0001 pilot `fact_slot` table. S0002 supplies cardinality and S0006 supplies legacy compatibility.

## Out of Scope

Fact versions and time (F0008), ontology validation of predicates (F0012/F0013), entity resolution (F0017), SourceAuthorityPolicy evaluation (F0018).

## Questions & Assumptions

G1 decided the predicate key form. The Architect owns the canonical encoding, the hash function and the omitted-versus-null rule. Assumption: slots are KB-owned semantic content (ADR-0061, ADR-0066 §1a).

## Definition of Done

- [ ] Seven ACs pass against PostgreSQL, including the concurrent and cross-KB negative fixtures.
- [ ] Normalization and fingerprint rules are documented with worked and boundary examples.
- [ ] Feature action records tests, coverage and required signoffs.
