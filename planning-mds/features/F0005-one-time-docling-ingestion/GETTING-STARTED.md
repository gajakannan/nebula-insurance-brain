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
