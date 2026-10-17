## Story Header

**Story ID:** F0004-S0003\
**Feature:** F0004 — Content artifact model\
**Title:** Preserve document-date provenance\
**Priority:** Critical\
**Phase:** MVP — v0.1A\
**Status:** Not Started

## User Story

**As a** persistence engineer\
**I want** retain a document date with its source and correction history\
**So that** downstream time interpretation never substitutes receipt time for what the document says.

## Context & Background

The F0004 amendment and ADR-0064 §3 authorize storage of a document's own date with CONTENT, SOURCE_METADATA or HUMAN provenance. Full time-context computation and reviewer UI remain F0016/F0022. See [PRD](PRD.md) for authority, scope and exclusions.

## Acceptance Criteria

- [ ] **F0004-S0003-AC1:** Given an attributable document date from content, source metadata or an authorized human decision, when it is recorded and reloaded, then its date value, source kind, document version, source/decision reference and recorded actor/time remain available together.
- [ ] **F0004-S0003-AC2:** Given an undated document with upload, sync, receipt or extraction timestamps, when its date metadata is read, then document date remains absent; none of those system timestamps is substituted.
- [ ] **F0004-S0003-AC3:** Given a date correction with attributable authority, when the corrected metadata is persisted, then the previous value and basis remain retrievable, the correction links to its predecessor, and the original and parse bundle hashes are unchanged. Updating source metadata does not rewrite an interpretation run's historical basis.
- [ ] **F0004-S0003-AC4:** Given invalid source kinds, missing provenance, cross-owner references or an unverified HUMAN attribution, when a mutation is requested, then it is rejected with an explicit reason, no successful mutation audit, and no lost prior value; authorization decisions remain audited.
- [ ] **F0004-S0003-AC5:** Given the June 1 effective / June 10 issued / June 12 received / June 14 accepted example, when F0004 records the content-sourced document date, then it retains June 10 and its source independently; it neither computes a canonical interval nor changes receipt/acceptance times.
- [ ] **F0004-S0003-AC6:** Given conflicting supplied document dates, when their provenance is stored, then the different candidates/bases remain distinguishable and no undocumented precedence rule selects a date. Resolution beyond an explicit authorized selection is outside F0004.

**Edge Cases & Error Scenarios:** Only relative wording such as “today” with an upload time → no document date. A forged reviewer identity or stale/unauthorized correction → deny without altering history. A partial/coarse source date must not acquire invented day/time precision; the architect must encode its supported representation explicitly.

## Interaction Contract

No UI; the named service handoff is the entry point. Render-only output or an in-memory round-trip cannot satisfy persistence requirements.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Authorized source-metadata ingestion or trusted human-decision handoff; authorized readback | Record attributable date metadata or append a correction | Source metadata only; bundle and previous records immutable | New attributable record with prior basis retained | Reload current and historical metadata and compare unchanged bundle hashes | Verified F0002 principals with current action/resource authority; no new grants |

**Validation and audit:** reject invalid or unauthorized input without altering accepted content or prior history. Record authorization decisions with the existing policy version; successful content/metadata mutations retain actor, timestamp, scope and identity in audit history. Failure never reports a successful mutation. Phase B binds exact interfaces, validation responses and events.

## Data Requirements

Document version/ownership, optional document date and supplied precision, CONTENT/SOURCE_METADATA/HUMAN source, attributable content/system/decision basis, actor and recorded time, correction lineage. No time-mention resolver or canonical valid-time field is implemented by this story.

## Role-Based Visibility

- Existing scoped ServicePrincipal ingestion authority permits the applicable publication handoff only.
- TenantMember/Reviewer reads require current artifact/evidence permission and parent/source restrictions; neither role gains unrestricted writes.
- HUMAN date provenance requires an attributable authorized human decision. All content stays internal and scoped; external broker/MGA access is excluded.

## Non-Functional Expectations

- Reliability: persisted readback after restart; explicit integrity/validation failures; no silent mutation of accepted bytes or provenance.
- Security: current resource authorization before access, immutable ownership and no cross-tenant disclosure.
- Verification: versioned contract checks and integration/negative cases, with at least 80% changed-runtime coverage in the later feature action. No new throughput/latency commitment is introduced.

## Dependencies

F0004-S0001 identity boundary; F0002 verified principal and current scope; F0003 append/history integrity; ADR-0037 and bounded ADR-0064 amendment. F0016 snapshots the interpretation basis; F0022 owns the interactive human workflow.

## Out of Scope

Date extraction model, automatic precedence across conflicting dates, calendar arithmetic, re-resolution scheduling, canonical effective dates, review screen or newly granted edit permission.

## Questions & Assumptions

No unresolved business question. This story uses the existing blueprint and bounded amendments, not broader acceptance of Proposed ADRs. Physical schema, compatibility matrix and interface/error details must be completed in Phase B before architecture approval.

## Definition of Done

- [ ] Every acceptance criterion has actual persisted-output or negative-case evidence.
- [ ] Permissions and audit expectations are verified; invalid input cannot alter prior accepted state.
- [ ] [EX-CONTENT-003](worked-examples.md) has a reproduction command and expected-versus-observed results; synthetic development cases remain outside the frozen holdout.
- [ ] Versioned fixtures validate and affected consumers retain compatibility.
- [ ] Required tests pass and documentation records remaining scope boundaries.
- [ ] Story status/index and append-only signoff provenance are updated in [STATUS](STATUS.md).

## Review Provenance

Implementation signoff belongs in STATUS.md. This planning draft is not runtime completion or reviewer approval.
