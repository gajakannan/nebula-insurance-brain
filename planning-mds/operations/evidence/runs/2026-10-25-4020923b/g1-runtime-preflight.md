# G1 — Runtime Preflight

**Feature:** F0005 — One-time document ingestion  
**Run:** `2026-10-25-4020923b`  
**Role:** DevOps  
**Updated:** 2026-10-25  
**Result:** PASS — resumed preflight on 2026-10-25T23:28 restored GPU, loopback and the pinned Brain model server (earlier attempts FAIL, retained below)

## Required runtime

F0005 requires the development-host GPU, a dedicated Brain vLLM 0.25.1 service on loopback port 8000 with model/tokenizer revision `cfbefacb99257ffa30c83adab238a50856ac3083`, Docker-managed PostgreSQL, and the pinned Docling/RapidOCR assets. The vLLM executable, candidate model snapshot, and `neuron/uv.lock` are present.

## Initial preflight — before Docker startup

Commands ran at `2026-10-25T22:48:30-04:00`; exact commands, output, and exit codes are in `commands.log`.

| Check | Result |
|---|---|
| `nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader` | **FAIL (255):** NVML reported GPU access blocked by the operating system. |
| `docker compose ps` | **FAIL (1):** Docker CLI was unavailable in the WSL 2 distro. |
| `ss -ltnH 'sport = :8000'` | **INCONCLUSIVE:** netlink access was denied; the return code did not establish port state. |
| Credential probe | **FAIL:** `BRAIN_INFERENCE_API_KEY`, `BRAIN_INFERENCE_MODEL_REVISION`, and `~/.brain-secrets` were absent. No secret value was read or logged. |

## Recheck after operator started Docker

Commands ran at `2026-10-25T22:55:02-04:00` and `2026-10-25T22:55:21-04:00`; exact entries are in `commands.log`.

| Check | Result |
|---|---|
| `docker compose ps` | **PASS:** Docker is reachable. `brain-postgres`, `brain-authentik-server`, and `brain-authentik-worker` report healthy. Compose warns that `AUTHENTIK_SECRET_KEY` and `AUTHENTIK_BOOTSTRAP_PASSWORD` are unset; no values were exposed. |
| `nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader` | **FAIL (255):** NVML still reports GPU access blocked by the operating system. |
| vLLM environment `torch.cuda.is_available()` probe | **FAIL:** PyTorch `2.11.0+cu130` reports `cuda_available=False` and `cuda_device_count=0`. |
| `ss -ltnH 'sport = :8000'` | **INCONCLUSIVE:** netlink access remains denied. |
| Unauthenticated GET to `http://127.0.0.1:8000/v1/models` | **INCONCLUSIVE:** the execution environment denied loopback access (`Operation not permitted`); the server state could not be verified. |
| Credential probe | **FAIL at this attempt:** the Brain API key, model revision variable, and `~/.brain-secrets` were absent. The vLLM binary, candidate model snapshot, and neuron lock are present. |

## Recheck after Brain secret setup

Checked on 2026-10-25 after the operator created `~/.brain-secrets`; exact probe command and exit code are in `commands.log`.

| Check | Result |
|---|---|
| Secret-file metadata | **PASS:** file exists with mode `0600`; a persisted `BRAIN_INFERENCE_API_KEY` is present and `VLLM_API_KEY` references it. No secret value was read or logged. |
| `nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader` | **FAIL (255):** GPU access remains blocked by the operating system. |
| vLLM environment PyTorch probe | **FAIL:** PyTorch `2.11.0+cu130` reports `cuda_available=False` and `cuda_device_count=0`. |
| Authenticated GET to `http://127.0.0.1:8000/v1/models` | **INCONCLUSIVE:** the execution environment denied loopback access (`Operation not permitted`); the server state could not be verified. |

## Resumed preflight — PASS (2026-10-25T23:26–23:28-04:00)

A new operator session resumed the same run. Exact commands and exit codes are appended to `commands.log`; no secret value was printed or logged.

| Check | Result |
|---|---|
| GPU | **PASS:** NVIDIA GeForce RTX 5070, 12,227 MiB, driver 610.88 (CUDA UMD 13.3); ~10.9 GiB held by the Brain vLLM process. |
| CUDA in the vLLM environment | **PASS:** vLLM 0.25.1, PyTorch 2.11.0+cu130, CUDA 13.0, `cuda.is_available()=True`. |
| Serving process | **PASS:** PID/PGID 16365 (owner `gajap`, UID 1000), `vllm serve microsoft/Phi-4-mini-instruct --revision cfbefacb99257ffa30c83adab238a50856ac3083 --tokenizer-revision cfbefacb99257ffa30c83adab238a50856ac3083 --host 127.0.0.1 --port 8000 --dtype auto --max-model-len 4096 --gpu-memory-utilization 0.90`, matching the runbook's candidate command. Process group: API server, resource tracker, `VLLM::EngineCore`. This PGID is the provider process-group owner for Step 0a quiescence. |
| Endpoint and authentication | **PASS:** `127.0.0.1:8000` listening on loopback only; an unauthenticated `/v1/models` request returns 401; an authenticated one returns `microsoft/Phi-4-mini-instruct`, `max_model_len=4096`. No other client was connected (0 established sessions). |
| Database | **PASS:** `brain-postgres`, `brain-authentik-server` and `brain-authentik-worker` healthy. |
| Dependency lock (S0001-AC1) | **PASS:** `uv sync --locked` succeeds for `neuron` and `engine`; Docling 2.126.0, Docling-Graph 1.9.1, docling-core 2.95.0, RapidOCR 3.9.2. No lock mismatch. |
| Model/OCR asset caches | **PASS:** HF cache holds `microsoft/Phi-4-mini-instruct`, `docling-project/docling-models` and `docling-layout-heron`; RapidOCR PP-OCRv6 det/rec and mobile-v2.0 cls assets are under the installed `rapidocr/models` package directory. Per-file digests are recorded at conversion time by S0005 (Step 3), not assumed here. |
| Regression baseline | **PASS:** `test_graph_pipeline_contract.py`, `test_vllm_graph_client.py` and `test_document_process_recovery.py` (including the PostgreSQL cases against `brain-postgres`): 40 passed, 0 skipped. JUnit: `artifacts/test-results/g1-regression-baseline.xml`. |
| Step 0a guard preconditions | **PASS:** host UID 1000; `/tmp` is tmpfs with working `flock`: a second independent process (different cwd) gets `BUSY` while the lock is held and acquires it after release. `/tmp/nebula-brain-inference-1000/` does not exist yet; the guard creates it 0700. The worker runs on the host, not in a container, so no bind-mount mapping applies. |

## Restoration assessment (before resume)

Starting Docker restored container access and healthy PostgreSQL/AuthentiK services. The Brain inference secret is now provisioned with private permissions, but CUDA visibility and loopback access remain blocked from this execution environment; the inference server state is unverified. No application tests, scans, or model requests were performed.

## Result (superseded attempt)

FAIL. Stop at G1 under the runtime-preflight stop condition. Keep the manifest `in-progress`; do not advance to G2 or declare feature completion. The secret is provisioned; resume this same run only after GPU and loopback access are available to the execution environment and the documented Brain inference server is running with the pinned model/tokenizer revision.

## Result

PASS. The runtime-preflight stop condition is cleared by the resumed checks above. Proceed to implementation (G2) under the approved assembly plan.
