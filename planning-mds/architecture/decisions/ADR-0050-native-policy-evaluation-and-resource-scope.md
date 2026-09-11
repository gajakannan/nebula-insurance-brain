# ADR-0050: Native Policy Evaluation and Resource Scope

## Status

- [ ] Proposed
- [x] Accepted (for the boundary F0001-S0006 proved; see Scope note)
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Settled:** 2026-09-10 (F0001-S0007), from F0001-S0006's live proof run on 2026-09-10
**Deciders:** Architect (record owner); backend-developer executed the proof
**Settled by:** F0001-S0006 (access boundaries, extension build, and restore); results recorded by F0001-S0007
**Source:** `planning-mds/architecture/master-blueprint.md` section 122

## Context

Proposed AuthX decision carried from the CRM reference architecture into the Brain (master blueprint sections 118 to 122). The CRM code establishes the reference contracts; the Brain implements the same contracts in its Python backend behind explicit adapters.

## Decision

**Accepted.** Casbin adapter plus typed scopes and parent/classification constraints; policy parity across runtimes.

`AuthorizationService` structurally conjuncts tenant/knowledge-base membership
against the resource's own tenant/knowledge-base *before* Casbin ever
evaluates a rule — a real Casbin `allow` on the wrong scope can never leak
through, because the membership match runs first and short-circuits to denial
otherwise. Casbin itself evaluates role/resource-type/action against
`planning-mds/security/policies/{model.conf,policy.csv}`, the same policy
files every resource type (content artifact, review task, fact slot) shares.

## Results (F0001-S0006, measured 2026-09-10)

- **Real Casbin evaluation, not a stub:** every authorization decision runs
  the actual `CasbinAuthorizationAdapter` against the committed policy files,
  for all three resource types this feature has (`content_artifact`,
  `review_task`, `fact_slot`).
- **Cross-scope denial proven across all three resource types in one place:**
  principal A (a real membership in tenant A) reads A's own content artifact,
  review task, and fact (200 on all three); the same principal is denied
  (404, never 403) the equivalent resource in tenant B, across all three —
  and a principal with a verified credential but zero memberships anywhere
  gets 404, not 401 (denial is authorization, not authentication).
  Test: `engine/tests/security/test_scope_isolation.py` (3 tests).
- **Audit records the decision inputs required for governance:** every
  `authorize()` call writes an `audit_event` with `policy_hash`,
  `grant_revision`, actor, resource, action, `decision`, and `reason_code`
  (`no_membership` when structurally denied before Casbin runs,
  `policy_denied` when Casbin itself denies, `allowed` otherwise) — the
  specific reason is never returned to the caller.
- **A reviewer cannot commit canonical truth (parent/classification-adjacent
  constraint, proven jointly with ADR-0044):** the `Reviewer` role has
  `review:annotate` but not `fact_slot:commit`; only `ServicePrincipal` has
  the latter. Attempting to commit as a `TenantMember` is denied identically
  to any other out-of-scope action.
  Test: `engine/tests/security/test_scope_isolation.py::test_principal_a_reads_own_resources_across_all_three_types`
  (the commit-attempt assertion within it).

## Scope note

"Policy parity across runtimes" in this ADR's own decision text refers to
cross-repository parity between the Brain's Python/Casbin evaluation and the
CRM reference's .NET/Casbin evaluation against shared fixtures (master
blueprint section 121.2 item 11) — that parity work is explicitly F0026's
scope (`F0026 — v0.1 hardening + Golden Corpus workflow + AuthX negative tests
and policy parity`), not F0001-S0006's. F0001-S0006 proved the Brain's own
native adapter and typed resource scopes correctly, in isolation; it did not
and was not meant to compare behavior against the CRM's C# implementation.
The same broader-matrix caveat in [ADR-0049](ADR-0049-shared-identity-and-verified-principal-boundary.md)'s
Scope note applies here too (items 4 to 11 beyond what's listed above remain
open, owned by F0002/F0018/F0021/F0026).

## Consequences

- Shared behavior fixtures and schema contracts guard against semantic drift between the CRM reference and the Brain implementation.
- The structural tenant/KB conjunction, real Casbin evaluation, and
  denial-never-discloses-existence behavior are now locked contracts other
  features build on.
- Cross-runtime policy parity (F0026) and the fuller permission catalog
  (F0002/F0018) remain open, tracked by their own features.

## References

- `planning-mds/architecture/master-blueprint.md` sections 118 to 123
- `engine/packages/brain-security/src/brain_security/authorization.py`, `casbin_adapter.py`
- `planning-mds/security/policies/model.conf`, `policy.csv`
- `engine/tests/security/test_scope_isolation.py`
- `planning-mds/features/F0001-repository-and-engineering-foundation/STATUS.md` (Backend Progress, S0006)
