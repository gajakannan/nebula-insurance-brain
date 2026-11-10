# G1 Runtime Preflight — F0007

- Run: `2026-11-09-b94cfa12`
- Role: DevOps
- Reviewer: Claude (Opus 5.5) / DevOps
- Date: 2026-11-09 (probes at 2026-11-10T01:35Z)
- Verdict: PASS
- runtime_bearing: true

## Runtime under test

F0007 is engine-only: a domain module set, a new `brain-factslots` package, migration 0012 and a commit hook. Its application runtime is the local Compose PostgreSQL plus the locked engine virtual environment (`engine/.venv`, Python 3.14 from `uv sync --locked`). The OIDC services (authentik) are not needed: the API tests override the principal dependency, and F0007 adds no route or identity flow.

| Probe | Result | Evidence |
|---|---|---|
| `docker compose ps` and health | `brain-postgres` (`brain-postgres:18-pgvector-age`) Up, health `healthy`. Authentik containers are not running, which F0007 does not need. | `artifacts/test-results/command-output/g1-compose-ps.txt` |
| Server and extensions | PostgreSQL 18.6; `vector` 0.8.6, `age` 1.8.0, `btree_gist` 1.8, matching `docker/DEPENDENCY-MATRIX.md` | same file |
| Migration lineage | Code head `0011`. The shared development database is at `0010`; F0007 never migrates or truncates it. | `artifacts/test-results/command-output/g1-alembic-current.txt` |
| Owned test databases | Created, connected to and dropped a throwaway database through `BRAIN_MIGRATION_ADMIN_URL=postgresql://brain:brain@localhost:5432/brain` | `artifacts/test-results/command-output/g1-owned-db-probe.txt` |
| Pre-change regression baseline | `test_bitemporal_commit`, `test_commit_concurrency`, `test_assertion_consumers`, `apps/api/tests/test_facts.py`, `test_reviews.py`: 27 passed, 0 skipped | `artifacts/test-results/command-output/g1-baseline-regression.txt`, `artifacts/test-results/g1-baseline-regression.xml` |

## Runtime-blocked protocol

If a later validation fails with connection, DNS or missing-container symptoms, the run stops code edits, records `runtime-blocked`, restores `brain-postgres`, and re-runs the same command unchanged before treating the failure as a defect.

## Environment contract

F0007 adds no environment variable, secret, container or port. The test-only `BRAIN_MIGRATION_ADMIN_URL` already exists for F0002/F0006 suites. CI wiring for the new suites is a G2 deployability item.
