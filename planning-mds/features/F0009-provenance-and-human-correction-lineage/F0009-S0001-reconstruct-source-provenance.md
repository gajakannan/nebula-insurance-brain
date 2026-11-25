# F0009-S0001 — Reconstruct source provenance

**Story ID:** F0009-S0001
**Feature:** F0009 — Provenance + human-correction lineage
**Title:** Reconstruct source provenance
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Not Started

## User Story

**As a** persistence engineer (Ingrid)
**I want** to retrieve the stored source lineage of an assertion or one exact accepted fact version
**So that** a consumer can explain a belief without confusing an extraction with canonical truth.

## Context & Background

Master blueprint §17 and ADR-0010 require an explanation grounded in stored evidence. F0006 already discovers assertion ancestry for eligibility; this story delivers a consumer-facing internal lineage result rather than replacing that guard.

## Acceptance Criteria

- [ ] **AC1:** Given an attributable v2 assertion with stored evidence, a permitted lineage read returns its assertion identity, origin, interpretation basis, supplied confidence, evidence identities and immutable document/version/artifact identities. Stored block/page/table/cell/span/selector, precision and text-origin metadata are carried at their actual precision.
- [ ] **AC2:** Given an exact canonical version ID, the explanation identifies that version and its slot, its stored evidence references and review-decision reference, and the assertions supporting it. A later version cannot be substituted for a requested historical version.
- [ ] **AC3:** Stored interpretation-run, ontology/profile/contract/model/prompt/parser versions and hashes are preserved when present. Unavailable fields are explicitly unavailable; no value is invented from current configuration, a clock or a model.
- [ ] **AC4:** A direct-evidence explanation and an existing derivation reference remain distinguishable. The service preserves an available derivation/input-version reference; where the derivation producer is undelivered, it reports that limitation and never fabricates document evidence or a complete derivation.
- [ ] **AC5:** A missing reference, cycle or exceeded traversal limit produces an explicit non-complete result or refusal; it cannot be labelled complete. The Architect must specify deterministic limits and result/error categories in Phase B.
- [ ] **AC6:** The reader uses persisted metadata and immutable content; it triggers zero Docling parses, model calls, canonical writes or learning actions. Current-authority checks complete before protected payloads are returned, and the read uses the existing authorization audit.
- [ ] **AC7:** Unknown and inaccessible roots have the same non-disclosing not found outward outcome. A known incomplete legacy root is distinguished from a complete modern explanation only after authorization; S0004 governs every linked resource.

## Edge Cases & Error Scenarios

Missing references, cycles or a traversal-limit refusal cannot report complete lineage (AC5). Unknown/inaccessible roots share the same outward failure (AC7).

## Interaction Contract

N/A — read-only story. Entry is the authorized internal lineage reader selected in Phase B. Completion is a returned, current-authorized result for an exact root or an explicit non-disclosing refusal. No editable state or save action is introduced.

## Data Requirements

Assertion/version root identity; tenant/KB scope; stored evidence and interpretation metadata; explicit completeness and evidence-versus-derivation classification. Root and metadata shapes are designed in Phase B.

Required fields and referential constraints are enforced before effects. Optional legacy metadata stays absent/qualified rather than invented. Persisted source text is not copied into denial output.

## Role-Based Visibility

Use the [PRD role matrix](PRD.md#role-based-access). TenantMember has only scoped read authority; Reviewer adds existing review annotation without canonical commit; ServicePrincipal uses its explicit scoped grants. Unverified, nonmember, cross-tenant/KB and external broker/MGA callers obtain no access. Current parent/classification restrictions apply to each source. Engineering personas confer no runtime role.

## Non-Functional Expectations

Zero unauthorized payload disclosure or partial mutation; zero source reparse/model calls. At least 80% changed executable-code coverage in the later feature run. PostgreSQL proves durable behavior and concurrency where applicable. No unmeasured latency target is asserted. Use existing authorization/decision audit and correlation fields.

## Dependencies

F0006 assertion/evidence contracts; F0008 exact version contract; existing F0002 authority. S0004 supplies the complete traversal-access acceptance suite.

## Out of Scope

A new public provenance/history route; source-authority selection; derivation execution; new extraction metadata producers.

## Questions & Assumptions

No open business-rule question is introduced. The [PRD assumptions](PRD.md#risks--assumptions) require Phase A review; storage, limits, contracts and rollback are explicit Architect decisions for Phase B. Requirements do not grant formal acceptance to a Proposed ADR.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] Permitted assertion and exact-version queries, independently expected metadata, missing/cyclic lineage fixtures and counters proving zero parse/model/write calls.
- [ ] Error scenarios, permission checks and audit/persistence expectations pass.
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.

## Review Provenance

Planning only. No runtime signoff is claimed. The Architect sets the required role matrix in [STATUS.md](STATUS.md) during Phase B; the feature action supplies actual evidence.
