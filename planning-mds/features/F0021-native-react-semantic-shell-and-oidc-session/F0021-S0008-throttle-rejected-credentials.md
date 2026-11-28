# F0021-S0008 — Throttle rejected credentials

**Story ID:** F0021-S0008
**Feature:** F0021 — Native React semantic shell + OIDC/session contract and safe re-auth behavior
**Title:** Throttle rejected credentials
**Priority:** High
**Phase:** MVP — v0.1B
**Status:** Not Started

## User Story

**As a** security administrator (Noor)
**I want** repeated bad credentials from one client throttled before they reach the engine, with one summary record per window
**So that** an attacker cannot grow the audit tables without bound, and I can still see that the attack happened.

## Context & Background

F0002 closeout carry-in (2026-09-28, medium): every unauthenticated or rejected-credential request writes one durable `authentication_event` row; the session/BFF boundary must throttle rejected-credential traffic, proven by a negative test showing bounded growth. Retention is F0026. Operator decision D4 (2026-11-27): 20 per client per 60 s, then `429` with `Retry-After`, no per-request row, one `rate_limited` event per client per window, on both the bearer API and the BFF cookie path.

## Acceptance Criteria

- [ ] **AC1:** For one client address, the first 20 rejected credentials within a 60-second window are answered and recorded exactly as today (generic `401`, one `authentication_event` each).
- [ ] **AC2:** From the 21st rejected credential in that window, the client receives `429` with a `Retry-After` header and a stable `rate_limited` problem code; no credential verification runs and no per-request `authentication_event` row is written. Exactly one `rate_limited` event is recorded for that client and window.
- [ ] **AC3:** A burst of 1,000 rejected credentials from one client within 60 seconds writes at most 21 `authentication_event` rows for that window.
- [ ] **AC4:** While a client is throttled, a request from it with a valid credential or session is still served normally; the throttle counts only rejected credentials, and requests from other clients are unaffected.
- [ ] **AC5:** The rule applies equally to bearer-API requests, cookie-authenticated requests with an unknown or ended session, and sign-in callback failures (S0001 AC4). The client address is the immediate peer, or a forwarded address only from a configured trusted proxy (PM assumption A6).

## Edge Cases & Error Scenarios

A window boundary mid-burst starts a new allowance of 20 plus one summary event. Counter state lost on restart: the allowance resets, which keeps the bound per window. Spoofed `X-Forwarded-For` from an untrusted peer is ignored. The "Too many attempts" page shows for browser sign-in throttling with the wait time.

## Interaction Contract

Entry: any request with a rejected credential. No user action; the result is `429` with `Retry-After`. Persistence evidence: `authentication_event` row counts per window. Audit: per-request events up to the limit, then one `rate_limited` event per client per window.

## Data Requirements

A new `rate_limited` authentication reason (schema change is Phase B); per-client counters with 60-second windows. Counter storage is a Phase B decision.

## Role-Based Visibility

Not role-dependent; applies before principal resolution.

## Non-Functional Expectations

Limit and window are configuration values with D4 defaults. The throttle check adds no database write for throttled requests. At least 80% changed executable-code coverage in the later feature run.

## Dependencies

F0002 `authentication_event` and reasons; S0001, S0002.

## Out of Scope

Retention of `authentication_event` rows (F0026); a global cap across clients; IdP-side lockout policy.

## Questions & Assumptions

No open business-rule question. Operator decision D4 and PM assumption A6 are in the [PRD](PRD.md#risks--assumptions). Counter store and multi-worker consistency are Phase B decisions; the bound in AC3 must hold across workers.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] The AC3 burst test against PostgreSQL, counting rows.
- [ ] Trusted-proxy and untrusted-forwarded-header tests.
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.
