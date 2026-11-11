# Read-only PostgreSQL identity CHECK proof

Date: 2026-11-09. Product: nebula-insurance-brain. Container: existing Compose `postgres` service, database `brain`, psql user `brain`.

The exact `ck_fact_slot_identity` expression was extracted from migration 0012. A CTE supplied otherwise valid SINGLE SLOT fields. No persistent table was read or written and no migration was applied.

Query output columns are `check_result IS NULL AS check_returns_unknown` and `check_result IS NOT FALSE AS postgres_check_accepts`.

| Candidate | psql exit | Raw output |
|---|---:|---|
| identity_version=1; fingerprint=NULL; otherwise valid v1 SLOT | 0 | `t\|t` |
| identity_version=NULL; all v1 fields including fingerprint populated | 0 | `t\|t` |

Full exact queries are in `architect-probes.json`. Successful raw command/output records, including both exit codes, are in `architect-postgres-raw.json`. The first scripted invocation could not access the Docker socket inside the sandbox. Both queries were then executed successfully via direct `docker compose exec -T postgres psql -U brain -d brain -X -A -t -v ON_ERROR_STOP=1 -c <query>` using the approved Docker Compose escalation. Docker Compose emitted warnings for unset Authentik environment variable names; no credential values were read or printed.

PostgreSQL CHECK rejects FALSE and accepts UNKNOWN. Requiring the entire expression `IS TRUE` rejects these incomplete identities while retaining correctly formed legacy/v1 branches.
