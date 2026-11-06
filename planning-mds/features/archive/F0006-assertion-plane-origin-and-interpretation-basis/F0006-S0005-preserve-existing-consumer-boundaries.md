# Preserve existing consumer boundaries

**Story ID:** F0006-S0005
**Feature:** F0006 — Assertion plane + origin + interpretation basis
**Title:** Preserve existing consumer boundaries
**Priority:** Critical
**Phase:** MVP
**Status:** Done

## User Story

**As a** Ingrid the Persistence Engineer
**I want** existing claim and correction history to survive the new assertion contract
**So that** a richer representation does not invalidate prior evidence or bypass established review.

## Context & Background

Existing F0001–F0005 importer, review and pilot commit consumers are real integration obligations. F0005's final rejection decision governs current defaults; older synthetic-proof prose cannot establish pipeline activation.

## Acceptance Criteria

- [x] **AC1:** A pre-change legacy result imports through the existing authorized path and remains readable with the same run/assertion/evidence identities and values. Replay retains its existing idempotence; no duplicate assertions or reviews are produced.
- [x] **AC2:** Legacy `MACHINE_EXTRACTION` and human-correction records retain source provenance and correction links across the compatible origin transition. Unknown legacy details stay unknown; no fabricated quote, predicate release, mood or qualified text origin is inserted.
- [x] **AC3:** Existing Review Panel correction entry and authenticated service preserve additive correction, stale-task refusal, evidence locator and audit behaviour. Authorized review of a legacy fixture still works; no new screen is required.
- [x] **AC4:** Existing pilot commit consumers retain their typed-legacy behaviour but reject unsupported new kinds, mood-bearing assertions and disallowed described-only use before canonical mutation. No new semantics are stripped to fit an old payload.
- [x] **AC5:** Cross-tenant/KB, revoked/unauthorized and malformed-input cases have zero unauthorized claim, correction or canonical effects; existing decision audit and protected-error behaviour remain intact.
- [x] **AC6:** Failure during a claim/evidence/review transaction leaves no partial rows; retry produces one logical import under the existing delivery identity. Migration and rollback instructions preserve already-recorded new semantics or explicitly stop incompatible readers/writers.
- [x] **AC7:** Independently authored synthetic expectations cover typed/open storage, admission reasons, mood, described evidence and operative-policy boundaries, using EX-GL-001 and EX-SEM-001/005–007. Observed runtime outputs, PostgreSQL cases and existing-consumer regression commands are recorded separately from illustrative examples; changed-code coverage is at least 80%. Defaults remain `direct-baseline`/v1 and no physical reparse is introduced.

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Existing importer | Deliver/replay legacy result | Existing authorized import rules | One logical import or atomic rejection | Fresh queries prove stable identities/counts | Existing scoped service principal |
| Existing review/commit boundary | Submit correction or attempt eligible pilot commit | Existing lifecycle/stale checks; new-kind restrictions enforced | Append correction or authorized existing commit; reject ineligible new semantics | Reload source, correction, review/audit and canonical rows | Existing reviewer/approver separation |

Regression tests exercise service entry points and PostgreSQL persistence, including rollback; render-only tests cannot satisfy them. Existing authorization/review/commit audit requirements remain mandatory.

## Data Requirements

Before/after identity and provenance snapshots, versioned fixtures, source-scoped evidence, correction chains, import delivery identity and canonical-effect counts. Do not rewrite archived feature evidence.

## Role-Based Visibility

Use existing verified principals and policy versions. External access and new grants remain excluded; test source/result/error isolation.

## Non-Functional Expectations

Atomic/idempotent integration, append-only provenance, zero reparse, at least 80% changed-code coverage. No new model-quality benchmark is claimed.

## Dependencies

S0001–S0004; delivered F0001–F0005 existing consumers and migrations. F0016/F0018 retain full orchestration ownership; this story protects current consumers without claiming those features complete.

## Out of Scope

Pipeline activation, v2 content-writer enablement, frozen release evaluation, full review-to-canonical orchestration and retroactive qualification of legacy evidence.

## Questions & Assumptions

No open business question. Phase B must enumerate the actual importer, review and pilot commit call sites and define a staged migration/rollback boundary. Planning requirements alone do not prove these tests passed.

## Definition of Done

- [x] Seven ACs pass with observed PostgreSQL and existing-entry-point evidence.
- [x] Structured examples validate; runtime results remain distinct from illustrative expectations.
- [x] Required signoffs are appended in STATUS.md and implementation evidence is captured by the feature action.

## Completion Evidence

PM verified all criteria and required signoffs in feature run `2026-11-02-5a00b0ff` on 2026-11-05. See [QE acceptance map](../../../operations/evidence/runs/2026-11-02-5a00b0ff/test-execution-report.md), [required signoffs](../../../operations/evidence/runs/2026-11-02-5a00b0ff/signoff-ledger.md), and [STATUS.md](STATUS.md). The SEC-01 trusted-local-fixture restriction and deferred hardening remain in the closeout; this completion does not activate a producer or authorize untrusted/production conversion.
