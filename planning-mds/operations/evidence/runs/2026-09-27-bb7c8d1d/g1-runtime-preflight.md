# Runtime Preflight — F0002 run 2026-09-27-bb7c8d1d

## Feature

- Feature ID: F0002
- Run ID: 2026-09-27-bb7c8d1d
- Date: 2026-09-27
- Owner: DevOps

## Runtime Services / Containers / Jobs

- `brain-postgres` (PostgreSQL 18, pgvector 0.8.6, AGE 1.8.0, btree_gist 1.8), which every engine integration and security test and the new migrations run against.
- `brain-authentik-server` / `brain-authentik-worker` (authentik 2026.2.0), the OIDC issuer for the verification boundary. Security tests use a real-crypto fake JWKS rather than a live token flow, as F0001 established.
- The engine uv workspace (Python 3.14 venv, requires >=3.13): API app, worker app, and kernel packages.
- The neuron uv workspace, only as the F0005 worker regression consumer (no AI runtime or vLLM needed; tests use recorded responses).

## Command Evidence

Each command is recorded in `commands.log` with its output artifact:

- `docker compose ps`: all three containers Up and healthy. Output:
  artifacts/test-results/g1-compose-ps.txt
- `pg_isready`, alembic version, and extensions: accepting connections, dev DB at revision `0003`, extensions present. Output:
  artifacts/test-results/g1-pg-ready.txt
- authentik liveness `/-/health/live/`: HTTP 200. Output:
  artifacts/test-results/g1-authentik-health.txt
- Baseline engine suite before any F0002 change: 145 passed, 4 skipped. The 4 skips are brain-jobs PostgreSQL proofs gated on `BRAIN_TEST_POSTGRES_URL`. Output:
  artifacts/test-results/g1-engine-baseline.txt
- Pre-migration snapshot `backups/f0002/brain-pre-0004-2026-09-27.dump` (pg_dump -Fc, sha256 recorded). Output:
  artifacts/test-results/g1-predump.txt

## Health Status

| Service | Status | Notes |
|---------|--------|-------|
| brain-postgres | healthy | revision 0003; 0004 never applied to this volume; semantic tables empty; 48 legacy F0001 audit rows (must remain unchanged) |
| brain-authentik-server | healthy | HTTP 200 liveness |
| brain-authentik-worker | healthy | compose healthcheck |
| engine test runtime | healthy | 145 passed / 4 skipped baseline |

## Restore Steps If Unavailable

- `docker compose up -d postgres authentik-server authentik-worker`, then wait for healthy.
- Restore the dev database from the snapshot:
  `docker exec -i brain-postgres pg_restore -U brain -d brain --clean --if-exists < backups/f0002/brain-pre-0004-2026-09-27.dump`.
  DevOps exercises this as a drill at G2 (deployability check).
- Tests with runtime symptoms (connection refused, missing container) are classified `runtime-blocked` and re-run unchanged after restore, per the feature action's triage rule.

## Result

PASS
