# F0021-S0002 — Protect cookie-authenticated calls with CSRF and origin checks

**Story ID:** F0021-S0002
**Feature:** F0021 — Native React semantic shell + OIDC/session contract and safe re-auth behavior
**Title:** Protect cookie-authenticated calls with CSRF and origin checks
**Priority:** Critical
**Phase:** MVP — v0.1B
**Status:** Not Started

## User Story

**As a** security administrator (Noor)
**I want** every browser call to the engine to be authenticated by the session and every state-changing call to prove it came from the Nebula page
**So that** another site cannot make a signed-in user's browser change anything, and the engine still decides authorization itself.

## Context & Background

ADR-0051 D2 requires CSRF and origin checks on every state-changing cookie-authenticated request. D3 keeps distinct outcomes for unauthenticated, expired-recoverable and denied requests. §120.5: UI guards are convenience only and the backend rejects direct requests; resource existence must not leak where policy requires. ADR-0049's verify-before-read ordering stays.

## Acceptance Criteria

- [ ] **AC1:** A shell call to an existing engine route (`/reviews/*`, `/content/*`, `/facts/*`) with a valid session cookie reaches the route under the session's principal, after the same credential verification and principal resolution as a bearer call; the route handler and its authorization are unchanged.
- [ ] **AC2:** A state-changing request (`POST`, `PUT`, `PATCH`, `DELETE`) authenticated by the session cookie is rejected with HTTP 403 and a stable `csrf_rejected` problem code, before any route handler or storage write runs (the rejection and its cause are recorded in the security audit log), when the CSRF token is missing or does not match the session, or when `Origin` (or `Referer` when `Origin` is absent) is not the shell's own origin, or `Sec-Fetch-Site` is `cross-site`.
- [ ] **AC3:** Safe methods (`GET`, `HEAD`) never change state and are not CSRF-checked; a cookie-authenticated `GET` from a cross-site context is still answered under normal authorization and the response cannot be read cross-origin (no permissive CORS headers are added).
- [ ] **AC4:** Outcomes are distinct and stable: no or unknown session → `401 unauthenticated`; a session past idle or absolute expiry, or whose refresh failed → `401 session_expired` (recoverable through S0004); an authorization denial → `403` with the session kept; a resource the policy hides → the existing non-disclosing `404`. None carries the internal reason.
- [ ] **AC5:** A request that carries both a session cookie and an `Authorization` header is refused with `400 ambiguous_credentials` and no route runs; the shell never sends a bearer token (PM assumption A4).
- [ ] **AC6:** The bearer-token path for non-browser callers behaves exactly as before for every existing route (regression suite unchanged and passing).

## Edge Cases & Error Scenarios

A CSRF token from an earlier session is rejected after re-authentication (tokens are bound to the session). A login-CSRF attempt (attacker-initiated callback) fails S0001 AC4 because the state is not the browser's own. A missing `Origin` and `Referer` on a state-changing request is refused.

## Interaction Contract

Entry: any shell screen calling the engine. Read requests carry the cookie; state-changing requests also carry the CSRF token the shell obtains from the session endpoint. Refusal result: a problem-details response the shell maps to sign-in, the session-expired dialog, an in-context denied message, or not-found. No editable state. Audit: the existing authorization decision audit for engine routes; CSRF refusals are recorded (event shape is Phase B).

## Data Requirements

Per-session CSRF secret; the shell's allowed origin as configuration. Token format and delivery are Phase B decisions.

## Role-Based Visibility

No role change. The engine's existing policy decides every outcome; the BFF adds only authentication and request-integrity checks.

## Non-Functional Expectations

Checks add no extra round trip to the IdP. At least 80% changed executable-code coverage in the later feature run.

## Dependencies

S0001 (session); existing engine routes and problem-details handlers.

## Out of Scope

New routes or grants; CORS for third-party origins; API gateway products.

## Questions & Assumptions

No open business-rule question. Whether the BFF runs in the engine process or as a separate same-origin service is a Phase B decision. PM assumption A4 applies.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] One negative test per AC2 refusal cause, proving no handler ran and no row was written.
- [ ] Existing bearer-path regression suite passes unchanged (AC6).
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.
