# F0011-S0003 — Validate qualified money and scoped identifiers

**Story ID:** F0011-S0003
**Feature:** F0011 — JSON Schema contract system
**Title:** Validate qualified money and scoped identifiers
**Priority:** High
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Ingrid the Persistence Engineer
**I want** to share structural definitions for exact money and namespace-qualified identifiers
**So that** Python and JavaScript preserve the same amount and identity instead of introducing float or namespace errors.

## Context & Background

ADR-0039 decisions 4–5 and ADR-0077 define the existing typed value shapes in fact-slot-key-v1. F0011 owns publication and failure fixtures; F0013 owns GL predicate meaning and F0017 owns enterprise resolution.
Source and boundary authority: [PRD](PRD.md), accepted ADR-0013, proposed ADR-0039,
and the shipped contracts cited in the PRD. Phase A requirements are approved; implementation has not started.

## Acceptance Criteria

The numbered criteria include happy paths, edge cases and error scenarios.

- [ ] **F0011-S0003-AC1:** The money definition retains type=money, an exact decimal string amount, uppercase three-letter currency and the existing optional basis. The existing accepted scientific-notation and length behavior is preserved; binary floating-point conversion is never used for authoritative money.
- [ ] **F0011-S0003-AC2:** Fixtures accept exact fractional and large decimal amounts and reject numeric JSON amounts, null, NaN/Infinity tokens, malformed decimal strings, missing currency and an invalid currency shape. Round trips retain decimal precision and original currency.
- [ ] **F0011-S0003-AC3:** Basis-required behavior is tested at the existing predicate-aware domain boundary. A schema-valid amount with the wrong basis or an unsupported currency code is not reported as semantically accepted merely because its shape is valid.
- [ ] **F0011-S0003-AC4:** The identifier definition requires type=identifier, scheme, identifier_type and value, preserving the shipped length/pattern limits and optional effective interval. Missing scheme/type/value and invalid effective-date formats have failure fixtures.
- [ ] **F0011-S0003-AC5:** Two identifiers with the same value under different schemes or identifier types remain distinguishable after each adapter round trip. No structural validator merges entities or infers uniqueness from a name, address or identifier string.
- [ ] **F0011-S0003-AC6:** Server-computed normalized_value and optional effective interval behavior remain compatible with F0007. Fixtures separate structural checks from normalization correctness and interval ordering, which stay with the existing domain validator.
- [ ] **F0011-S0003-AC7:** At least one fixture per money/identifier boundary names its expected structural result and, where different, its domain result. Converted money without a supported provenance contract and an unqualified bare identifier cannot pass as the published typed carrier.

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

Existing money_value and identifier_value definitions, amount/currency/basis, scheme/type/value, optional normalization/effective interval and synthetic fixtures.

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

F0011-S0001; accepted F0007/ADR-0077 behavior. F0013 applies GL qualifiers, F0017 resolves identities, F0065 later compares qualified GL money.

Related stories: the six slices and their order are indexed in [README](README.md).

## Out of Scope

Currency conversion, exchange-rate feeds, universal financial formulas, new identifier schemes, GL ontology authoring and probabilistic/deterministic entity resolution.

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
