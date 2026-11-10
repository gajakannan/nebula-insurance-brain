# Deployability Check — F0007 run 2026-11-09-b94cfa12

- Role: DevOps
- Reviewer: Claude (Opus 5.5) / DevOps
- Date: 2026-11-09

## Runtime / Deployment Config Changes

| Change | Paths |
|---|---|
| New workspace package `brain-factslots` (no third-party dependency) | `engine/packages/brain-factslots/**`; `engine/pyproject.toml`; `engine/apps/api/pyproject.toml`; `engine/packages/brain-persistence/pyproject.toml`; `engine/packages/brain-testing/pyproject.toml` |
| Lockfiles: the only change is the editable `brain-factslots` entry | `engine/uv.lock` (+35 lines), `neuron/uv.lock` (+23 lines, because `brain-testing` is a neuron path dependency) |
| Package data: the pinned ISO 4217 list | `engine/packages/brain-domain/pyproject.toml`, `brain_domain/data/iso4217-2026-01.txt` |
| Migration `0012` | `engine/migrations/versions/0012_f0007_factslot_identity.py` |
| CI: `brain-factslots` added to mypy and to a per-package coverage gate (`runtime-suites`); new PostgreSQL step for the F0007 suites plus the two F0006 migration drills (`runtime-stack`) | `.github/workflows/ci-gates.yml` |
| Backup inventory compatibility: hash only the columns present at the database's revision | `scripts/ops/verify_content.py` |

No change to `docker-compose.yml`, the Dockerfiles, `config/`, the environment variables, secrets, ports or containers.

## Migrations / Rollback

- **Lineage:** `0011 → 0012`, the single head (G0 lineage check; `alembic heads`).
- **Deterministic pilot rows:** `test_factslot_migration.py` seeds them at 0011 and checks them after upgrade, downgrade and upgrade again. They stay byte-identical to the committed `engine/tests/fixtures/factslots/pilot-before.json`, and so does the schema hash of `canonical_fact_version`, including its constraints.
- **Refused downgrade:** with an identity-v1 row present, the downgrade refuses and the database stays at 0012 with the data intact.
- **Clone of the local dev database** (`artifacts/runtime/dev_clone_migration.sh`, output `artifacts/test-results/command-output/g2-dev-clone-migration.txt`): 0010 → 0011 → 0012 → 0011 → 0012 applied cleanly. The dev database held no fact rows at the time, so pilot-row preservation rests on the deterministic seed test above. The shared dev database itself was only read.
- **Rollback procedure** (assembly plan "Rollout, Rollback and Caching"):
  1. Stop resolver callers. None exist in production composition yet.
  2. Identity-v1 slots and versions stay readable.
  3. Downgrade refuses while identity-v1 or qualifier rows exist. Evidence is never deleted to make a downgrade pass.

## Env / Config Contract

No new runtime variable. Production composition registers only the `sys` predicates (`brain_api.deps.get_predicate_registry`); the `test` namespace is reachable only through a test dependency override. `BRAIN_MIGRATION_ADMIN_URL` is the existing test-only variable that the F0002/F0006 suites already use.

## Manifest Boolean Cross-Check

| Boolean | Value | Reason |
|---|---|---|
| `runtime_bearing` | true | `engine/**` runtime packages and migration changed |
| `deployment_config_changed` | true | migration and `.github/workflows/ci-gates.yml` |
| `security_sensitive_scope` | true | ownership keys, derived restrictions and authorization-before-reason. No path under `auth/` or `authz/` matched, so the Phase B risk assessment sets this, not a path class |
| `frontend_in_scope` | false | no `experience/` path |

## Build / Start / Smoke Results

| Check | Result | Evidence |
|---|---|---|
| `uv lock --check` (engine, neuron); `uv sync --locked` | consistent | `artifacts/test-results/command-output/g2-deployability-static.txt` |
| `docker compose config -q` | ok, no compose change | same |
| CI workflow parses; 2 F0007 steps present | ok | same |
| API boots on a fresh database at head; `/openapi.json` 200 | ok | `artifacts/security/dast/run-dast.log`, `uvicorn.log` |
| Full engine suite on an owned database at head | 816 passed | `artifacts/test-results/g2-engine-full.xml` |
| The CI F0007 step exactly as committed | 148 passed, `brain_factslots` 98.25% | `artifacts/test-results/g2-f0007-ci-step.xml` |
| Neuron suite after relock | 264 passed, 41 skipped (CI-equivalent lanes) | `artifacts/test-results/g2-neuron-suite.xml` |

## Runtime Warnings

- The Alembic `path_separator` deprecation warning already existed before F0007; it is not changed here.
- The backup drill (`test_job_event_reason_migration` backup and restore) already failed on `main` because of the 0011 mapped column. The `verify_content.py` fix repairs it, and the drill now runs in CI. Recorded as a carry-in repair, not F0007 scope growth: 0012 would otherwise have caused the same failure for `fact_slot`.

## Result

PASS
