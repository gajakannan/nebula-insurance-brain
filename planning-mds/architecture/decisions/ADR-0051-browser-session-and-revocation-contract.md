# ADR-0051: Browser Session and Revocation Contract

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Decision recorded:** 2026-11-08 by the operator (blueprint requirement-ownership amendment). Features plan against the decision below. The status stays Proposed until the carryover tests below pass.
**Owner:** Architect + Security Reviewer
**Proving feature:** F0021
**Formal acceptance:** master blueprint section 121.2 items 8 (session transport) and 9 (mutation continuity) pass against the real issuance, storage, renewal and logout flow, including an upstream revocation failure.
**Source:** `planning-mds/architecture/master-blueprint.md` sections 119.3, 120.5 and 122

## Context

The CRM reference mixes two session models: an in-memory/HttpOnly-cookie design and browser-direct renewal that serializes tokens into `sessionStorage`. Its logout revokes a refresh token that the browser flow never set (section 119.3). The Brain must choose one model.

## Decision

1. **Same-origin backend-for-frontend (BFF).** The browser holds only an opaque `Secure`, `HttpOnly`, `SameSite` session cookie. The server holds the access and refresh tokens and performs renewal.
2. **CSRF and origin checks** protect every state-changing cookie-authenticated request.
3. **Kept from the CRM:** PKCE and state protection, distinct outcomes for unauthenticated, expired-recoverable and denied requests, a single coalesced renewal path, work-restoration UX, and no automatic replay of approve, promote, retract, publish or external actions after renewal.
4. **Logout revokes upstream.** Logout revokes the server-held refresh token at the identity provider and ends the server session; a failure is reported, not hidden by clearing the cookie.
5. **No browser token storage.** Access and refresh tokens never reach browser storage. The SPA-token alternative is rejected so the two models are never mixed.
6. **Cache hygiene.** Query caches and in-flight work are cleared on logout, principal change, tenant switch and relevant grant revision.

## Consequences

- F0021 implements the BFF routes, cookie and CSRF configuration and the coalesced renewal path.
- The CRM's own session design is not changed by this record.

## References

- `planning-mds/architecture/master-blueprint.md` sections 118 to 123
