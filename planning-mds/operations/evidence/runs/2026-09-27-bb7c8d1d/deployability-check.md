# Deployability Check — F0002 run 2026-09-27-bb7c8d1d

**Owner:** DevOps
**Date:** 2026-09-27

> The framework spec (`feature.yaml`) names this artifact `g2-deployability-check.md`, while the validator requires `deployability-check.md`. The validator's name is used here. The mismatch was first recorded in F0003 run 2026-08-29-16075bda and is carried as a follow-up in README.md.

## Scope

- Schema: migrations 0005 (expand) and 0006 (constrain), down_revision chain 0004 → 0005 → 0006.
- Configuration: new non-secret `config/authx-identity-profile.yaml`. The API also accepts `BRAIN_IDENTITY_PROFILE_PATH`, and `BRAIN_OIDC_ISSUER` must be one of its issuers or the API refuses to start.
- Operational scripts: `scripts/dev/reconcile_authx.py`, `scripts/dev/provision_delegation.py`, `scripts/dev/revoke_membership.py` (same CLI arguments; now also requires an operator ID and approval reference, via flags or `BRAIN_OPERATOR_PRINCIPAL_ID`/`BRAIN_APPROVAL_REF`).
- No new container, service, port, secret, or image. `docker-compose.yml` is unchanged.

## Checks executed (application runtime)

| Check | Result | Evidence |
|---|---|---|
| `docker compose config -q` and `scripts/dev/check_pins.py` | compose valid; all images pinned | artifacts/test-results/g2-devops-compose-pins.txt |
| Pre-migration snapshot of the dev database (pg_dump -Fc) | taken before any migration | artifacts/test-results/g1-predump.txt |
| Dev database migrated 0003 → 0004 → 0005 → 0006 | head 0006; 48 legacy audit rows retained | artifacts/test-results/g2-dev-db-migrate.txt |
| Restore drill: snapshot restored into a scratch database, verified, migrated to head, dropped | restored at 0003 with 48 audit rows; migrated to 0006; legacy audit digest identical before and after (e12f16345b695146d21b22f2436d7578) | artifacts/test-results/g2-devops-restore-drill.txt |
| Expand-only rollback (0006 → 0004 → 0006) on a throwaway database | clean round trip | artifacts/test-results/g2-devops-migration-roundtrip.txt |
| 0006 refuses un-reconciled data without changing the schema; invalid job UUID text stops 0005 before any change | proven | artifacts/test-results/g2-engine-pytest.txt |
| Operator runbook on the dev database: reviewed mapping, then dry-run, then digest-bound apply with `--activate-policy` | applied; policy release `sha256:059497cd…168ee` active | artifacts/test-results/g2-dev-reconcile-dryrun.json, artifacts/test-results/g2-dev-reconcile-apply.json |
| API process starts with the committed identity profile and serves under ZAP | started; 0 FAIL | artifacts/security/g2-api-server.log, artifacts/security/g2-zap-report.json |
| Lockfiles consistent for CI `uv sync --locked` | engine and neuron `uv lock --check` pass | artifacts/test-results/g2-devops-lock-check.txt |

## Rollback and operations notes

- Before 0006 is applied, rollback means restoring the pre-migration snapshot or downgrading the unused expansion. After records depend on the contract, use a forward repair (ADR-0061). 0006's downgrade drops only constraints.
- A fresh environment needs the reconciliation apply with `--activate-policy` once after `alembic upgrade head`. Until then every protected route returns a sanitized 503 (fail closed), by design.
- The engine security suites share the local dev database and truncate F0002 registries and the policy pointer between tests (a pre-existing F0001 pattern). After running them locally, re-run the activation step. This is carried as a low follow-up: move those suites to an isolated database.

## Recommendations

- [low] Move the engine PostgreSQL security/integration suites to an isolated per-run database so they cannot reset the developer's dev-database state — owner: DevOps; follow-up: deferred-no-followup

Result: PASS WITH RECOMMENDATIONS
