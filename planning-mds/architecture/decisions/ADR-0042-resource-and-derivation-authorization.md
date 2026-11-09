# ADR-0042: Resource and Derivation Authorization

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Decision recorded:** 2026-11-08 by the operator (blueprint requirement-ownership amendment). Features plan against the decision below. The status stays Proposed under the section 106 decision posture until the proof below is recorded.
**Owner:** Architect + Security Reviewer
**Proving features:** F0002 (resource scope, parent/classification conjunction; delivered for its bounded scope), F0018 (authorization envelope at commit), F0020/F0023 (query and display), F0065 (derived assessments), F0026 (isolation proof)
**Formal acceptance:** the section 110.2 restricted-note case and the section 121.2 items 4 and 5 projection-leakage cases pass in F0026, with PostgreSQL row security tested under the actual application and worker roles.
**Source:** `planning-mds/architecture/master-blueprint.md` sections 110.1, 110.2 and 116

## Context

Tenant IDs are necessary but insufficient. Entity visibility does not imply access to every fact about the entity, and derived results can leak the restricted material they were computed from (sections 110.1 and 110.2).

## Decision

1. **One authorization envelope** carries principal, tenant, knowledge-base grants, resource restrictions, purpose and the current authorization-policy revision through every enforcement point: API, worker, commit, query, review, export, model context and cache.
2. **Ownership binding.** Every child row and foreign key binds to its tenant owner. Object-store reads, exports and review tasks go through the same envelope.
3. **Row security is defense in depth, not the boundary.** New tenant-owned tables enable PostgreSQL row-level security policies tested under the real application and worker roles (no superuser, `BYPASSRLS` or table-owner shortcuts). Application authorization remains the primary control.
4. **Derived results inherit restrictions.** A user receives a derived result only if entitled to all of its evidence dependencies, unless an explicit, authorized declassification or aggregation policy applies. This covers titles, counts, embeddings, summaries and assessments.
5. **Caches are partitioned** by effective authorization context and invalidated on grant revision.
6. **Recheck before emission.** Authorization is checked again before content goes to a model, an answer is returned, or evidence is opened.

## Consequences

- F0018 Phase B designs the envelope and the row-security policy pattern for new tables; F0026 proves isolation.
- F0065 assessments and F0069 answers record their evidence dependencies so that rule 4 can be enforced.
- Graph and vector projections (F0033/F0034) must validate their own query paths; relational policies are not assumed to cover AGE traversals.

## References

- `planning-mds/architecture/master-blueprint.md` sections 106.3, 110.1, 110.2, 116, 120.3 and 121.2
