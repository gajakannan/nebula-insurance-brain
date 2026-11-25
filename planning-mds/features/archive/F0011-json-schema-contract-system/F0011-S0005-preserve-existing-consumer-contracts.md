# F0011-S0005 — Preserve existing consumer contracts

**Story ID:** F0011-S0005
**Feature:** F0011 — JSON Schema contract system
**Title:** Preserve existing consumer contracts
**Priority:** High
**Phase:** MVP
**Status:** Done

## User Story

**As a** Ingrid the Persistence Engineer
**I want** to adopt the shared contracts at existing validation boundaries without rewriting accepted history
**So that** contract consolidation cannot weaken admission or change a historical answer.

## Context & Background

F0004/F0006 already validate packaged content and assertion schemas; F0007/F0008 ship domain carriers and temporal responses. F0011 must inventory each existing owner and select integration points in Phase B instead of adding a disconnected validation utility.
Source and boundary authority: [PRD](PRD.md), accepted ADR-0013, proposed ADR-0039,
and the shipped contracts cited in the PRD. Phase A requirements are approved; implemented and closed out in feature run 2026-11-22-885e8734.

## Acceptance Criteria

The numbered criteria include happy paths, edge cases and error scenarios.

- [x] **F0011-S0005-AC1:** The integration inventory names every existing in-scope content, assertion/result, FactSlot/answer and temporal-response contract, its consumer entry point, compatibility test and disposition: adopt, delegate to the same published definition, or retain a documented versioned boundary.
- [x] **F0011-S0005-AC2:** Tests enter the actual selected consumer boundaries and prove valid payload acceptance and malformed payload refusal. A standalone parity harness without consumer integration cannot satisfy this story.
- [x] **F0011-S0005-AC3:** The F0006 version dispatcher preserves the legacy result path and explicit v2 path. An unsupported version or failed validation cannot retry through a more permissive reader; disabled v2 support continues to reject v2.
- [x] **F0011-S0005-AC4:** Existing F0007 identity-v1 answers and F0008 temporal metadata retain their declared wire shapes and semantics. Legacy pilot values retain their supported legacy path without fabricated identities, absence scopes or evidence.
- [x] **F0011-S0005-AC5:** Invalid input cannot persist an assertion, canonical version, review decision or partial business mutation through an affected entry point. For a write path, tests query authoritative state after refusal and confirm its established audit/refusal behavior.
- [x] **F0011-S0005-AC6:** Existing tenant/KB, source READ, evidence-admission and atomic commit checks still execute. Positive structural validation never implies authorization, source completeness, semantic acceptance or canonical approval.
- [x] **F0011-S0005-AC7:** The feature requires no reparse or reinterpretation of existing documents and no historical payload rewrite. Any storage change justified in Phase B has an explicit compatibility and rollback proof, with migration numbering after the current 0015 head.

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

Versioned content/assertion/answer/temporal contracts, consumer selectors, historical fixtures and integration dispositions; no new business entity required by Phase A.

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

F0011-S0001–S0004; F0001/F0006 direct prerequisites. Shipped F0004/F0007/F0008 contracts are compatibility inputs; F0009/F0010/F0018 behavior remains owned by those features.

Related stories: the six slices and their order are indexed in [README](README.md).

## Out of Scope

A new canonical commit service, new HTTP routes or grants, a database-backed schema registry required by assumption, legacy data cleanup and changes to extraction activation.

## Questions & Assumptions

No unresolved business question. The Architect must settle the supported subset,
reference/format policy, artifact authority, exact consumer inventory and adapter
mechanism during Phase B without changing the shipped semantics silently.
The boundary between structural validation, domain validation and authorization
is intentional; the PRD governs any apparent conflict.

## Definition of Done

- [x] Every numbered acceptance criterion has observed passing evidence.
- [x] Positive, negative and boundary cases pass through the named real consumers.
- [x] Applicable authorization and audit requirements remain proven.
- [x] Reproducible artifacts and usage documentation are complete.
- [x] Story filename matches Story ID; story index is regenerated when changed.
- [x] Required independent story signoffs are appended to STATUS.md in the feature run.

## Review Provenance

Runtime implementation, test evidence and independent reviewer signoffs are recorded in feature run 2026-11-22-885e8734. See [STATUS](STATUS.md) for the append-only
provenance table; the Architect sets the final required role matrix in Phase B.
