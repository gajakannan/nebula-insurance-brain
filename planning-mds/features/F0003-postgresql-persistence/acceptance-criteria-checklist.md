# F0003 — Acceptance criteria review

**Review scope:** Phase A requirement quality; this is not implementation acceptance.  
**Planning run:** 2026-09-30-6632006b.

## Clarity and testability

- [x] Each requirement has a database-observable pass/fail result.
- [x] Existing PostgreSQL and tenancy decisions are traced to F0001/F0002 and accepted ADRs.
- [x] The §78 inventory boundary is explicit: F0003 owns inventory and shared persistence rules; feature owners retain domain behavior and later-phase delivery.
- [x] No user-facing screen or direct end-user database access is implied.
- [x] Existing semantic examples are cited; F0003 introduces no new insurance-domain concept.
- [x] Migration and PostgreSQL-specific edge cases are identified; SQLite fixtures are not treated as proof of PostgreSQL constraints.

## Acceptance coverage

| Requirement | Story | Expected cases |
|---|---|---|
| Full §78 table ownership and phase inventory | F0003-S0001 | Every entry has one owner, phase, source contract, and migration boundary; future-only entries remain deferred |
| Tenant/workspace/knowledge-base reference integrity | F0003-S0002 | Valid parent references persist; mismatched owner keys fail without partial writes; existing IDs survive migrations |
| Valid/recorded-time and authoritative-write integrity | F0003-S0003 | Valid intervals persist; invalid or overlapping intervals fail in PostgreSQL; concurrent conflict has one winner; fact/audit/outbox are atomic |
| Safe schema evolution | F0003-S0004 | Supported upgrade preserves data and identifiers; invalid backfill stops with explicit reconciliation; schema head is deterministic |

## Quality and boundaries

- [x] Existing audit and authorization requirements remain with F0002 and the owning operation; database connectivity is not treated as authorization.
- [x] Original source bytes remain in the provider-neutral content-artifact store.
- [x] No production performance threshold is invented.
- [x] Implementation coverage floor is at least 80%; actual coverage evidence belongs to the feature action.
- [x] Direct dependencies are F0001/F0002; impacted feature references and pending evidence audit are recorded in the run artifact trace.
- [x] Infrastructure-story technical-focus warnings are intentional; the internal persistence-engineer persona and downstream feature value are explicit.

## Phase B handoff

- [ ] Architect maps the §78 inventory to owning features and migration stages.
- [ ] Architect documents the concrete SQLAlchemy/Alembic changes and PostgreSQL 18 integration checkpoints.
- [ ] Architect assigns required signoff roles in STATUS.md.
- [ ] KG feature and node shards are updated and compiled; generated projections are not hand-edited.
- [ ] All G5 exit validations pass before requesting Phase B approval.
