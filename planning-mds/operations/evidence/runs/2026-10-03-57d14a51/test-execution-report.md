# Test Execution Report — F0003-postgresql-persistence run 2026-10-03-57d14a51

## Commands Executed

| Lane | Command / source | Result | Raw evidence |
|---|---|---|---|
| Clean PostgreSQL 18 schema upgrade | Alembic upgrade against disposable brain_f0003_g2 after installing database-local extensions | PASS; revisions 0001 through 0007 applied | artifacts/test-results/f0003-migration-run-record.md |
| PostgreSQL acceptance and migration integration | Six planned F0003 integration/security modules against brain_f0003_g2 and the Compose admin database | 12 passed, 0 failed, 0 skipped | See raw artifact list below |
| Persistence package coverage gate | Hosted CI run 37251703741, runtime-suites job 111580493891, same PR head 1e9db3381d63c8634b52d8e172ccd36a1e3cdf73 | 11 passed; 87.78% package coverage; gate passed | See raw artifact list below |

The PostgreSQL command covered test_authx_migration.py (4 cases), test_bitemporal_commit.py (1), test_persistence_contract.py (1), test_commit_concurrency.py (1), test_outbox_replay.py (1), and test_authx_audit.py (4). The migration cases prove preservation of existing IDs and audit history, fail-closed behavior for mixed-KB reconciliation and invalid IDs, a single successful reconciliation audit, and the 0007 append-only/ownership safeguards.

## Pass/Fail Counts

| Lane | Total | Pass | Fail | Skip | Retries |
|---|---:|---:|---:|---:|---:|
| F0003 live PostgreSQL acceptance and migration | 12 | 12 | 0 | 0 | 1 migration setup retry after adding the database-local extension |
| brain-persistence package coverage suite (hosted CI) | 11 | 11 | 0 | 0 | 0 |

## Skipped Tests And Rationale

No tests in the F0003 PostgreSQL acceptance command were skipped. The suite connected to the live local PostgreSQL 18 service.

## Raw Test Artifact Paths

- artifacts/test-results/f0003-postgres.xml
- artifacts/test-results/f0003-postgres-run.md
- artifacts/test-results/f0003-migration-run-record.md
- artifacts/test-results/g2-ci-37241111686.md
- artifacts/coverage/f0003-postgres.xml
- artifacts/coverage/brain-persistence-ci-coverage.log

## Failed / Retried Command History

- The first clean-database migration attempt stopped at revision 0003 because btree_gist was not installed in the newly created database. Installing the extension in that database and rerunning alembic upgrade head succeeded through 0007. See artifacts/test-results/f0003-postgres-run.md
- A repeated createdb command returned “database already exists.” The shell then ran alembic upgrade head, which completed successfully.
- Earlier G2 attempts in this run could not reach PostgreSQL from the sandbox and did not complete. They are superseded by the complete local PostgreSQL acceptance run above.
- An optional local repeat of the package coverage suite was interrupted before pytest produced output. It is not counted as a result; the same package suite passed in the hosted run cited above.

## AC Coverage Result

| Story | Outcome |
|---|---|
| F0003-S0001 | Plan ownership and phase boundaries passed G0; the quality review confirmed source and storage-port boundaries. |
| F0003-S0002 | PASS: migration integration suite exercised owner/reference preservation, cross-owner rejection, and audit/history preservation. |
| F0003-S0003 | PASS: live PostgreSQL tests covered reload, bitemporal exclusion, concurrent commits, idempotent outbox replay, and required audit behavior. |
| F0003-S0004 | PASS: the migration run record identifies the operator account, ISO timestamp, revision, and outcome; PostgreSQL migration tests cover fail-closed backfill, no partial writes, successful reconciliation audit, and deterministic head. |

## Result

Result: PASS
