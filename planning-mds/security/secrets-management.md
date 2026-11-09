# Secrets Management — Nebula Insurance Brain

Status: Baseline (v0.1 local scope)
Last Updated: 2026-11-08
Owner: Security + DevOps

## Objective

Keep credentials out of the repository, out of logs and out of processes that do not need them. This baseline covers the local Docker Compose topology (ADR-0054); a production secret store is a pre-pilot decision.

## Secret Categories

| Secret | Consumer | Local source |
| --- | --- | --- |
| `AUTHENTIK_SECRET_KEY`, `AUTHENTIK_BOOTSTRAP_PASSWORD` | authentik server and worker | `.env` (git-ignored); template in `.env.example` |
| `BRAIN_DATABASE_URL`, `BRAIN_WORKER_DATABASE_URL`, `BRAIN_MIGRATION_ADMIN_URL` | API, worker, migrations | Environment; local defaults are non-secret development values |
| `BRAIN_INFERENCE_API_KEY` | Worker → local vLLM | `~/.brain-secrets` (mode 0600), never `.env` or the repo |
| OIDC client configuration | API / future BFF (F0021) | authentik blueprint and environment |

## Baseline Controls

- `.env*` is git-ignored except `.env.example`, which holds placeholders only.
- The worker reads credentials only from the environment (`worker_cli` docstring); configuration files cannot name the inference guard directory or carry credentials.
- The conversion child receives an allowlisted environment with no database, inference or application credentials (ADR-0074). In cgroup mode only two session paths are added (`XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS`), which are not credentials.
- Manifests and run metadata store secret references, never secret values (section 110.4).
- Every feature security review runs gitleaks over the changed source; F0006's final run reported zero results.

## Rotation And Revocation

- Local development secrets are rotated by regenerating `.env` values and restarting the stack; authentik's key rotation follows its upstream procedure.
- The inference key is rotated by replacing `~/.brain-secrets` and restarting vLLM and the worker.
- Production rotation intervals, automated rotation and revocation runbooks are defined with the production secret store before a pilot.

## Local Development Rules

- Never paste real credentials into issues, PRs, evidence runs or test fixtures.
- Test databases use isolated schemas and non-secret local credentials.
- Evidence packages record commands with environment variable names, not values.

## Incident Response Expectations

If a secret is committed or logged: revoke and rotate it immediately, purge it from history only with operator approval, record the incident in a dated review under `reviews/`, and rerun the secrets scan.

## Sign-Off

Baseline authored 2026-11-08 (SEC-02). Production secret storage remains open (blueprint 117.1 item 3).
