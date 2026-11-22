# F0011-S0004 — Prove cross-language contract conformance

**Story ID:** F0011-S0004
**Feature:** F0011 — JSON Schema contract system
**Title:** Prove cross-language contract conformance
**Priority:** High
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Dana the Platform Engineer
**I want** to run identical structural cases through every supported client and server adapter
**So that** client and server cannot disagree silently about a supported wire payload.

## Context & Background

Master blueprint sections 25–27, 98 and 112 require Python/AJV parity, Pydantic conformance and a defined schema subset. AJV is absent from the current experience package; the future feature run must add a runnable conformance consumer.
Source and boundary authority: [PRD](PRD.md), accepted ADR-0013, proposed ADR-0039,
and the shipped contracts cited in the PRD. Phase A requirements are approved; implementation has not started.

## Acceptance Criteria

The numbered criteria include happy paths, edge cases and error scenarios.

- [ ] **F0011-S0004-AC1:** One shared case inventory runs through the Python JSON Schema validator, the Pydantic adapter and headless AJV. Every case declares contract/version, input and expected structural acceptance; no runner substitutes a mock for one of these consumers.
- [ ] **F0011-S0004-AC2:** The inventory covers every supported validation keyword and format, reference resolution, composition and conditional branches used by the selected contracts. Tests include an accepting case and a rejecting case for each validation behavior.
- [ ] **F0011-S0004-AC3:** All runners match the expected accept/reject result on 100% of cases. A runner crash, missing dependency, unsupported format, unresolved reference, skipped case or missing result fails conformance.
- [ ] **F0011-S0004-AC4:** Pydantic model generation/adaptation and serialization are demonstrated on the selected contracts. A Python-accepted instance serializes to schema-valid JSON without extra fields, dropped required values or lost monetary precision; input validation performs no implicit coercion.
- [ ] **F0011-S0004-AC5:** OpenAPI references the same published definitions for in-scope components. A contract check resolves and validates those references against the bundle; independently maintained copies or incompatible schema dialect translation fail the drift check.
- [ ] **F0011-S0004-AC6:** Custom x-nebula annotations and declared UI metadata are retained across the selected contract outputs, with an explicit unsupported-annotation policy. Metadata cannot be evaluated as structural validation, policy authorization or evidence verification.
- [ ] **F0011-S0004-AC7:** A deliberate mutation of one packaged schema, one expected result or one generated consumer is detected. Results record case ID, contract version and consumer versions without exposing protected instance content.

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

Shared valid/invalid cases, consumer/version inventory, generated/adapted Pydantic models, OpenAPI references and declared annotation/UI metadata.

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

F0011-S0001–S0003. F0021 is not a prerequisite: the JavaScript proof is headless and creates no React screen.

Related stories: the six slices and their order are indexed in [README](README.md).

## Out of Scope

Schema-driven form UI, ontology inference, extraction prompts, browser UX and extending every future contract before its owning feature is planned.

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
