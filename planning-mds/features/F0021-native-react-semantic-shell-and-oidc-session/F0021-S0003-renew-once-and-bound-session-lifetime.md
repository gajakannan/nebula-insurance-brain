# F0021-S0003 — Renew once and bound session lifetime

**Story ID:** F0021-S0003
**Feature:** F0021 — Native React semantic shell + OIDC/session contract and safe re-auth behavior
**Title:** Renew once and bound session lifetime
**Priority:** Critical
**Phase:** MVP — v0.1B
**Status:** Not Started

## User Story

**As a** business reviewer (Rosa)
**I want** my session renewed quietly on the server while I keep working, and ended by the server when I stop
**So that** I am not interrupted every few minutes, and a session I walked away from cannot be used.

## Context & Background

ADR-0051 D1 places renewal on the server; D3 keeps a single coalesced renewal path. §120.5 and §119.5 require timeouts and revocation in the session control plane; an idle-warning modal is UX, not the boundary. Operator decision D1 (2026-11-27): 30-minute idle, 8-hour absolute, warning 2 minutes before idle expiry.

## Acceptance Criteria

- [ ] **AC1:** When the server-held access token is expired or within its renewal margin, the next request triggers a server-side refresh-token grant and then proceeds under the renewed token; the browser sees no redirect and no new cookie value other than an unchanged session identifier.
- [ ] **AC2:** For one session, any number of concurrent requests arriving while renewal is needed cause exactly one upstream refresh call; the other requests wait for its result and then proceed (on success) or all receive `401 session_expired` (on failure). This holds across BFF worker processes.
- [ ] **AC3:** When the IdP returns a rotated refresh token, the new one replaces the old one atomically; a renewal that fails (revoked, expired or invalid refresh token, or IdP unavailable after the bounded retry defined in Phase B) ends the session server-side and records the renewal failure in the authentication audit; further requests are rejected with HTTP 401 `session_expired`.
- [ ] **AC4:** A session with no user-initiated request for 30 minutes is ended by the server; background session-status checks do not extend it (PM assumption A5). A request after that gets `401 session_expired` even if the cookie is still present.
- [ ] **AC5:** A session is ended by the server 8 hours after sign-in regardless of activity or successful renewals; continuing requires a full IdP authentication (S0004), never a silent renewal.
- [ ] **AC6:** At 28 minutes of idle time the shell shows a non-blocking warning with a countdown and a "Stay signed in" action that sends one user-initiated request; dismissing or ignoring the warning does not change the server's idle deadline.

## Edge Cases & Error Scenarios

Clock skew between BFF and IdP: renewal margin and token expiry checks tolerate skew within the verifier's existing leeway. A renewal racing a logout: logout wins and the renewed tokens are discarded and revoked (S0005). A principal disabled after sign-in: the next request is refused as in F0002 (`unauthenticated`), and the session is ended.

## Interaction Contract

Entry: any authenticated request. No user action is needed for renewal. Idle-warning action: "Stay signed in" sends one request; result is the extended idle deadline shown in the status bar. Persistence evidence: session record timestamps (last activity, idle deadline, absolute deadline) observed before and after. Audit: renewal failures and server-ended sessions are recorded (event shape is Phase B).

## Data Requirements

Session last-activity, idle deadline, absolute deadline, renewal lock or equivalent; refresh-token rotation timestamp. Exact mechanisms are Phase B decisions.

## Role-Based Visibility

Applies to every human session equally; no role-specific timeouts in v0.1.

## Non-Functional Expectations

Renewal adds at most one IdP round trip per burst (AC2). Timeouts are configuration values with the D1 defaults. At least 80% changed executable-code coverage in the later feature run.

## Dependencies

S0001 (session), S0004 (what the user sees after `session_expired`), S0005 (logout race).

## Out of Scope

Role- or tenant-specific timeouts; step-up authentication; device binding.

## Questions & Assumptions

No open business-rule question. Operator decision D1 and PM assumption A5 are in the [PRD](PRD.md#risks--assumptions). Renewal margin, lock mechanism and retry bound are Phase B decisions.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] A concurrency test with at least 20 parallel requests proving one upstream refresh (AC2), shared with S0009.
- [ ] Time-controlled tests for idle and absolute expiry (AC4, AC5).
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.
