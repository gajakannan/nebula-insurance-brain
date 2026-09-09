# ADR-0054: Repository Layout, Runtime Roots, and Local Development Topology

## Status

- [ ] Proposed
- [x] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-06
**Amended:** 2026-09-08 by [ADR-0057](ADR-0057-nebula-owns-the-native-evidence-review-panel.md) — see Consequences
**Deciders:** Operator (layout, 2026-09-05), Architect (topology, F0001 Phase B)
**Source:** BLUEPRINT sections 2.2 to 2.4; master blueprint sections 77, 114.3; F0001 plan run `2026-09-06-cdb5d8cb`

## Context

The master blueprint's original section 77 used an `apps/` plus `packages/` monorepo. The nebula-agents framework that drives this product hardcodes three runtime roots (`engine/`, `experience/`, `neuron/`) in its role write scopes, path classes, symbol extraction roots, and knowledge-graph tooling. Section 114.3 also calls for a modular monolith of API, worker, and web over PostgreSQL, object storage, and Label Studio, with the package list treated as code boundaries rather than deployable services.

## Decision Drivers

- Zero framework changes to adopt the product; the CRM precedent uses the same roots.
- Keep the blueprint's package granularity as import-time boundaries.
- One tested dependency matrix, not generic compatibility claims (section 114.3).
- Separate GPU-bound inference from the Compose stack so model lifecycle does not couple to the API (the CRM's ADR-035 pattern).

## Decision

1. Runtime roots: `engine/` (FastAPI API under `apps/api`, worker under `apps/worker`, kernel packages under `packages/brain-*`, Alembic under `migrations/`), `neuron/` (AI runtime packages `brain-ingestion`, `brain-extraction`, `brain-interpretation`, later reasoning, conversation, learning, evolution, agent-tools), `experience/` (React, from F0021). Import packages use the `brain_` prefix.
2. One uv workspace per Python root with its own committed lockfile; `requires-python >= 3.13`.
3. Authored semantic assets stay top-level: `ontology/`, `profiles/`, `schemas/` (runtime), `knowledge-packs/`, `integrations/label-studio/`, `golden-corpus/`. Design-time shared JSON Schemas live in `planning-mds/schemas/`.
4. Local topology: Docker Compose runs PostgreSQL 18 (built with pgvector, Apache AGE, btree_gist), MinIO as the S3-compatible content store, Label Studio Community, and authentik; the vLLM inference service runs on the host GPU outside Compose (ADR-0055). The API and worker run from the uv workspaces during development and as containers in CI.
5. `docker/DEPENDENCY-MATRIX.md` pins every component with the source it was verified against; `latest` tags are rejected by CI.

ASCII companion of the container view (Mermaid in `planning-mds/architecture/c4-container.md`):

```text
 developer / CI                      host GPU
      │                                 │
      ▼                                 ▼
 ┌───────────────┐   ┌──────────────────────────────┐
 │ engine/api    │──▶│ vLLM (Phi-4-mini-instruct)   │◀── neuron/ adapters
 │ engine/worker │   │ OpenAI-compatible, :8000     │
 └──────┬────────┘   └──────────────────────────────┘
        │ SQLAlchemy / asyncpg            ▲
        ▼                                 │ chunk text only
 ┌────────────────────── docker compose ──┴──────────────────────┐
 │ postgres:18 (+vector,+age,+btree_gist)     minio        authentik      │
 └───────────────────────────────────────────────────────────────┘
```

## Options Considered

1. **Keep `apps/` and `packages/` as authored:** faithful to the original blueprint, but every framework tool needs per-product patching.
2. **Adopt `engine/experience/neuron` and nest packages (chosen):** framework works unchanged; package boundaries preserved.
3. **Flatten packages into one `engine` package:** simplest, but discards the blueprint's boundary design.

## Consequences

- **Amendment, 2026-09-08 (ADR-0057).** Decision points 3 and 4 change: the `integrations/label-studio/` asset tree is removed, and the Compose stack no longer runs a Label Studio service. `experience/` gains the Nebula Review Panel, which F0022 depends on, so the React root is no longer entirely deferred to F0021. `engine/packages/brain-review-labelstudio/` is dropped; `engine/packages/brain-review/` keeps the whole review boundary. The runtime roots, workspace rules, and dependency-matrix requirement are unchanged.
- Framework role ownership maps cleanly: backend-developer owns `engine/`, ai-engineer owns `neuron/`, frontend-developer owns `experience/`.
- Path-class extensions are required for `neuron/`, the asset trees, and lowercase security packages (registered at init).
- The inference service is a documented host prerequisite, not a container; CI runs S0003 against a recorded fixture when no GPU is present, and the live proof runs on the developer host.

## Security & Compliance Notes

- Secrets never live in the repository; `.env.example` documents variables and a gitignored secrets file supplies values.
- authentik binds to localhost in the default Compose configuration.

## References

- BLUEPRINT sections 2.2 to 2.4; master blueprint sections 77, 114.3
- CRM precedent: nebula-insurance-crm `docker-compose.yml`, ADR-035
- F0001 assembly plan Steps 1 and 2
