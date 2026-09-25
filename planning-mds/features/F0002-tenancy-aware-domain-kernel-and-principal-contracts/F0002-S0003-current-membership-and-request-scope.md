# F0002-S0003 — Resolve current memberships and intersect requested scope

**Story ID:** F0002-S0003
**Feature:** F0002 — Tenancy-aware domain kernel + verified stable principal and scope contracts
**Title:** Resolve current memberships and intersect requested scope
**Priority:** Critical
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Dana the Platform Engineer
**I want** derive current tenant, KB and resource entitlements from trusted state
**So that** filters, historical query dates and stale grants cannot widen access.

## Context & Background

Master blueprint sections 65, 66 and 120 require authority union followed by request intersection. Structural membership is distinct from broker/account/policy restrictions.
Source requirements: [PRD](PRD.md), master blueprint sections 65–66 and 120–121; persona details in [personas](personas.md).

## Acceptance Criteria

- [ ] **AC1:** Given multiple current grants, when effective scope is resolved, then authorized scope is their permitted union; a supplied filter only intersects that scope and cannot add a tenant, KB, account, policy or broker relationship.
- [ ] **AC2:** Given one tenant with sibling KBs and workspaces, when a principal has a grant only for one KB, then the sibling remains inaccessible even when the same entity is referenced by both KBs.
- [ ] **AC3:** Given two broker relationships in the same tenant/KB, when authority covers only one, then requesting the other cannot select its records; broker_tenant_id is never substituted for structural tenant_id.
- [ ] **AC4:** Given an expired, revoked or missing membership, when the next protected operation resolves scope, then it denies access; a previously constructed context or a business query date before revocation cannot reinstate the grant.
- [ ] **AC5:** Given mixed roles across KB memberships, when a resource is selected, then a role granted in a different KB cannot authorize an action on that resource.
- [ ] **AC6:** Given unavailable grant state or a missing required scope attribute, when a decision is needed, then the operation returns a sanitized failure and releases no protected content; it cannot fall back to an unrestricted scope.
- [ ] **AC7:** Given a trusted grant change, when the scope is reread, then the current revision and effective outcome change together and an audit record identifies the actor and affected scope.

**Edge cases and error scenarios:** Each denial criterion is tested independently from the happy path. Invalid credentials use the existing generic 401 contract; inaccessible protected resources use the existing non-disclosing 404 contract. Trusted provisioning validation errors return an explicit safe failure with no partial write. Infrastructure errors never become an allow.

## Interaction Contract

No UI — backend contracts and existing API/service entry points only.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Trusted grant provisioning/revocation boundary and protected read/write entry points | Apply an explicit grant change, then request a scoped operation | Trusted grant changes only; client filters never edit grants | Grant revision/state persists; unauthorized changes fail | New request after persisted change observes current authority | Existing pilot roles; no implicit workspace, tenant-wide or sibling-KB inheritance |

Render-only behavior cannot satisfy this story. Protected mutations require durable audit; authorization decisions are append-only. Event payload names and persistence mechanisms are Phase B contract decisions, constrained by the acceptance outcomes above.

## Data Requirements

Required: verified principal, current tenant/KB membership, role grants, effective/expiry/revocation state, grant revision and authoritative resource restrictions. Optional requested filters and business times remain untrusted narrowing/query inputs.
Validation rejects missing required values, contradictory ownership and unsupported actions; defaults cannot add authority. IDs in examples are synthetic labels, not a decision about wire formats.

## Role-Based Visibility

The pilot reuses the exact role/action grants in [PRD — Role-Based Access](PRD.md#role-based-access), subject to all mandatory scope restrictions. No anonymous or external-broker access is introduced. User/service/agent is principal kind, not a permission grant. Trusted operational provisioning is distinct from a public runtime permission.

## Non-Functional Expectations

Zero successful unauthorized reads or writes in the story’s isolation cases. Current authorization applies at each protected boundary, including the next operation after revocation. Preserve existing stable identities and audit history. No external service or production latency claim is established by planning; Phase B specifies measurement and failure handling.

## Dependencies

F0002-S0001 and F0002-S0002; F0001 current membership/revocation behavior.
Contract examples: EX-AUTHX-002, EX-AUTHX-007, EX-AUTHX-008, EX-AUTHX-009 in [worked examples](worked-examples.md). Downstream consumers are listed in the PRD.

## Out of Scope

New business-role assignments, administration UI, live hybrid/vector/graph search (F0033–F0035), browser cache lifecycle (F0021), jurisdictional access rules.

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
