# F0009-S0003 — Trace temporal version lineage

**Story ID:** F0009-S0003
**Feature:** F0009 — Provenance + human-correction lineage
**Title:** Trace temporal version lineage
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Done

## User Story

**As a** persistence engineer (Ingrid)
**I want** to distinguish corrected source claims, replaced canonical beliefs and unchanged split remainders
**So that** a history explanation states why a version exists without treating a remainder as a new extraction.

## Context & Background

Accepted ADR-0078 and migrations 0014–0015 ship close-only versions, same-slot split_of_version_id, ending_refs and canonical_fact_change. F0009 consumes those facts and leaves the F0010 change vocabulary and retraction decision with F0010.

## Acceptance Criteria

- [x] **AC1:** An explanation of a canonical version preserves its exact valid/recorded coordinates and stored fact-answer/v1 and fact-temporal/v1 metadata, including legacy qualification and validity uncertainty. A historical coordinate cannot be silently answered using current canonical state.
- [x] **AC2:** For a retroactive split, each remainder identifies its stored split_of_version_id predecessor in the same slot. Its original payload, evidence and timestamps remain attributable to that predecessor; the remainder is never presented as a fresh human or machine claim.
- [x] **AC3:** The result distinguishes assertion-correction links, version split links and canonical_fact_change old/new links, retaining stored reason, actor/time and commit identity where available. F0009 introduces no replacement change-reason vocabulary.
- [x] **AC4:** Supporting evidence and `ending_refs` inside the version’s evidence JSON are distinct categories. Both preserve exact referenced identities and follow current source-access checks; ending evidence is never relabelled as original supporting evidence.
- [x] **AC5:** A reviewed assertion with no canonical commit is explained as a reviewed assertion only. If an independently authorized commit already references that correction, the reader follows the stored link; it creates no commit and infers no acceptance from a review decision.
- [x] **AC6:** A broken or cross-slot split link, missing change endpoint or cyclic history cannot produce a complete explanation. Cross-tenant/KB references are denied without disclosing target identity or payload, including under elevated application-database privileges.
- [x] **AC7:** The read/refusal uses the existing authorization audit, with no canonical timeline event. The reader performs zero updates to canonical versions/change rows and preserves the database close-only rule. Existing two-coordinate fact reads, unknown-validity outcomes and the PRESENT succession guard keep their shipped behavior; retraction semantics are deferred to F0010.

## Edge Cases & Error Scenarios

Cross-slot, missing and cyclic links cannot report complete history (AC6). A read performs no mutation; the existing authorization audit records the read/refusal rather than a new canonical timeline event (AC7).

## Interaction Contract

N/A — read-only story. Entry is the authorized internal lineage reader selected in Phase B. Completion is a returned, current-authorized result for an exact root or an explicit non-disclosing refusal. No editable state or save action is introduced.

## Data Requirements

Exact version and slot IDs; split_of_version_id; canonical_fact_change endpoints/reason; evidence refs and ending_refs; recorded/valid coordinates and temporal qualification; stored commit and review links.

Required fields and referential constraints are enforced before effects. Optional legacy metadata stays absent/qualified rather than invented. Persisted source text is not copied into denial output.

## Role-Based Visibility

Use the [PRD role matrix](PRD.md#role-based-access). TenantMember has only scoped read authority; Reviewer adds existing review annotation without canonical commit; ServicePrincipal uses its explicit scoped grants. Unverified, nonmember, cross-tenant/KB and external broker/MGA callers obtain no access. Current parent/classification restrictions apply to each source. Engineering personas confer no runtime role.

## Non-Functional Expectations

Zero unauthorized payload disclosure or partial mutation; zero source reparse/model calls. At least 80% changed executable-code coverage in the later feature run. PostgreSQL proves durable behavior and concurrency where applicable. No unmeasured latency target is asserted. Use existing authorization/decision audit and correlation fields.

## Dependencies

F0008 including migration 0015 and both remediation runs; F0007 answer/slot identity; S0001 provenance reader; S0004 linked-resource authority.

## Out of Scope

F0010 retraction/closure rules, new temporal mutation algorithms, full F0020 history API, a separate relationship-version table.

## Questions & Assumptions

No open business-rule question is introduced. The [PRD assumptions](PRD.md#risks--assumptions) require Phase A review; storage, limits, contracts and rollback are explicit Architect decisions for Phase B. Requirements do not grant formal acceptance to a Proposed ADR.

## Definition of Done

- [x] Every AC above has a concrete observed proof in the later feature run.
- [x] PostgreSQL retroactive split with exact predecessor/remainder expectations, separately authorized reviewed commit, ending-source revocation and unchanged historical bytes.
- [x] Error scenarios, permission checks and audit/persistence expectations pass.
- [x] Documentation and tracker state reflect observed results.
- [x] Required story-level review provenance is appended to STATUS.md in the feature action.

## Review Provenance

Planning only. No runtime signoff is claimed. The Architect sets the required role matrix in [STATUS.md](STATUS.md) during Phase B; the feature action supplies actual evidence.
