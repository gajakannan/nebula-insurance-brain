# G1 Runtime Preflight — F0008

- Run: `2026-11-17-1a4ae2f0`
- Role: DevOps
- Reviewer: Claude (Opus 5.5) / DevOps
- Date: 2026-11-17
- Verdict: PASS
- runtime_bearing: true

## Runtime under test

F0008 touches only the engine:

- migration 0014;
- domain and temporal modules;
- the persistence repository;
- the `/facts` route mapping.

Its runtime is the local Compose PostgreSQL plus the locked engine virtual environment (`engine/.venv`, Python 3.14.4). It does not need authentik, because the API tests override the principal dependency and F0008 adds no identity flow.

## Restoration performed

At session start the Docker Desktop daemon was stopped: `npipe` dockerDesktopLinuxEngine was missing and port 5432 refused connections. Docker Desktop was started on the host. `brain-postgres` then came up under its restart policy and reported `healthy`. No code was edited before this preflight.

The first baseline attempt failed with `UndefinedColumnError: fact_slot.identity_version`. That was runtime state, not a code defect: the shared development database `brain` sits at revision `0010` while the code head is `0013`. F0008 leaves the shared database alone. A disposable database, `brain_f0008_shared`, was created with `btree_gist` and migrated to head. The same baseline command then re-ran unchanged against it and passed.

## Probes

| Probe | Result | Evidence |
|---|---|---|
| `docker compose ps` and health | `brain-postgres` (`brain-postgres:18-pgvector-age`) is Up and `healthy` on port 5432 | `artifacts/test-results/g1-compose-ps.txt` |
| Server and extensions | PostgreSQL 18.6, `vector` 0.8.6, `age` 1.8.0, `btree_gist` 1.8. These match `docker/DEPENDENCY-MATRIX.md`. The `brain` role is a superuser in this local stack. | same file |
| Migration lineage | The code head is `0013`. The shared `brain` database is at `0010` and is not modified. The disposable `brain_f0008_shared` database migrated cleanly from 0001 to 0013. | `artifacts/test-results/command-output/g1-shared-db-upgrade-head.txt` |
| Owned test databases | The F0006/F0007 harness creates and drops `f0006_qe_*` databases through `BRAIN_MIGRATION_ADMIN_URL=postgresql://brain:brain@localhost:5432/brain`. The baseline exercised this in the F0007 suites. | baseline output |
| tzdata (ADR-0078 D2) | PostgreSQL uses system tzdata `2025b-4+deb13u1` (`--with-system-tzdata`, 487 zone names). Python `zoneinfo` uses host system tzdata `2026e`, and the `tzdata` package is not installed. The versions differ. D2 makes the database authoritative, so the service check is advisory. No fixture zone (`America/Chicago`, `Etc/GMT+6`, `UTC`) differs between these releases for the 2025–2026 instants used. | `artifacts/test-results/g1-tzdata-versions.txt` |
| Pre-change regression baseline | 74 passed, 0 failed, 0 skipped. Suites: `test_bitemporal_commit`, `test_commit_concurrency`, `apps/api/tests/test_facts.py`, `test_factslot_answers`, `test_factslot_ownership`, `test_factslot_migration`, `brain-temporal` unit tests. | `artifacts/test-results/command-output/g1-baseline-regression.txt`, `artifacts/test-results/g1-baseline-regression.xml` |

## Runtime-blocked protocol

If a later validation fails with a connection, DNS or missing-container symptom, the run stops code edits and records `runtime-blocked`. It then restores `brain-postgres` (and Docker Desktop if needed) and re-runs the same command unchanged. Only a failure that persists after that is treated as a defect.

## Environment contract

F0008 adds no environment variable, secret, container or port. The shared-database suites in this run use `BRAIN_DATABASE_URL=postgresql+asyncpg://brain:brain@localhost:5432/brain_f0008_shared`, a disposable database migrated to head, as CI does with its fresh database. The owned-database suites use the existing test-only `BRAIN_MIGRATION_ADMIN_URL`. Wiring the new suites into CI is a G2 deployability item.
