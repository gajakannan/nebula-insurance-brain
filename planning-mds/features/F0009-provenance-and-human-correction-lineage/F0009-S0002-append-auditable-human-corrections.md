# F0009-S0002 — Append auditable human corrections

**Story ID:** F0009-S0002
**Feature:** F0009 — Provenance + human-correction lineage
**Title:** Append auditable human corrections
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Not Started

## User Story

**As a** business reviewer (Rosa)
**I want** to retain my correction beside the machine interpretation and the decision I actually submitted
**So that** a later reviewer can attribute and reconstruct both interpretations without erasing either.

## Context & Background

ADR-0037 and accepted ADR-0044 already define append-only correction, duplicate and stale outcomes, and separate annotation from canonical acceptance. F0009 completes the durable lineage over that existing boundary.

## Acceptance Criteria

- [ ] **AC1:** A permitted effective CORRECT through the existing review decision entry point appends a HUMAN_REVIEW assertion linked to the exact original assertion and the durable decision, review item and batch; it retains the verified reviewer, submitted assertion revision, decision/action, reason when supplied, decision time, evidence actually seen and declared precision.
- [ ] **AC2:** Correcting a version-2 assertion creates a version-2 child with the F0006 semantics and current admission checks. The original assertion, its semantics/evidence, immutable source artifact and existing canonical versions remain unchanged.
- [ ] **AC3:** The correction, decision, correction linkage and review_decision_recorded audit persist together or roll back together. A fresh read after transaction completion reconstructs the same identities, corrected value and evidence; a rendered success alone cannot satisfy the story.
- [ ] **AC4:** Replay of the same authorized decision event returns the prior duplicate outcome with no second correction, decision, audit effect or learning reservation. Authorization is evaluated under current grants before exposing that prior outcome.
- [ ] **AC5:** A decision against a stale assertion remains attributed and auditable with a non-applied outcome, the submitted correction/evidence where supplied, and no corrected assertion or learning reservation. Existing stale-item routing is preserved.
- [ ] **AC6:** Two distinct authorized corrections competing for one review item cannot overwrite the first applied decision or its assertion. The losing attempt has an auditable non-applied outcome under ADR-0044, without acquiring canonical authority. Phase B reconciles this with the existing already-decided rejection path.
- [ ] **AC7:** BLOCKED/EVIDENCE_UNRESOLVED, REJECT and ACCEPT do not create a corrected assertion or a correction reservation. Unresolved evidence cannot be accepted or corrected; current malformed/forbidden decision failures remain non-applying and are audited through their existing authorization/decision path.
- [ ] **AC8:** Reviewer authority alone creates zero canonical versions, canonical change rows or commit outbox effects. The reviewer identity is resolved from the authenticated principal, never trusted from submitted identity fields.

## Edge Cases & Error Scenarios

Replay, stale, competing and unresolved-evidence decisions have the non-applying outcomes in AC4–7. Atomic failure leaves no correction or reservation (AC3).

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Existing authorized review decision service / POST /reviews/batches/{id}/decisions | Submit the governed operation | Only a current authorized operation may apply; stale/blocked/duplicate outcomes follow the ACs | Append scoped records atomically; no silent overwrite | Query in a fresh session and compare persisted identities/values and audit | Verified existing authority only; no new permission |

No new screen is introduced. Validation/authorization failure cannot report a successful mutation. Existing error envelopes remain; Phase B specifies any added failure categories. Persistence and audit evidence are mandatory; render-only behavior cannot satisfy this story.

## Data Requirements

Existing decision event identity; exact assertion revision; original/created assertion and review links; reviewer and timestamp; submitted reason/comment/value/evidence as applicable; applied/stale/duplicate outcome.

Required fields and referential constraints are enforced before effects. Optional legacy metadata stays absent/qualified rather than invented. Persisted source text is not copied into denial output.

## Role-Based Visibility

Use the [PRD role matrix](PRD.md#role-based-access). TenantMember has only scoped read authority; Reviewer adds existing review annotation without canonical commit; ServicePrincipal uses its explicit scoped grants. Unverified, nonmember, cross-tenant/KB and external broker/MGA callers obtain no access. Current parent/classification restrictions apply to each source. Engineering personas confer no runtime role.

## Non-Functional Expectations

Zero unauthorized payload disclosure or partial mutation; zero source reparse/model calls. At least 80% changed executable-code coverage in the later feature run. PostgreSQL proves durable behavior and concurrency where applicable. No unmeasured latency target is asserted. Use existing authorization/decision audit and correlation fields.

## Dependencies

F0006 correction semantics and evidence ancestry; F0002 verified principal and mutation authorization; ADR-0044/0037/0058; S0005 reserves a future learning reference for effective corrections.

## Out of Scope

A redesigned review workflow or screen; new review/adjudicate/approve grants; automatic canonical acceptance; second-review business policy.

## Questions & Assumptions

No open business-rule question is introduced. The [PRD assumptions](PRD.md#risks--assumptions) require Phase A review; storage, limits, contracts and rollback are explicit Architect decisions for Phase B. Requirements do not grant formal acceptance to a Proposed ADR.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] Existing review entry-point integration with a fresh-session query, rollback injection, replay, stale and concurrent submissions, source checksums and a zero-canonical-effects assertion.
- [ ] Error scenarios, permission checks and audit/persistence expectations pass.
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.

## Review Provenance

Planning only. No runtime signoff is claimed. The Architect sets the required role matrix in [STATUS.md](STATUS.md) during Phase B; the feature action supplies actual evidence.
