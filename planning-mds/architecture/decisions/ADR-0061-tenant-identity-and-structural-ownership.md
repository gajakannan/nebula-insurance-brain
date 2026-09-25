# ADR-0061: Tenant identity and structural ownership

## Status

- [x] Proposed — F0002 Phase B design; design approved by user 2026-09-25; implementation proof pending
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-25
**Deciders:** Architect; product choices confirmed by the user at F0002 G1 and Phase A approved with `approve-phase-a`.

## Context

ADR-0030 establishes Tenant → Workspace → KnowledgeBase. F0001 stores tenant/KB UUIDs on selected root records, while children inherit ownership through joins; workspace and tenant registries do not yet exist. The operator selected tenant-scoped entity identity and explicit KB access. Stable principal identity is a separate identity-provider boundary and must retain existing UUIDs.

## Decision

Introduce structural registries and composite ownership constraints. A tenant entity identity has one tenant owner and may have explicit associations with several KBs in that tenant; semantic records and grants remain KB-scoped. No identity association creates a permission. Global principal/external-identity records, tenant/workspace roots and security control records are structural records, not KB-owned semantic content; do not manufacture a KB owner for them. Existing KB semantic rows gain explicit ownership where absent.

```text
Tenant -> Workspace -> KnowledgeBase -> KB-owned semantic rows
   |                       |
   +-> EntityIdentity <----+ EntityKB association (not an access grant)
Principal -> current Membership -> one Tenant/KB + role/restrictions
```

Preserve existing principal, source, artifact, assertion, fact and review IDs. Add external identity aliases keyed uniquely by verified `(issuer, subject)` and linked to the existing principal. Only an explicitly approved operational link may add an alias; do not merge principal histories or infer identity from email. Concurrent first resolution uses a unique insert-or-read path, not find-then-unprotected-insert.

Migration is expand → inventory and explicit reconciliation → backfill → validate → constrain. A reviewed local mapping supplies missing workspace ownership and resource restrictions. It may seed synthetic development data but cannot infer production grants from a known tenant/KB UUID. Mixed-owner or orphan legacy records stop the migration with a report; the operator repairs source associations before retry. No arbitrary reassignment, synthetic grants or destructive ID rewrite.

## Alternatives and consequences

- KB-local entity identity would duplicate an entity across KBs and contradict the operator’s choice.
- A global cross-tenant entity registry would create a new sharing boundary outside the PRD.
- Inferring workspace or entitlement from email or existing IDs would hide incomplete migration data; require an explicit mapping instead.
- More composite keys and migration checks are required, but ownership can be proven at the database and service boundaries. Full entity resolution and semantic persistence remain F0017 and F0003.

## Acceptance and rollback

Backend and QE must prove S0001/S0002 against PostgreSQL, including two tenants, sibling KBs/workspaces, concurrent principal resolution, retained UUIDs, and rejection of invalid backfill without partial writes. Architect and Security review the constraints; DevOps verifies expand/restore. Acceptance is limited to these boundaries after evidence exists; this planning record claims none of those tests ran.

Before constraints are enabled, rollback restores the pre-migration snapshot or reverses unused expansion only. Once new records depend on the contract, use a forward repair; do not run destructive downgrade against authoritative content.

## References

- [Approved F0002 PRD](../../features/F0002-tenancy-aware-domain-kernel-and-principal-contracts/PRD.md)
- [Assembly plan](../../features/F0002-tenancy-aware-domain-kernel-and-principal-contracts/feature-assembly-plan.md)
- [ADR-0030](ADR-0030-tenancy-is-structural.md), [ADR-0049](ADR-0049-shared-identity-and-verified-principal-boundary.md)
