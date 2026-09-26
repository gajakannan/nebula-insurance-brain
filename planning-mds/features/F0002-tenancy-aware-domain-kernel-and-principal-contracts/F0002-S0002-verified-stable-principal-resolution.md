# F0002-S0002 — Resolve verified credentials to stable typed principals

**Story ID:** F0002-S0002
**Feature:** F0002 — Tenancy-aware domain kernel + verified stable principal and scope contracts
**Title:** Resolve verified credentials to stable typed principals
**Priority:** Critical
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Dana the Platform Engineer
**I want** reuse stable principal identity only after credential verification
**So that** forged identity cannot select protected storage or change audit ownership.

## Context & Background

ADR-0049 accepted F0001’s verify-before-read and issuer-namespaced identity boundary. F0002 preserves those identifiers and makes the user/service/agent distinction explicit for downstream consumers.
Source requirements: [PRD](PRD.md), master blueprint sections 65–66 and 120–121; persona details in [personas](personas.md).

## Acceptance Criteria

- [ ] **AC1:** Given a valid receiving-service credential, when the verified issuer/subject pair is resolved repeatedly or concurrently, then exactly one stable internal principal is selected; process restart and new sessions do not replace that ID.
- [ ] **AC2:** Given equal subject text from two different issuers, when resolution occurs, then different principals are returned unless an explicitly approved identity link exists; email address equality never links identities or grants membership.
- [ ] **AC3:** Given missing, malformed, expired, not-yet-valid, wrong-signature, wrong-issuer, wrong-audience or unsupported credential type, when a protected entry point is called, then it returns the existing generic unauthenticated response before principal provisioning, membership lookup or protected resource access.
- [ ] **AC4:** Given a disabled principal, when otherwise valid credentials are presented, then protected access is denied; the internal reason is audited and no resource existence is disclosed.
- [ ] **AC5:** Given a client or model submits principal ID, principal kind, roles or acting-user fields, when trusted context is built, then those values cannot override verified identity and trusted principal records.
- [ ] **AC6:** Given an identity-provider migration or proposed identity link, when no approved mapping exists, then the system does not silently merge existing owners or reassign audit history; the operator receives a reconciliation requirement.
- [ ] **AC7:** Given existing user, service and agent fixtures, when the context is consumed, then principal kind and identity are explicit and cannot be inferred from a requested role or changed by request payload.

**Edge cases and error scenarios:** Each denial criterion is tested independently from the happy path. Invalid credentials use the existing generic 401 contract; inaccessible protected resources use the existing non-disclosing 404 contract. Trusted provisioning validation errors return an explicit safe failure with no partial write. Infrastructure errors never become an allow.

## Interaction Contract

No UI — backend contracts and existing API/service entry points only.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Verified principal-resolution boundary | Resolve a credential, provision a first-seen identity or apply an approved identity mapping | Only after verification; linking requires explicit operational approval | One durable principal mapping; no automatic merge or role grant | Repeat/concurrent resolution and fresh-process read return the same ID | Identity creation grants no tenant/KB access; disabled principals cannot access protected resources |

Render-only behavior cannot satisfy this story. Protected mutations require durable audit; authorization decisions are append-only. Event payload names and persistence mechanisms are Phase B contract decisions, constrained by the acceptance outcomes above.

## Data Requirements

Required: verified issuer, subject, stable principal ID, principal kind (user/service/agent), enabled status, verification outcome, audit actor and trace. Raw tokens are not stored in decisions. Optional approved external-identity links preserve the existing principal ID.
Validation rejects missing required values, contradictory ownership and unsupported actions; defaults cannot add authority. IDs in examples are synthetic labels, not a decision about wire formats.

## Role-Based Visibility

The pilot reuses the exact role/action grants in [PRD — Role-Based Access](PRD.md#role-based-access), subject to all mandatory scope restrictions. No anonymous or external-broker access is introduced. User/service/agent is principal kind, not a permission grant. Trusted operational provisioning is distinct from a public runtime permission.

## Non-Functional Expectations

Zero successful unauthorized reads or writes in the story’s isolation cases. Current authorization applies at each protected boundary, including the next operation after revocation. Preserve existing stable identities and audit history. No external service or production latency claim is established by planning; Phase B specifies measurement and failure handling.

## Dependencies

F0001-S0006/S0007 and ADR-0049; F0002-S0001 for structural ownership fixtures.
Contract examples: EX-AUTHX-004, EX-AUTHX-005, EX-AUTHX-006 in [worked examples](worked-examples.md). Downstream consumers are listed in the PRD.

## Out of Scope

Self-service identity linking, a new identity-provider UI, BFF/browser sessions (F0021), cross-product privileged database access or automatic CRM ID replacement.

## Questions & Assumptions

No open product question: the operator selected tenant-scoped entity identity with explicit KB grants and reuse of the existing pilot roles on 2026-09-25. Architecture must preserve the accepted F0001 boundaries; schemas, migration/backfill, contract versioning and adapter details are decided in Phase B before its approval. Planning does not accept proposed ADRs or count synthetic cases as observed proof.

## Definition of Done

- [ ] All acceptance criteria and independent deny cases pass through the stated entry point.
- [ ] Permissions and current scope are enforced; persisted state and audit are checked after mutations.
- [ ] Regression tests pass and changed kernel coverage meets the feature’s 80% floor.
- [ ] Exact reproduction commands, actual results and documentation are recorded in the implementation run.
- [ ] Story filename matches Story ID; generated story index is current.
- [ ] Required reviewers record evidence-backed signoff in STATUS.md.

## Review Provenance

See [STATUS.md](STATUS.md), Required Signoff Roles and Story Signoff Provenance. No implementation or reviewer signoff is asserted by this planning draft.
