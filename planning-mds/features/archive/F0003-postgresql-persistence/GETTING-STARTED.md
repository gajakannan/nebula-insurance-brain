# F0003 — PostgreSQL persistence implementation entry point

This is an implementation handoff for the later `feature` action. Planning approval does not mean runtime work or database verification has happened.

## Read first

1. `PRD.md` for accepted scope and non-goals.
2. `feature-assembly-plan.md` for the §78 owner/phase inventory, existing migration origins, and build sequence.
3. `F0003-S0001` through `F0003-S0004` for acceptance criteria and dependency boundaries.
4. `planning-mds/architecture/decisions/ADR-0002-postgresql-is-the-authoritative-runtime-store.md`, ADR-0007, ADR-0008, ADR-0010, ADR-0030, and ADR-0059.
5. F0001's accepted persistence proofs and F0002's tenancy/ownership contracts before changing any shared key or constraint.

## Implementation boundary

- Work from the accepted migration head in `engine/migrations/versions/`; retain revisions 0001–0007 and existing IDs/history.
- Keep shared SQLAlchemy mappings and repository mechanics in `engine/packages/brain-persistence/`. Keep domain-specific columns and behavior with the owner named in the assembly inventory.
- Add an owner feature's table only after its accepted contract exists. Do not materialize later-phase §78 rows early.
- Treat the `role` and `permission` entries as an explicit F0002 representation reconciliation. Do not create relational tables or change F0002 policy without an approved owner decision.
- Carry ownership keys through child and multi-parent foreign keys. Preserve F0002 immutability and authorization boundaries.
- Use PostgreSQL 18 to verify range/GiST, composite-FK, concurrent-write, transactional rollback, and migration behavior. SQLite results cannot prove those database invariants.
- Keep facts, required audit, and outbox writes in the owner operation's transaction. Keep projections rebuildable and idempotent.
- Preserve evidence/derivation links and append-only corrections. Keep original artifact bytes in the configured storage port; do not put source text or runtime secrets in migration state/logs.

## Verification handoff

The feature action must map every acceptance criterion to named tests and actual evidence, run clean-install and accepted-head upgrade paths on PostgreSQL 18, measure changed persistence coverage at or above 80%, and collect the required QE, Code Reviewer, Security Reviewer, DevOps, and Architect signoffs. The plan run did not execute implementation tests or create feature evidence.
