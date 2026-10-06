# G2 Deployability Check — F0003-postgresql-persistence run 2026-10-03-57d14a51

## Runtime / Deployment Config Changes

No Dockerfile, Compose file, CI workflow, environment contract, startup script, or migration file changed in this run. The code change is an integration test; the other product edit is the STATUS.md progress matrix.

## Migrations / Rollback

No migration was added or altered. The approved plan requires additive-only migrations when a concrete schema gap is proven; this run did not identify such a gap. There is no migration rollback operation for this test-only change.

## Env / Config Contract

No environment variable or config key was added or changed.

## Manifest Boolean Cross-Check

- `runtime_bearing=true`: correct for the persistence feature and PostgreSQL integration lane.
- `deployment_config_changed=false`: correct; no deployment configuration or migration file changed.
- `security_sensitive_scope=false`: correct for the changed paths; Security Reviewer remains required by the feature's STATUS.md role matrix.

## Build / Start / Smoke Results

G1 recorded PostgreSQL Compose health and `pg_isready` success. Hosted CI run `37241111686` also built and started the PostgreSQL 18 stack, verified extensions, applied engine migrations to head, and passed its focused PostgreSQL suites; see `artifacts/test-results/g2-ci-37241111686.md`. The local sandbox still blocks host socket and Docker API access, and the broader runtime suite did not reach pytest.

## Runtime Warnings

G1 observed unset optional Authentik interpolation variables in Compose. No variable values were recorded; this did not affect the PostgreSQL health check.

## Result

Result: PASS
