# F0021-S0001 — Sign in through the BFF with an opaque session

**Story ID:** F0021-S0001
**Feature:** F0021 — Native React semantic shell + OIDC/session contract and safe re-auth behavior
**Title:** Sign in through the BFF with an opaque session
**Priority:** Critical
**Phase:** MVP — v0.1B
**Status:** Not Started

## User Story

**As a** business reviewer (Rosa)
**I want** to sign in to Nebula through our identity provider and get a session that the server holds for me
**So that** I can work in the browser without any reusable token being stored where a script or a stolen profile could read it.

## Context & Background

ADR-0051 D1 and D5 choose a same-origin BFF: the browser holds only an opaque `Secure`, `HttpOnly`, `SameSite` cookie and the server holds the tokens. D3 keeps the CRM's PKCE and state protection. §118.1 requires the Brain to be a distinct protected resource with an explicit audience; ADR-0049 requires verify-before-read and issuer-namespaced principals. Today the only UI takes a raw bearer token (F0001-S0004).

## Acceptance Criteria

- [ ] **AC1:** Given an unauthenticated browser opens any shell route, the BFF starts an OIDC authorization-code flow against authentik with PKCE (`S256`), a single-use `state` and a `nonce`, and stores the verifier, state, nonce and requested return route server-side only. The browser receives no token and no verifier.
- [ ] **AC2:** On a successful callback, the BFF exchanges the code, verifies the ID token (signature, issuer, audience, expiry, nonce) and the access token through the existing verifier, resolves the stable principal through the F0002 resolver, and creates a server-side session. The response sets exactly one session cookie whose value is an opaque random identifier of at least 128 bits, with `Secure`, `HttpOnly`, `SameSite=Lax` or stricter, `Path=/` and no `Domain` attribute.
- [ ] **AC3:** Access, refresh and ID tokens never appear in a cookie value, a URL, a response body, a response header other than the BFF's own upstream calls, or any browser storage (`localStorage`, `sessionStorage`, IndexedDB, Cache Storage).
- [ ] **AC4:** A callback with a missing, unknown, expired (older than 10 minutes) or already-used `state`, a nonce mismatch, an IdP `error` parameter, or a code exchange failure is rejected: it creates no session, sets no session cookie, writes one `authentication_event` audit row with a specific internal reason, and shows a sign-in failure page with a "Sign in again" action and no internal reason text.
- [ ] **AC5:** After sign-in the browser lands on the requested return route only if it is a same-origin relative path matching a registered shell route; absolute URLs, scheme-relative `//` paths, backslash variants, encoded variants of these and unregistered paths land on `/` instead.
- [ ] **AC6:** A token whose client (`azp`/`client_id`) is not a declared human client, or whose principal is DISABLED, creates no session and lands on the sign-in failure page; the refusal is recorded with its reason.
- [ ] **AC7:** Signing in again in the same browser while a session exists for the same principal replaces the old session (the old identifier is invalid immediately); a different principal ends the old session first and clears all shell caches (S0005 AC5 behavior).

## Edge Cases & Error Scenarios

Two tabs starting sign-in concurrently each get their own `state`; only the completed one creates a session, and the other's callback fails as AC4 (used/unknown state). IdP unreachable at start: a "sign-in unavailable" page with retry and no session. Session-fixation: a cookie value presented before sign-in is never adopted (AC7 issues a fresh identifier).

## Interaction Contract

Entry: any shell route without a valid session, or the "Sign in" / "Sign in again" action. Action: redirect to authentik and back to the BFF callback. Result: session created and redirect to the sanitized return route, or the sign-in failure page. Persistence evidence: a server-side session row/record exists for the principal and the cookie authenticates `GET /session` (S0006). No editable state. Audit: one `authentication_event` per refusal; a success event is a Phase B decision.

## Data Requirements

Session record fields listed in the [PRD](PRD.md#data-requirements); pending-authorization record (state, nonce, PKCE verifier, return route, created-at). Storage and encryption at rest are Phase B decisions.

## Role-Based Visibility

Any verified human USER principal may sign in; a principal with no memberships lands on the Home "no access yet" state (S0006). Service and agent clients cannot create browser sessions. See the [PRD role matrix](PRD.md#role-based-access).

## Non-Functional Expectations

Sign-in completes without client-side token handling. The session identifier comes from a CSPRNG. At least 80% changed executable-code coverage in the later feature run.

## Dependencies

F0002 principal resolver and verifier; authentik dev blueprint (a confidential BFF client is a Phase B change); S0006 for the landing page.

## Out of Scope

Account linking, IdP migration, external users, self-registration; production TLS and ingress (F0026).

## Questions & Assumptions

No open business-rule question. PM assumptions A1 and A4 apply ([PRD](PRD.md#risks--assumptions)). Cookie name/prefix, `SameSite` value, client registration and the local HTTPS profile are Phase B decisions.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] Negative tests for each AC4 failure and each AC5 return-route variant.
- [ ] Browser storage inspection evidence for AC3 (shared with S0009).
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.
