# F0021 — Native React semantic shell + OIDC/session contract and safe re-auth behavior

**Status:** Planned
**Phase:** v0.1B
**Roadmap:** Later

## Overview

The native React semantic shell with the OIDC session contract and safe re-auth behavior is the first user-facing surface (section 3, 120.5).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0036](../../architecture/decisions/ADR-0036-nebula-keeps-a-native-semantic-ux-onyx-is-a-reference-implementation.md), [ADR-0049](../../architecture/decisions/ADR-0049-shared-identity-and-verified-principal-boundary.md), [ADR-0051](../../architecture/decisions/ADR-0051-browser-session-and-revocation-contract.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0021.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## F0002 closeout carry-in (2026-09-28)

F0002 (tenancy-aware AuthX kernel) closed with one recommendation assigned to this feature. It is recorded in the [F0002 security review](../../operations/evidence/runs/2026-09-27-bb7c8d1d/security-review-report.md) and accepted as deferred in the [F0002 PM closeout](../../operations/evidence/runs/2026-09-27-bb7c8d1d/pm-closeout.md). Carry it into this feature's PRD and stories when the feature is planned. The feature status is unchanged.

- **[medium] Rate-limit rejected credentials at the BFF/edge.** Since F0002, every unauthenticated or rejected-credential request writes one durable `authentication_event` row (null principal, route template, reason, no token). Without edge rate limiting, this lets an attacker amplify storage. The session/BFF boundary this feature introduces must throttle rejected-credential traffic before it reaches the engine. Acceptance evidence is a negative test showing that a burst of bad credentials produces bounded `authentication_event` growth. Retention of those rows belongs to F0026.

## Graph Observatory carry-in (2026-10-13)

[ADR-0072](../../architecture/decisions/ADR-0072-observatory-is-a-read-only-projection.md) (Proposed) governs this planned work. Carry these requirements into the PRD; the feature status is unchanged. Design: [design note section 10](../../architecture/graph-observatory-design.md#10-delivery-approach-carry-the-contract-in-now-land-the-observatory-in-v02b). The scoped Observatory is [F0067](../F0067-graph-observatory/README.md).

- Provide a route-level feature flag and lazy-loading seam, so a heavy view such as F0067 can load on demand without growing the base bundle.
- State management, server-state caching and styling are app-wide choices made here; F0067 inherits them and adds only rendering dependencies.
- **No new v0.1 scope** beyond the seam: no Observatory dependency enters v0.1.
