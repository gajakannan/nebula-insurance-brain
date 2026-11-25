# G1 Runtime Preflight — F0009

- Role: DevOps
- Reviewer: Claude (Opus 5.5) / DevOps
- Date: 2026-11-24
- Run: `2026-11-24-08701e37`
- Verdict: PASS. The engine, node and dedicated PostgreSQL validation runtime is ready.

Result: PASS

## Runtime

The [run-local compose definition](artifacts/runtime/compose.yaml) starts two validation containers on the existing `nebula-insurance-brain_default` network. Both report healthy:

- `engine-validation`: the cached `brain-f0011-contract-engine:2026-11-22-885e8734` image (Python 3.14.4, uv 0.11.31, nonroot `app`). It uses a writable task virtual environment at `/tmp/f0009-engine-venv`, built with `uv sync --project engine --group contract-build --locked`.
- `node-validation`: `node:22` (Node 22.23.1) with pnpm 12.21.0 through corepack, matching `experience/package.json` `packageManager`. The frozen install succeeded ([node-install.txt](artifacts/runtime/node-install.txt)).

The existing `brain-postgres` service (`brain-postgres:18-pgvector-age`, healthy) hosts a new dedicated database, `brain_f0009`, owned by the application role, with `btree_gist`. Alembic brought it from empty to **0015 (head)**. F0009 tests use this database only, so the integration databases of other features are not touched. Owned-database migration suites create and drop their own temporary databases through `BRAIN_MIGRATION_ADMIN_URL`. No credential beyond the existing local development role is introduced, and artifacts redact the connection user and password.

## Baseline (before any F0009 code change)

| Check | Result | Artifact |
|---|---|---|
| Full engine suite (`pytest -c engine/pyproject.toml engine`) | 1628 passed, 3 failed, 5 errors | [g1-baseline-engine.txt](artifacts/test-results/g1-baseline-engine.txt) |
| brain-jobs PostgreSQL suite with the psycopg test URL | 5 passed | [g1-baseline-jobs-postgres.txt](artifacts/test-results/g1-baseline-jobs-postgres.txt) |
| `scripts/contracts/generate.py --check` | pass, 86 artifacts, digest `054119f1…` | [g1-baseline-contracts.txt](artifacts/test-results/g1-baseline-contracts.txt) |

Triage of the non-passing baseline results. Both are pre-existing and environmental; neither is a code defect, and no code was edited.

- **5 errors (`brain-jobs/tests/test_postgres.py`).** My first invocation passed a non-psycopg URL. Rerunning with the required `postgresql+psycopg` scheme gives 5/5 passing. G2 passes this variable on every full run.
- **3 failures** (`test_content_restore_v2.py` ×2 and `test_job_event_reason_migration.py::test_backup_and_isolated_restore…`). They exit 127 because `pg_dump`/`pg_restore` are not installed in the cached engine image (`which pg_dump` exits 1). These are F0004/F0005 backup-restore proofs over files F0009 does not modify. They stay a known validation-image limitation: G2 reports them separately and does not count them as F0009 regressions or passes.

## Readiness for G2

- PostgreSQL is reachable from the engine container, and migration 0016 will be applied to `brain_f0009` with an upgrade/downgrade proof.
- The F0011 contract toolchain (`generate.py --check`) and `experience` `contracts:check` dependencies are installed.
- Runtime failure triage rule: on any connection-type failure, stop code edits, re-run this preflight, then repeat the unchanged command.
