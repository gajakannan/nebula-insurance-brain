# F0009-S0005 — Reserve a learning-candidate reference

**Story ID:** F0009-S0005
**Feature:** F0009 — Provenance + human-correction lineage
**Title:** Reserve a learning-candidate reference
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Not Started

## User Story

**As a** business reviewer (Rosa)
**I want** to my effective correction to carry a durable reference that future governed learning can consume
**So that** a correction can later become an explicitly reviewed benchmark candidate without silently changing a holdout.

## Context & Background

The F0009 2026-11-08 ownership amendment and master blueprint §§88/106.3 assign a reserved LearningCandidate reference only. F0041 owns learning behavior and F0026 owns the Golden Corpus workflow.

## Acceptance Criteria

- [ ] **AC1:** Each new effective non-stale CORRECT decision with a created corrected assertion has one server-owned reserved LearningCandidate reference linked to that exact decision and original/corrected assertion, tenant/KB and reviewer/time provenance.
- [ ] **AC2:** Reservation, correction linkage, corrected assertion, decision and decision audit commit atomically. An injected reservation failure rolls the operation back; it cannot leave an effective correction without its required reference.
- [ ] **AC3:** Duplicate replay returns the same reservation identity and creates zero extra reservations or audit effects. Concurrent submissions cannot attach two reservations to the same effective correction.
- [ ] **AC4:** ACCEPT, REJECT, BLOCKED, stale and losing already-decided attempts create no reservation. Pre-feature decisions are not backfilled with fabricated candidates or fabricated historical timestamps.
- [ ] **AC5:** A reservation conveys no candidate approval, canonical authority, independent evidence count or benchmark membership. The operation triggers zero learning/model jobs, promotion actions, automatic dataset writes or frozen-holdout changes.
- [ ] **AC6:** The reference can be retrieved only within the authorized correction lineage and remains scoped/append-only with that lineage. Unauthorized reference access is non-disclosing and audited under the existing authority; F0041 can later adopt the identity without reinterpreting the correction.

## Edge Cases & Error Scenarios

Reservation failure rolls back the correction (AC2). Replay/concurrency and non-effective actions cannot create extra reservations (AC3–4).

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Existing authorized review decision service / POST /reviews/batches/{id}/decisions | Submit the governed operation | Only a current authorized operation may apply; stale/blocked/duplicate outcomes follow the ACs | Append scoped records atomically; no silent overwrite | Query in a fresh session and compare persisted identities/values and audit | Verified existing authority only; no new permission |

No new screen is introduced. Validation/authorization failure cannot report a successful mutation. Existing error envelopes remain; Phase B specifies any added failure categories. Persistence and audit evidence are mandatory; render-only behavior cannot satisfy this story.

## Data Requirements

Server-owned reserved reference identity and exact decision/original/corrected assertion provenance, structural tenant/KB, actor/time. The Architect chooses additive storage and future identity adoption, without designing the F0041 learning model.

Required fields and referential constraints are enforced before effects. Optional legacy metadata stays absent/qualified rather than invented. Persisted source text is not copied into denial output.

## Role-Based Visibility

Use the [PRD role matrix](PRD.md#role-based-access). TenantMember has only scoped read authority; Reviewer adds existing review annotation without canonical commit; ServicePrincipal uses its explicit scoped grants. Unverified, nonmember, cross-tenant/KB and external broker/MGA callers obtain no access. Current parent/classification restrictions apply to each source. Engineering personas confer no runtime role.

## Non-Functional Expectations

Zero unauthorized payload disclosure or partial mutation; zero source reparse/model calls. At least 80% changed executable-code coverage in the later feature run. PostgreSQL proves durable behavior and concurrency where applicable. No unmeasured latency target is asserted. Use existing authorization/decision audit and correlation fields.

## Dependencies

S0002 effective correction; S0004 authority; F0009 ownership amendment; master blueprint §§88, 96 and 106.3.

## Out of Scope

A LearningCandidate processing pipeline, scoring, promotion, full candidate schema, automatic Golden Corpus export or any holdout change.

## Questions & Assumptions

No open business-rule question is introduced. The [PRD assumptions](PRD.md#risks--assumptions) require Phase A review; storage, limits, contracts and rollback are explicit Architect decisions for Phase B. Requirements do not grant formal acceptance to a Proposed ADR.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] Fresh-session lookup of one reservation, duplicate and concurrent attempts, transaction-failure injection, negative action matrix and zero producer/dataset calls.
- [ ] Error scenarios, permission checks and audit/persistence expectations pass.
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.

## Review Provenance

Planning only. No runtime signoff is claimed. The Architect sets the required role matrix in [STATUS.md](STATUS.md) during Phase B; the feature action supplies actual evidence.
