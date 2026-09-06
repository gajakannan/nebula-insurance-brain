# F0001 — Repository and engineering foundation — Getting Started

## Prerequisites

- [ ] Docker with Compose v2
- [ ] Python 3.13 and `uv`
- [ ] Node 20 and pnpm (only for the KG TypeScript symbol extractor; no frontend in this feature)
- [ ] A GL policy package for the proofs (native PDF plus a scanned variant); see the clarification decisions in `PRD.md`
- [ ] Framework session: `nebula-agents` checked out as a sibling with `NEBULA_PRODUCT_ROOT` exported

## Services to Run

```bash
docker compose up -d postgres objectstore labelstudio authentik   # S0002 stack
# inference service on the host GPU, per docker/local-inference-runbook.md (vLLM, microsoft/Phi-4-mini-instruct, :8000)
uv run --directory engine fastapi dev apps/api/src/brain_api/app.py   # API on :8080
uv run --directory engine python -m brain_worker.main                 # worker (ingestion + outbox projector)
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `BRAIN_DATABASE_URL` | PostgreSQL 18 connection | compose default |
| `BRAIN_OBJECT_STORE_ENDPOINT`, `_ACCESS_KEY`, `_SECRET_KEY`, `_BUCKET` | MinIO content store | compose defaults, bucket `content` |
| `BRAIN_LABELSTUDIO_URL`, `BRAIN_LABELSTUDIO_TOKEN_ENV`, `BRAIN_LABELSTUDIO_WEBHOOK_SECRET_ENV` | Label Studio Community API and webhook trust | names only; values from `~/.brain-secrets` |
| `BRAIN_OIDC_ISSUER`, `BRAIN_OIDC_AUDIENCE` | authentik verification | compose defaults |
| `BRAIN_INFERENCE_BASE_URL`, `BRAIN_INFERENCE_MODEL`, `BRAIN_INFERENCE_API_KEY_ENV`, `BRAIN_INFERENCE_CONTEXT_LIMIT` | vLLM endpoint, `microsoft/Phi-4-mini-instruct`, key name, `4096` | see runbook |
| `BRAIN_GRANT_CACHE_SECONDS` | Bound on revocation propagation | `30` |

## Seed Data

- Proof fixture: one GL policy package with a deliberately low-confidence limit extraction and one endorsement effective June 1, received June 12 (sections 86, 87)
- Two principals in two tenants for the access proof (section 115.4)

## How to Verify

1. `python3 scripts/run-lifecycle-gates.py` passes.
2. `uv run --directory engine pytest` and `uv run --directory neuron pytest` pass.
3. Each proof harness prints its measured results and the ADR records them (S0007).

## Key Files

| Layer | Path | Purpose |
|-------|------|---------|
| Backend | `engine/apps/api/src/brain_api/` | app factory, `/health`, deps, routes (content, reviews, facts) |
| Backend | `engine/packages/brain-{domain,persistence,content,security,temporal,review,review-labelstudio}/` | kernel packages per the assembly plan |
| AI runtime | `neuron/` | Docling and Docling-Graph adapters, proof harness for S0003 |
| Containers | `docker/`, `docker-compose.yml` | Dependency stack and pinned matrix |

## Notes

- Section 114.3: pin one exact combination of Python, PostgreSQL, AGE, pgvector, Docling, Docling-Graph, and Label Studio; do not rely on generic compatibility claims.
- Section 111.1: prove the Label Studio workflow with the selected edition before estimating anything that depends on it.
