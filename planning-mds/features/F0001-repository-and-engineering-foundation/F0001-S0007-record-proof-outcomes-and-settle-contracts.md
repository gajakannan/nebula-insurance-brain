## Story Header

**Story ID:** F0001-S0007
**Feature:** F0001 — Repository and engineering foundation
**Title:** Record proof outcomes and settle the pre-build contracts
**Priority:** High
**Phase:** Infrastructure

## User Story

**As a** Dana the Platform Engineer
**I want** each proof's measured results and unresolved limitations recorded in its governing ADR, the dependency matrix completed, and the open decisions the proofs answer written into the blueprint
**So that** ADR-0040, ADR-0041, ADR-0044, ADR-0049, and ADR-0050 move from Proposed to Accepted or amended before v0.1A starts building on them

## Context & Background

Master blueprint section 115.4 states that proofs are small implementation investigations whose actual results and unresolved limitations must be recorded in ADRs before the respective interfaces are treated as stable. Section 106 sets the decision posture: recommendations become accepted decisions only when their stated tests, owners, and release gates are satisfied. Section 117.1 lists the decisions still owed; items 3 and 4 are answered by these proofs.

## Acceptance Criteria

**Happy Path:**
- **Given** S0003 has run
- **When** ADR-0040 is updated
- **Then** its status is Accepted or Amended, and it records the second-run conversion and OCR counts, the precision levels observed per binding, and any limitation found

- **Given** S0005 has run
- **When** ADR-0041 is updated
- **Then** it records the chosen recorded-interval policy, the concurrency result, and the outbox replay result

- **Given** S0004 has run
- **When** ADR-0044 is updated
- **Then** it records the selected Label Studio edition, the workflow steps proven, the access behavior observed for an out-of-scope reviewer, and the isolation controls required

- **Given** S0006 has run
- **When** ADR-0049 and ADR-0050 are updated
- **Then** they record the verification results, the revocation propagation time, and the policy parity fixture outcome

- **Given** all proofs
- **When** the blueprint is updated
- **Then** BLUEPRINT section 2.1 names the pinned host image, PostgreSQL build, and model-provider data policy, section 4.8 marks section 117.1 items 3 and 4 as answered, and `docker/DEPENDENCY-MATRIX.md` is complete

**Alternative Flows / Edge Cases:**
- A proof fails an acceptance criterion → the ADR records the failure and the interface stays Proposed; the feature cannot close until the owning story is fixed or the limitation is accepted by the operator in writing
- A proof result contradicts a master blueprint statement listed in section 116.1 → the reconciliation is recorded in the ADR and the blueprint section is annotated, never silently changed

## Interaction Contract

N/A — documentation and governance story; no runtime mutation. The ADR status changes are file edits reviewed through the feature's code review.

## Data Requirements

**Required Fields:**
- For each ADR: status, date, measured results table, limitations, references to the harness output paths under the feature run's `artifacts/`
- `docker/DEPENDENCY-MATRIX.md`: every pinned component with version and verification source

**Optional Fields:**
- Follow-up feature references for accepted limitations

**Validation Rules:**
- ADR status changes cite an artifact path that exists in the feature evidence package

## Role-Based Visibility

**Roles that can execute:**
- Platform engineer and architect — author the records; the architect owns the ADR files (agent-map ownership)

**Data Visibility:**
- InternalOnly content: none beyond measured results
- ExternalVisible content: none

## Non-Functional Expectations

- Performance: N/A
- Security: no fixture text or credentials in the recorded results
- Reliability: every recorded number traces to an artifact in the evidence package

## Dependencies

**Depends On:**
- F0001-S0003, F0001-S0004, F0001-S0005, F0001-S0006 — the proofs

**Related Stories:**
- F0002, F0004, F0005, F0008, F0009, F0018, F0022 — consumers of the settled contracts

## Business Rules

1. Proposed decisions become accepted only when their stated tests, owners, and release gates are satisfied (master blueprint section 106).

## Out of Scope

- Settling ADR-0038, ADR-0039, ADR-0042, ADR-0043, ADR-0045 to ADR-0048, ADR-0051 to ADR-0053 (later features)

## UI/UX Notes

- N/A

## Questions & Assumptions

**Open Questions:**
- [ ] None

**Assumptions (to be validated):**
- The operator accepts limitations in writing through the feature's gate-decisions record

## Definition of Done

- [ ] Acceptance criteria met
- [ ] Edge cases handled
- [ ] Permissions enforced (N/A — documentation)
- [ ] Audit/timeline logged (N/A — git history is the record)
- [ ] Tests pass (N/A — documentation; link check passes)
- [ ] Documentation updated
- [ ] Story filename matches `Story ID` prefix
- [ ] Story index regenerated

## Review Provenance

Recorded in `STATUS.md` (Required Signoff Roles, Story Signoff Provenance).
