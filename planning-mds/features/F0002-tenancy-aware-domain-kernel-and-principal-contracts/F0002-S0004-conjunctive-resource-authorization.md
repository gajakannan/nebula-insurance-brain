# F0002-S0004 — Enforce parent, classification and source restrictions together

**Story ID:** F0002-S0004
**Feature:** F0002 — Tenancy-aware domain kernel + verified stable principal and scope contracts
**Title:** Enforce parent, classification and source restrictions together
**Priority:** Critical
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Rosa the Business Reviewer
**I want** access only review resources and evidence permitted by every applicable restriction
**So that** a role allow or visible parent cannot expose restricted evidence or grant business approval.

## Context & Background

Sections 66, 110 and 120 require action, actual parent scope, classification, source restrictions and evidence dependencies in addition to current membership. ADR-0042 remains proposed; this story proves a bounded kernel contract rather than accepting all derived-result surfaces.
Source requirements: [PRD](PRD.md), master blueprint sections 65–66 and 120–121; persona details in [personas](personas.md).

## Acceptance Criteria

- [ ] **AC1:** Given a current membership and permitted action, when parent scope, classification or source access denies the resource, then authorization denies; each restriction is independently tested while all other conditions allow.
- [ ] **AC2:** Given a permitted classification but a denied parent, when content or a review task is requested, then the protected operation returns the same non-disclosing denial used for an inaccessible resource.
- [ ] **AC3:** Given supplied parent/classification/source attributes disagree with trusted stored attributes, when the request is evaluated, then only server-hydrated attributes determine access; missing required attributes fail closed.
- [ ] **AC4:** Given a derived-resource fixture with two supporting evidence dependencies and access to only one, when the resource is requested, then it is denied; entity visibility alone is insufficient. No declassification exemption is introduced in F0002.
- [ ] **AC5:** Given a valid Reviewer grant, when annotate is requested within scope, then it can be allowed and its audit records the authenticated reviewer, resource/action, policy version, grant revision, outcome and trace; adjudication, business approval and canonical commit remain denied unless separately granted by an owning feature.
- [ ] **AC6:** Given a resource was authorized for display but its grant, parent or restriction changed before evidence access or decision submission, when the operation executes, then current authority is checked again and no unauthorized read or write succeeds.
- [ ] **AC7:** Given the existing content, fact and review resource kinds, when the kernel decision is integrated, then no resource data is emitted before its constraints pass; denied and nonexistent protected IDs retain equivalent external error semantics.

**Edge cases and error scenarios:** Each denial criterion is tested independently from the happy path. Invalid credentials use the existing generic 401 contract; inaccessible protected resources use the existing non-disclosing 404 contract. Trusted provisioning validation errors return an explicit safe failure with no partial write. Infrastructure errors never become an allow.

## Interaction Contract

No UI — backend contracts and existing API/service entry points only.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Existing protected content read, evidence access and review decision submission | Read evidence or submit an annotation | Current Reviewer annotate grant; read grants are resource-specific | Authorized annotation persists with authenticated reviewer; denial leaves no decision or canonical mutation | Fresh read shows accepted annotation only; revoked submission leaves state unchanged | Current membership AND action AND parent AND classification/source/dependency checks; Reviewer never gains commit permission |

Render-only behavior cannot satisfy this story. Protected mutations require durable audit; authorization decisions are append-only. Event payload names and persistence mechanisms are Phase B contract decisions, constrained by the acceptance outcomes above.

## Data Requirements

Required: actual resource type/ID, tenant/KB, action, trusted parent ownership, classification/source restrictions and current policy/grant revisions. Derived-resource fixtures carry explicit dependency references. Restriction vocabularies are policy inputs; absent required inputs are not unrestricted.
Validation rejects missing required values, contradictory ownership and unsupported actions; defaults cannot add authority. IDs in examples are synthetic labels, not a decision about wire formats.

## Role-Based Visibility

The pilot reuses the exact role/action grants in [PRD — Role-Based Access](PRD.md#role-based-access), subject to all mandatory scope restrictions. No anonymous or external-broker access is introduced. User/service/agent is principal kind, not a permission grant. Trusted operational provisioning is distinct from a public runtime permission.

## Non-Functional Expectations

Zero successful unauthorized reads or writes in the story’s isolation cases. Current authorization applies at each protected boundary, including the next operation after revocation. Preserve existing stable identities and audit history. No external service or production latency claim is established by planning; Phase B specifies measurement and failure handling.

## Dependencies

F0002-S0002/S0003; F0001 existing protected content/fact/review surfaces and accepted ADR-0050 boundary.
Contract examples: EX-AUTHX-010, EX-AUTHX-011, EX-AUTHX-012, EX-AUTHX-013 in [worked examples](worked-examples.md). Downstream consumers are listed in the PRD.

## Out of Scope

Production-wide derived-result rollout, declassification workflow, full Document 360 (F0022), assessment rendering (F0065), broad canonical approval/commit orchestration (F0018).

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
