# C4 Level 2 — Containers (F0001 topology)

Created 2026-09-06 (F0001 Phase B, ADR-0054). Updated by any feature that adds a service, changes inter-container communication, or introduces infrastructure.

```mermaid
C4Container
    title Nebula Insurance Brain — Containers (local development, F0001)
    Person(dev, "Developer / CI")
    Container_Boundary(compose, "docker compose") {
        ContainerDb(pg, "PostgreSQL 18", "pgvector, Apache AGE, btree_gist", "Authoritative store: principals, artifacts, assertions, fact slots, bitemporal versions, audit, outbox")
        Container(minio, "MinIO", "S3-compatible", "Content artifact bundles under tenant/knowledge-base/document/version")
        Container(ls, "Label Studio Community", "Python", "Task presentation and annotation workflow")
        Container(ak, "authentik", "OIDC", "Identity provider; two proof tenants")
    }
    Container(api, "engine/apps/api", "Python 3.13, FastAPI", "Verifies credentials, authorizes, serves /health, /content, /reviews, /facts; receives webhooks; commits facts")
    Container(worker, "engine/apps/worker", "Python 3.13", "Ingestion jobs; idempotent outbox projector")
    Container(neuron, "neuron/ packages", "Python 3.13, Docling, Docling-Graph", "Parse-once bundles; interpretation runs with context guard")
    Container_Ext(vllm, "vLLM", "host GPU, :8000", "microsoft/Phi-4-mini-instruct, 4,096-token context, bearer auth")
    Rel(dev, api, "HTTPS")
    Rel(api, pg, "SQLAlchemy / asyncpg")
    Rel(worker, pg, "SQLAlchemy / asyncpg")
    Rel(api, minio, "S3 API")
    Rel(neuron, minio, "S3 API (bundles)")
    Rel(neuron, pg, "runs, assertions")
    Rel(neuron, vllm, "chunk text only")
    Rel(api, ls, "create tasks (REST)")
    Rel(ls, api, "annotation webhooks (shared secret)")
    Rel(api, ak, "JWKS / discovery")
```

The API, worker, and `neuron/` packages form one modular monolith (section 114.3); the package list is a code boundary, not a deployment topology. The inference service is a host prerequisite documented in `docker/local-inference-runbook.md`.
