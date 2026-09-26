# F0002-S0001 — Preserve structural tenancy and tenant-scoped entity identity

**Story ID:** F0002-S0001
**Feature:** F0002 — Tenancy-aware domain kernel + verified stable principal and scope contracts
**Title:** Preserve structural tenancy and tenant-scoped entity identity
**Priority:** Critical
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Ingrid the Persistence Engineer
**I want** establish tenant, workspace, knowledge-base ownership and entity identity boundaries
**So that** downstream semantic records cannot cross an ownership boundary or gain access through shared identity.

## Context & Background

ADR-0030 requires structural tenancy from the first schema. The operator selected tenant-scoped entity identity with explicit KB access at G1; the full entity-resolution algorithm remains F0017.
Source requirements: [PRD](PRD.md), master blueprint sections 65–66 and 120–121; persona details in [personas](personas.md).

## Acceptance Criteria

- [ ] **AC1:** Given two tenants, two workspaces in one tenant, and two KBs in one workspace, when ownership is resolved, then each KB resolves to exactly one workspace and tenant; a workspace or KB reference from a different tenant is rejected without a persisted partial association.
- [ ] **AC2:** Given an authoritative semantic record, when it is accepted, then its tenant and KB agree with the authoritative ownership hierarchy and its parent references; missing or conflicting ownership is rejected, including through worker entry points.
- [ ] **AC3:** Given the same entity is explicitly referenced in two KBs within one tenant, when its identity is resolved, then the tenant-scoped identity can be the same while each KB retains separate grants and KB-owned semantic records; the reference creates no membership or grant.
- [ ] **AC4:** Given identical external entity identifiers in different tenants, when identity is resolved, then they cannot select a shared tenant-owned entity or expose whether the other tenant has a matching entity.
- [ ] **AC5:** Given F0001 principal, membership, and semantic records, when the new tenancy contracts are introduced, then existing valid ownership and principal identifiers remain unchanged; inconsistent legacy ownership produces an explicit reconciliation failure instead of guessed grants.
- [ ] **AC6:** Given any rejected ownership mutation, when persisted state is queried again, then no cross-scope association exists and the denied operation is auditable without returning another tenant’s identifiers.

**Edge cases and error scenarios:** Each denial criterion is tested independently from the happy path. Invalid credentials use the existing generic 401 contract; inaccessible protected resources use the existing non-disclosing 404 contract. Trusted provisioning validation errors return an explicit safe failure with no partial write. Infrastructure errors never become an allow.

## Interaction Contract

No UI — backend contracts and existing API/service entry points only.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Trusted platform provisioning and semantic-write boundary | Provision ownership or associate a record | Explicit trusted operation; no public administration screen | Valid hierarchy/association persists atomically; conflicting ownership fails | Reload ownership and association through a fresh storage context | Platform provisioning is operational authority, not a new business role; runtime actors remain constrained by current grants |

Render-only behavior cannot satisfy this story. Protected mutations require durable audit; authorization decisions are append-only. Event payload names and persistence mechanisms are Phase B contract decisions, constrained by the acceptance outcomes above.

## Data Requirements

Required: tenant ID, workspace ID and owner tenant, KB ID and owner workspace/tenant, semantic-record tenant/KB, tenant-scoped entity ID, actor and recording time. Optional external identifiers are namespaced metadata, never access grants.
Validation rejects missing required values, contradictory ownership and unsupported actions; defaults cannot add authority. IDs in examples are synthetic labels, not a decision about wire formats.

## Role-Based Visibility

The pilot reuses the exact role/action grants in [PRD — Role-Based Access](PRD.md#role-based-access), subject to all mandatory scope restrictions. No anonymous or external-broker access is introduced. User/service/agent is principal kind, not a permission grant. Trusted operational provisioning is distinct from a public runtime permission.

## Non-Functional Expectations

Zero successful unauthorized reads or writes in the story’s isolation cases. Current authorization applies at each protected boundary, including the next operation after revocation. Preserve existing stable identities and audit history. No external service or production latency claim is established by planning; Phase B specifies measurement and failure handling.

## Dependencies

F0001 accepted foundation; no dependency on F0003’s full semantic persistence model or F0017’s resolver implementation.
Contract examples: EX-AUTHX-001, EX-AUTHX-002, EX-AUTHX-003 in [worked examples](worked-examples.md). Downstream consumers are listed in the PRD.

## Out of Scope

Full semantic tables (F0003), deterministic matching/merge (F0017), cross-tenant entity sharing, tenant/KB administration UI, automatic tenant reassignment.

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
