# F0011-S0001 — Resolve versioned offline contracts

**Story ID:** F0011-S0001
**Feature:** F0011 — JSON Schema contract system
**Title:** Resolve versioned offline contracts
**Priority:** High
**Phase:** MVP
**Status:** Done

## User Story

**As a** Dana the Platform Engineer
**I want** to resolve an explicit structural contract version from a reproducible local bundle
**So that** every consumer validates against the intended contract without fetching remote definitions.

## Context & Background

ADR-0013 and master blueprint sections 25–27/112 require one cross-language structural contract. Existing content and assertion packages already have local schema loaders; F0011 must reconcile their ownership and reuse them where appropriate.
Source and boundary authority: [PRD](PRD.md), accepted ADR-0013, proposed ADR-0039,
and the shipped contracts cited in the PRD. Phase A requirements are approved; implemented and closed out in feature run 2026-11-22-885e8734.

## Acceptance Criteria

The numbered criteria include happy paths, edge cases and error scenarios.

- [x] **F0011-S0001-AC1:** Every contract in the Phase B inventory declares JSON Schema Draft 2020-12, a unique immutable identity and an explicit version; the bundle resolves both local fragments and declared inter-schema references without network access.
- [x] **F0011-S0001-AC2:** The inventory identifies the authored source, packaged/generated consumers, owner and version selector for every in-scope contract. Two different schema contents cannot claim the same released identity; a conflicting identity fails bundle validation.
- [x] **F0011-S0001-AC3:** An unknown contract version, unresolved reference, unsupported dialect or unsupported validation keyword produces an explicit failure. None can select a different version, fetch a URL, or silently reduce validation.
- [x] **F0011-S0001-AC4:** The supported keyword/format policy and the treatment of x-nebula annotations are documented and executable. Known annotations survive packaging; annotations alone never grant permission, prove evidence or establish insurance applicability.
- [x] **F0011-S0001-AC5:** Structural validation leaves its input unchanged: it inserts no defaults, coerces no types and removes no unknown properties. A closed object with an undeclared property fails rather than losing that property.
- [x] **F0011-S0001-AC6:** A malformed contract bundle fails before the affected consumer accepts an instance. The diagnostic identifies contract/version and rule location without echoing instance values, source quotes or credentials.
- [x] **F0011-S0001-AC7:** The same pinned bundle produces the same schema identities and reference closure in a fresh process and an installed distribution outside the repository. Planning-only paths are not required at runtime. Artifact publication records version and check evidence; no business audit/timeline event applies to read-only validation.

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

Contract identity/version, dialect, supported keywords/formats, annotation metadata, reference closure and artifact inventory; no tenant business records.

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

F0001 and F0006; reuse existing content/assertion loader behavior. No dependency on the future F0012 ontology vocabulary or F0015 extraction compiler.

Related stories: the six slices and their order are indexed in [README](README.md).

## Out of Scope

Schema authoring UI, remote schema registries, arbitrary user-supplied schema execution, ontology/profile compilation and release activation workflows.

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
