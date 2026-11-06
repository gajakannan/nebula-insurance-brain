# Deployability Check — F0006 run 2026-11-02-5a00b0ff

Reviewer: Codex (DevOps role). Date: 2026-11-02. Post-review verification: 2026-11-03.

## Runtime / Deployment Config Changes

F0006 adds migration `engine/migrations/versions/0011_f0006_assertion_semantics.py`,
the internal brain-assertions package, packaged offline schemas, workspace dependencies,
and regenerated engine/Neuron lockfiles. External dependency versions are unchanged.
There is no new application deployable, route, grant, production environment variable,
pipeline activation, or config default. Runtime/deployment evidence is isolated in
`artifacts/runtime/{Dockerfile,compose.yaml,immutable-smoke.yaml,security-compose.yaml}`.
These are local validation configurations, not a production deployment definition.

The multi-stage images retain the pinned F0005 dependency baselines and copy both
the locked virtual environment and current package sources into the runtime stages.
Both runtime users are UID 1000. Validation services use the existing PostgreSQL
network and dedicated `brain_f0006_runtime` database; per-test F0006 databases are
randomly named, owned by their fixture, and removed after each test. Historical
`brain` data is not used for destructive test cleanup.

## Migrations / Rollback

Migration 0011 is additive over 0010: assertion contract discriminator, document-local
references/name claims, immutable semantic extensions, and integrity/append-only guards.
PostgreSQL tests prove legacy values/IDs survive upgrade and empty downgrade/re-upgrade,
while populated downgrade refuses rather than erasing v2 data. Evidence:
`artifacts/test-results/g3-sec04-regression.xml` (migration, ownership and authority cases),
`artifacts/runtime/deployment-verification.json` (live revision 0011, PostgreSQL 18.6).
ORM ownership keys mirror existing migration 0005 to support isolated test schemas;
they introduce no new database semantics.

Rollout order: back up database and retained content, quiesce writers, apply migration
0011, deploy guard-capable API/review/importer consumers and verify health, then allow
explicit service callers. The automatic importer remains v1-only. Do not enable a new
producer or switch content/extraction defaults as part of this feature.

Rollback before v2 data may downgrade to 0010 using Alembic after quiescing writers.
Once any extension/reference/name/v2 row exists, retain 0011 and the guard-capable
readers/correction/commit consumers. Stop incompatible old writers/readers; roll forward
or restore a reviewed backup through a separate operational decision. Never delete
v2 records to make downgrade succeed. The refusal is exercised in the migrated-PG suite.

## Env / Config Contract

Production configuration keys are unchanged. `direct-baseline` and the v1 content
writer remain the committed defaults, verified by the container probe. Validation
uses existing BRAIN_DATABASE_URL/BRAIN_WORKER_DATABASE_URL with a dedicated database;
test-only BRAIN_MIGRATION_ADMIN_URL enables owned temporary databases and
BRAIN_TEST_POSTGRES_URL enables isolated recovery schemas. Local development database
credentials in this harness are disposable fixture credentials, not deployment secrets.
The optional OCR regression needed its container-local RapidOCR model directory made
writable by UID 1000; this does not modify host packages or activate an extraction path.

## Manifest Boolean Cross-Check

runtime_bearing=true: engine application, package and integration-test changes.
deployment_config_changed=true: migration, package/lock changes and run-local Docker files.
security_sensitive_scope=true: source READ requirements, correction lineage and protected
commit guards. frontend_in_scope=false: no experience paths or UI behavior change.
No false-to-true scope escape or extra feature is introduced.

## Build / Start / Smoke Results

- Locked engine and Neuron image builds passed after both review repairs: `artifacts/test-results/command-output/sec04-runtime-build.log`.
- Latest application images started and healthy: `artifacts/test-results/command-output/sec04-runtime-start.log`.
- The owned validation database's empty-v2 migration refresh preserved its legacy row fingerprint and deployed the repaired guard: `artifacts/runtime/migration-carrier-refresh.json`.
- API/storage, migration, defaults and wheel schema equality passed: `artifacts/runtime/deployment-verification.json`.
- Both immutable images match all 20 changed production Python source hashes and import new packages without a source bind mount: `artifacts/runtime/engine-immutable.json`, `artifacts/runtime/neuron-immutable.json`.
- Packaged wheel contains all four exact approved schema files: `artifacts/runtime/wheels/brain_contracts-0.1.0-py3-none-any.whl`.
- As-built impact routing: `artifacts/test-results/command-output/devops-diff-impact.log`. New/untracked paths are additionally captured in the changed-line inventory; G7 owns graph reconciliation.

## Runtime Warnings

This proves local synthetic development deployability. Production rollout, live model
qualification and F0005 activation remain outside scope. The Neuron dependency scanner
reports inherited advisories; Security must interpret them at G3 before approval.
Deprecation warnings from Alembic/Docling/test transport do not change test outcomes.
No production deployment is claimed.

## Result

PASS for the bounded local deployment/migration contract. Security review and the
overall feature approval are separate required gates.
