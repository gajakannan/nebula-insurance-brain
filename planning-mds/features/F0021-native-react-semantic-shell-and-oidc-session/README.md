# F0021 — Native React semantic shell + OIDC/session contract and safe re-auth behavior

**Status:** Planned — Phase A approved 2026-11-27 (plan run `2026-11-27-6cda122a`); Phase B approved 2026-11-27 (`approve-phase-b`); plan-review CONDITIONALLY READY; Phase A and B rework approved 2026-11-28 (rework run `2026-11-28-831962b8`); next: feature run
**Phase:** v0.1B
**Roadmap:** Now (2026-11-20 roadmap review; pulled forward from Later on 2026-11-10)

## Overview

The native React semantic shell with the OIDC session contract and safe re-auth behavior is the first user-facing surface (section 3, 120.5).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0036](../../architecture/decisions/ADR-0036-nebula-keeps-a-native-semantic-ux-onyx-is-a-reference-implementation.md), [ADR-0049](../../architecture/decisions/ADR-0049-shared-identity-and-verified-principal-boundary.md), [ADR-0051](../../architecture/decisions/ADR-0051-browser-session-and-revocation-contract.md).

## Requirement-ownership amendment (2026-11-08)

The 2026-11-08 review of the master blueprint against the feature portfolio assigned these requirements to this feature (master blueprint section 106.3). Carry them into the PRD and stories when the feature is planned; the feature status is unchanged.

- **Dependencies:** F0002 (previously F0001).
- ADR-0051 decision recorded 2026-11-08 - same-origin BFF with an opaque HttpOnly session cookie, server-held tokens and renewal, CSRF and origin checks, and upstream revocation on logout. No browser token storage. Formal acceptance needs section 121.2 items 8 and 9.

## Documents

- [PRD](PRD.md) — scope, operator decisions D1–D4, PM assumptions A1–A8, screens
- [Personas](personas.md)
- [Acceptance criteria checklist](acceptance-criteria-checklist.md) — 55 ACs
- [STATUS](STATUS.md)
- [Feature assembly plan](feature-assembly-plan.md) — build order, reconciliation R1–R7, AC-to-proof map
- [GETTING-STARTED](GETTING-STARTED.md)
- [BFF API design](bff-api-design.yaml), [migration design](migration-design.sql), [contract inventory](contract-inventory.yaml)
- Governing design: proposed [ADR-0082](../../architecture/decisions/ADR-0082-bff-session-runtime-and-shell-foundation.md), refining [ADR-0051](../../architecture/decisions/ADR-0051-browser-session-and-revocation-contract.md)
- The feature shard is `planning-mds/kg-source/features/F0021.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|
| [F0021-S0001](F0021-S0001-sign-in-through-the-bff-with-an-opaque-session.md) | Sign in through the BFF with an opaque session | Not Started |
| [F0021-S0002](F0021-S0002-protect-cookie-authenticated-calls-with-csrf-and-origin-checks.md) | Protect cookie-authenticated calls with CSRF and origin checks | Not Started |
| [F0021-S0003](F0021-S0003-renew-once-and-bound-session-lifetime.md) | Renew once and bound session lifetime | Not Started |
| [F0021-S0004](F0021-S0004-re-authenticate-without-losing-work-or-replaying-mutations.md) | Re-authenticate without losing work or replaying mutations | Not Started |
| [F0021-S0005](F0021-S0005-log-out-with-upstream-revocation-and-cache-hygiene.md) | Log out with upstream revocation and cache hygiene | Not Started |
| [F0021-S0006](F0021-S0006-show-identity-and-knowledge-base-context-in-the-shell.md) | Show identity and knowledge-base context in the shell | Not Started |
| [F0021-S0007](F0021-S0007-provide-the-route-seam-and-rehost-the-review-panel.md) | Provide the route seam and rehost the review panel | Not Started |
| [F0021-S0008](F0021-S0008-throttle-rejected-credentials.md) | Throttle rejected credentials | Not Started |
| [F0021-S0009](F0021-S0009-prove-session-transport-and-mutation-continuity.md) | Prove session transport and mutation continuity | Not Started |

**Total Stories:** 9

## F0002 closeout carry-in (2026-09-28)

F0002 (tenancy-aware AuthX kernel) closed with one recommendation assigned to this feature. It is recorded in the [F0002 security review](../../operations/evidence/runs/2026-09-27-bb7c8d1d/security-review-report.md) and accepted as deferred in the [F0002 PM closeout](../../operations/evidence/runs/2026-09-27-bb7c8d1d/pm-closeout.md). Carry it into this feature's PRD and stories when the feature is planned. The feature status is unchanged.

- **[medium] Rate-limit rejected credentials at the BFF/edge.** Since F0002, every unauthenticated or rejected-credential request writes one durable `authentication_event` row (null principal, route template, reason, no token). Without edge rate limiting, this lets an attacker amplify storage. The session/BFF boundary this feature introduces must throttle rejected-credential traffic before it reaches the engine. Acceptance evidence is a negative test showing that a burst of bad credentials produces bounded `authentication_event` growth. Retention of those rows belongs to F0026.

## Graph Observatory carry-in (2026-10-13)

[ADR-0072](../../architecture/decisions/ADR-0072-observatory-is-a-read-only-projection.md) (Proposed) governs this planned work. Carry these requirements into the PRD; the feature status is unchanged. Design: [design note section 10](../../architecture/graph-observatory-design.md#10-delivery-approach-carry-the-contract-in-now-land-the-observatory-in-v02b). The scoped Observatory is [F0067](../F0067-graph-observatory/README.md).

- Provide a route-level feature flag and lazy-loading seam, so a heavy view such as F0067 can load on demand without growing the base bundle.
- State management, server-state caching and styling are app-wide choices made here; F0067 inherits them and adds only rendering dependencies.
- **No new v0.1 scope** beyond the seam: no Observatory dependency enters v0.1.
