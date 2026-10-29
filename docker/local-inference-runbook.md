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

## F0005 candidate model revision

The Graph candidate's offline tokenizer check uses `microsoft/Phi-4-mini-instruct` at cached commit `cfbefacb99257ffa30c83adab238a50856ac3083`. This is an explicit candidate pin, not a claim that F0001's historical server ran that revision. Its tokenizer loads from local assets with remote Python code disabled.

For the live Graph proof, start a dedicated Brain server with that same model and tokenizer revision; do not infer a revision from the model name returned by `/models`:

```bash
source ~/.brain-secrets
export BRAIN_INFERENCE_MODEL_REVISION=cfbefacb99257ffa30c83adab238a50856ac3083
~/.venvs/brain-vllm/bin/vllm serve microsoft/Phi-4-mini-instruct \
  --revision "$BRAIN_INFERENCE_MODEL_REVISION" \
  --tokenizer-revision "$BRAIN_INFERENCE_MODEL_REVISION" \
  --host 127.0.0.1 --port 8000 --dtype auto \
  --max-model-len 4096 --gpu-memory-utilization 0.90
```

The candidate client counts chat-template token IDs plus a conservative schema reservation. If reported usage exceeds its reservation, it records the incurred usage and refuses further calls in that attempt. Follow [F0005's live smoke instructions](../planning-mds/features/archive/F0005-one-time-docling-ingestion/GETTING-STARTED.md#opt-in-live-smoke-proof). Live model quality and serving-revision parity have not been verified by the offline tests.

## F0005 host guard and provider quiescence (DevOps)

The processing worker is a single host-guarded owner of the dedicated Brain provider. Every processing process on the host, whatever its checkout, content root, tenant or temporary configuration, acquires the same advisory lock under `/tmp/nebula-brain-inference-<uid>/` (mode `0700`, derived from the account UID; no environment or configuration override exists) before any queue claim, conversion or model request. A second worker exits `inference_guard_busy`. Submission-only and import-only commands do not take the guard.

**Preflight: record the provider.** With the server started by the command above, record its process-group identity once (this is the allowlist the worker checks):

```bash
export BRAIN_INFERENCE_BASE_URL=http://127.0.0.1:8000/v1
neuron/.venv/bin/python -m brain_ingestion.provider_supervisor record --pid "$(pgrep -f 'vllm serve microsoft/Phi-4-mini-instruct' | head -1)"
neuron/.venv/bin/python -m brain_ingestion.provider_supervisor status
```

The record holds the PID, process-group ID, kernel start time, serving argv and working directory; no credential. `record` accepts only a `vllm serve` process-group leader whose argv binds the guarded `--host` and `--port` and contains no `--api-key`; anything else is refused as `provider_record_invalid`, both when it is recorded and whenever the file is used. The provider process-group owner is the account that started `vllm serve` (UID 1000 on the development host); only that account may run the worker or the supervisor. Stop other clients of the dedicated server before processing.

**Uncertain request recovery.** Before each provider request the worker durably writes `<key>.inflight.json`; it clears it only after a terminal provider response or a refused connection. After an HTTP timeout, broken transport, cancellation without confirmed completion or a worker crash, the marker stays dirty: the worker stops claiming and every replacement exits `provider_quiescence_required`. A healthy `/health` response never clears it. Recover only with:

```bash
source ~/.brain-secrets
export BRAIN_INFERENCE_BASE_URL=http://127.0.0.1:8000/v1
neuron/.venv/bin/python -m brain_ingestion.provider_supervisor quiesce
```

Holding the guard, `quiesce` sends SIGTERM to the recorded process group (SIGKILL after 60 s), confirms every member (API server and `VLLM::EngineCore`) has exited, restarts the identical recorded command with the same model/tokenizer revision, waits for `/health`, an authenticated model listing and a refused unauthenticated listing (a restart without `VLLM_API_KEY` fails as `provider_restart_unauthenticated`, never "ready"), records the new identity, writes a source-free receipt under `<key>.receipts/` and only then clears the marker. If the recorded PID now names another process, group or command line, or the group cannot be confirmed gone, it fails closed (`provider_ownership_unconfirmed` / `provider_exit_unconfirmed`) and leaves the marker dirty; investigate manually and never delete the marker by hand. The F0005 qualification harness runs this same sequence automatically per injected fault on the development host.

**Infrastructure faults.** If the in-flight marker cannot be written durably (for example `/tmp` full or read-only), nothing is sent and the worker exits `inflight_marker_not_durable` without failing the job; queued jobs are reclaimed after their lease once the directory is healthy.

**Failure reasons.** Job history records one stable reason per failed attempt (migrations 0009/0010): model unavailable, timeout, HTTP error, malformed or schema-invalid output, budget exceeded, deadline exceeded, contract fallback; conversion failed or timed out; storage write failed; interpretation failed (after a ready bundle); stage-guard mismatch; unsupported targeting or output; authorization denied; cancelled. A job converts at most twice, counted from durable `conversion_started` events.

**Conversion children.** Physical conversion runs in a spawned child process group with private staging under `/tmp/nebula-brain-inference-<uid>/conversion/`. The parent decides a 300-second deadline, then terminates the whole group (SIGTERM, 2 s, SIGKILL, 3 s reap). If the group cannot be confirmed gone the worker stops with `converter_cleanup_unconfirmed`, leaving the launch receipt and staging for inspection; the next worker's startup reaper kills only a group whose recorded start time matches, and otherwise fails closed. Do not remove this directory while a worker or the provider is live; reboot/`/tmp` cleanup requires the provider stopped and the quiescence procedure above.
