# F0002 — Tenancy-aware domain kernel + verified stable principal and scope contracts

## Feature Header

**Feature ID:** F0002
**Feature Name:** Tenancy-aware domain kernel + verified stable principal and scope contracts
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Draft
**Planning run:** 2026-09-25-3c64470a (Plan A+B, new)
**Approval:** Phase A approved by user (`approve-phase-a`, 2026-09-25); Phase B approved by user (`approve-phase-b`, 2026-09-25).

## Feature Statement

**As a** platform or persistence engineer supporting insurance knowledge workers
**I want** one tenancy-aware domain and verified-principal contract enforced by existing protected consumers
**So that** each future semantic feature preserves ownership, current authority and accountable actions.

## Business Objective

- **Goal:** Make the first semantic kernel safe to extend without reimplementing identity and scope in each feature.
- **Baseline:** F0001 proved verified credentials, stable issuer/subject identity, three protected resource kinds, native Casbin and current tenant/KB membership. It did not settle the complete section 121.2 matrix.
- **Metric / target:** All six stories and their scoped allow/deny fixtures pass; zero unauthorized disclosures or mutations in those fixtures; stable existing principal IDs retained; every authorization decision auditable; at least 80% coverage on changed kernel code.
- Measurements and runtime results belong to the feature action. This plan supplies requirements and synthetic expected cases only.

## Problem Statement

Proof-specific identity and membership handling is insufficient as the shared contract for tenant/workspace/KB ownership, parent and source restrictions, delegation and downstream audit. A visible entity or a Casbin role allow must not bypass narrower evidence access. F0002 turns the accepted foundation into reusable contracts with bounded consumer integration.

## Scope & Boundaries

**In Scope:**

1. Structural Tenant → Workspace → KnowledgeBase ownership and tenant/KB consistency for authoritative semantic records and their parents.
2. Tenant-scoped entity identity, separate explicit KB access, and no grant creation through entity resolution or cross-KB references. Full entity resolution remains F0017.
3. Stable internal principal identity from verified issuer/subject, distinct user/service/agent kinds, disabled identities, concurrent first resolution and explicit identity-link/migration handling.
4. Trusted current memberships, union of permitted authority, request-filter intersection and separation of structural tenancy from broker/account/policy scope.
5. Conjunctive membership, action, actual parent/resource, classification/source and evidence-dependency restrictions, with bounded integration through existing content/fact/review consumers.
6. Bounded expiring delegation, independent current-grant checks and autonomous services limited to their own grants.
7. Durable decision audit and a reusable negative-case fixture matrix, preserving F0001 regression behavior and current access at review submission/commit boundaries.

**Out of Scope:**

- New tenant/KB/role/delegation administration UI or new business-role assignments.
- Full semantic persistence (F0003), entity matching/merging (F0017), or automatic canonical acceptance after review (F0018).
- Browser login/session/BFF behavior (F0021), complete review UI and evidence assembly (F0022), production-grade assessment access (F0065).
- Live hybrid/vector/graph retrieval and cache enforcement (F0033–F0035), conversation/MCP transports (F0037–F0047), generalized execution gate (F0059).
- Cross-tenant shared entity records, implicit sharing, declassification exemptions or jurisdiction-specific policies.
- Production qualification and cross-runtime policy parity (F0026). Proposed ADR-0042 is not globally accepted by passing a bounded kernel test.

## Personas

Reuse Dana (platform/security), Ingrid (persistence) and Rosa (business review), scoped in [personas.md](personas.md). These are existing product personas; no new business role is implied by an engineering persona.

## Acceptance Criteria Overview

- [ ] Tenant/workspace/KB ownership cannot be crossed by parent references or supplied identifiers (S0001).
- [ ] Verified issuer/subject resolves to one stable typed principal, with no pre-verification protected lookup (S0002).
- [ ] Current grants determine effective scope; filters and past business dates cannot add authority (S0003).
- [ ] Every required resource restriction participates in authorization, including evidence dependencies (S0004).
- [ ] Delegated authority is bounded by current actor grants and explicit delegation limits; autonomous services use their own grants (S0005).
- [ ] Existing consumers reproduce all applicable fixture outcomes with durable, non-secret audit and no role widening (S0006).

Detailed acceptance review: [acceptance-criteria-checklist.md](acceptance-criteria-checklist.md). Independent expected cases: [worked-examples.md](worked-examples.md).

## UX / Screens

No new or materially changed screens. Existing callers observe preserved generic unauthenticated/non-disclosing denied responses. Product workflows are verified principal resolution → current scope → protected operation → audit, and trusted grant revocation → next-operation denial. Backend review submission is checked without changing the Review Panel interaction design.

## Screen Layouts (ASCII)

No UI — shared backend domain/security contracts and bounded integration through existing protected API/service entry points. Desktop/mobile wireframes do not apply.

## Data Requirements

| Concept | Required meaning / boundary |
|---|---|
| Tenant, Workspace, KnowledgeBase | Structural hierarchy; KB ownership resolves to exactly one workspace and tenant |
| Entity identity | Stable within tenant; KB-owned records and grants remain separate; identity is not visibility |
| Principal | Stable internal identity from verified issuer/subject; kind user/service/agent; enabled state |
| Membership / role grant | Trusted current association of principal to tenant/KB authority; revision and lifecycle are explicit |
| ResourceScope | Effective permitted resources; client analytical filters only narrow it |
| Authorization context | Verified actor, current grant revision, authoritative resource/parent/restrictions, action, policy version, current enforcement time and separate business query times |
| Delegation | Explicit acting identities, action/resource ceiling, expiry and revocation; not a new role grant |
| Decision audit | Actor/delegate, scope where resolved, resource/action, policy/grant revision, outcome/reason, trace and timestamp; no tokens or protected content |

Existing definitions: [glossary](../../domain/glossary.md). These rows state requirements; Phase B must settle schema fields, lifecycle representation, migration/backfill and audit failure semantics, and add missing glossary/contract references. Synthetic examples below define the expected behavior independently of those implementation choices.

## Role-Based Access

Operator decision: reuse the existing pilot grants in [policy.csv](../../security/policies/policy.csv). Each allow still requires current membership, authoritative restrictions and any delegation ceiling.

| Role | Permitted pilot resource/actions | Explicit limits |
|---|---|---|
| TenantMember | content_artifact:read; review_task:read; fact_slot:read | No annotation, ingestion or commit from this role |
| Reviewer | review_task:read; review_task:annotate | No canonical commit, adjudication, business approval or unrestricted evidence read |
| ServicePrincipal | content_artifact:read/ingest/interpret; fact_slot:read/commit | Own explicit grants or bounded delegation; no general administrator bypass |
| No applicable role grant | None | A verified identity or AgentPrincipal kind alone grants no access |

Multiple role grants apply only in their authorized membership context. This feature does not silently give Reviewer every TenantMember permission. Operational provisioning is trusted platform setup, not an additional public business role. New resource/action grants need their owning feature’s approval.

## Success Criteria

Six unstarted stories define observable behavior across valid and denied operations. Each implemented story must reproduce the referenced EX-AUTHX cases and preserve F0001 boundary tests. No unauthorized data or mutation may appear in the scoped negative suite. No successful protected operation may lose required audit. Measure latency during implementation; no production latency budget is invented here.

## Decisions, Risks & Assumptions

- **G1 decision, user 2026-09-25:** “Tenant-scoped identity; explicit KB access”. Cross-KB references never create a grant. This resolves master blueprint section 117.1 item 2 for entity identity/KB sharing in this feature.
- **G1 decision, user 2026-09-25:** “Reuse the existing pilot roles”. This selects F0001’s three roles; new business-role grants remain with their owning features.
- Accepted ADR-0049/0050 apply only to their measured F0001 boundaries. Broader authorization requirements remain to be proven; ADR-0042 remains Proposed.
- A principal’s stable identity is separate from tenant-scoped entity identity. Preserve F0001 principal IDs and approved identity mappings; do not generate unrelated cross-product identities by default.
- The historical master-blueprint section 116.1 assigns review-to-commit integration to F0002, while F0018 owns full canonical commit and F0022 owns review authority. F0002 covers the shared authorization boundary and existing consumer proof; Phase B must explicitly reconcile that wording before approval, preserving the independent commit check and avoiding automatic promotion.
- Phase B decisions: compatible domain/schema boundaries; approved identity-link mechanism; tenancy backfill and constraints; policy input types and failure behavior; delegation lifecycle; audit durability; API compatibility; exact fixtures and test commands. These cannot relax the product outcomes or broaden pilot grants.

## Dependencies

- **Direct:** archived [F0001](../archive/F0001-repository-and-engineering-foundation/README.md), accepted foundation. Its latest-run pointer identifies approved run `2026-09-12-855d2b93`; scoped raw ADR-0049/0050 results supply the identity/authorization baseline. Full dependency revalidation is audit pending for the implementation action.
- **Impacted consumers:** F0003–F0017 semantic storage/ingestion/identity; F0018 commit; F0020 queries; F0021 session; F0022 review; F0023 views; F0026 qualification; F0033–F0040 retrieval/conversation; F0047 MCP; F0065 assessment. These are contract consumers, not delivered prerequisites. KG lookup explicitly records F0065’s dependency; other impact is derived from their raw blueprint scope.
- Dependency evidence and unresolved reconciliation are recorded in the run’s artifact-trace.md and gate-decisions.md. No repo-wide feature-evidence validation is substituted for this audit.

## Related Stories

- [F0002-S0001](F0002-S0001-structural-tenancy-and-entity-identity.md) — Preserve structural tenancy and tenant-scoped entity identity.
- [F0002-S0002](F0002-S0002-verified-stable-principal-resolution.md) — Resolve verified credentials to stable typed principals.
- [F0002-S0003](F0002-S0003-current-membership-and-request-scope.md) — Resolve current memberships and intersect requested scope.
- [F0002-S0004](F0002-S0004-conjunctive-resource-authorization.md) — Enforce parent, classification and source restrictions together.
- [F0002-S0005](F0002-S0005-bounded-delegation-and-service-authority.md) — Bound delegated and autonomous service authority.
- [F0002-S0006](F0002-S0006-audit-and-consumer-contract-proof.md) — Prove audited kernel behavior through existing consumers.

## Rollout & Enablement

Plan approval authorizes architecture design only at G3, then implementation readiness only after G4/G5 and explicit Phase B approval. Runtime migration, deployment and reviewer signoff belong to the later feature action. Existing records and principal identifiers must survive migration; ambiguous legacy ownership must be surfaced for reconciliation.

## Architecture Traceability (Phase B)

The [assembly plan](feature-assembly-plan.md) maps all six stories to files, service contracts, persistence, authorization and tests. [ADR-0061](../../architecture/decisions/ADR-0061-tenant-identity-and-structural-ownership.md) specifies ownership/identity; [ADR-0062](../../architecture/decisions/ADR-0062-current-authorization-and-durable-decisions.md) specifies current authorization, audit and the explicit review-to-commit ownership reconciliation. These design additions do not change the approved requirements. Architecture design approved by user on 2026-09-25; runtime proof remains pending.
