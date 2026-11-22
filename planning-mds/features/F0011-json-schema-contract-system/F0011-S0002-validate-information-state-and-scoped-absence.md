# F0011-S0002 — Validate information state and scoped absence

**Story ID:** F0011-S0002
**Feature:** F0011 — JSON Schema contract system
**Title:** Validate information state and scoped absence
**Priority:** High
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Ingrid the Persistence Engineer
**I want** to validate the shipped state-plus-value answer and the exact scope of an absence
**So that** a missing answer cannot turn into an explicit negative or disclose restricted source material.

## Context & Background

ADR-0039 decisions 1–3 and accepted ADR-0077 already define fact-answer/v1. This story publishes and exercises those structural contracts without redefining the F0007 carrier or the F0008 temporal read state.
Source and boundary authority: [PRD](PRD.md), accepted ADR-0013, proposed ADR-0039,
and the shipped contracts cited in the PRD. Phase A requirements are approved; implementation has not started.

## Acceptance Criteria

The numbered criteria include happy paths, edge cases and error scenarios.

- [ ] **F0011-S0002-AC1:** Shared fixtures include an accepted instance for each of the nine fact-answer/v1 states: PRESENT, NOT_PROCESSED, NOT_FOUND, NOT_STATED, ILLEGIBLE, AMBIGUOUS, CONFLICTING, EXPLICIT_NEGATIVE and NOT_APPLICABLE.
- [ ] **F0011-S0002-AC2:** PRESENT requires a typed value and forbids absence scope. Every other state forbids a value. Missing state, an unknown state, a bare null, PRESENT without value and a non-PRESENT answer with value are rejected.
- [ ] **F0011-S0002-AC3:** NOT_FOUND and NOT_STATED require content_artifact_id, profile_release_ref and at least one nonempty pages or block_ids selection. The published schema preserves the existing page/block bounds, uniqueness constraints and positive page numbering.
- [ ] **F0011-S0002-AC4:** Missing or empty absence selections, duplicate pages/blocks, an invalid artifact identifier and an omitted release reference have explicit failure fixtures. NOT_PROCESSED and NOT_APPLICABLE reject scope as the existing carrier requires.
- [ ] **F0011-S0002-AC5:** The same absence payload never means global absence. Worked and boundary examples distinguish an unsearched source, a searched scope with no statement, an explicit negative, and an expected endorsement that was not supplied.
- [ ] **F0011-S0002-AC6:** ACCESS_DENIED is rejected as an answer state. Existing denied-resource tests continue to return their established non-disclosing response before protected absence metadata is exposed; schema validity cannot bypass READ checks.
- [ ] **F0011-S0002-AC7:** Fixture expectations distinguish structural validity from artifact ownership, source existence, evidence admissibility and temporal validity. F0008 validity-unknown remains a temporal result, not a tenth information state.

## Interaction Contract

No UI. The entry point is the documented contract build/validation command or the
existing consumer named in the Phase B inventory. Reviewed contract sources are
editable in version control; released identities and historical payloads are not
edited in place. Success is a persisted artifact/check result and, for an existing
write consumer, its established transaction result verified by a fresh read.
Validation failure refuses the artifact/input with a non-disclosing diagnostic.
Only repository maintainers publish contract artifacts; runtime callers retain
the existing principal, role, tenant/KB and lifecycle restrictions. Render-only
proof cannot satisfy these criteria. Contract generation has no business timeline
event; existing write/refusal audit behavior remains mandatory where applicable.

## Data Requirements

Existing fact-answer/v1 envelope, typed value reference, absence scope and valid/invalid fixtures; exact scope fields remain those of the shipped contract.

Required versus optional fields and validation rules remain explicit in the
versioned source contract; Phase B identifies the exact definitions and adapters.

## Role-Based Visibility

Internal maintainers execute build/conformance tools. This creates no runtime
permission or grant. Existing authorized consumers retain their access checks;
unauthorized callers receive the established denied/non-disclosing response.
Public diagnostics contain contract/case IDs and rule locations, never protected
payload values, credentials or evidence quotes.

## Non-Functional Expectations

Deterministic, offline reference resolution; no silent case skips or type coercion.
Correctness is 100% of the declared case inventory. Changed executable-line coverage
is at least 80%; this threshold is a feature-run obligation, not a claim of planning coverage.
Errors and edge cases are acceptance criteria above. No end-user latency or
throughput service-level target is introduced by this infrastructure feature.

## Dependencies

F0011-S0001; existing F0007 answer carrier and F0008 temporal contract as compatibility baselines. F0016 later records actual interpretation scopes; F0014/F0023 own package completeness and display.

Related stories: the six slices and their order are indexed in [README](README.md).

## Out of Scope

Inferring source absence, manufacturing negative facts, changing canonical truth, reinterpretation, package-completeness computation and a review/display screen.

## Questions & Assumptions

No unresolved business question. The Architect must settle the supported subset,
reference/format policy, artifact authority, exact consumer inventory and adapter
mechanism during Phase B without changing the shipped semantics silently.
The boundary between structural validation, domain validation and authorization
is intentional; the PRD governs any apparent conflict.

## Definition of Done

- [ ] Every numbered acceptance criterion has observed passing evidence.
- [ ] Positive, negative and boundary cases pass through the named real consumers.
- [ ] Applicable authorization and audit requirements remain proven.
- [ ] Reproducible artifacts and usage documentation are complete.
- [ ] Story filename matches Story ID; story index is regenerated when changed.
- [ ] Required independent story signoffs are appended to STATUS.md in the feature run.

## Review Provenance

No implementation or reviewer signoff yet. See [STATUS](STATUS.md) for the append-only
provenance table; the Architect sets the final required role matrix in Phase B.
