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

## Governed retrieval carry-in (2026-11-06)

**Status:** Requirements and threat-model inputs only; no security acceptance or runtime proof. Applies to F0033–F0036, F0067 replay and conditional F0068 under Proposed [ADR-0076](../architecture/decisions/ADR-0076-governed-graph-assisted-evidence-retrieval.md). Security owns D9 concrete cache-key, invalidation and replay authorization rules in F0035 Phase B. [Design](../architecture/governed-evidence-retrieval-design.md); [EX-RET-002/004/006](../examples/governed-evidence-retrieval.md); handoff §8.

Assets include immutable evidence, source/canonical bindings, typed paths, scores/counts, versioned retrieval and numerical artifacts, caches and traces. Actors are verified knowledge workers, reviewers, bounded service/agent principals and adversarial callers. Trust boundaries run from caller filters to engine-resolved scope/current authority, from canonical/content stores to derived projections, from retrieval to model context, and from recorded traces/caches to replay consumers. Client filters narrow scope; server-resolved basis fields never create grants.

| STRIDE concern | Concrete risk / required control | Required proof owner |
|---|---|---|
| Spoofing | Caller forges principal, root or authorization-basis reference; resolve identity/current grants server side using existing AuthX | Backend + Security, F0035 |
| Tampering | Mixed artifact generations or altered node maps/weights change scores; checksums, coherent input versions and atomic publication; derived records cannot write canonical state | Architect + Backend, F0033/F0034; AI Engineer, F0068 |
| Repudiation | Selection is falsely reported as answer use, or replay omits effective fallback; record basis/actual versions, completeness and grounded answer attribution | Backend + QE, F0035/F0036 |
| Information disclosure | Restricted intermediaries, future topology, spectral bases, counts, caches or timing influence output; constrain the complete eligible domain before scoring/logging and require exact compatibility | Security + QE, RET-35-03 and RET-68-02 |
| Denial of service | Unbounded traversal or numerical work exhausts resources; cap hops, candidates, fan-out, edge types, time and per-tenant cost; no normal-path global per-query decomposition | Backend + AI Engineer, F0035/F0068 |
| Elevation of privilege | Broader grants widen a requested root, stale decisions revive access, or different grant slices are combined; root narrowing, conjunctive dependency checks, final reauthorization and current-authority replay | Backend + Security, F0035/F0036/F0067 |

Authorize seeds, intermediate vertices, edges and evidence dependencies before they affect ranks, visible counts/facets or logs. Endpoint visibility alone does not authorize a relationship. Reuse the execution facade and source/dependency restrictions; do not assemble authority from unrelated grant slices. Missing or incompatible backends can use compatible authorized lexical/hybrid retrieval, otherwise a gap. Current-only topology cannot answer a historical request.

For F0068, matching tenant IDs or filtering final rows is insufficient: the complete influence domain, root, requested scope, mode, snapshot, valid/known coordinates and precision, ontology/content/model/edge profile and authorization revisions must match. Never slice a restricted global eigenbasis and claim isolation. Any relaxation needs a reviewed equivalence/non-influence proof. Projection manifests record build authority but grant no access. Read caches, artifacts and replay under current grants/restrictions; rollback is subject to the same compatibility checks.

Sanitized non-blocking traces contain operation facts and authorized references, not source excerpts, model chain-of-thought or public internal fingerprints/topology summaries. Enforce existing retention/deletion policy on source-bearing derivatives. Trace failure marks incompleteness; it does not manufacture evidence or fail an otherwise authorized answer. F0067 remains read-only and follows answer access.

Acceptance requires non-influence, tenant/root isolation, revocation, historical and source/canonical proofs, negative counts/facets/log/cache/replay tests and assessment of timing channels. With admissible inputs unchanged, mutate/revoke an unauthorized node/edge and compare returned IDs, paths, scores, selected context and visible counts. Any unresolved influence leak blocks that scoring path; spectral quality gains cannot waive it. The feature plan must turn this input into its reviewed threat model and executable proof matrix before approval.
