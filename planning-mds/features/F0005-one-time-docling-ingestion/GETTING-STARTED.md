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

`neuron/tests/integration/test_parse_once_reinterpret.py` remains the F0001 direct-vLLM comparison baseline. Local inference setup is documented in `docker/local-inference-runbook.md`. Live Graph comparison and the durable worker proof are still required before activation.

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
