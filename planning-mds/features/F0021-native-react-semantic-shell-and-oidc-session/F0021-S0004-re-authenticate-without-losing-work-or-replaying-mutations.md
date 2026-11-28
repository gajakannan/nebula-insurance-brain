# F0021-S0004 — Re-authenticate without losing work or replaying mutations

**Story ID:** F0021-S0004
**Feature:** F0021 — Native React semantic shell + OIDC/session contract and safe re-auth behavior
**Title:** Re-authenticate without losing work or replaying mutations
**Priority:** Critical
**Phase:** MVP — v0.1B
**Status:** Not Started

## User Story

**As a** business reviewer (Rosa)
**I want** to sign in again in place when my session ends, keep what I was doing, and decide myself whether a blocked decision is sent
**So that** an expired session never costs me my work and never submits a decision on my behalf.

## Context & Background

ADR-0051 D3 keeps work-restoration UX and forbids automatic replay of approve, promote, retract, publish or external actions after renewal. §121.2 item 9: a re-confirmed request checks the current fact revision and authority. §119.5: restores are keyed by principal and tenant/KB context; browser storage does not protect drafts. Operator decision D3 (2026-11-27): popup re-authentication keeps in-memory work; redirect fallback restores only the sanitized route.

## Acceptance Criteria

- [ ] **AC1:** When any call returns `401 session_expired`, the shell keeps the current page and its unsaved in-memory input, shows the session-expired dialog, and lists each blocked state-changing request by a human-readable label as "not submitted". No state-changing request is retried.
- [ ] **AC2:** "Sign in again" opens the IdP sign-in in a popup through the BFF (S0001 flow). On success the popup closes, the page receives only a completion signal (never a token or code), and the dialog closes with the page and its input unchanged.
- [ ] **AC3:** After re-authentication, a blocked read (`GET`) is retried once automatically; each blocked state-changing request is shown in the re-confirmation dialog and is sent only when the user chooses "Submit now". "Cancel" discards it and keeps the page input.
- [ ] **AC4:** A re-confirmed request is a new request: it carries the new session's CSRF token and the engine re-checks current authority and current resource revision; a stale item or a lost grant is rejected with the engine's existing denied or not found response, which the shell shows in context without retrying; the engine's existing audit records the re-confirmed request like any other.
- [ ] **AC5:** If the re-authenticated principal differs from the one that owned the page, the shell discards all in-memory work and blocked requests, clears caches (S0005 AC5) and lands on Home; nothing from the previous principal is shown or sent.
- [ ] **AC6:** If the popup is blocked or closed without completing, the dialog offers "Sign in on this page", which performs a full redirect sign-in and returns to the sanitized current route (S0001 AC5); the dialog states beforehand that unsaved input will be lost, and no input is written to browser storage.
- [ ] **AC7:** The popup completion signal is accepted only from the shell's own origin and only for the pending re-authentication it started; any other message is ignored.

## Edge Cases & Error Scenarios

Several tabs expired at once: each tab shows its own dialog; completing sign-in in one tab lets the others continue after their own "Sign in again" or on their next call (the session cookie is shared). The user dismisses the dialog: the page stays read-only for engine calls until signed in. Absolute-lifetime expiry (S0003 AC5) uses the same dialog.

## Interaction Contract

Entry: any `401 session_expired` response while on a shell page. Actions: "Sign in again" (popup), "Sign in on this page" (redirect), "Discard and sign out", then per blocked mutation "Submit now" or "Cancel". Result: page resumes with input intact, or a sanitized-route reload. Persistence evidence: the re-confirmed mutation's engine response and its existing audit row; the blocked attempt has no engine-side effect. Read-only behavior: blocked reads retry once; blocked mutations never retry without the explicit action. Audit: the re-confirmed request is audited as a normal request.

## Data Requirements

In-memory list of blocked requests with label, method, route and body, held only in page memory. No browser storage.

## Role-Based Visibility

Applies to every signed-in principal; the engine's existing authority decides the re-confirmed request.

## Non-Functional Expectations

No automatic replay of any state-changing request under any timing. At least 80% changed executable-code coverage in the later feature run; component and end-to-end tests cover AC1–AC7.

## Dependencies

S0001, S0002, S0003; S0007 (the Review Panel decision submission is the reference mutation); S0009 proves AC3–AC5 against real authentik.

## Out of Scope

An idempotent command protocol for controlled retry (§120.5 later work); draft persistence across reloads.

## Questions & Assumptions

No open business-rule question. Operator decision D3 is in the [PRD](PRD.md#risks--assumptions). The popup messaging mechanism and blocked-request queue design are Phase B decisions.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] Negative test proving zero engine-side effects from a blocked mutation until "Submit now".
- [ ] Principal-change test (AC5) and popup-blocked fallback test (AC6).
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.
