# F0021-S0009 — Prove session transport and mutation continuity

**Story ID:** F0021-S0009
**Feature:** F0021 — Native React semantic shell + OIDC/session contract and safe re-auth behavior
**Title:** Prove session transport and mutation continuity
**Priority:** Critical
**Phase:** MVP — v0.1B
**Status:** Not Started

## User Story

**As a** security administrator (Noor)
**I want** the session contract proven in a real browser against the real identity provider, including the failure cases
**So that** ADR-0051 is accepted on observed evidence rather than on assertions that a cookie was cleared.

## Context & Background

ADR-0051's formal acceptance needs master blueprint §121.2 items 8 (session transport) and 9 (mutation continuity) to pass against the real issuance, storage, renewal and logout flow, including an upstream revocation failure. §119.3: test logout with actual issuance, storage and renewal, not only a cookie-clear response. ADR-0049 leaves items 8 and 9 open for F0021.

## Acceptance Criteria

- [ ] **AC1:** An end-to-end suite runs a real browser against the local stack (authentik from the dev blueprint, PostgreSQL, engine, BFF, built shell) and, after sign-in, renewal and logout, inspects cookies, `localStorage`, `sessionStorage`, IndexedDB, Cache Storage, URLs and response bodies: no access, refresh or ID token appears, and the session cookie has the S0001 AC2 attributes.
- [ ] **AC2:** The suite forces access-token expiry and fires at least 20 parallel requests; authentik observes exactly one refresh grant for the session, and the rotated refresh token is the one later revoked at logout.
- [ ] **AC3:** The suite forces an upstream revocation failure (IdP revocation endpoint unreachable or erroring) and observes the server session ended, the failure recorded, and the revocation-failed warning shown; with revocation available, it observes the revoked refresh token rejected by authentik afterwards.
- [ ] **AC4:** In one browser, principal A signs out and principal B signs in (and separately, principal B completes a popup re-authentication on A's page): no data, cache entry or blocked request from A is shown to or sent for B; and every tested malicious return route lands on `/`.
- [ ] **AC5:** Mutation continuity with the rehosted Review Panel: the session is expired while a reviewer has an unsent decision; the decision is not received by the engine until "Submit now"; after re-confirmation the engine checks current item state and authority, and a variant where the item became stale or the grant was revoked during the gap is refused without retry.

## Edge Cases & Error Scenarios

The suite runs from a clean volume and is repeatable; a flaky IdP start is a harness failure, not a pass. Results record the authentik version and, per browser, the browser version and pass/fail; both Chromium and Firefox must pass.

## Interaction Contract

Entry: the proof harness command run by a developer or CI job. Result: a pass/fail report with per-check evidence (storage dumps, IdP event logs, engine audit rows) stored in the feature run's evidence. No product state is changed beyond the disposable local stack.

## Data Requirements

Synthetic principals and review fixtures from the dev blueprint and seed scripts; no real tenant data.

## Role-Based Visibility

Uses synthetic TenantMember and Reviewer principals in two tenants (existing dev blueprint principals plus any Phase B additions).

## Non-Functional Expectations

Deterministic and repeatable from a clean environment; total runtime recorded. Browser matrix for this proof: at least Chromium and Firefox (A1 covers the full support list).

## Dependencies

S0001–S0008; dev authentik blueprint; existing review fixtures (F0001-S0004, F0002).

## Out of Scope

§121.2 items 1–7 and 10–12 beyond what F0001/F0002 already proved (F0018, F0022, F0026); production ingress.

## Questions & Assumptions

No open business-rule question. The end-to-end tool (Playwright is proposed in BLUEPRINT §2.1), how the upstream failure is injected, and how IdP-side refresh grants are counted are Phase B decisions.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] Evidence package contains storage inspections, IdP-side observations and audit rows for each AC.
- [ ] ADR-0051 acceptance is presented to the operator with this evidence (acceptance itself is a separate operator decision).
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.
