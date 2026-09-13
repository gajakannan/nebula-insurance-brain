# Deployability Check — F0001-repository-and-engineering-foundation run 2026-09-12-855d2b93

**Role:** DevOps
**Date:** 2026-09-12

## Remediation Deployment Scope

No Docker, Compose, migration, environment, or CI deployment configuration changed in
this remediation. The existing healthy Compose preflight remains valid; the only runtime
change is application-level structured security logging and its tests.

## Runtime / Deployment Config Changes

- `docker-compose.yml` (new): `postgres` (custom-built image), `authentik-server`,
  `authentik-worker`. Content-artifact storage is a local filesystem directory
  (`config/local.yaml`), not a Compose service.
- `docker/postgres/Dockerfile` (new): `FROM postgres:18.0-trixie`, builds pgvector v0.8.6
  and Apache AGE `PG18/v1.8.0-rc0` from source; `docker/postgres/init/*.sql` creates the
  `vector`/`age`/`btree_gist` extensions.
- `docker/authentik/blueprints/nebula-brain-dev.yaml` (new): declarative dev-seed blueprint
  (two tenant users, one service client).
- `.github/workflows/ci-gates.yml` (extended this run): added the `runtime-stack` OIDC
  discovery retry loop, expanded the `runtime-suites` mypy invocation and per-package
  coverage gates to cover `brain-temporal`/`apps/worker` (added at S0005, previously
  ungated).
- `engine/migrations/versions/0001..0003` (new): `content_and_interpretation`,
  `principals_audit_and_review`, `fact_slots_and_commits`.
- `config/local.yaml` (new, committed, non-secret): local filesystem object-store
  configuration.
- `.env.example` (new): documents `AUTHENTIK_SECRET_KEY`/`AUTHENTIK_BOOTSTRAP_PASSWORD`;
  no secrets committed.

## Migrations / Rollback

All three migrations were applied and downgraded cleanly against the live compose
Postgres multiple times across S0003–S0006 (most recently re-verified 2026-09-10 as part
of this run's fresh `docker compose down -v && up -d` cycle):

```text
$ alembic -c alembic.ini upgrade head
Running upgrade  -> 0001, content and interpretation
Running upgrade 0001 -> 0002, principals audit and review
Running upgrade 0002 -> 0003, fact slots and commits
```

`0003`'s `canonical_fact_version` table carries a `EXCLUDE USING gist` constraint;
downgrade drops it and all four new tables cleanly (verified 2× this run).

## Env / Config Contract

| Variable | Purpose | Default |
|---|---|---|
| `BRAIN_DATABASE_URL` | PostgreSQL 18 connection | compose default |
| `config/local.yaml` | Local filesystem content-artifact store | committed default |
| `BRAIN_OIDC_ISSUER`, `BRAIN_OIDC_AUDIENCE` | authentik verification | compose defaults |
| `BRAIN_INFERENCE_BASE_URL`, `BRAIN_INFERENCE_MODEL`, `BRAIN_INFERENCE_API_KEY_ENV`, `BRAIN_INFERENCE_CONTEXT_LIMIT` | vLLM endpoint | see `docker/local-inference-runbook.md` |
| `BRAIN_GRANT_CACHE_SECONDS` | Documented upper bound for a future membership cache | `30` (no cache implemented yet — see `STATUS.md` Deferred Non-Blocking Follow-ups) |
| `AUTHENTIK_SECRET_KEY`, `AUTHENTIK_BOOTSTRAP_PASSWORD` | authentik bootstrap secrets | never committed; `.env` (gitignored) locally, CI-generated per run |

No storage environment variable is required — `config/local.yaml` is committed and
contains only non-secret defaults, per ADR-0059.

## Manifest Boolean Cross-Check

`evidence-manifest.json`: `runtime_bearing: true`, `deployment_config_changed: true`,
`security_sensitive_scope: true`. All three agree with the changes enumerated above
(new `docker-compose.yml`, migrations, and the S0006 identity/authz surface).

## Build / Start / Smoke Results

```text
- build: docker compose build postgres → exit 0
- start: docker compose up -d → postgres healthy ~10s, authentik healthy ~35s (fresh volume, this run)
- smoke: docker exec brain-postgres psql -U brain -d brain -c "\dx" → vector, age, btree_gist present
- smoke: python3 scripts/dev/seed_principals.py → all 3 seeded principals verified via ROPC
- smoke: alembic upgrade head / downgrade base / upgrade head → clean round trip
- smoke: uv run pytest -q (engine, live stack) → 129 passed
```

## Runtime Warnings

- The `postgres:18.0-trixie` base image tag is not immutable across point releases —
  server measured at 18.6 despite the pinned `18.0` tag string. Non-blocking; recorded in
  `docker/DEPENDENCY-MATRIX.md` as a version-drift finding, not a pin violation.
- authentik's healthcheck reports healthy ~15s before its custom blueprint actually
  finishes applying (OIDC discovery isn't served until then). CI's retry loops
  (`seed_principals.py`, and now the OIDC discovery check added this run) both cover this;
  a first-time local `docker compose up -d` without retries can appear to fail transiently.

## Result

PASS
