# F0002-S0005 — Bound delegated and autonomous service authority

**Story ID:** F0002-S0005
**Feature:** F0002 — Tenancy-aware domain kernel + verified stable principal and scope contracts
**Title:** Bound delegated and autonomous service authority
**Priority:** Critical
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Dana the Platform Engineer
**I want** distinguish a service acting under its own grant from an agent acting for a user
**So that** background work cannot borrow broader authority or continue after its authority expires.

## Context & Background

Sections 66 and 120.4 require both acting identities, explicit delegation limits and current authority. F0002 owns the reusable contract and a bounded consumer proof; F0047 owns the later MCP transport.
Source requirements: [PRD](PRD.md), master blueprint sections 65–66 and 120–121; persona details in [personas](personas.md).

## Acceptance Criteria

- [ ] **AC1:** Given an agent acting for a user, when a protected operation is requested, then the verified agent identity, acting user, delegation reference, allowed actions/resources and expiry are resolved from trusted state.
- [ ] **AC2:** Given an operation allowed by the delegation but denied by the actor’s current grant, or allowed by the actor but outside the delegation ceiling, when evaluated, then it is denied; authority is the intersection, never a union.
- [ ] **AC3:** Given an expired/revoked delegation or a revoked user membership during a job, when the next protected operation executes, then access is denied even if an earlier job step succeeded.
- [ ] **AC4:** Given a forged actor/delegation identifier, when supplied by a client/model, then it cannot replace authenticated identities or trusted delegation state.
- [ ] **AC5:** Given an autonomous ServicePrincipal without a human delegate, when it performs a pilot action, then it uses only its own explicit grant and is audited as a service; it never impersonates a human or gains an implicit tenant-wide bypass.
- [ ] **AC6:** Given an agent asks for an unregistered action, wider scope, onward delegation or a direct canonical write outside an authorized commit boundary, when processed, then it is rejected without widening authority or mutating canonical state.
- [ ] **AC7:** Given an allowed delegated fixture operation, when persisted output is inspected, then both identities, delegation reference, policy and grant revisions are traceable; the same operation outside its ceiling leaves no protected mutation.

**Edge cases and error scenarios:** Each denial criterion is tested independently from the happy path. Invalid credentials use the existing generic 401 contract; inaccessible protected resources use the existing non-disclosing 404 contract. Trusted provisioning validation errors return an explicit safe failure with no partial write. Infrastructure errors never become an allow.

## Interaction Contract

No UI — backend contracts and existing API/service entry points only.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Trusted delegation boundary and bounded job consumer | Execute an explicitly delegated operation or autonomous service operation | Valid current delegation for delegated work; explicit service grant otherwise | Only an allowed operation can persist output; expiry/revocation prevents the next operation | Query accepted output and decision audit; assert no denied mutation | Existing roles only; no default Agent role grant, delegation UI, or onward delegation permission |

Render-only behavior cannot satisfy this story. Protected mutations require durable audit; authorization decisions are append-only. Event payload names and persistence mechanisms are Phase B contract decisions, constrained by the acceptance outcomes above.

## Data Requirements

Required for delegated work: acting user ID, agent/service principal ID, trusted delegation ID, permitted actions/resources, expiry/revocation, current authority revision and policy version. Autonomous services explicitly omit human delegation and use their own grants.
Validation rejects missing required values, contradictory ownership and unsupported actions; defaults cannot add authority. IDs in examples are synthetic labels, not a decision about wire formats.

## Role-Based Visibility

The pilot reuses the exact role/action grants in [PRD — Role-Based Access](PRD.md#role-based-access), subject to all mandatory scope restrictions. No anonymous or external-broker access is introduced. User/service/agent is principal kind, not a permission grant. Trusted operational provisioning is distinct from a public runtime permission.

## Non-Functional Expectations

Zero successful unauthorized reads or writes in the story’s isolation cases. Current authorization applies at each protected boundary, including the next operation after revocation. Preserve existing stable identities and audit history. No external service or production latency claim is established by planning; Phase B specifies measurement and failure handling.

## Dependencies

F0002-S0002/S0003/S0004; no dependency on future MCP or conversation products.
Contract examples: EX-AUTHX-014, EX-AUTHX-015, EX-AUTHX-016 in [worked examples](worked-examples.md). Downstream consumers are listed in the PRD.

## Out of Scope

MCP transport/tools (F0047), conversation execution (F0037–F0040), generalized Execution Gate (F0059), delegation administration UI, automatic delegation renewal.

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
