# Test Plan — F0004 run 2026-10-17-8a6cc79f

## Story-to-AC Mapping

| Story | AC | Test expectation | Owner |
|---|---|---|---|
| F0004-S0001 | AC1 | versioned_content round-trip; worker process recovery; restore v1/v2 | QE; Backend/AI fast tests |
| F0004-S0001 | AC2 | missing inventory/hash/asset; fenced publication failures | QE; Backend/AI fast tests |
| F0004-S0001 | AC3 | manifest/projection quality and producer round-trip | QE; Backend/AI fast tests |
| F0004-S0001 | AC4 | content_consumer_versions two profiles; content_worker_v2 parser/OCR forbidden | QE; Backend/AI fast tests |
| F0004-S0001 | AC5 | immutable store conflict/exact retry; pending-source concurrency | QE; Backend/AI fast tests |
| F0004-S0001 | AC6 | migration_states publication/audit/commit/expiry faults | QE; Backend/AI fast tests |
| F0004-S0002 | AC1 | actual native/scanned/mixed projection; durable index verification | QE; Backend/AI fast tests |
| F0004-S0002 | AC2 | strict record origin/producer/anchor union and missing producer failure | QE; Backend/AI fast tests |
| F0004-S0002 | AC3 | OCR real fixture; stored transcript/figure contract fixtures only | QE; Backend/AI fast tests |
| F0004-S0002 | AC4 | Unicode/rotation/multi-region/unavailable geometry fixtures | QE; Backend/AI fast tests |
| F0004-S0002 | AC5 | merged cells/headers/continuation and ambiguity evidence fixtures | QE; Backend/AI fast tests |
| F0004-S0002 | AC6 | mixed origin rejection; ORIGIN_UNAVAILABLE v1 fallback; missing producer hard failure | QE; Backend/AI fast tests |
| F0004-S0002 | AC7 | same single publication event as S0001 AC6 | QE; Backend/AI fast tests |
| F0004-S0003 | AC1 | PostgreSQL candidate round-trip CONTENT/SOURCE_METADATA/HUMAN | QE; Backend/AI fast tests |
| F0004-S0003 | AC2 | default undated and processing-time field rejection | QE; Backend/AI fast tests |
| F0004-S0003 | AC3 | append correction/selection/clear; pinned historical date and unchanged bundle | QE; Backend/AI fast tests |
| F0004-S0003 | AC4 | denied/default/revoked/mismatched receipts, bad quote and transactional rollback | QE; Backend/AI fast tests |
| F0004-S0003 | AC5 | exact June effective/issued/received/accepted PostgreSQL example | QE; Backend/AI fast tests |
| F0004-S0003 | AC6 | conflicting candidates; no selection without verified human receipt; CAS concurrency | QE; Backend/AI fast tests |
| F0004-S0004 | AC1 | API v1/v2 trusted key; importer/worker current authority on actual accepted artifact | QE; Backend/AI fast tests |
| F0004-S0004 | AC2 | Reviewer-only/cross-tenant/KB/revocation restrictions before bytes | QE; Backend/AI fast tests |
| F0004-S0004 | AC3 | 0007 reader/0008 expansion; backfill/blocked/quarantine/repair; unsupported versions | QE; Backend/AI fast tests |
| F0004-S0004 | AC4 | real isolated dump/restore; every DB/object hash; citations/date/owner/index checks | QE; Backend/AI fast tests |
| F0004-S0004 | AC5 | existing worker/process-kill/Graph baseline/direct/dense compatibility | QE; Backend/AI fast tests |
| F0004-S0004 | AC6 | four worked-example reproduction mapping and contract fixture validation | QE; Backend/AI fast tests |

## Test Strategy

Developer-owned fast lanes: brain-content contracts/stores/dates/config/run markers; security execution and queue fences; ingestion projection/provenance; versioned Graph consumption. QE owns independent PostgreSQL migration/fault/date/operator/concurrency/restore expectations and API access cases. Both lanes execute in locked application jobs. Each PostgreSQL fixture owns a fresh database or schema; no cleanup touches shared development tables.

API tests exercise real common storage and ORM metadata under current F0002 authority. Worker cases use the existing claim/heartbeat/fence/retry/completion/outbox lifecycle. Actual Docling native/scanned/mixed PDFs prove producer observation; recorded HTTP responses isolate orchestration/evidence from model quality. Process-kill tests prove recovery across publication/run/completion/importer boundaries. Local restore tests invoke actual pg_dump/pg_restore in unique containers and compare exact inventories.

## Developer-vs-QE Test Ownership

Backend: engine packages, authorized boundaries, migrations and service tests. AI: pinned converter, projection and saved-native consumers. QE: independent AC expectations, integration and coverage. DevOps: locked build/start/health, migration/restore/runbook. Security: scanner interpretation/current authority review. One Codex session performs these role passes; no independent external reviewer identity is claimed.

## Test Data / Fixtures

All new data is synthetic development material outside the frozen holdout. Real converter fixtures are generated native text, raster scans and mixed pages. Transcript/description fixtures test storage contracts only. Human/source-metadata verifiers are explicit controlled receipts; production defaults deny. No test grants permission based on a manifest, source hash or receipt alone.

## Happy / Edge / Error / Auth / Accessibility / Regression Cases

Happy/restart: exact marker/file bytes, source/version/recipe identities, two profiles, persisted runs/dates/indexes. Errors: missing/corrupt files, unknown versions, invalid provenance/geometry/table links, empty conversion, failed audit/commit, lease/authority expiry, missing/tampered fallback intent, unsafe restore inventory. Authority: current grants, owner and source restrictions, no Reviewer-only read grant, verified human selection, denied effects and failed-read audit only. Regression: F0001/F0002/F0005 affected consumers and generic queue lifecycle.

No frontend behavior changes: browser E2E, visual, accessibility and UI performance lanes are not in scope. No new throughput/latency budget is asserted; F0005/F0026 own operational qualification. Optional live inference/tokenizer cases remain separate and their skips must be named. Recorded responses do not qualify model accuracy or production Graph activation.

## Coverage and Security

At least 80% of changed Python runtime executable statements; retain raw lane JSON/XML and combined coverage. Include unmeasured changed statements as misses rather than silently dropping files. SQL guards and shell backup/restore are verified by actual PostgreSQL/CLI execution, with explicit non-Python coverage notes. All four security scan classes execute through framework wrappers and application/scanner containers; no unavailable tool may be silently skipped.

## Risks And Mitigations

Legacy metadata stays nullable and truthful; authorized operator jobs alone quarantine/repair. Default v2 flag stays false pending compatibility/review. Actual direct-mode Graph provenance lacks native refs and remains partial/unresolved. Date selection needs an owning trusted human workflow; no new route grants it. Restore is a quiesced local snapshot, without distributed-snapshot claims.

## Result

PASS. Final observed results are in test-execution-report.md.
