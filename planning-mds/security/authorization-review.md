# Authorization Review — Nebula Insurance Brain

**Status:** Draft
**Date:** 2026-09-05
**Owner:** Security role (completes during Phase B of F0002 and F0018)

## Scope

This review seeds the Brain's authorization model from the master blueprint (sections 65, 66, 110, and 118 to 122). It is a draft until the permission catalog, Casbin model and policy files, and the carryover tests in section 121.2 exist in this repository.

## Identity and principals

- Identity provider: authentik OIDC. Verified `(issuer, subject)` maps to a stable internal principal through a governed registry contract (proposed ADR-0049).
- Principal kinds: UserPrincipal, ServicePrincipal, AgentPrincipal; Membership, Role, Permission, ResourceScope are first-class (section 66).
- Reviewer identity: the reviewer is the authenticated session principal in the native Review Panel, so there is no callback to trust and no second directory to map (ADR-0057); annotation permission remains separate from adjudication and canonical approval authority (sections 75, 111.2, 125; proposed ADR-0044 and ADR-0052).

## Policy evaluation

- Native Casbin adapter behind an AuthorizationService; typed, server-hydrated resource attributes; cross-runtime behavior fixtures to prove parity with the CRM reference (proposed ADR-0050).
- Decision = current tenant and knowledge-base membership AND permitted action AND actual resource or parent scope AND classification and source restrictions AND delegation limits (section 66).
- Structural tenancy (`tenant_id`, `knowledge_base_id`) is resolved from verified identity and trusted grants, separately from broker, distribution, account, policy, and evidence scope; request filters may only narrow (section 65, ADR-0030).

## Enforcement points

API, commit services, search, vector retrieval, AGE traversal, evidence access, ontology access, conversation context assembly, MCP, and the execution gate. Security filters participate during retrieval, never after (section 66). Historical business query dates cannot reinstate revoked permissions (proposed ADR-0053).

## CRM gaps that must not be copied (section 119)

1. Unverified identity selecting Neuron-owned records (high).
2. Document parent attributes not enforced by the Casbin adapter (high).
3. Token storage and logout not forming one contract (high design inconsistency); the Brain proposes a same-origin BFF with server-held tokens (proposed ADR-0051).
4. Policy parity drift between catalog, matrix, and runtime (medium); the Brain tests all three together.

## Audit

Every authorization decision records policy version or hash, grant revision, actor and delegate, resource and action, decision and reason codes, and trace ID. Baseline enforcement and audit are v0.1 obligations (sections 66, 89).

## Required evidence before acceptance

- Carryover test matrix from section 121.2 implemented and passing for the affected boundaries.
- Isolation, revocation, graph, vector, export, and chat leakage suite passing (section 115.2 Authorization gate).
- Permission catalog and review boundaries documented per section 120.2, with policy files under `policies/`.
