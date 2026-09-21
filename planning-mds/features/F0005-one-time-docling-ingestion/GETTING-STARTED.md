# F0005 — Getting started

The candidate adapter is implemented; the production integration is incomplete. Read [compatibility evidence](compatibility-evidence.md) for the exact pin, tested boundary, and remaining gates. ADR-0060 is Proposed.

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
