# F0005 — One-time document ingestion — Status

**Overall Status:** Synthetic development scope complete; local qualification and gated activation re-planned. The opt-in candidate and its development proof are implemented. ADR-0060 remains Proposed. See [compatibility evidence](compatibility-evidence.md) and the [synthetic comparison](synthetic-comparison.json).\
**Last Updated:** 2026-10-23\
**Plan Run:** `2026-10-23-9a04b327` (first F0005 plan run)

## Planning Position

Plan run `2026-10-23-9a04b327` re-plans the remaining work against shipped F0002–F0004. Operator decisions at G1 (2026-10-23): local live qualification on the development host with gated activation; a synthetic qualification corpus with independent expectations and independent agent-role reviewers; F0005 enables the F0004 v2 writer as an activation step (new story S0005); F0016 owns document-date candidates. The PRD fixes the qualification thresholds. Phase A was approved with `approve-phase-a` and Phase B with `approve-phase-b` on 2026-10-23. The plan is ready for the feature action, starting with Step 0 preflight and the Step 1 corpus. Planning does not authorize implementation or change delivery priority.

## Synthetic development scope (2026-09-20 to 2026-09-22)

The authorized scope uses synthetic development fixtures. Architecture/article reconciliation, the pinned Graph integration, durable recovery, bounded transport, evidence mapping, and a reproducible recorded-response comparison are delivered. This is the completion boundary for the current development work. The production proof gates below remain release requirements, not prerequisites for completing this scope.

The comparison runs the direct baseline, Graph direct, and Graph dense over three synthetic cases. All nine retain the saved native JSON without conversion. Dense performs skeleton/fill requests across multiple chunks and passes the unique, ambiguous, and multi-region evidence expectations. The historical baseline chooses a first match for repeated values; Graph direct lacks usable item refs on these longer fixtures and remains unresolved. These are observed development limitations, not measured model quality. The worker's current direct default remains opt-in.

Multi-region text now requires continuous source coverage and preserves separate selectors through assertion import, review-item creation, and region selection in the Review Panel. Mixed or incomplete evidence remains unresolved. The mapper version is 2. Dense legacy-mode hints retain Nebula's schema-enforced transport and validation.

## Candidate runtime delivery — 2026-09-20

The candidate has been merged to main from `feature/docling-graph-delivery`, based on `a60350d`. It remains opt-in; it does not replace the accepted F0001 baseline or imply release acceptance.

- `CheckpointStore` verifies scope, inventory, source/native and bundle hashes. Manifest-last publication supports identical retries. Missing files in a published bundle or run are integrity failures, never cache misses that trigger re-parsing. Filesystem writes use private temporary files, fsync, and atomic publication.
- `DocumentJobQueue` and migration 0004 provide artifact leases, generations, heartbeats, scoped idempotency, cancellation, finite retries, event history, and a completion outbox. PostgreSQL fences use the current database clock after lock acquisition. Four PostgreSQL queue tests cover competing claims, expired-generation fencing, child-process exit/reclaim after checkpoint publication, and lease expiry during a row-lock wait. Five additional cases now prove worker/importer recovery at the boundaries described below; infrastructure and live-provider failure recovery remain open.
- `DocumentWorker` performs conversion/checkpoint publication, saved-JSON interpretation, fenced output publication, and recovery of a successful prior attempt. Jobs pin profile version and schema hash. Artifact metadata is registered before model extraction, so model failure leaves the content available to authorized engine readers. A real process-exit test recovers published output without a conversion or model call.
- `DocumentJobAuthorization` re-reads active principal status, unrevoked grants, and Casbin policy at sensitive boundaries; decisions are audited. Only the existing `ServicePrincipal` role receives the new `ingest` and `interpret` grants. The CLI is a trusted-operator interface, not an unauthenticated public upload endpoint.
- `DocumentResultImporter` atomically inserts source/artifact metadata, the interpretation run, assertions, evidence, review items, and an outbox acknowledgement. An injected review insertion failure rolls back the entire import; retry creates one set of rows. Unresolved evidence remains unresolved and enters provenance review. No canonical fact is accepted by this importer. Entity/relationship output is rejected until its downstream mapping exists.
- The shared DTO lives in `engine/packages/brain-contracts`; the old neuron import remains compatible. Parser, pipeline, model, template, limits, and run-owned provenance metadata remain distinct. Unique native text and table-cell locations are supported; ambiguous or normalized values are unresolved.
- `python -m brain_ingestion.worker_cli` provides opt-in submission, worker, and import-only commands. Both dependency locks resolve and both runtime environments sync offline.

**Verification:** the combined runtime suite passed **80 tests**, with **5 live tests skipped** (two PostgreSQL and three model-service checks). This is local compatibility evidence, not live extraction quality or PostgreSQL concurrency evidence. See [compatibility evidence](compatibility-evidence.md) and [run instructions](GETTING-STARTED.md).

**Remote CI:** [run 35589532922](https://github.com/gajakannan/nebula-insurance-brain/actions/runs/35589532922) passed all five jobs on `4712811`: engine **126 passed / 21 skipped**, neuron **63 passed / 9 skipped**, PostgreSQL queue proof **4 passed**, and PostgreSQL worker/importer recovery **5 passed**. The general suites skip unavailable live services; the dedicated database job supplies PostgreSQL and executes all nine database proof cases. All configured coverage, lint/type, frontend, planning, and framework gates passed, along with OIDC discovery and the seeded principals.

**Worker/importer recovery — 2026-09-21:** real child processes exit after bundle publication, extraction-result publication, job completion, midway through result import, and after import commits. Every case recovers with one conversion, one recorded model call, one assertion/evidence/review set, and one acknowledged completion. The importer rollback case leaves no partial assertion or run. These tests run real Graph stages and authorization with synthetic native content and recorded HTTP responses; they do not exercise a physical parser, live provider, or infrastructure failure.

**Earlier CI failure:** [run 35535414661](https://github.com/gajakannan/nebula-insurance-brain/actions/runs/35535414661) on `a64f0eb` passed all four database cases, then failed at OIDC application readiness. CI now bounds each HTTP request, allows 180 seconds for application readiness, and captures stack diagnostics on failure. The subsequent successful run `35552348580` observed one 404 followed by a 200; the earlier failure's cause remains unconfirmed because its logs were not retained.

**Remaining before activation:** qualify live-provider and deployment/storage failures; compare live Graph chunking with the direct baseline on independently expected, approved corpus cases; qualify serving-tokenizer parity, deployment concurrency, credentials/logs, retention/deletion, and property/relationship evidence including multi-region cases; record the required reviewer verdicts. The current worker supports fixed GL templates. Production compilation (F0015), full run lifecycle (F0016), relationship semantics and affected-content evolution (F0032) remain their planned feature scopes, not delivered by this candidate. Targeted requests explicitly fail rather than broadening to full-document extraction. ADR-0060 remains Proposed.

## Story Checklist

| Story | Title | Status |
|---|---|---|
| [F0005-S0001](F0005-S0001-pin-and-process-source-documents.md) | Pin and process source documents | In Progress |
| [F0005-S0002](F0005-S0002-persist-artifacts-and-recover-jobs.md) | Persist artifacts and recover jobs | In Progress |
| [F0005-S0003](F0005-S0003-reinterpret-saved-json-and-map-evidence.md) | Reinterpret saved JSON and map evidence | In Progress |
| [F0005-S0004](F0005-S0004-evaluate-and-activate-proven-pipeline.md) | Evaluate and activate the proven pipeline | In Progress — synthetic comparison complete; live comparison planned |
| [F0005-S0005](F0005-S0005-qualify-text-origin-and-enable-v2-publication.md) | Qualify text origin and enable v2 publication | Not Started |

## Recommendation Audit

| Recommendation | Planning state | Delivery / proof still required |
|---|---|---|
| New orchestration ADR | ADR-0060 Proposed; acceptance gates explicit | Complete all four proof gates and obtain actual reviewer verdicts |
| Existing ADR invariants | Dated links preserve ADR-0003/0004/0040/0055/0058/0059 and F0001 results; bounded artifact/reuse/evidence tests pass | Complete production qualification against those contracts |
| Consistent blueprints, C4, article | Proposed target distinguished from current runtime | Update actual runtime descriptions after activation |
| Artifact and run identity | F0004/F0016 specify separate parser/pipeline/recipe/profile metadata and run-owned provenance | Shared result DTO and candidate persistence implemented; full F0016 lifecycle remains planned |
| F0004/F0005 feature planning | Neutral F0005 title; four stories; F0004 dependency explicit; synthetic development scope delivered | Remaining production qualification and signoffs for S0001–S0004 |
| Profiles and interpretation | F0014/F0015/F0016 scope updated | Compiler and production run service implementation |
| Targeted evolution | F0032 now owns affected-content-only scheduling proof | Demonstrate bounded input, original refs, zero reparse |
| Review and release | F0022/F0026 cases specified; synthetic multi-region evidence survives import and Review Panel decisions | Live property/relationship evidence qualification and measured corpus results |
| Runtime, dependency lock, misleading adapter name | Candidate adapter, shared ParseResult, explicit direct baseline, pyproject/uv.lock pin, package/schema/input metadata implemented and tested | Candidate composition, metadata, scalar evidence and durable services implemented; full proof and activation pending |
| Full-document versus chunked extraction | Nine recorded-response runs compare the direct baseline, Graph direct, and Graph dense; schema, abstention, evidence, and zero-conversion expectations checked | Live quality/cost/latency/review measurements; synthetic token estimates and timing are not serving measurements |
| Local inference and operations | Bounded SDK client implemented; 23 offline tests cover budgets, cancellation, shared concurrency, errors, redacted diagnostics, and cached serving tokenizer | Live serving parity, deployment replica limits, credential/log and retention review, and operational qualification |
| Temporal and archive | v0.1 jobs / v0.3 Temporal retained; F0001 unchanged | No architecture replacement or reopened archive required |

## Proof Gates

- [ ] Exact-version native/scanned conversion, checkpoint, restart, and saved-JSON reuse.
- [ ] Insurer-critical property/relationship evidence, table and multi-region cases.
- [ ] Corpus comparison and timeout/partial/invalid-output/retry/restart cases.
- [ ] Local vLLM, secrets, concurrency, tenant access, and retention.
- [ ] Activation prerequisite added 2026-09-25 (validate finding A-4). Before S0004 activates the candidate pipeline, published blocks carry `text_origin` (`STATED`, `OCR`, `TRANSCRIBED`, `DESCRIBED`) and the producing engine, and the evidence mapping locates quotes on the server under the ADR-0065 admission contract. The alternative is a recorded deferral of both to F0004/F0016 with rationale. F0004 delivered the text-origin storage and fallback; plan run `2026-10-23-9a04b327` assigns the live qualification and switch to S0005. See [ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md) and [validate run 2026-09-25-463eecdd](../../operations/evidence/runs/2026-09-25-463eecdd/architect-validation-report.md).

## Required Signoff Roles

Architecture reviews the checkpoint and invariants; QA reviews independent results; security reviews boundaries and resource/retention controls; code review covers runtime integration. Named reviewers and their actual verdicts remain pending.

## Story Signoff Provenance

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|

No verdicts recorded. Planning checks do not satisfy any proof gate.
# F0005 — One-time document ingestion

**Status:** Planned feature; synthetic development scope complete. Local qualification and gated activation re-planned and approved (Phase A and B) in plan run `2026-10-23-9a04b327`; feature action not started. ADR-0060 remains Proposed.
**Phase:** v0.1A
**Roadmap:** Next

## Overview

Process each document version into an immutable content artifact and reuse it for later interpretations. Proposed [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) evaluates Docling-Graph as the coordinator, with Docling underneath and Nebula owning persistence, evidence, durable jobs, and canonical authority. The existing folder path remains stable for references.

## Documents

- [PRD](PRD.md): scope and acceptance.
- [Assembly plan](feature-assembly-plan.md): reconciliation with shipped F0002–F0004, qualification steps, failure injection, pipeline selection, decision and rollback.
- [Status](STATUS.md): recommendation audit, pending proofs, and actual signoffs.
- [Acceptance criteria checklist](acceptance-criteria-checklist.md): per-criterion verification state.
- [Getting started](GETTING-STARTED.md): current baseline and planning checks.

## Stories

| ID | Title | Status |
|---|---|---|
| [F0005-S0001](F0005-S0001-pin-and-process-source-documents.md) | Pin and process source documents | In Progress |
| [F0005-S0002](F0005-S0002-persist-artifacts-and-recover-jobs.md) | Persist artifacts and recover jobs | In Progress |
| [F0005-S0003](F0005-S0003-reinterpret-saved-json-and-map-evidence.md) | Reinterpret saved JSON and map evidence | In Progress |
| [F0005-S0004](F0005-S0004-evaluate-and-activate-proven-pipeline.md) | Evaluate and activate the proven pipeline | In Progress — synthetic comparison complete |
| [F0005-S0005](F0005-S0005-qualify-text-origin-and-enable-v2-publication.md) | Qualify text origin and enable v2 publication | Not Started |

**Total Stories:** 5

F0004 is an explicit prerequisite. Fixed proof templates avoid a dependency cycle with the later F0015 compiler. F0016/F0032 carry the production run, document-date candidate production (operator decision 2026-10-23) and targeted-evolution requirements; F0026 carries release qualification. Archived F0001 remains unchanged.
# F0005 — Getting started

The candidate adapter is implemented; the production integration is incomplete. Read [compatibility evidence](compatibility-evidence.md) for the exact pin, tested boundary, and remaining gates. ADR-0060 is Proposed.

The remaining work, local live qualification and gated activation, is specified in the [assembly plan](feature-assembly-plan.md) (plan run `2026-10-23-9a04b327`). Its corpus, harness, fault proxy, `extraction.pipeline` setting and migration 0009 do not exist yet; the commands below cover only what is implemented.

From the repository root:

```bash
uv sync --locked --project neuron
LITELLM_LOCAL_MODEL_COST_MAP=True HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2 \
  neuron/.venv/bin/python -m pytest neuron/tests/integration/test_graph_pipeline_contract.py -q
python3 scripts/validation/validate_plan_readiness.py --plan-scope feature --target F0005
python3 scripts/run-lifecycle-gates.py
```

Native/scanned tests need the Docling model assets cached. The model client returns recorded values: these tests do not measure extraction accuracy. The filesystem checkpoint test executes storage I/O inline because this restricted environment cannot deliver asyncio's thread wakeups; it does not prove worker crash recovery.

`neuron/tests/integration/test_parse_once_reinterpret.py` remains the F0001 direct-vLLM comparison baseline. Local inference setup is documented in `docker/local-inference-runbook.md`. Worker recovery and PostgreSQL queue tests now have recorded results; live Graph comparison and deployment qualification are still required before activation.

## Bounded model client

`brain_extraction.vllm_graph_client.VllmGraphClient` implements Graph's model-client protocol with a self-hosted OpenAI-compatible transport. It disables SDK retries, redirects, and environment proxy discovery on its default transport. Create one client per attempt and share a `BoundedSemaphore` across clients in the worker; close each client after use. Supply the token counter from `cached_model_token_counter(model_id, model_revision)`, using the exact serving model/tokenizer revision. Production worker composition still owns the endpoint allowlist and cross-process concurrency limit.

The client reserves input/schema/output tokens before each request and applies call/token budgets across repairs. Queued work observes cancellation and the attempt deadline. In-flight HTTP work is bounded by transport timeouts; cancellation prevents accepting its result and scheduling another request, but does not interrupt a provider operation already running. The deadline is not a hard process-kill guarantee. Diagnostics contain hashes, usage, and reason codes, not prompts, responses, or API keys. They still need persistence under the authorized run.

Run the offline transport tests:

```bash
LITELLM_LOCAL_MODEL_COST_MAP=True HF_HUB_OFFLINE=1 \
  neuron/.venv/bin/python -m pytest neuron/tests/integration/test_vllm_graph_client.py -q
```

## Opt-in live smoke proof

Start the dedicated Brain vLLM server using the [candidate revision instructions](../../../docker/local-inference-runbook.md#f0005-candidate-model-revision). Supply its credential through `BRAIN_INFERENCE_API_KEY` as described there. Then run:

```bash
export BRAIN_INFERENCE_MODEL_REVISION=cfbefacb99257ffa30c83adab238a50856ac3083
BRAIN_RUN_LIVE_GRAPH_PROOF=1 LITELLM_LOCAL_MODEL_COST_MAP=True HF_HUB_OFFLINE=1 \
  neuron/.venv/bin/python -m pytest neuron/tests/integration/test_graph_live_inference.py -q
```

This test performs actual model requests for two GL profiles over saved JSON with conversion forbidden. It is skipped unless explicitly enabled. It does not replace the chunked corpus comparison, evidence-mapping proof, or worker recovery gates.

## Candidate worker and result import

The candidate now has a runnable composition and engine import. It stays opt-in while ADR-0060 is Proposed. Use one worker process/replica for qualification; its shared model semaphore does not impose a distributed GPU quota. The fixed-template worker currently uses Graph's `direct` contract. Chunked comparison must explicitly exercise the service's `dense` contract; the direct-path tests are not chunking proof.

Install both locked workspaces, then apply the migration to a **development** PostgreSQL database. Set `BRAIN_DATABASE_URL` for Alembic and `BRAIN_WORKER_DATABASE_URL` for the worker to the same `postgresql+psycopg` database through the local secret mechanism. The configured filesystem root must be immutable and shared by the worker and importer.

```bash
uv sync --locked --project engine
uv sync --locked --project neuron
cd engine/migrations
../.venv/bin/alembic upgrade head
cd ../..
```

Provide `BRAIN_WORKER_PRINCIPAL_ID` for an active, provisioned service principal with an unrevoked `ServicePrincipal` membership in the target tenant/knowledge base. The CLI trusts the local operator to select that identity; expose an authenticated application boundary before making submission available to external callers. Do not grant service roles to arbitrary uploaders. Both ingestion and interpretation decisions are checked and audited, including after a job restarts.

Set `NEBULA_TENANT_ID` and `NEBULA_KB_ID` to the provisioned scope. Submit a development fixture:

```bash
export BRAIN_ENABLE_GRAPH_CANDIDATE=1
neuron/.venv/bin/python -m brain_ingestion.worker_cli \
  --policy-dir planning-mds/security/policies \
  --enqueue neuron/fixtures/gl-policy-declarations.pdf \
  --tenant "$NEBULA_TENANT_ID" --knowledge-base "$NEBULA_KB_ID" --profile gl-limits-a
```

For processing, supply `BRAIN_INFERENCE_BASE_URL`, `BRAIN_INFERENCE_API_KEY`, `BRAIN_INFERENCE_MODEL`, and the immutable `BRAIN_INFERENCE_MODEL_REVISION` through the inference runbook's credential mechanism. Cache the matching tokenizer and Docling assets first. `--once` processes at most one job and one pending import; omit it to poll until SIGINT/SIGTERM. Shutdown waits for the current activity; it is not a hard kill for a converter or provider operation already in progress.

```bash
neuron/.venv/bin/python -m brain_ingestion.worker_cli \
  --policy-dir planning-mds/security/policies --once
neuron/.venv/bin/python -m brain_ingestion.worker_cli \
  --policy-dir planning-mds/security/policies --import-only --once
```

Submission is idempotent for a source/recipe/actor/profile identity. A second profile reuses the same bundle and creates a separate job/run. Published successful attempts are recovered without new model calls. An outbox import failure leaves the acknowledgement pending and rolls back all imported rows. Investigate the stable failure code, correct the cause, and rerun import; never delete a bundle to clear a model error. Source-bearing outputs and failed/partial runs live beneath the protected object-store root; production retention must include `runs/` as well as `bundles/` and `sources/`. No automatic retention policy is invented here. OS-killed workers can leave private temporary files; cleanup must run with workers stopped or with a reviewed age/lease policy.

## PostgreSQL qualification

Set `BRAIN_TEST_POSTGRES_URL` to a disposable development PostgreSQL database using the psycopg driver. The tests create and drop only their own random schemas. They fail on a configured but unreachable database; they skip only when the variable is absent.

```bash
neuron/.venv/bin/python -m pytest engine/packages/brain-jobs/tests/test_postgres.py -q
LITELLM_LOCAL_MODEL_COST_MAP=True HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2 \
  neuron/.venv/bin/python -m pytest \
  neuron/tests/integration/test_document_process_recovery.py -k postgresql -q
```

Run the combined offline suite documented in [compatibility evidence](compatibility-evidence.md) as well. Neither this PostgreSQL test nor the live model smoke test replaces the approved corpus comparison, operational qualification, and reviewer acceptance gates.

CI's `runtime-stack` job applies the engine migrations to its disposable PostgreSQL database and runs four isolated-schema document-job tests: competing claims, expired-generation fencing, child-process exit/reclaim after checkpoint publication, and lease expiry while publication waits for a row lock.

It also runs five worker/importer process-exit cases: after bundle publication, after extraction-result publication, after job completion, midway through result import, and after import commits. These use real Graph stages, authorization, artifact registration, and result import, with synthetic native content and recorded model responses. Recovery must retain one conversion, one model call, one assertion/evidence/review set, and one acknowledged completion. Each test owns an isolated schema populated from the application metadata; migration execution is a separate CI step.

To run these five cases offline with SQLite, omit the database variable and use `-k sqlite` instead. A configured but unreachable PostgreSQL database is a failure, never a skip. These cases do not establish live provider behavior, machine/database/storage failure recovery, retention acceptance, or extraction quality.

## Synthetic development comparison

The current scope uses synthetic development fixtures. No model endpoint or credential is required:

```bash
LITELLM_LOCAL_MODEL_COST_MAP=True HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2 \
  neuron/.venv/bin/python neuron/benchmarks/docling_graph_comparison.py \
  --output /tmp/nebula-synthetic-comparison.json
```

Choose a new output path on each run. The runner creates temporary verified bundles and executes the baseline, Graph direct, and Graph dense using HTTP MockTransport recordings. It forbids conversion during interpretation and checks that saved native JSON is unchanged. Nine runs cover unique, repeated, and multi-region values; the aggregate field is deliberately absent to exercise abstention. The command fails if dense falls back to direct, loses its chunking, or fails the development expectations.

The [recorded report](synthetic-comparison.json) contains per-case schema/value/abstention/evidence checks, model phases and call counts, chunk counts, token estimates, local elapsed time, and review-candidate counts. Token estimates use cl100k_base and elapsed time excludes inference. Recorded responses dictate the values: these measurements demonstrate orchestration and grounding behavior, not accuracy, provider cost, or live latency. Direct Graph evidence on these longer fixtures remains unresolved where upstream supplies no usable item references. Dense preserves the references and passes the evidence expectations.

Live corpus qualification and production signoff are later release work. They do not block this synthetic development scope or change the opt-in activation boundary.
