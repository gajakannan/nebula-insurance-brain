# ADR-0053: Permission-Safe Retrieval and Historical Access

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Decision recorded:** 2026-11-08 by the operator (blueprint requirement-ownership amendment). Features plan against the decision below. The status stays Proposed until the carryover tests below pass.
**Owner:** Architect + Security Reviewer
**Proving features:** F0020/F0023/F0069 (v0.1 query, display and constrained answers), F0026 (v0.1 negative tests), F0033 to F0036 and F0046/F0047 (projections, v0.2)
**Formal acceptance:** section 121.2 items 5 (projection leakage), 6 (conversation access) and 12 (temporal separation) pass for the v0.1 surfaces in F0026; projection cases are added as each v0.2 projection ships.
**Source:** `planning-mds/architecture/master-blueprint.md` sections 110.1, 120.3 and 122

## Context

Bitemporal queries can ask what was known in the past. They must not bring back access that has since been revoked, and every projection (search, vector, graph, cache) must apply the same grants as the canonical store.

## Decision

1. **Current grants always apply.** Every read — including a query as of a past valid or recorded time — is authorized against the principal's current grants and policy revision.
2. **History is not an access path.** A historical query reconstructs past knowledge, never past permissions. Privileged audit can reconstruct prior authorization decisions without executing them.
3. **Authorization before shaping.** Rows, counts, facets, snippets, titles, graph paths, embeddings and aggregates are filtered before they are computed or returned. Unfiltered candidates never reach a model.
4. **Revocation mid-conversation.** After a user loses access, later turns, history rendering, cached answers, evidence links and review tasks follow the new policy. Revoked content cannot re-enter through a summary or learned artifact.

## Consequences

- F0020 and F0023 apply rules 1 to 3 to the v0.1 query API and Entity 360; F0069 applies rule 4 to the constrained policy question.
- F0026 runs the v0.1 negative tests; F0033 to F0036 extend them to projections.

## References

- `planning-mds/architecture/master-blueprint.md` sections 110.1, 118 to 123
