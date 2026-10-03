# F0003 — PostgreSQL persistence

## Feature Header

**Feature ID:** F0003  
**Feature Name:** PostgreSQL persistence  
**Priority:** Critical  
**Phase:** MVP — v0.1A  
**Status:** Phase A requirements approved — Phase B design pending
**Planning run:** 2026-09-30-6632006b (Plan A+B, existing)  
**Approval:** Phase A approved with `approve-phase-a`; Phase B approval pending.

## Feature Statement

**As a** persistence engineer  
**I want** a versioned PostgreSQL persistence contract for the Brain’s core records  
**So that** product features can store evidence and semantic state durably while preserving ownership, provenance, and temporal integrity.

## Business Objective

- **Goal:** Turn the F0001 persistence proof and F0002 tenancy-aware kernel into a stable persistence foundation for the v0.1 feature sequence.
- **Metric:** Every §78 table is assigned an owning feature and delivery phase; each delivered table has a migration, explicit keys and constraints, and acceptance coverage.
- **Baseline:** F0001 supplied PostgreSQL 18, the first SQLAlchemy/Alembic schema, and measured transaction and temporal proofs. F0002 added structural ownership and identity safeguards through migrations 0005–0007.
- **Target:** Preserve existing identifiers and accepted data; reject invalid ownership and ambiguous temporal state at the database boundary; achieve at least 80% coverage on changed persistence code during implementation.

## Problem Statement

The first runtime slices have persistence models and PostgreSQL-specific integrity rules, but the full product table inventory spans multiple features and release phases. Without a shared inventory and migration boundary, later features could duplicate tables, weaken tenant ownership, place source bytes in the database, or rely on application checks for invariants that PostgreSQL must enforce.

F0003 establishes the shared persistence contract and a complete §78 inventory with feature ownership. Domain behavior and later-phase tables remain with their owning features.

## Scope & Boundaries

**In Scope:**

1. Maintain a complete table inventory for master-blueprint §78, with the owning feature, release phase, schema source, and migration boundary for each table.
2. Define the shared PostgreSQL 18 persistence layer and its SQLAlchemy/Alembic conventions for the v0.1 semantic kernel.
3. Preserve F0002’s tenant, workspace, knowledge-base, principal, and ownership constraints across persisted references.
4. Preserve database-level valid-time and recorded-time integrity for canonical fact versions, including PostgreSQL range and GiST exclusion behavior.
5. Keep authoritative semantic writes, required audit records, and outbox publication within their declared transaction boundary.
6. Evolve the existing F0001/F0002 schema without silently replacing stable identifiers, history, or ownership.
7. Validate PostgreSQL-specific behavior against PostgreSQL 18; SQLite-only tests cannot establish range or exclusion-constraint behavior.

**Out of Scope:**

- Rebuilding the local PostgreSQL/pgvector/AGE container stack already proven by F0001.
- Storing original source bytes or immutable content-artifact bundles in PostgreSQL; those remain behind the content-artifact storage ports under ADR-0059.
- Changing identity, role, membership, authorization, or delegation policy owned by F0002.
- Owning domain behavior for content artifacts, assertions, ontology releases, profiles, canonical commits, review, retrieval, conversations, or process execution; those remain with their named features.
- Materializing v0.2+ behavior or activating future-only tables before their owning feature defines the requirements.
- Adding a public API, UI, graph projection, or vector retrieval surface.

**Phase A scope assumption confirmed at G3:** “Full table inventory” means F0003 owns the complete §78 ownership and phase map plus the shared persistence contract. Domain-specific fields and behavior are delivered by their owning feature; future-phase tables are not pulled forward into v0.1 merely because they appear in §78.

## Acceptance Criteria Overview

- [ ] Every table in master-blueprint §78 has an owning feature, delivery phase, and source contract; future-phase entries remain explicitly deferred.
- [ ] Delivered v0.1 persistence models and migrations preserve the accepted F0001/F0002 identifiers, ownership, provenance, and transaction rules.
- [ ] PostgreSQL rejects cross-owner relationships and overlapping canonical fact periods even when application validation is bypassed.
- [ ] A failed multi-record write leaves no partial authoritative fact, audit, or outbox state; a successful write remains readable after process restart.
- [ ] Migration and PostgreSQL integration cases cover both successful upgrade and invalid/backfill failure paths; changed persistence code meets the 80% coverage floor during implementation.

## UX / Screens

No new or materially changed screens. F0003 is a backend persistence and migration capability used by existing services and workers.

## Screen Layouts (ASCII)

No UI — storage contracts and migration behavior have no end-user surface. Operational commands and database health belong to the existing platform runbooks.

## Data Requirements

| Data area | Required meaning and boundary |
|---|---|
| Ownership | Tenant/workspace/knowledge-base keys and parent relationships follow F0002; child references cannot cross their declared owner. |
| Source and artifacts | PostgreSQL stores semantic metadata and references; original bytes and immutable content bundles stay in the provider-neutral content store. |
| Canonical facts | Valid and recorded ranges remain distinct; database constraints prevent ambiguous overlap; evidence and change lineage remain addressable. |
| Audit and outbox | Required records share the transaction boundary declared by the owning operation; audit history remains append-only where specified. |
| Schema changes | Alembic migrations preserve stable IDs and historical data and make backfill/reconciliation explicit. |
| Flexible values | JSONB is used only where the owning contract permits structured extension data; it does not replace normalized authoritative fields. |

Existing semantic examples remain authoritative: the valid/recorded-time and concurrency cases in F0001-S0005 and the temporal walkthrough in EX-GL-001/EX-SEM-003; the tenant/knowledge-base boundary cases in F0002 EX-AUTHX-001–003. F0003 introduces no new insurance-domain concept.

## Role-Based Access

| Role | Access level | Notes |
|---|---|---|
| Application service or worker | Read/write through its owning persistence port | Must arrive with the authorization and scope established by the owning service; database connectivity is not a user grant. |
| Persistence engineer | Operate schema migrations and approved local verification | Engineering responsibility does not confer business-data access. |
| End user | No direct database access | Protected reads and writes remain behind F0002 authorization and the owning API/service. |

## Success Criteria

- All §78 entries have one owning feature and a delivery phase; no future behavior is implicitly accepted by an inventory row.
- PostgreSQL-specific integrity cases are tested against PostgreSQL 18 rather than inferred from SQLite.
- Existing F0001/F0002 migration history and stable identifiers remain intact.
- Invalid ownership or overlapping temporal state cannot be persisted.
- F0003 implementation coverage is at least 80%; no production latency target is claimed without a measured release target.

## Risks & Assumptions

- **Risk:** The §78 list spans v0.1 through later releases. **Mitigation:** Maintain the ownership/phase map and defer domain-specific schema detail to each feature.
- **Risk:** SQLite fixtures do not enforce PostgreSQL range and GiST constraints. **Mitigation:** Require PostgreSQL 18 integration coverage for database-only invariants.
- **Assumption:** PostgreSQL 18 and btree_gist remain the v0.1 baseline established by F0001 and ADR-0008.
- **Assumption:** Existing F0001/F0002 records and identifiers must be preserved; no unreviewed destructive migration is allowed.

## Dependencies

- **Direct:** F0001 repository and engineering foundation (accepted PostgreSQL 18 stack and persistence proofs); F0002 tenancy-aware domain kernel (structural ownership and durable authorization/audit contracts).
- **Impacted consumers:** F0004 content-artifact model; F0005 ingestion/recovery; F0006–F0010 assertion, FactSlot, bitemporal, provenance, and change semantics; F0014–F0018 profiles, interpretation, and commits; F0020 temporal query; F0026 recovery; F0033–F0035 retrieval projections.
- F0005-S0002 explicitly requires F0002/F0003 persistence contracts for production wiring. The full dependency audit remains pending for implementation evidence; plan approval does not validate feature-evidence packages.

## Related Stories

- F0003-S0001 — Inventory core persistence ownership and phase boundaries
- F0003-S0002 — Enforce persisted ownership and reference integrity
- F0003-S0003 — Preserve temporal and transactional integrity
- F0003-S0004 — Evolve the schema without losing accepted state

## Rollout & Enablement

Phase B defines the migration and integration sequence. Runtime migrations, restore proof, deployment qualification, and implementation evidence belong to the later feature action.

## Architecture Traceability (Phase B)

Pending Architect design and explicit Phase B approval. Accepted baseline decisions include ADR-0002 (PostgreSQL authority), ADR-0007 (full bitemporality), ADR-0008 (database-level temporal integrity), ADR-0010 (mandatory provenance), and ADR-0059 (provider-neutral content-artifact storage).
