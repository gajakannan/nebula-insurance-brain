# Deployability Check — F0008 (run 2026-11-17-1a4ae2f0)

- Role: DevOps
- Reviewer: Claude (Opus 5.5) / DevOps
- Date: 2026-11-17
- Verdict: PASS (local development deployability; the production host stays open under F0026)

## What deploys

- **Migration `0014_f0008_bitemporal_contract.py`** (`down_revision = "0013"`, the single head). It adds:
  - 16 nullable columns;
  - CHECKs;
  - a composite self-FK;
  - a partial index;
  - three functions and six triggers.

  It modifies no existing row and adds no table, role, grant, RLS policy, `BYPASSRLS` role or `SECURITY DEFINER` function. Every function is `SECURITY INVOKER` with a pinned `search_path`.
- **Engine code** in existing packages (`brain_domain`, `brain_temporal`, `brain_persistence`, `brain_api`). There is no new package, dependency, container, port, environment variable or secret. `uv.lock` and every `pyproject.toml` are unchanged against `origin/main`.

## Evidence

| Check | Result | Evidence |
|---|---|---|
| Runtime preflight | PASS; Docker Desktop restored, `brain-postgres` healthy | `g1-runtime-preflight.md` |
| Fresh database to head (0001→0014) | PASS | `artifacts/test-results/command-output/g1-shared-db-upgrade-head.txt` and the fresh run before the final regression |
| Alembic CLI cycle `upgrade head → downgrade 0013 → upgrade head` | PASS; `current` reads 0014, 0013, 0014 | `artifacts/test-results/command-output/g2-migration-cycle.txt` |
| Up/down/up on seeded pilot and F0007 identity-v1 rows, byte-identical snapshot | PASS | `test_temporal_migration.py::test_s0007_ac1_ac2_ac4_ac6_*` |
| Downgrade guard: refuses while v1 or lineage rows exist and names them | PASS | `test_temporal_migration.py::test_s0007_ac4_*` |
| Upgrade preflight: refuses a bad identity-v1 envelope, repairs nothing, stays at 0013 | PASS | `test_temporal_migration.py::test_d7_*` |
| Revision coordination with F0011 | F0011 is still Planned with no branch, and no remote branch has a `0014`. Whichever lane merges second renumbers. | `artifacts/test-results/g0-migration-lineage.json` |
| CI wiring | A new runtime-stack step runs the F0008 unit and PostgreSQL suites against owned databases with a `brain_temporal` coverage floor (`.github/workflows/ci-gates.yml`). The no-database package gates still pass: `brain_temporal` 96.6%, `brain_api` 82.3%, `brain_domain` 90.8%, `brain_factslots` 87.7%. | `test-execution-report.md` |
| Test-harness cleanup under the new truncate triggers | The three shared-DB cleanup fixtures use `SET LOCAL session_replication_role = replica`, which is superuser-only. The CI AuthX security job, which truncates after `alembic upgrade head`, is covered. | full regression |

## Rollback

- **While no temporal-v1 row exists:** `alembic downgrade 0013` restores the pilot schema exactly, with no row rewritten.
- **Once a temporal-v1 row exists:** the downgrade refuses and names the blocking version IDs, so the only way back is to roll forward. This matches the assembly plan's rollback section.

## Environment contract

- No environment variable is added.
- The tests use the existing test-only `BRAIN_MIGRATION_ADMIN_URL` and `BRAIN_DATABASE_URL`.
- Operators: the shared development database `brain` is at revision 0010 and stays untouched by this run. Running `alembic upgrade head` there applies 0011–0014.
