# F0021-S0006 — Show identity and knowledge-base context in the shell

**Story ID:** F0021-S0006
**Feature:** F0021 — Native React semantic shell + OIDC/session contract and safe re-auth behavior
**Title:** Show identity and knowledge-base context in the shell
**Priority:** High
**Phase:** MVP — v0.1B
**Status:** Not Started

## User Story

**As a** GL underwriter (Priya)
**I want** the shell to show who I am signed in as, which tenants and knowledge bases I can work in, and which one is active
**So that** I always know whose data I am looking at, and switching context never shows me stale data.

## Context & Background

Operator decision D2 (2026-11-27) puts a Home page with identity and current memberships, and an active knowledge-base selector that only narrows, into F0021. F0002 memberships carry tenant, knowledge base, role and grant revision; authorization stays resource-based in the engine. ADR-0051 D6 requires cache clearing on tenant switch and relevant grant revision.

## Acceptance Criteria

- [ ] **AC1:** A signed-in session can read a session endpoint that returns the principal's display name, principal kind, issuer, session idle and absolute deadlines, the CSRF token for state-changing calls, the principal's current (unrevoked) memberships as tenant, knowledge base and role with display names, the current grant revision, and the active knowledge base. It returns no token and no other principal's data.
- [ ] **AC2:** Home shows the display name, the session state, and the membership list with the active knowledge base marked. The shell header shows the display name, the active knowledge-base selector and "Sign out" on every shell route.
- [ ] **AC3:** A principal with no current membership sees Home with a "no access yet" message naming no tenant or knowledge base, an empty selector and "Sign out"; no engine data route is called.
- [ ] **AC4:** Choosing another membership in the selector updates the active knowledge base through a CSRF-protected request, clears caches and in-flight work (S0005 AC5) before rendering, and persists across reload within the session (PM assumption A7). A requested knowledge base that is not a current membership is rejected and the active value is unchanged.
- [ ] **AC5:** The active knowledge base only narrows what the shell asks for. A direct engine request for a resource in another knowledge base that the principal may read is still decided by the engine's existing authorization policy; the selector never grants or denies access by itself.
- [ ] **AC6:** If a membership is revoked while the session is active (the revocation itself is audited by F0002), the next session-endpoint read shows the new grant revision and membership list; if the active knowledge base was revoked, it resets to none and caches are cleared.

## Edge Cases & Error Scenarios

A display name missing from the ID token falls back to the preferred username, then to "Signed-in user"; the subject identifier is never shown as a name. Tenant and knowledge-base display names come from server data, never from token claims. Session endpoint failure: the shell shows a retryable error state, not a signed-out state.

## Interaction Contract

Entry: Home (`/`) and the header selector on every shell route. Editable state: only the active knowledge base. Action: select a membership → CSRF-protected update → caches cleared → views reload. Persistence evidence: the value survives reload and is returned by the session endpoint. Read-only: identity and membership list. Validation failure: a non-member knowledge base is refused with a message, value unchanged. Audit: the active-context change is a session preference, not an authorization event; whether it is recorded is a Phase B decision.

## Data Requirements

Session endpoint response shape (Phase B schema); active knowledge base stored with the session.

## Role-Based Visibility

A principal sees only its own memberships. No role sees another principal's memberships.

## Non-Functional Expectations

WCAG 2.2 AA with zero serious or critical axe violations (A2); desktop and 360-px layouts per the [PRD screen layouts](PRD.md#screen-layouts-ascii); all strings from translation resources (A3). At least 80% changed executable-code coverage in the later feature run.

## Dependencies

S0001, S0005; F0002 membership store.

## Out of Scope

Membership administration, tenant creation, role requests; lists of documents or entities (F0022, F0023).

## Questions & Assumptions

No open business-rule question. Operator decision D2 and PM assumptions A2, A3 and A7 are in the [PRD](PRD.md#risks--assumptions). The session endpoint path and schema are Phase B decisions.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] Component tests for the empty-membership state, selector switch and revocation reset.
- [ ] axe results for Home at desktop and 360-px widths.
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.
