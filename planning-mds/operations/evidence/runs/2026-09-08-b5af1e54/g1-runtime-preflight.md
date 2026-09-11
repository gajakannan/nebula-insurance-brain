# G1 — Runtime Preflight — F0001 run 2026-09-08-b5af1e54

**Role:** DevOps
**runtime_bearing:** true (F0001 creates `engine/`, `neuron/`, `docker-compose.yml`, and runs an inference service; see `feature-assembly-plan.md` Steps 1–2)

## Host inventory

| Check | Command | Result |
|---|---|---|
| Docker | `docker ps` | v available; daemon healthy; 6 containers already running (see collision check below) |
| Docker Compose | `docker compose version` | v5.3.1 |
| uv | `uv --version` | 0.11.31 |
| Python | `python3 --version` | 3.14.4 (host default; `engine/`/`neuron/` pin 3.13+ per BLUEPRINT §2.1 inside their own uv-managed venvs, so this is not blocking) |
| GPU | `nvidia-smi` | NVIDIA GeForce RTX 5070, 12,227 MiB total, 11,943 MiB free, 0 compute processes running — sufficient headroom for `microsoft/Phi-4-mini-instruct` on vLLM per ADR-0055 |
| PostgreSQL 18 image | `docker images` | not yet pulled (only `postgres:16`, the CRM's tag); Step 2 must build the custom pgvector+AGE image per ADR-0054, not pull a stock tag |

## Port collision check (mandatory — a sibling product, `nebula-insurance-crm`, is running live containers on this host)

| Container (existing) | Host ports | Brain's planned service | Collision? |
|---|---|---|---|
| `nebula-authentik-server` | 9000, 9443 | `authentik` (own instance, own Postgres/Redis, per `feature-assembly-plan.md` line 139: "authentik ... its own PostgreSQL and Redis per the CRM pattern") | **YES** — Brain's compose file must not default to authentik's stock 9000/9443 host ports |
| `nebula-db` | 5433→5432 | `postgres` (F0001's own PostgreSQL 18, pgvector+AGE) | No — CRM already remapped off the 5432 default; Brain may use the 5432 default or its own remap without conflict today, but must not assume 5433 is free for its own db if it later runs alongside |
| `nebula-api` | 8080 | Brain API (port not yet pinned in the assembly plan/dependency matrix) | No current conflict; DevOps should pin a Brain API host port distinct from 8080/8200/8082 (e.g. 8100) in the Step 2 compose file to avoid future collision |
| `nebula-neuron` | 8200 | none directly (Brain's vLLM/inference runs outside Compose on the host GPU per ADR-0055, no fixed port claimed yet) | No current conflict; DevOps should pin the vLLM host port (e.g. 8001) distinct from 8200 in the local-inference runbook |
| `nebula-temporal`, `nebula-temporal-ui` | 7233, 8082 | none (Temporal not in F0001 scope) | No |

**Finding (non-blocking, actionable at Step 2):** the authentik host-port collision is real and must be resolved by DevOps when authoring `docker-compose.yml` in Step 2 — remap Brain's authentik to non-default host ports (e.g. `9010:9000`, `9444:9443`) rather than reusing 9000/9443. This does not block G1: it is an implementation instruction for the DevOps role in Step 2, recorded here so it isn't rediscovered as a runtime-blocked failure during preflight-and-triage.

## Runtime Preflight & Failure Triage

No application runtime containers exist yet for F0001 (Step 2 has not run) — there is nothing to health-check beyond the host capability inventory above. This preflight will be re-run per the "Runtime Preflight & Failure Triage (Mandatory)" procedure in `agents/actions/feature.md` before every compile/test/lint/security command once Step 2 stands up the Brain's own `docker compose` stack.

## Outcome

**PASS.** Host has Docker, Compose, uv, and a free GPU with adequate memory for the pinned inference profile. One actionable, non-blocking finding recorded: authentik host-port remap required in Step 2 to coexist with the already-running `nebula-insurance-crm` stack on this host.
