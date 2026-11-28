# F0021-S0005 — Log out with upstream revocation and cache hygiene

**Story ID:** F0021-S0005
**Feature:** F0021 — Native React semantic shell + OIDC/session contract and safe re-auth behavior
**Title:** Log out with upstream revocation and cache hygiene
**Priority:** Critical
**Phase:** MVP — v0.1B
**Status:** Not Started

## User Story

**As a** security administrator (Noor)
**I want** sign-out to revoke the session at the identity provider, end it in Nebula, clear what the browser loaded, and tell the user if revocation failed
**So that** "signed out" is true, and nothing from one user's session is shown to the next.

## Context & Background

ADR-0051 D4: logout revokes the server-held refresh token at the IdP and ends the server session; a failure is reported, not hidden by clearing the cookie. D6: query caches and in-flight work are cleared on logout, principal change, tenant switch and relevant grant revision. §119.3 found the CRM revoking a token its browser flow never set.

## Acceptance Criteria

- [ ] **AC1:** "Sign out" sends a CSRF-protected request authenticated by the session cookie; the BFF revokes the session's refresh token at authentik's revocation endpoint (RFC 7009), ends the server session, and clears the session cookie (expired `Set-Cookie` with the same attributes).
- [ ] **AC2:** The token revoked is the one the session actually holds after any rotation (S0003 AC3); after logout, a refresh-token grant with that token fails at authentik.
- [ ] **AC3:** If revocation fails (IdP unreachable, non-2xx, timeout), the server session is still ended and its tokens discarded, the failure is recorded durably in the audit log with the principal and reason, and the signed-out page shows the revocation-failed warning. The response never reports success for a failed revocation.
- [ ] **AC4:** After logout, the old session identifier is rejected with HTTP 401 `unauthenticated` for every route, including when replayed from another client.
- [ ] **AC5:** On logout, principal change (S0001 AC7, S0004 AC5), active knowledge-base switch (S0006 AC4) or a change in the principal's grant revision reported by the session endpoint, the shell aborts in-flight requests and clears all query caches and in-memory resource data before rendering anything for the new state.
- [ ] **AC6:** Other open tabs of the same browser show the signed-out state on their next server call and within 60 seconds of the logout (PM assumption A8), without showing data loaded before the logout.
- [ ] **AC7:** After revocation, the BFF ends the user's IdP session through authentik's end-session endpoint, so the next "Sign in" asks for credentials; if that step fails it is reported the same way as AC3.

## Edge Cases & Error Scenarios

Logout while a renewal is in flight: logout wins and any newly issued tokens are revoked (S0003). Logout with an already-expired session: cookie cleared, signed-out page shown, no revocation attempted for discarded tokens, and the outcome says so. Double-click on "Sign out": one revocation attempt.

## Interaction Contract

Entry: "Sign out" in the shell header or the session-expired dialog's "Discard and sign out". Result: signed-out page with the revocation outcome. Persistence evidence: session record ended; revocation outcome recorded; authentik rejects the revoked refresh token. Audit: a durable record of every logout outcome, including failures (event shape is Phase B).

## Data Requirements

Logout outcome record: principal, session reference (not the cookie value), revocation result, end-session result, timestamp. Grant revision exposed by the session endpoint (S0006).

## Role-Based Visibility

Every signed-in principal can sign out. No data is shown after logout.

## Non-Functional Expectations

Revocation timeout is bounded (Phase B value) so sign-out never hangs. At least 80% changed executable-code coverage in the later feature run.

## Dependencies

S0001, S0003, S0006; authentik revocation and end-session endpoints.

## Out of Scope

Administrator-initiated session termination screens; back-channel logout from the IdP (later hardening, F0026).

## Questions & Assumptions

No open business-rule question. PM assumption A8 is in the [PRD](PRD.md#risks--assumptions). The cross-tab signal mechanism and grant-revision polling interval are Phase B decisions.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] Forced upstream-failure test for AC3 (shared with S0009).
- [ ] Cache-clearing tests for each AC5 trigger.
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.
