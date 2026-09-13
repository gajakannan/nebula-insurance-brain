## Story Header

**Story ID:** F0001-S0005
**Feature:** F0001 — Repository and engineering foundation
**Title:** Proof: bitemporal commit under retroactive and concurrent change
**Priority:** High
**Phase:** Infrastructure

## User Story

**As a** Ingrid the Persistence Engineer
**I want** the canonical commit algorithm implemented for one FactSlot with independent valid-time and recorded-time ranges, database-level overlap exclusion, and a transactional outbox
**So that** retroactive endorsements, later corrections, and concurrent commits are proven to produce unambiguous accepted state that answers the section 87 questions at every time coordinate

## Context & Background

Full bitemporality (ADR-0007) and database-level temporal integrity (ADR-0008) are baseline decisions. Master blueprint section 109.2 specifies the mutation algorithm and notes that PostgreSQL's single-range temporal key does not by itself implement two independent overlap conditions; section 109.3 requires facts, audit, and outbox in one transaction with idempotent projectors. Section 115.4 names this proof; proposed ADR-0041 is settled by the outcome.

## Acceptance Criteria

**Happy Path:**
- **Given** a FactSlot EachOccurrence with an accepted value of $2,000,000 valid from 2026-01-01 and recorded on 2026-01-10
- **When** an endorsement effective 2026-06-01 received 2026-06-12 sets $5,000,000 and is accepted on 2026-06-14
- **Then** queries return $2,000,000 valid as of 2026-05-15, $5,000,000 valid as of 2026-07-01, $2,000,000 for "known on 2026-06-05", and $5,000,000 for "known on 2026-06-15"

- **Given** the accepted endorsement
- **When** a later correction moves the effective date from 2026-06-01 to 2026-06-03
- **Then** the affected valid interval is split, the superseded belief's recorded visibility closes, and every prior version remains readable at its original recorded coordinates with change reason `corrected`

- **Given** any commit
- **When** it succeeds
- **Then** the fact version, review linkage, audit event, and outbox event are written in one database transaction and the response returns a semantic commit id and the resulting fact-version ids

- **Given** `source_received_at`, `artifact_created_at`, `assertion_created_at`, and `canonical_accepted_at`
- **When** the endorsement is committed
- **Then** all four are stored separately and recorded time equals `canonical_accepted_at`

**Alternative Flows / Edge Cases:**
- Two concurrent commits target the same slot with overlapping valid and recorded ranges → exactly one succeeds; the other fails with a serialization or exclusion error; no ambiguous accepted state exists afterwards
- A commit supplies an empty or null range → rejected with a validation error before any write
- The worker is killed after the transaction commits and before the projector runs → outbox replay processes the event once; the accepted value is readable from canonical storage throughout

## Interaction Contract

N/A — proof harness driven by tests and a CLI under a service principal; no user-facing mutation.

## Data Requirements

**Required Fields:**
- `fact_slot`: id, entity id, slot type, tenant, knowledge base
- `canonical_fact_version`: slot id, value, valid range, recorded range, change reason, evidence reference, commit id
- `canonical_fact_change`: reason enum (superseded, corrected, retracted, expired, invalidated, merged, split)
- `outbox_event`: commit id, payload, processed watermark
- Exclusion constraints on (slot, valid range, recorded range) using range types and btree_gist

**Optional Fields:**
- Review decision linkage when the change originates from S0004

**Validation Rules:**
- Ranges are non-empty and non-null (section 109.2 step 3)
- Recorded time is the canonical acceptance time, distinct from receipt (section 109.2)

## Role-Based Visibility

**Roles that can execute:**
- Persistence engineer — runs the harness
- Service principal — the commit actor in the proof, authorized against a minimal policy

**Data Visibility:**
- InternalOnly content: fixture policy facts
- ExternalVisible content: none

## Non-Functional Expectations

- Performance: the proof suite, including the concurrency case, runs within 2 minutes in CI against the containerized database
- Security: commits require an authenticated actor and an authorization decision recorded in the audit event
- Reliability: constraints are enforced by the database, not only by application code

## Dependencies

**Depends On:**
- F0001-S0002 — PostgreSQL with btree_gist

**Related Stories:**
- F0001-S0004 — supplies a review-originated correction case
- F0001-S0007 — records the outcome in ADR-0041

## Business Rules

1. Canonical facts maintain both valid and recorded periods (ADR-0007); overlap is prevented at the database (ADR-0008).
2. Every ended fact records why it ended (ADR-0009).
3. Receipt on June 12 is not canonical acceptance on June 12 if review completes on June 14 (section 109.2).

## Out of Scope

- The production canonical commit service with the full permission catalog (F0018)
- Graph and vector projections (F0033, F0034); the projector in this proof is a stub that records processed events
- Multivalued slots and relationship identity rules (section 109.1, F0007)

## UI/UX Notes

- N/A

## Questions & Assumptions

**Open Questions:**
- [ ] Architect to decide: is closing a recorded interval the only permitted update to a historical version, or does an append-only event representation derive intervals (section 109.2)?

**Assumptions (to be validated):**
- Two independent exclusion conditions are expressed as an explicit multi-column exclusion constraint rather than the single-range temporal key syntax (reference R6)

## Definition of Done

- [x] Acceptance criteria met
- [x] Edge cases handled
- [x] Permissions enforced (service principal authorized)
- [x] Audit/timeline logged (audit and outbox in the commit transaction)
- [x] Tests pass
- [x] Documentation updated (ADR-0041 input for S0007)
- [x] Story filename matches `Story ID` prefix
- [x] Story index regenerated

## Review Provenance

Recorded in `STATUS.md` (Required Signoff Roles, Story Signoff Provenance).
