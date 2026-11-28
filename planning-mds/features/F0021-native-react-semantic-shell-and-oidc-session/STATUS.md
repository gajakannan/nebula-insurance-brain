# F0021 — Native React semantic shell + OIDC/session contract and safe re-auth behavior — Status

**Overall Status:** Planned — Phase A and Phase B approved; plan-review next
**Last Updated:** 2026-11-27
**Plan Run:** `2026-11-27-6cda122a` (A+B, new)
**Phase A:** Approved 2026-11-27 (`approve-phase-a`)
**Phase B:** Approved 2026-11-27 (`approve-phase-b`, confirming R1 and R2); design in [assembly plan](feature-assembly-plan.md) and proposed [ADR-0082](../../architecture/decisions/ADR-0082-bff-session-runtime-and-shell-foundation.md)
**Implementation:** Not started

## Story Checklist

| Story | Title | Status |
|---|---|---|
| F0021-S0001 | [Sign in through the BFF with an opaque session](F0021-S0001-sign-in-through-the-bff-with-an-opaque-session.md) | Not Started |
| F0021-S0002 | [Protect cookie-authenticated calls with CSRF and origin checks](F0021-S0002-protect-cookie-authenticated-calls-with-csrf-and-origin-checks.md) | Not Started |
| F0021-S0003 | [Renew once and bound session lifetime](F0021-S0003-renew-once-and-bound-session-lifetime.md) | Not Started |
| F0021-S0004 | [Re-authenticate without losing work or replaying mutations](F0021-S0004-re-authenticate-without-losing-work-or-replaying-mutations.md) | Not Started |
| F0021-S0005 | [Log out with upstream revocation and cache hygiene](F0021-S0005-log-out-with-upstream-revocation-and-cache-hygiene.md) | Not Started |
| F0021-S0006 | [Show identity and knowledge-base context in the shell](F0021-S0006-show-identity-and-knowledge-base-context-in-the-shell.md) | Not Started |
| F0021-S0007 | [Provide the route seam and rehost the review panel](F0021-S0007-provide-the-route-seam-and-rehost-the-review-panel.md) | Not Started |
| F0021-S0008 | [Throttle rejected credentials](F0021-S0008-throttle-rejected-credentials.md) | Not Started |
| F0021-S0009 | [Prove session transport and mutation continuity](F0021-S0009-prove-session-transport-and-mutation-continuity.md) | Not Started |

## Story × Role Progress

Cells: not-started / in-progress / done / not-in-scope; review columns resolve to PASS/FAIL in the feature action. No AI/model scope.

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|---|---|---|---|---|---|---|---|---|
| F0021-S0001 | not-started | not-started | not-in-scope | not-started | - | - | not-started | Not Started |
| F0021-S0002 | not-started | not-started | not-in-scope | not-started | - | - | not-in-scope | Not Started |
| F0021-S0003 | not-started | not-started | not-in-scope | not-started | - | - | not-in-scope | Not Started |
| F0021-S0004 | not-in-scope | not-started | not-in-scope | not-started | - | - | not-in-scope | Not Started |
| F0021-S0005 | not-started | not-started | not-in-scope | not-started | - | - | not-in-scope | Not Started |
| F0021-S0006 | not-started | not-started | not-in-scope | not-started | - | - | not-in-scope | Not Started |
| F0021-S0007 | not-in-scope | not-started | not-in-scope | not-started | - | - | not-started | Not Started |
| F0021-S0008 | not-started | not-started | not-in-scope | not-started | - | - | not-in-scope | Not Started |
| F0021-S0009 | not-started | not-started | not-in-scope | not-started | - | - | not-started | Not Started |

## Backend Progress

- [ ] BFF sign-in, session store and cookie (S0001)
- [ ] CSRF/origin checks and outcome taxonomy (S0002)
- [ ] Coalesced renewal and server-enforced session bounds (S0003)
- [ ] Logout with upstream revocation and end-session (S0005)
- [ ] Session endpoint with memberships, active knowledge base and flags (S0006, S0007)
- [ ] Rejected-credential throttling (S0008)

## Frontend Progress

- [ ] Shell frame, Home, selector and error screens (S0006)
- [ ] Session-expired dialog, popup re-auth and re-confirmation (S0004)
- [ ] Cache hygiene on every trigger (S0005)
- [ ] Route/flag/lazy-load seam and rehosted Review Panel (S0007)

## Cross-Cutting

- [ ] Real-browser proof of §121.2 items 8 and 9 (S0009)
- [ ] WCAG 2.2 AA, zero serious/critical axe violations (A2)
- [ ] At least 80% changed executable-code coverage

## Required Signoff Roles

Quality Engineer, Code Reviewer, Security Reviewer, DevOps, Architect (set at feature G0).

## Story Signoff Provenance

Appended by the feature action. Append-only.

| Story | Role | Verdict | Run | Date |
|---|---|---|---|---|
