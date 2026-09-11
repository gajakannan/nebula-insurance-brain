# ADR-0041: Atomic Semantic Commit and Projection Delivery

## Status

- [ ] Proposed
- [x] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Settled:** 2026-09-10 (F0001-S0007), from F0001-S0005's live proof run on 2026-09-10
**Deciders:** Architect (record owner); backend-developer executed the proof
**Settled by:** F0001-S0005 (bitemporal commit under retroactive and concurrent change); results recorded by F0001-S0007
**Source:** `planning-mds/architecture/master-blueprint.md` section 116

## Context

Proposed in the master blueprint pre-build requirements to settle: Canonical transaction + audit + outbox; versioned/rebuildable projections.

Example and reference: Crash after commit; section 109.

## Decision

**Accepted.** Canonical transaction + audit + outbox; versioned/rebuildable projections.

`canonical_fact_version.valid` and `.recorded` are independent PostgreSQL
`tstzrange` columns — the recorded-interval policy this ADR settles is two
genuinely independent temporal dimensions, not one range doing double duty.
Overlap on both dimensions at once is impossible by construction: a
`EXCLUDE USING gist (slot_id WITH =, valid WITH &&, recorded WITH &&)`
constraint enforces it at the database level, beneath and independent of the
application-level row lock. One transaction writes the fact version(s), the
`canonical_fact_change` lineage row(s), the `audit_event`, and the
`outbox_event` together; a killed worker replays the outbox exactly once
because the projector's own watermark (`processed_at`), not the outbox
producer, decides what is left to do.

## Results (F0001-S0005, measured 2026-09-10)

- **Section 87 matrix after reload:** an endorsement narrows the answer for
  `[2026-01-01, 2026-06-01)` via a `SPLIT` remainder while the original
  version's own `valid`/`recorded` ranges are never rewritten — every prior
  version stays readable at its original recorded coordinates. Proven against
  both an in-memory fake (algorithm) and a real reload from Postgres.
  Tests: `engine/packages/brain-temporal/tests/test_commit.py`,
  `engine/tests/integration/test_bitemporal_commit.py`.
- **Concurrency: exactly one winner.** Two concurrent commits on the same slot
  race through two independent `asyncio` tasks and two independent DB sessions.
  `SELECT ... FOR UPDATE` on the `fact_slot` row serializes them; the loser's
  lock wait ends only after the winner commits, then it observes
  `expected_current_version_id` no longer current and raises `StaleVersionError`
  — one winner, one rejection, zero ambiguous states. A manual `psql` probe
  additionally confirmed the GiST exclusion constraint itself independently
  rejects an overlapping-`recorded` insert, even with disjoint `valid` ranges —
  the database-level backstop behind the row lock.
  Test: `engine/tests/integration/test_commit_concurrency.py`.
- **Outbox replay processes once.** A commit's `outbox_event` row is picked up
  by `OutboxProjector.run_once()`; calling it again (simulating a worker
  restart after a kill) processes zero further events — idempotent by
  construction, since `unprocessed()` excludes anything already watermarked.
  Test: `engine/tests/integration/test_outbox_replay.py`.
- **Timestamps stored separately, as required:** `source_received_at`,
  `artifact_created_at`, `assertion_created_at`, and `canonical_accepted_at`
  are four distinct columns on `canonical_fact_version`; `recorded`'s lower
  bound equals `canonical_accepted_at`, not any of the other three.

## References

- `planning-mds/architecture/master-blueprint.md` section 116 and the section cited above
- `engine/packages/brain-temporal/src/brain_temporal/commit.py` (`CanonicalCommitService`)
- `engine/migrations/versions/0003_fact_slots_and_commits.py`
- `engine/tests/integration/test_bitemporal_commit.py`, `test_commit_concurrency.py`, `test_outbox_replay.py`
- `planning-mds/features/F0001-repository-and-engineering-foundation/STATUS.md` (Backend Progress, S0005)
