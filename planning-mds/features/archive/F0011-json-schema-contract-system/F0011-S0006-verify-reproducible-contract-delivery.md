# F0011-S0006 — Verify reproducible contract delivery

**Story ID:** F0011-S0006
**Feature:** F0011 — JSON Schema contract system
**Title:** Verify reproducible contract delivery
**Priority:** High
**Phase:** MVP
**Status:** Done

## User Story

**As a** Dana the Platform Engineer
**I want** to reproduce and check all published contract artifacts from a clean checkout and installed packages
**So that** downstream ontology and profile features receive a verifiable contract instead of repository-local assumptions.

## Context & Background

F0011 is the head of the contract/ontology dependency lane. Its completion requires executable artifact generation/checking, documented version boundaries and concrete consumer evidence, while F0012/F0015 remain separate feature runs.
Source and boundary authority: [PRD](PRD.md), accepted ADR-0013, proposed ADR-0039,
and the shipped contracts cited in the PRD. Phase A requirements are approved; implementation is in progress in feature run 2026-11-22-885e8734.

## Acceptance Criteria

The numbered criteria include happy paths, edge cases and error scenarios.

- [x] **F0011-S0006-AC1:** A documented command sequence builds or packages the declared schemas and consumer artifacts and runs the complete conformance/integration checks from a clean checkout. The evidence records exact commands, exits, dependency versions and artifact identities.
- [x] **F0011-S0006-AC2:** Repeated generation from identical inputs yields identical contract artifacts. CI refuses stale, missing, hand-modified or reference-incomplete outputs and reports the affected artifact and regeneration command.
- [x] **F0011-S0006-AC3:** An installed Python package and the JavaScript consumer validate the selected bundle outside the source checkout with network schema retrieval disabled. No planning directory, development fixture path or developer-local absolute path is needed in production.
- [x] **F0011-S0006-AC4:** The continuing EX-GL-001 and information-state examples have glossary, boundary-case and owning story/contract links. Structured fixtures validate against their declared local schema; synthetic development data is labeled and kept outside frozen evaluation data.
- [x] **F0011-S0006-AC5:** Feature evidence maps every acceptance criterion to observed results; all required cases pass and changed executable-line coverage is at least 80%. Build/readiness checks cannot be reported as runtime proof or formal acceptance of ADR-0039.
- [x] **F0011-S0006-AC6:** The handoff identifies the supported dialect/subset, annotations, defaults/coercion/ref policy, schema authority, compatible readers, consumer adoption and rollback procedure. ADR-0039 remains Proposed until both its schema and incomplete-package display proof requirements are fulfilled. Generation records an artifact/check audit trail rather than a business timeline mutation.

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

Artifact manifest/check results, command documentation, version inventory, case-to-AC mapping and downstream handoff; completion evidence belongs to the future feature run.

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

F0011-S0001–S0005; existing F0001 build/CI foundation. F0012 can plan alongside this feature but starts implementation after F0011 completes.

Related stories: the six slices and their order are indexed in [README](README.md).

## Out of Scope

Production hosting, ontology release approval, module compatibility reasoning, workbenches, repo-wide feature-evidence audits and claiming all of ADR-0039 accepted.

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

Runtime implementation and test evidence is recorded in feature run 2026-11-22-885e8734; independent reviewer signoff is pending. See [STATUS](STATUS.md) for the append-only
provenance table; the Architect sets the final required role matrix in Phase B.
