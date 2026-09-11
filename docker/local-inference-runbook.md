# Local Inference Runbook — vLLM / Phi-4-mini-instruct (F0001-S0002)

Adapted from `nebula-insurance-crm/neuron/neuron-local-phi-vllm-wsl2-runbook.md`, the CRM's
validated profile on this same host/GPU (ADR-035). Brain runs its **own** vLLM process and
secrets file, isolated from the CRM's — do not share `~/.neuron-secrets` or its API key
across products.

## Validated environment (this host, confirmed 2026-09-08)

```text
GPU:      NVIDIA GeForce RTX 5070 (12,227 MiB total, ~11.9 GiB free with no other GPU process)
Python:   3.12 (vLLM's own venv; independent of engine/neuron's 3.13+ uv workspaces)
vLLM:     0.25.1 (docker/DEPENDENCY-MATRIX.md pin — matches the CRM's validated build)
Model:    microsoft/Phi-4-mini-instruct, bfloat16, 4,096-token context (ADR-0055)
Port:     8000 (confirmed free at F0001-G1 preflight; distinct from the CRM's neuron on :8200)
```

## 1. Create the environment (once)

```bash
mkdir -p ~/.venvs
uv venv ~/.venvs/brain-vllm --python 3.12
uv pip install --python ~/.venvs/brain-vllm/bin/python -U vllm==0.25.1 --torch-backend=auto
```

## 2. Secrets (never in the repo or `.env`)

```bash
umask 077
cat > ~/.brain-secrets <<'EOF'
export BRAIN_INFERENCE_API_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export VLLM_API_KEY="$BRAIN_INFERENCE_API_KEY"
export VLLM_WSL2_ENABLE_PIN_MEMORY=1
export VLLM_USE_FLASHINFER_SAMPLER=0
EOF
chmod 600 ~/.brain-secrets
source ~/.brain-secrets
```

`VLLM_API_KEY` authenticates clients without the key ever appearing in a process listing
(vLLM 0.25.1 accepts `--api-key` on the command line too, but that leaks the key via `ps`
on a shared host — use the environment variable instead, matching the CRM's rule).

## 3. Start the server

```bash
source ~/.brain-secrets
: "${VLLM_API_KEY:?source ~/.brain-secrets first}"

~/.venvs/brain-vllm/bin/vllm serve microsoft/Phi-4-mini-instruct \
  --host 127.0.0.1 \
  --port 8000 \
  --dtype auto \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.90
```

## 4. Verify (F0001-S0002 acceptance criterion)

```bash
curl -s -H "Authorization: Bearer $VLLM_API_KEY" http://127.0.0.1:8000/v1/models | python3 -m json.tool
```

Expected: the response lists `microsoft/Phi-4-mini-instruct` with `max_model_len: 4096`.

## 5. Neuron configuration

`neuron/` (from F0001-S0003 onward) reads the endpoint from environment, never hardcoded:

| Variable | Value |
|---|---|
| `BRAIN_INFERENCE_BASE_URL` | `http://127.0.0.1:8000/v1` |
| `BRAIN_INFERENCE_MODEL` | `microsoft/Phi-4-mini-instruct` |
| `BRAIN_INFERENCE_API_KEY_ENV` | `BRAIN_INFERENCE_API_KEY` (name of the env var holding the key, not the key itself) |
| `BRAIN_INFERENCE_CONTEXT_LIMIT` | `4096` |

## Known failure modes (see the CRM runbook for full detail)

- **`ERROR: VLLM_API_KEY is not configured`** — `~/.brain-secrets` was not sourced in this shell.
- **CUDA OOM on startup** — another GPU process is running; `nvidia-smi` and free it first (this
  host runs no other GPU workload by default; the CRM's vLLM, if started, must be stopped first
  since a single RTX 5070 cannot serve two 7+ GiB model weights concurrently at this VRAM budget).
- **Port 8000 already bound** — confirm no other local server owns it (`ss -ltn | grep :8000`);
  override with `--port` and update `BRAIN_INFERENCE_BASE_URL` to match.
