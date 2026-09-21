# F0005 — One-time document ingestion — Status

**Overall Status:** Candidate implementation in progress; production delivery incomplete. ADR-0060 is Proposed. The exact pin and six contract tests are recorded in [compatibility evidence](compatibility-evidence.md). No live-model acceptance, runtime activation, or reviewer signoff claimed.
**Last Updated:** 2026-09-20

## Candidate runtime delivery — 2026-09-20

The candidate has been merged to main from `feature/docling-graph-delivery`, based on `a60350d`. It remains opt-in; it does not replace the accepted F0001 baseline or imply release acceptance.

- `CheckpointStore` verifies scope, inventory, source/native and bundle hashes. Manifest-last publication supports identical retries. Missing files in a published bundle or run are integrity failures, never cache misses that trigger re-parsing. Filesystem writes use private temporary files, fsync, and atomic publication.
- `DocumentJobQueue` and migration 0004 provide artifact leases, generations, heartbeats, scoped idempotency, cancellation, finite retries, event history, and a completion outbox. PostgreSQL fences use the current database clock after lock acquisition. Migrations and all four PostgreSQL tests passed on `a64f0eb`: competing claims, expired-generation fencing, child-process exit/reclaim after checkpoint publication, and lease expiry during a row-lock wait. This proves queue recovery; full worker/model/import and infrastructure recovery remain separate operational gates.
- `DocumentWorker` performs conversion/checkpoint publication, saved-JSON interpretation, fenced output publication, and recovery of a successful prior attempt. Jobs pin profile version and schema hash. Artifact metadata is registered before model extraction, so model failure leaves the content available to authorized engine readers. A real process-exit test recovers published output without a conversion or model call.
- `DocumentJobAuthorization` re-reads active principal status, unrevoked grants, and Casbin policy at sensitive boundaries; decisions are audited. Only the existing `ServicePrincipal` role receives the new `ingest` and `interpret` grants. The CLI is a trusted-operator interface, not an unauthenticated public upload endpoint.
- `DocumentResultImporter` atomically inserts source/artifact metadata, the interpretation run, assertions, evidence, review items, and an outbox acknowledgement. An injected review insertion failure rolls back the entire import; retry creates one set of rows. Unresolved evidence remains unresolved and enters provenance review. No canonical fact is accepted by this importer. Entity/relationship output is rejected until its downstream mapping exists.
- The shared DTO lives in `engine/packages/brain-contracts`; the old neuron import remains compatible. Parser, pipeline, model, template, limits, and run-owned provenance metadata remain distinct. Unique native text and table-cell locations are supported; ambiguous or normalized values are unresolved.
- `python -m brain_ingestion.worker_cli` provides opt-in submission, worker, and import-only commands. Both dependency locks resolve and both runtime environments sync offline.

**Verification:** the combined runtime suite passed **80 tests**, with **5 live tests skipped** (two PostgreSQL and three model-service checks). This is local compatibility evidence, not live extraction quality or PostgreSQL concurrency evidence. See [compatibility evidence](compatibility-evidence.md) and [run instructions](GETTING-STARTED.md).

**Remote CI:** [run 35552348580](https://github.com/gajakannan/nebula-insurance-brain/actions/runs/35552348580) passed all five jobs on `9379e84`: engine **126 passed / 21 skipped**, neuron **58 passed / 4 skipped**, and the dedicated PostgreSQL proof **4 passed in 3.18 seconds**. Skipped cases in the general suites include unavailable live services; the dedicated database job supplies its own PostgreSQL service. All configured package coverage gates passed. OIDC discovery and all three seeded principals also passed.

**Earlier CI failure:** [run 35535414661](https://github.com/gajakannan/nebula-insurance-brain/actions/runs/35535414661) on `a64f0eb` passed all four database cases, then failed at OIDC application readiness. CI now bounds each HTTP request, allows 180 seconds for application readiness, and captures stack diagnostics on failure. The successful run above observed one 404 followed by a 200; the earlier failure's cause remains unconfirmed because its logs were not retained.

**Remaining before activation:** qualify full worker/model/import recovery on PostgreSQL and deployment/storage failures; compare live Graph chunking with the direct baseline on independently expected, approved corpus cases; qualify serving-tokenizer parity, deployment concurrency, credentials/logs, retention/deletion, and property/relationship evidence including multi-region cases; record the required reviewer verdicts. The current worker supports fixed GL templates. Production compilation (F0015), full run lifecycle (F0016), relationship semantics and affected-content evolution (F0032) remain their planned feature scopes, not delivered by this candidate. Targeted requests explicitly fail rather than broadening to full-document extraction. ADR-0060 remains Proposed.

## Story Checklist

| Story | Title | Status |
|---|---|---|
| [F0005-S0001](F0005-S0001-pin-and-process-source-documents.md) | Pin and process source documents | In Progress |
| [F0005-S0002](F0005-S0002-persist-artifacts-and-recover-jobs.md) | Persist artifacts and recover jobs | In Progress |
| [F0005-S0003](F0005-S0003-reinterpret-saved-json-and-map-evidence.md) | Reinterpret saved JSON and map evidence | In Progress |
| [F0005-S0004](F0005-S0004-evaluate-and-activate-proven-pipeline.md) | Evaluate and activate the proven pipeline | Not Started |

## Recommendation Audit

| Recommendation | Planning state | Delivery / proof still required |
|---|---|---|
| New orchestration ADR | ADR-0060 Proposed; acceptance gates explicit | Complete all four proof gates and obtain actual reviewer verdicts |
| Existing ADR invariants | Dated links preserve ADR-0003/0004/0040/0055/0058/0059 and F0001 results | Demonstrate compatibility with those contracts |
| Consistent blueprints, C4, article | Proposed target distinguished from current runtime | Update actual runtime descriptions after activation |
| Artifact and run identity | F0004/F0016 specify separate parser/pipeline/recipe/profile metadata and run-owned provenance | Shared result DTO and candidate persistence implemented; full F0016 lifecycle remains planned |
| F0004/F0005 feature planning | Neutral F0005 title; four stories; F0004 dependency explicit | S0001–S0004 execution |
| Profiles and interpretation | F0014/F0015/F0016 scope updated | Compiler and production run service implementation |
| Targeted evolution | F0032 now owns affected-content-only scheduling proof | Demonstrate bounded input, original refs, zero reparse |
| Review and release | F0022/F0026 evidence and failure/quality cases specified | Panel mapping and measured corpus results |
| Runtime, dependency lock, misleading adapter name | Candidate adapter, shared ParseResult, explicit direct baseline, pyproject/uv.lock pin, package/schema/input metadata implemented and tested | Candidate composition, metadata, scalar evidence and durable services implemented; full proof and activation pending |
| Full-document versus chunked extraction | F0001 one-call baseline retained; candidate tests use direct mode | Comparative schema/quality/cost/latency/review results |
| Local inference and operations | Bounded SDK client implemented; 23 offline tests cover budgets, cancellation, shared concurrency, errors, redacted diagnostics, and cached serving tokenizer | Live serving parity, deployment replica limits, credential/log and retention review, and operational qualification |
| Temporal and archive | v0.1 jobs / v0.3 Temporal retained; F0001 unchanged | No architecture replacement or reopened archive required |

## Proof Gates

- [ ] Exact-version native/scanned conversion, checkpoint, restart, and saved-JSON reuse.
- [ ] Insurer-critical property/relationship evidence, table and multi-region cases.
- [ ] Corpus comparison and timeout/partial/invalid-output/retry/restart cases.
- [ ] Local vLLM, secrets, concurrency, tenant access, and retention.

## Required Signoff Roles

Architecture reviews the checkpoint and invariants; QA reviews independent results; security reviews boundaries and resource/retention controls; code review covers runtime integration. Named reviewers and their actual verdicts remain pending.

## Story Signoff Provenance

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|

No verdicts recorded. Planning checks do not satisfy any proof gate.
