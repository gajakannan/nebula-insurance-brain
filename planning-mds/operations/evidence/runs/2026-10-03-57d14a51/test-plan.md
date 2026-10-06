---
template: test-plan
version: 2.0
applies_to: quality-engineer
---

# Test Plan — F0003-postgresql-persistence run 2026-10-03-57d14a51

## Story-to-AC Mapping

| Story | AC | Lane | Test ID | Owner |
|---|---|---|---|---|
| F0003-S0001 | §78 table ownership, phase, source contract, and migration boundary | Static plan validation | `G0` plus feature assembly plan review | Architect |
| F0003-S0001 | Existing provenance remains linked; later-phase behavior stays deferred; bytes remain behind storage ports | Static contract review | `feature-assembly-plan.md` and ADR-0059 boundary review | Architect / QE |
| F0003-S0002 | Valid owner references persist and are readable in a new session | PostgreSQL integration | `engine/tests/integration/test_authx_migration.py` | QE |
| F0003-S0002 | Cross-owner references fail without partial writes | PostgreSQL integration | `engine/tests/integration/test_authx_migration.py` | QE |
| F0003-S0002 | Existing IDs and valid history survive additive migration | Migration integration | `engine/tests/integration/test_authx_migration.py` | QE |
| F0003-S0003 | Valid and recorded periods remain independently queryable | PostgreSQL integration | `engine/tests/integration/test_bitemporal_commit.py` | QE |
| F0003-S0003 | Fact, required audit, and outbox writes are atomic; committed state survives a new session | PostgreSQL integration/security | `engine/tests/integration/test_bitemporal_commit.py`; `engine/tests/security/test_authx_audit.py` | QE |
| F0003-S0003 | Conflicting ranges and concurrent writes cannot leave ambiguous accepted state | PostgreSQL integration | `engine/tests/integration/test_persistence_contract.py`; `engine/tests/integration/test_commit_concurrency.py` | QE |
| F0003-S0003 | Outbox retry is idempotent | PostgreSQL integration | `engine/tests/integration/test_outbox_replay.py` | QE |
| F0003-S0004 | Accepted migration sequence preserves identifiers and reaches deterministic head | Migration integration | `engine/tests/integration/test_authx_migration.py` plus clean PostgreSQL 18 upgrade | QE / DevOps |
| F0003-S0004 | Ambiguous backfill fails closed and migration audit records outcome | Migration integration/review | `test_mixed_kb_batch_blocks_reconciliation_without_partial_writes`; `test_expand_reconcile_constrain_preserves_ids_and_enforces_ownership` | QE / DevOps |

## Test Strategy

- Unit/contract: engine contract tests using the existing engine virtualenv.
- Integration: live PostgreSQL 18 using the Compose database; SQLite is not accepted as evidence for range or owner constraints.
- Migration: test the supported upgrade path from the accepted F0002 head on a clean PostgreSQL database and verify preserved IDs/history.
- Security: verify audit persistence and owner isolation through existing F0002-facing tests; the Security Reviewer remains required by STATUS.md.
- No frontend, accessibility, or E2E lane applies to this infrastructure feature.

## Developer-vs-QE Test Ownership

Developer-owned: persistence package unit/contract tests and migration implementation tests. QE-owned: live PostgreSQL owner/reference, bitemporal exclusion, concurrency, transaction rollback, outbox replay, and clean-upgrade acceptance. DevOps owns the operational upgrade/recovery check.

## Test Data / Fixtures

Use isolated tenant, knowledge-base, fact-slot, commit, and migration fixtures against the real PostgreSQL 18 service. Do not use production records or source bytes. Existing integration fixtures truncate their owned fact tables after each test.

## Happy / Edge / Error / Auth / Accessibility / Regression Cases

- Happy: valid tenant/KB parent references; valid temporal ranges; commit and reload; supported upgrade with stable IDs.
- Edge/error: mismatched owner keys, overlapping valid and recorded ranges, concurrent conflicting writes, ambiguous backfill, migration failure, audit/outbox write failure.
- Auth/regression: owner isolation and atomic audit behavior; idempotent outbox replay; preserve F0001/F0002 IDs and migration contracts.
- Accessibility: not applicable; there is no user interface in scope.

## Risks And Mitigations

- Tests requiring PostgreSQL were run against a disposable PostgreSQL 18 Compose database. The first migration attempt lacked the database-local `btree_gist` extension; after installing it, the clean upgrade reached `0007` and all planned PostgreSQL acceptance tests passed.
- Existing migration tests cover mixed-KB backfill rejection without partial writes and successful reconciliation audit recording; no additional migration test was needed.

## Result

Result: PASS
