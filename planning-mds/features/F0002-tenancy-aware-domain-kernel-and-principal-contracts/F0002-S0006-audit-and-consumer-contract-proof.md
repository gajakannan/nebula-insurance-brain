# F0002-S0006 — Prove audited kernel behavior through existing consumers

**Story ID:** F0002-S0006
**Feature:** F0002 — Tenancy-aware domain kernel + verified stable principal and scope contracts
**Title:** Prove audited kernel behavior through existing consumers
**Priority:** Critical
**Phase:** MVP
**Status:** Not Started

## User Story

**As a** Dana the Platform Engineer
**I want** trace every kernel authorization outcome and reproduce the same rules across existing entry points
**So that** downstream features receive a tested contract instead of disconnected identity and permission types.

## Context & Background

F0001 provides protected reads, annotation submission and a commit service. This story integrates F0002 contracts with those consumers and records acceptance evidence; it does not deliver the later full canonical pipeline.
Source requirements: [PRD](PRD.md), master blueprint sections 65–66 and 120–121; persona details in [personas](personas.md).

## Acceptance Criteria

- [ ] **AC1:** Given an allow or deny decision, when recorded, then audit includes current time, verified actor, actor kind, delegate when applicable, resource/action, tenant/KB context when safely resolved, policy hash/version, grant revision, decision/reason code and trace ID; unresolved identity is explicitly marked rather than fabricated.
- [ ] **AC2:** Given a rejected credential, when authentication audit is inspected, then no access token or protected payload is present and neither principal nor protected resource storage was used to enrich the rejection.
- [ ] **AC3:** Given a protected mutation succeeds, when domain state and audit are reread, then the mutation has a durable decision reference and authenticated actor; an audit persistence failure cannot produce an unaudited successful protected operation.
- [ ] **AC4:** Given content/fact/review reads, review submission and the existing commit boundary, when the shared allow/deny fixtures run through each applicable consumer, then the outcomes match the contract and denied calls produce zero protected mutations.
- [ ] **AC5:** Given a Reviewer annotation and a separate ServicePrincipal commit attempt, when tested, then annotation does not grant commit authority; commit independently rechecks current authorization and preserves its existing audit/outbox transaction. F0002 does not automatically promote an annotation to truth.
- [ ] **AC6:** Given the EX-AUTHX cases and the section 121.2 matrix, when acceptance is reported, then each applicable case records actual output against the independently authored expectation, and every deferred category names an owning feature instead of being counted as passed.
- [ ] **AC7:** Given the completed implementation candidate, when security and regression checks run, then all scoped negative cases pass with zero unauthorized disclosures, existing F0001 boundary tests pass, and changed kernel code meets the 80% coverage floor. Record measured latency; no unmeasured production latency SLO is claimed.

**Edge cases and error scenarios:** Each denial criterion is tested independently from the happy path. Invalid credentials use the existing generic 401 contract; inaccessible protected resources use the existing non-disclosing 404 contract. Trusted provisioning validation errors return an explicit safe failure with no partial write. Infrastructure errors never become an allow.

## Interaction Contract

No UI — backend contracts and existing API/service entry points only.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Existing protected API/service operations and reproducible test harness | Read, annotate or request an existing service-authorized commit | Each operation must pass current authority at its execution boundary | Allowed mutations and decision references persist; denied mutations do not | Fresh storage read and audit query establish outcome; failure injection proves audit behavior | TenantMember reads, Reviewer annotations and ServicePrincipal bounded pilot operations remain separate |

Render-only behavior cannot satisfy this story. Protected mutations require durable audit; authorization decisions are append-only. Event payload names and persistence mechanisms are Phase B contract decisions, constrained by the acceptance outcomes above.

## Data Requirements

Decision records and traces as listed in AC1; independently authored fixture inputs/expected outcomes; observed results, coverage report and exact reproduction commands supplied during implementation. No tokens, sensitive content or fabricated principal IDs in audit.
Validation rejects missing required values, contradictory ownership and unsupported actions; defaults cannot add authority. IDs in examples are synthetic labels, not a decision about wire formats.

## Role-Based Visibility

The pilot reuses the exact role/action grants in [PRD — Role-Based Access](PRD.md#role-based-access), subject to all mandatory scope restrictions. No anonymous or external-broker access is introduced. User/service/agent is principal kind, not a permission grant. Trusted operational provisioning is distinct from a public runtime permission.

## Non-Functional Expectations

Zero successful unauthorized reads or writes in the story’s isolation cases. Current authorization applies at each protected boundary, including the next operation after revocation. Preserve existing stable identities and audit history. No external service or production latency claim is established by planning; Phase B specifies measurement and failure handling.

## Dependencies

F0002-S0001 through S0005; F0001 existing content/review/fact and audit/outbox contracts.
Contract examples: EX-AUTHX-017, EX-AUTHX-018; every prior case through applicable consumers in [worked examples](worked-examples.md). Downstream consumers are listed in the PRD.

## Out of Scope

Cross-repository .NET/Python runtime parity and production qualification (F0026), new approval workflow and full canonical integration (F0018), browser session delivery (F0021), feature closeout evidence during this plan run.

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
