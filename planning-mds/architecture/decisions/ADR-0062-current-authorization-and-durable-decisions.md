# ADR-0062: Current authorization and durable decisions

## Status

- [x] Proposed — F0002 Phase B design; design approved by user 2026-09-25; runtime/security proof pending
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-25
**Deciders:** Architect; pilot role reuse approved by the user in Phase A.

## Context

F0001’s AuthorizationService uses the first matching membership; ResourceRef.classification does not reach the active Casbin matcher. API read audit uses flush without an explicit commit. The later F0005 worker has its own synchronous authorizer, correctly re-reading grants and committing audit, but must not become an independent interpretation of the shared contract.

## Decision

Keep Casbin as the role/resource/action evaluator and retain every current policy row. Add mandatory typed checks around it: active verified identity, current membership, actual parent scope, classification/source restrictions, evidence dependencies and delegation ceiling. Preserve complete grant slices; allow if at least one matching slice permits the entire resource/action. Never flatten separate grant attributes into a Cartesian product of permissions.

```text
verified credential -> stable principal -> current grant slices
                                          + trusted resource restrictions
                                          + optional bounded delegation
                                          -> pure conjunctive evaluator -> durable decision
                                                                        -> protected operation
```

An internal context is assembled by trusted repositories, never deserialized from a client/model as authority. Request filters only intersect authority. No grant cache in v1; pin an immutable policy release containing both model and policy hashes, and take current database revisions at every protected operation. Business query time is not authorization time.

For delegated work, require verified executor, current acting-user grants and a server-owned expiring delegation bound to that executor. Its ceiling cannot add actions/resources. No onward delegation in v1. Autonomous services use their own grants and have no fabricated human actor. Both sync worker and async API adapters invoke the same pure evaluator and decision shape.

Read allows and denials must commit a minimal audit transaction before returning protected content or a denial. Write allows are recorded atomically with business state and its existing outbox; denied/failed writes roll back business work and persist the decision in a separate audit transaction. Audit failure returns a sanitized unavailable outcome and releases no protected content or successful mutation. Invalid credentials use a separate durable authentication-event sink without looking up a principal or protected resource; identity fields remain unresolved. Historical audit rows remain immutable.

Authority revision and resource restriction locks serialize changes with protected operations. A revoke completed before the next operation must be observed; an already linearized operation may finish. Expiry is rechecked immediately before the effect. No claim is made to recall already downloaded data.

## Ownership reconciliation

Master blueprint §116.1’s historical phrase “review-decision-to-canonical-commit wiring itself is F0002’s integration” is narrowed by the approved PRD: F0002 integrates common authorization and audit into existing review/commit consumers and proves they stay independent. F0018 owns the full review-to-canonical acceptance orchestration; F0022 owns review evidence assembly and UI. Annotation does not trigger canonical acceptance in F0002. This records reconciliation without rewriting approved product scope.

## Alternatives and consequences

Duplicating all restrictions in Casbin expressions would hide typed hydration and is unnecessary to keep the current pilot policy. A shared mutable grant cache would complicate revocation and is deferred. Auditing only in the business transaction loses denied operations after rollback; a detached audit for successful writes breaks atomicity. Use the split transaction rules above.

## Acceptance

S0003–S0006 prove each restriction independently, all-grant selection, no mixed-slice widening, bounded delegation, revocation/expiry and injected audit failures through existing API and worker consumers. QE/Security and Architect sign off actual evidence; DevOps verifies deployment/migration. ADR-0042/0052/0053 retain Proposed status for their broader surfaces. Cross-runtime policy parity is F0026. This ADR does not accept those global obligations by passing schema or planning checks.

## References

- [F0002 assembly plan](../../features/F0002-tenancy-aware-domain-kernel-and-principal-contracts/feature-assembly-plan.md)
- [ADR-0050](ADR-0050-native-policy-evaluation-and-resource-scope.md)
- [ADR-0052](ADR-0052-delegated-agents-and-review-authority.md), [ADR-0053](ADR-0053-permission-safe-retrieval-and-historical-access.md)
