# Check structural admission and evidence

**Story ID:** F0006-S0003
**Feature:** F0006 — Assertion plane + origin + interpretation basis
**Title:** Check structural admission and evidence
**Priority:** Critical
**Phase:** MVP
**Status:** Done

## User Story

**As a** Mateo the Document Intelligence Engineer
**I want** a claim's grounding to be checked against its stored source
**So that** invented quotations and model offsets cannot masquerade as evidence.

## Context & Background

ADR-0065 specifies structural admission; ADR-0058 governs honest evidence precision. F0006 owns the contract and executable checks. F0016 owns durable drop records, counts and run outcomes.

## Acceptance Criteria

- [x] **AC1:** Given the claimed immutable block, admission locates its quote using a documented deterministic normalization. A missing quote yields `QUOTE_NOT_IN_SOURCE` and no admitted assertion. Unicode, whitespace and hyphenation fixtures test the mapping back to original text.
- [x] **AC2:** A name outside its introducing quote yields `NAME_NOT_IN_QUOTE`; a name already claimed by another entity in the same document yields `NAME_CLAIMED_BY_ANOTHER`. No vocabulary word list decides names or silently merges entities.
- [x] **AC3:** Time words outside their assertion quote yield `TIME_NOT_IN_QUOTE`; an unlisted subject yields `UNKNOWN_REFERENCE`. An undeclared object is retained as a literal with `OBJECT_UNDECLARED` signal, not silently dropped.
- [x] **AC4:** Malformed items yield `MALFORMED_ITEM`; truncated output yields `TRUNCATED_OUTPUT` while complete independently valid items remain available; a block with no parsable output yields `BLOCK_UNINTERPRETED`.
- [x] **AC5:** Every reject/signal outcome exposes run/block, reason, model/prompt identity, raw-item hash and an access-controlled excerpt contract for F0016. No outcome is silently lost. Truncation/uninterpreted outcomes explicitly require F0016 PARTIAL/NOT_PROCESSED handling, not COMPLETE/NOT_FOUND.
- [x] **AC6:** Model-provided selectors/offsets confer no authority. The server derives locations against stored content for PDF, DOCX, XLSX and CSV fixtures; repeated text, normalized text and multi-region evidence never invent a unique span. Coarser/unresolved precision remains explicit under ADR-0058.
- [x] **AC7:** A genuine $500,000 quote paired with a misread $5,000,000 value passes grounding, retains the value and reaches the existing semantic review boundary; structural admission does not claim to verify business meaning (EX-SEM-005b).
- [x] **AC8:** Unauthorized block access and cross-tenant/KB references are denied before source inspection/disclosure, preserving existing access-decision audit. Rejected candidates produce no assertion/evidence write; processing performs zero conversion/OCR calls and never creates a canonical fact.

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Authorized interpretation-output admission boundary | Check candidate batch | Immutable source; new candidates only | Return accepted items and explicit reject/signal outcomes | Consumer test observes retained outcomes; rejected items absent from assertion storage | Existing scoped producer; no bypass from supplied offsets |

No new screen. F0006 does not create the F0016 drop table or orchestration. Audit expectations: existing access-decision audit applies; per-item outcomes are the future durable-drop handoff. Tests must exercise the admission service contract, not only its result rendering.

## Data Requirements

Stored original/normalized text mapping, authoritative source locator, candidate refs, protected outcome metadata and explicit precision. Reason vocabulary follows ADR-0065, with `OBJECT_UNDECLARED` distinguished as a signal.

## Role-Based Visibility

Only principals already authorized to the source may access quotes and outcome excerpts. Errors cannot reveal content from another scope.

## Non-Functional Expectations

Deterministic checks, zero model calls for structural admission, zero reparse; no destructive source normalization.

## Dependencies

S0001/S0002 claim contracts; F0002 authorization; F0004 persisted blocks/selectors. F0016 consumes outcomes and owns durable drop/run lifecycle. F0022 displays drops later.

## Out of Scope

Semantic truth verification, model word lists, durable interpretation-drop storage, full-run status transitions and live open extraction.

## Questions & Assumptions

No open business question. Architect must reconcile the case/spacing example EX-SEM-005 with ADR-0065's normalization description, define deterministic ambiguity handling and preserve original selectors. This is a bounded algorithm/contract decision, not permission to fabricate grounding.

## Definition of Done

- [x] Eight ACs pass with positive and negative outcome fixtures and the four native formats.
- [x] All rejection/signal reasons and consumer obligations are documented and observed.
- [x] Feature action records tests, coverage and required signoffs.

## Completion Evidence

PM verified all criteria and required signoffs in feature run `2026-11-02-5a00b0ff` on 2026-11-05. See [QE acceptance map](../../../operations/evidence/runs/2026-11-02-5a00b0ff/test-execution-report.md), [required signoffs](../../../operations/evidence/runs/2026-11-02-5a00b0ff/signoff-ledger.md), and [STATUS.md](STATUS.md). The SEC-01 trusted-local-fixture restriction and deferred hardening remain in the closeout; this completion does not activate a producer or authorize untrusted/production conversion.
