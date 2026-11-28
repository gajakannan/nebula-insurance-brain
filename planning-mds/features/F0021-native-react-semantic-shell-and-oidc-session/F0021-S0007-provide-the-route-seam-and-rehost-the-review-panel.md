# F0021-S0007 — Provide the route seam and rehost the review panel

**Story ID:** F0021-S0007
**Feature:** F0021 — Native React semantic shell + OIDC/session contract and safe re-auth behavior
**Title:** Provide the route seam and rehost the review panel
**Priority:** High
**Phase:** MVP — v0.1B
**Status:** Not Started

## User Story

**As a** platform engineer (Dana)
**I want** one place where later screens register a route, a feature flag and a lazily loaded module, and the existing Review Panel moved onto it behind the session
**So that** F0022, F0023 and F0067 add screens without growing the base bundle or touching session code, and reviewers stop pasting tokens into URLs.

## Context & Background

Graph Observatory carry-in (2026-10-13, ADR-0072, design note §10): F0021 provides a route-level feature flag and lazy-loading seam, and makes the app-wide state, server-state caching and styling choices that F0067 inherits; no Observatory dependency enters v0.1. Operator decision D2 (2026-11-27): rehost the F0001-S0004 proof Review Panel behind the cookie session and remove the token-in-URL entry. BLUEPRINT §2.1 names the frontend stack; Phase B confirms it.

## Acceptance Criteria

- [ ] **AC1:** A route is registered in one place with its path, a feature-flag key and a lazily imported module. With the flag off, the route renders the not-found screen, its module is never requested, and it does not appear in navigation.
- [ ] **AC2:** With the flag on, the module loads on first navigation and renders inside the shell frame; a failed module load shows a retryable error screen and leaves the shell usable.
- [ ] **AC3:** A production build places each lazily registered route's code in its own chunk; the base entry chunk contains none of it, shown by a build report kept as evidence. A size budget for the base entry chunk is recorded at Phase B and checked in CI.
- [ ] **AC4:** Flag values come from server configuration through the session endpoint (no build-time-only switch), so a flag can change without a rebuild; an unknown flag key is treated as off.
- [ ] **AC5:** The Review Panel is reachable at a shell route taking the review item identifier as a path parameter, behind the session. Its reads and decision submission go through the cookie session (S0002) with the panel's existing behavior and engine routes unchanged: the engine's decision receipt and audit row are produced as today, and an item the principal is denied shows not found.
- [ ] **AC6:** The proof-scope launch form and the `?token=` / bearer text-field entry are removed; a URL carrying a `token` query parameter is not read, and the shell strips it from the address bar without sending it anywhere.

## Edge Cases & Error Scenarios

Navigating directly to a flagged-off route URL shows not-found without fetching the chunk. Toggling a flag off while the route is open takes effect on the next navigation. A review item the principal may not read shows the engine's non-disclosing not-found.

## Interaction Contract

Entry: shell navigation or a direct URL. The route seam is configuration, not a user mutation. The rehosted panel keeps its existing decision submission (entry: panel → decide → submit; persistence evidence: the engine's existing decision receipt and audit row; role: Reviewer under existing policy; validation failures: the engine's existing problem responses). Re-authentication during a submission follows S0004.

## Data Requirements

Route registry entries (path, flag key, module); flag values in the session endpoint response (Phase B schema).

## Role-Based Visibility

Flags control visibility only; they never authorize. The Review Panel's data and decisions are authorized by the engine as today.

## Non-Functional Expectations

App-wide choices made here are recorded in Phase B (router, server-state cache, client state, styling, component library, test stack) and inherited by F0022, F0023 and F0067. WCAG 2.2 AA for the shell frame and error screens (A2). At least 80% changed executable-code coverage in the later feature run.

## Dependencies

S0001, S0002, S0004, S0006; F0001-S0004 Review Panel and its routes; F0011 generated contracts.

## Out of Scope

Changes to the panel's renderers, batching or reviewer authority (F0022); the Observatory and its rendering dependencies (F0067); a remote flag service.

## Questions & Assumptions

No open business-rule question. Operator decision D2 is in the [PRD](PRD.md#risks--assumptions). Route paths, flag configuration source, chunk budget and the stack confirmation are Phase B decisions.

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] Build report showing the base chunk free of flagged-route code (AC3).
- [ ] Existing Review Panel component tests pass under the rehosted route.
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.
