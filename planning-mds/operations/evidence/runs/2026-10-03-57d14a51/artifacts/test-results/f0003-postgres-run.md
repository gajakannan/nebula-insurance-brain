# F0003 PostgreSQL Run Output

## Schema upgrade

Target: disposable local Compose database `brain_f0003_g2` (not production).

The first `alembic upgrade head` attempt stopped at revision `0003` because `btree_gist` had not been installed in this newly created database. The extension was then installed in the target database and the migration was retried. The retry completed through revision `0007`:

```text
Running upgrade  -> 0001, content and interpretation
Running upgrade 0001 -> 0002, principals audit and review
Running upgrade 0002 -> 0003, fact slots and commits
Running upgrade 0003 -> 0004, Fenced document jobs and a completion outbox.
Running upgrade 0004 -> 0005, F0002 tenancy and AuthX substrate — expand (ADR-0061/0062).
Running upgrade 0005 -> 0006, F0002 tenancy and AuthX — validate and constrain (ADR-0061).
Running upgrade 0006 -> 0007, F0002 database safeguards (BLUEPRINT §4.11, 2026-09-28).
```

The subsequent repeated `createdb` returned `database already exists`; the following `alembic upgrade head` command still ran and completed successfully.

## PostgreSQL acceptance tests

```text
engine/.venv/bin/python -m pytest \
  engine/tests/integration/test_authx_migration.py \
  engine/tests/integration/test_bitemporal_commit.py \
  engine/tests/integration/test_persistence_contract.py \
  engine/tests/integration/test_commit_concurrency.py \
  engine/tests/integration/test_outbox_replay.py \
  engine/tests/security/test_authx_audit.py \
  -q --cov=brain_persistence
```

Result: **12 passed, 0 failed, 0 skipped**, in 6.20 seconds. Pytest reported 12 Alembic `path_separator` deprecation warnings; no test failed. Per-test names and timing are in `f0003-postgres.xml`; the focused-run coverage report is `../coverage/f0003-postgres.xml`.
