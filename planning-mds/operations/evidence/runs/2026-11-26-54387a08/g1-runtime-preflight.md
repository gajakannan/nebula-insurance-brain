# G1 Runtime Preflight — F0012

- Role: DevOps
- Reviewer: Claude (Opus 5.5) / DevOps
- Date: 2026-11-26
- Run: `2026-11-26-54387a08`
- Verdict: PASS. The engine, node and dedicated PostgreSQL validation runtime is ready.

Result: PASS

## Runtime

The [run-local compose definition](artifacts/runtime/compose.yaml) starts two validation containers on the existing `nebula-insurance-brain_default` network. Both report healthy ([compose-up.txt](artifacts/runtime/compose-up.txt)).

- `engine-validation` runs the cached `brain-f0011-contract-engine:2026-11-22-885e8734` image (Python 3.14.4, uv 0.11.31). Its task virtual environment is `/tmp/f0012-engine-venv`, built with `uv sync --project engine --group contract-build --locked` ([uv-sync.txt](artifacts/runtime/uv-sync.txt)).
- `node-validation` runs `node:22` for the `experience` AJV contract conformance.

The existing `brain-postgres` service (`brain-postgres:18-pgvector-age`, healthy) hosts a new dedicated database, `brain_f0012`, with `btree_gist` ([create-db.txt](artifacts/runtime/create-db.txt)). Alembic brought it from empty to **0016 (head)** ([alembic-upgrade-0016.txt](artifacts/runtime/alembic-upgrade-0016.txt)). F0012 tests use this database only. Owned-database migration suites create and drop their own temporary databases through `BRAIN_MIGRATION_ADMIN_URL`. No new credential is introduced.

## Baseline (before any F0012 code change)

| Check | Result | Artifact |
|---|---|---|
| Full engine suite (`pytest -c engine/pyproject.toml engine`, PostgreSQL test URL `brain_f0012`) | 1729 passed, 3 failed | [g1-baseline-engine.txt](artifacts/test-results/g1-baseline-engine.txt) |
| `scripts/contracts/generate.py --check` | pass, 101 artifacts, bundle digest `17189a61…` | [g1-baseline-contracts.txt](artifacts/test-results/g1-baseline-contracts.txt) |
| G0-4 legacy slot-type inventory (`SELECT slot_type, count(*) FROM fact_slot WHERE identity_version IS NULL`) on `brain`, `brain_f0009`, `brain_f0012` | 0 rows in every database | [g1-legacy-slot-types.txt](artifacts/test-results/g1-legacy-slot-types.txt) |

The 3 failures are pre-existing and environmental: `test_content_restore_v2.py` ×2 and `test_job_event_reason_migration.py::test_backup_and_isolated_restore…`. They exit because `pg_dump`/`pg_restore` are not in the cached engine image, the same limitation F0009 recorded. They cover F0004/F0005 backup-restore over files F0012 does not modify. G2 reports them separately, the host lane re-runs them, and they are not counted as F0012 regressions or passes.

The local databases hold no legacy pilot slots, so the S0005 AC5 inventory keeps the code-known values from the plan: `limit` and `each_occurrence_limit` (unmapped, owner F0013) and `__OPEN_STATEMENT_V2__` (not a predicate). G2 adds a source scan for slot-type literals.

## Readiness for G2

- PostgreSQL is reachable from the engine container. Migration 0017 will be applied to `brain_f0012` and proven with upgrade and refused downgrade.
- The F0011 contract toolchain is installed for the three new resources.
- Runtime failure triage rule: on any connection-type failure, stop code edits, re-run this preflight, then repeat the unchanged command.
