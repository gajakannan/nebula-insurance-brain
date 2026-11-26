# F0012-S0006 — Gate activation with an impact report

**Story ID:** F0012-S0006
**Feature:** F0012 — Foundation ontology
**Title:** Gate activation with an impact report
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Not Started

## User Story

**As a** domain steward (Sameer)
**I want** a predecessor-to-candidate impact report that I review before a release can be activated, and audited activation and rollback
**So that** a change that alters conclusions or tightens a constraint is seen and decided before new work uses it, and history is never rewritten.

## Context & Background

ADR-0045's compatibility and impact gate and master blueprint §112 require a reviewed report that separates dependency reach, inference changes, validation/consumer changes and replayed outcomes, and that keeps unsupported or incomplete analysis unresolved. Operator decision D7 (G1, 2026-11-25) delivers the report and gated activation in F0012; populations with no producer yet are reported as unexamined. EX-ONT-003 and EX-ONT-004 are the worked cases.

## Acceptance Criteria

- [ ] **AC1:** The report names the predecessor and candidate release IDs, manifests and dependency locks, lists every changed term, and assigns each change one class: additive, constraint tightening, rename/alias, semantic change, split, merge or retirement. A change that cannot be classified marks the report incomplete.
- [ ] **AC2:** The report compares the inference closures of both releases over the supported rules (`subClassOf`, `subPropertyOf`, `inverseOf`) restricted to predecessor terms and lists added and removed entailments, with the ruleset and scope stated. An entailment change in a change labelled additive is reported (EX-ONT-003). An analysis that is truncated or unsupported is marked unresolved, never "no change".
- [ ] **AC3:** The report lists, per consumer, constraints that were tightened, loosened, or changed in applicability, stage or data basis, even when the inference closure is unchanged (EX-ONT-004).
- [ ] **AC4:** For the tenant/KB in scope, the report counts affected FactSlots by predicate key and assertions that reference affected predicates, each with its denominator. Populations with no producer yet (profiles and templates, assessments, projections) are listed as unexamined with the reason, never as zero.
- [ ] **AC5:** Activation requires a reviewed report bound to the exact predecessor and candidate digests, with reviewer identity, decision and time, and an explicit activation grant. Activation without a report, with a report for other digests, or with a report containing unresolved items is rejected with a typed reason and audited as a denial. A first release with no predecessor has a report that says so.
- [ ] **AC6:** Activation and rollback are append-only, audited selections of the release used for future work in a tenant/KB. Rollback selects an earlier installed release; neither changes release contents nor the release reference on existing slots, versions or assertions. A fresh-session query returns the full selection history in order.
- [ ] **AC7:** For a split of a foundation concept (§112 acceptance), the report lists the affected predicates, FactSlots and assertions; after activation, reads of existing data still resolve the original release; after rollback, new work uses the earlier release and both releases and their selections remain.

## Edge Cases & Error Scenarios

Two concurrent activations for one tenant/KB produce exactly one current selection and one refusal (no lost update). A report whose candidate digest no longer matches the installed release is refused at activation. An activation denied for missing grant is audited.

## Interaction Contract

Entry points: a report command (read-only over installed releases and scoped data), a review-recording command and an activation/rollback command, each acting as an authenticated principal. Activation is allowed only for an installed candidate with a matching reviewed report and the activation grant. Success appends one selection row; proof is a fresh-session selection-history query. Every decision, including denials, writes an audit record. Report generation writes nothing to canonical data.

## Data Requirements

Report content (release IDs, digests, change classes, closure diff, constraint diff, reach counts with denominators, unexamined populations, unresolved items), review record (reviewer, decision, time, bound digests), append-only activation/rollback selections per tenant/KB. Storage, report format and the grant names are Phase B decisions.

## Role-Based Visibility

Report generation needs authorization for scoped read of the data it counts; recording a review and activating need explicit grants named in Phase B, checked by the existing authorization service. Counts never reveal data outside the principal's scope. See the [PRD role matrix](PRD.md#role-based-access).

## Non-Functional Expectations

Deterministic report for the same inputs. PostgreSQL proves concurrent activation and append-only selection. Report generation time is measured and recorded. At least 80% changed executable-code coverage in the later feature run.

## Dependencies

S0002 change records; S0004 installed releases; S0005 predicate keys for reach; existing F0002 authority and audit.

## Out of Scope

Replaying stored assessments (F0065, reported as unexamined); conservative-extension proof beyond the supported subset (F0030/F0062); reinterpretation of existing documents (F0016); projection rebuild (F0034).

## Questions & Assumptions

No open business-rule question. Operator decision D7 and PM assumption A1 are in the [PRD](PRD.md#risks--assumptions). Whether reviewer and activator may be the same principal is a Phase B decision recorded with the grant design.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] EX-ONT-003/004 fixtures, split scenario, unresolved-analysis fixture, concurrent activation, rollback history query, audit queries.
- [ ] Error scenarios, permission checks and persistence expectations pass.
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.

## Review Provenance

Planning only. No runtime signoff is claimed. The Architect sets the required role matrix in [STATUS.md](STATUS.md) during Phase B; the feature action supplies actual evidence.
