# G1 Runtime Preflight — F0007 remediation

Role: DevOps / Codex. Date: 2026-11-09.

## Runtime and Commands

Initial preflight checked the locked engine virtual environment plus Compose PostgreSQL. Combined implementation validation uses the existing project application images through this run's `artifacts/runtime/compose.yaml`, with current source mounted read-only and only `/evidence` writable. The F0006 image has the unchanged third-party runtime; PYTHONPATH adds the current F0007 workspace package. Container Python3.14.4, current brain_factslots path and PostgreSQL connectivity were verified in artifacts/container-preflight.txt before the combined suites. Exact commands/timestamps are in commands.log. The initial native red/unit probes are supplemental; final runtime suite evidence comes from application containers.

- Python 3.14.4; pytest, SQLAlchemy, psycopg, asyncpg and brain_factslots imports available.
- brain-postgres healthy; PostgreSQL18.6; AGE1.8.0, pgvector0.8.6, btree_gist1.8.
- Shared development database is at0010. It is not migrated, truncated or repaired by remediation.
- Integration/migration tests use the existing BRAIN_MIGRATION_ADMIN_URL fixture to create/drop owned databases. New migration0013 preflight and upgrade refusal are exercised only on owned databases.
- No UI, model or OIDC behavior changes; principal dependency overrides apply to API tests as in the existing feature harness.

## Failure Triage

Connection/service failures stop code edits and trigger runtime recheck, then an identical retry before defect classification. Sandbox network/Docker failures use explicit escalation; no bypass. Data inventory on the shared database is read-only and revision-aware; a missing F0007 table/columns is reported as not yet adopted, not repaired.

## Result

PASS
