# Guard mood and described evidence

**Story ID:** F0006-S0004
**Feature:** F0006 — Assertion plane + origin + interpretation basis
**Title:** Guard mood and described evidence
**Priority:** Critical
**Phase:** MVP
**Status:** Done

## User Story

**As a** Rosa the Business Reviewer
**I want** conditional wording and model descriptions to retain their limits
**So that** the system cannot silently treat an offered term or a chart description as an accepted fact.

## Context & Background

The authorized ADR-0065 amendment adds mood and text-origin safeguards. It does not deliver a normative engine, a new review screen or automatic statement classification.

## Acceptance Criteria

- [x] **AC1:** Source-word mood qualifiers round-trip unchanged on both assertion kinds. A supplied mood-bearing claim is ineligible for canonical facts regardless of confidence or fact mode; omitting a future routing engine cannot remove this guard.
- [x] **AC2:** Synthetic subjectivity, offered/quoted limit, warranty and conditional-coverage cases retain the quoted qualifier and cannot assert that the required event happened or the offered coverage is bound. No automatic vocabulary-based mood classifier is introduced.
- [x] **AC3:** An issued policy's operative provision can remain a typed fact about the policy's contractual terms; it does not assert the embedded condition is true about the insured or premises (EX-SEM-007).
- [x] **AC4:** Evidence inherits block text origin and producer provenance from F0004. Described-only support requires `DESCRIBED_EVIDENCE` review and cannot auto-accept, close or supersede a canonical fact; an attempted bypass is rejected without a canonical write (EX-SEM-006).
- [x] **AC5:** `OCR`/`TRANSCRIBED` support is admissible at its actual precision, retaining producer confidence when present. Missing or legacy/unqualified origin is not silently promoted to qualified `STATED`; unresolved provenance retains the existing review requirement.
- [x] **AC6:** Authorized review/consumer hooks retain mood, basis, assertion origin, evidence origin and eligibility reasons on reload, preserving existing review and authorization audit. Unauthorized readers receive no source or excerpt. Open/mood/described guards remain independent: satisfying one does not clear another.

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Authorized assertion/review handoff | Submit evidenced claim with qualifiers | New assertion or existing additive correction only | Preserve claim and restriction/review reason; refuse ineligible canonical use | Scoped consumer query retains qualifiers, origin and review reason | Existing producer/reviewer authority; annotation does not grant canonical approval |

Existing review/audit semantics apply. F0006 supplies the guard/hook contract and protects existing consumers; F0018 owns the full future canonical service and F0022 owns new display. No new normative destination is executed in this feature.

## Data Requirements

Source-word mood; block origin/producer; support evidence set; canonical eligibility and review reason. Assertion origin and evidence text origin are separate dimensions.

## Role-Based Visibility

Existing source/evidence and review authorization applies. No role may bypass the assertion-kind or mood restriction by supplying high confidence; no new grants.

## Non-Functional Expectations

Zero ineligible canonical effects in negative fixtures; original claim/evidence remains inspectable under existing access scope.

## Dependencies

S0001/S0002 retention and S0003 grounding; F0004 origin and legacy fallback; F0002 review/commit authorization. S0005 covers legacy bypass paths. F0052/F0053 future routing and F0022 display remain separate delivery obligations.

## Out of Scope

Mood extraction/classifier, normative/subjectivity/scenario execution, automated acceptance policy and new UI.

## Questions & Assumptions

No open business question. Admission does not infer mood or contract issuance from a word list. Fixtures supply explicit source context; live producers are the owning future features' responsibility.

## Definition of Done

- [x] Six ACs pass including operative-provision and legacy-origin boundaries.
- [x] No consumer bypass grants canonical eligibility.
- [x] Documented hooks, examples, tests and feature signoffs align.

## Completion Evidence

PM verified all criteria and required signoffs in feature run `2026-11-02-5a00b0ff` on 2026-11-05. See [QE acceptance map](../../../operations/evidence/runs/2026-11-02-5a00b0ff/test-execution-report.md), [required signoffs](../../../operations/evidence/runs/2026-11-02-5a00b0ff/signoff-ledger.md), and [STATUS.md](STATUS.md). The SEC-01 trusted-local-fixture restriction and deferred hardening remain in the closeout; this completion does not activate a producer or authorize untrusted/production conversion.
