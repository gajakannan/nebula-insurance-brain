# Deployability Check — F0004 run 2026-10-17-8a6cc79f

Owner: Codex, DevOps role. 2026-10-19.

## Runtime / Deployment Config Changes

Additive revision 0008 plus adjacent frozen SQL; brain-content/persistence
dependency and package-data metadata; both locked workspaces; new operator
script entry point; config/local.yaml content.v2_writer_enabled=false; local
backup/restore/verifiers and docker/content-integrity-runbook.md.
Run-scoped digest-pinned Python/uv Dockerfile and Compose validation jobs build
both workspaces with uv sync --locked, without creating a product deployment
boundary. UID/GID 1000 jobs use isolated content/model caches. The dedicated
restore job alone has the operator Docker client/socket and socket group 1001
to create uniquely named throwaway containers on the dependency network.
It publishes no database port. It never consumes the production queue.

## Migrations / Rollback

0001–0007 are unchanged. 0008 expands nullable legacy metadata/new tables and
guards; legacy single-version uniqueness remains until operator reconciliation.
Real owned-database tests verify old-schema reader compatibility, expand,
idempotent readiness/indexes/audit, corruption/operator transitions and empty
downgrade. Any retained v2/fallback/index/date/repair/state history refuses
destructive downgrade; use forward repair and restore original bytes.
Global uniqueness reconciliation authorizes/verifies every artifact, requires
a quiesced window and drops only the catalog single-column version constraint.

Shared development tables were not migrated/truncated. Apply 0008 and complete
operator inventory/backfill/reconciliation before enabling v2 writers in a
real deployment. Default false is intentional; the writer capability is proved
under explicit test configuration.

## Env / Config Contract

Product setting content.v2_writer_enabled defaults false and rejects non-booleans.
Existing worker principal/database/policy contracts remain. Ops backup requires
BRAIN_WRITERS_QUIESCED=1 after stopping ingestion/date/operator writes.
Optional local paths/container/database/Python/network/image overrides are
documented in docker/content-integrity-runbook.md. They configure operator
procedures and grant no application permission. No new secret value is stored.

## Manifest Boolean Cross-Check

runtime_bearing=true; deployment_config_changed=true;
security_sensitive_scope=true; frontend_in_scope=false. These match code,
migration/config and authorization/audit changes. No frontend lane is claimed.

## Build / Start / Smoke Results

All logs are under artifacts/test-results:
- g2-security-remediated-locked-build.txt: both locked image builds exit 0.
- g2-remediated-runtime-start.txt and g2-remediated-runtime-health.txt:
  engine, neuron and restore jobs healthy.
- g2-final-engine-tests.txt: 227 pass with real PostgreSQL cases.
- g2-final-neuron-tests.txt: 85 pass, including actual PDF/OCR and all
  process-kill cases; four optional inference/tokenizer skips.
- g2-restore-subprocess-coverage.txt: actual v1/v2 isolated dump/restore,
  exact all-table/object inventories, date selection history and two citations
  per drill; four pass. Restore does not repair/promote orphan objects.
- g2-wheel-schema-deployment-proof.txt: five schemas load from built wheel
  with repository fallback disabled.
- g2-structured-contract-examples.txt: six schemas, 40 expected-valid/invalid
  examples, no failures.

## Runtime Warnings

Preserved initial socket/cache/network failures are diagnostic history. The
restore job's socket GID/network repair was verified before retry. Existing
healthy dependency containers were not recreated; unset Authentik-variable
warnings did not require reading secrets. Dependency fixes preserve Docling
2.126.0/core/parse/Graph/RapidOCR/Torch pins. The remaining Docling advisories
and public health/OpenAPI passive-header warnings need G3 Security judgment.
No production deployment, live-model quality or throughput claim is made.

## Result

PASS
