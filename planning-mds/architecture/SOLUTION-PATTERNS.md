# SOLUTION-PATTERNS.md — Nebula Insurance Brain

Project-level implementation conventions every role follows. Seeded by the Architect at F0001 Phase B from the master blueprint and the accepted ADRs; changes go through an ADR first.

## Metadata

- Project: Nebula Insurance Brain
- Version: 0.1
- Last Updated: 2026-09-06
- Owners: Architect (patterns), Security (pattern 1 co-sign)
- Scope: `engine/`, `neuron/`, `experience/` (from F0021), runtime assets, contracts under `planning-mds/`

## Pattern Categories

- `MUST` - mandatory convention for this solution
- `SHOULD` - recommended convention unless a documented exception exists
- `MAY` - optional convention based on feature needs

## Pattern Scope Labels

- `Universal` - technology-agnostic rule expected in any stack
- `Stack-Specific` - tied to a concrete framework/tool choice
- `Hybrid` - universal policy with stack-specific implementation details

---

## 1. Authorization Pattern

### Scope
- Label: `Hybrid`
- Stack context: authentik OIDC, native Casbin adapter in `brain_security`, PostgreSQL-backed principals and memberships

### Decision
- Policy model: verified `(issuer, subject)` → stable internal principal; structural tenancy (tenant, knowledge base) resolved from current grants; Casbin evaluates `(role, resource type, action, condition)` over server-hydrated typed attributes; authorization is the conjunction of membership, action, resource or parent scope, classification, and delegation limits.
- Enforcement point: every API route through `brain_api.deps.current_principal` plus `AuthorizationService.authorize`; commit services re-authorize; search, vector, and graph paths filter before rows, counts, facets, and snippets; MCP uses the same path.

### Rationale
- Master blueprint sections 66, 118 to 120; ADR-0030; proposed ADR-0049, ADR-0050, ADR-0053. The CRM gaps in section 119 are not copied.

### Applied In
- Backend: `brain_security` (verifier, resolver, adapter, audit); routes in `brain_api.routes.*`
- Frontend: renders what the API returns; never derives permissions client-side (F0021)
- AI layer: `neuron/` calls the engine as the acting principal; the model server receives no identity data

### Enforcement Level
- `MUST`

### Example

```text
p, TenantMember, content_artifact, read, r.obj.knowledge_base_id == r.sub.knowledge_base_id
p, Reviewer, review_task, annotate, r.obj.knowledge_base_id == r.sub.knowledge_base_id
p, ServicePrincipal, fact_slot, commit, r.obj.knowledge_base_id == r.sub.knowledge_base_id
```

Denials are reported as 404; reason codes live only in `audit_event`.

---

## 2. Audit and Timeline Pattern

### Scope
- Label: `Hybrid`
- Stack context: PostgreSQL append-only tables written inside the same transaction as the change

### Decision
- What gets logged: every authorization decision (policy hash, grant revision, actor and delegate, resource, action, decision, reason code, trace id); every canonical commit (commit id, fact versions, change reason, evidence); every review decision; every interpretation run.
- Event immutability policy: `audit_event`, `outbox_event`, `canonical_fact_change`, `review_event`, and `review_decision` are append-only; corrections create new rows linked to the originals (ADR-0037).

### Rationale
- Sections 17, 66, 109.3; ADR-0009, ADR-0010, ADR-0037; proposed ADR-0041.

### Applied In
- Data model: `audit_event`, `outbox_event`, `canonical_fact_change`, `review_event`
- Workflow engine: none in v0.1; Temporal (F0050) proposes state changes only through commit services (ADR-0028)

### Enforcement Level
- `MUST`

### Example

```json
{"actor_principal_id": "…", "resource_type": "fact_slot", "action": "commit", "decision": "allow", "policy_hash": "sha256:…", "grant_revision": 7, "trace_id": "…"}
```

---

## 3. API Design Pattern

### Scope
- Label: `Hybrid`
- Stack context: FastAPI, OpenAPI 3.1 contract in `planning-mds/api/brain-api.yaml`, JSON Schema 2020-12 in `planning-mds/schemas/`

### Decision
- API style: REST over root resource paths (`/content/{id}`, `/facts/{id}`, `/reviews/{id}`); no `/api` prefix; nouns only; versioning by OpenAPI `info.version` until a breaking change forces a path version.
- Error format: RFC 9457 `ProblemDetails` with a stable `code` and a `traceId` extension member (the one camelCase field, required by the framework API contract validator), media type `application/problem+json`.
- Pagination approach: cursor-based (`cursor`, `limit` up to 100) for list endpoints (none in F0001).
- Time coordinates: `validAsOf` and `knownAsOf` query parameters on canonical reads, defaulting to now.

### Rationale
- Section 68; ADR-0013; the framework API validator rejects `/api` prefixes and requires ProblemDetails on error responses.

### Applied In
- API contracts: `planning-mds/api/brain-api.yaml`
- Service endpoints: `brain_api.routes.*`

### Enforcement Level
- `MUST`

### Example

```http
GET /facts/8b2c…?validAsOf=2026-07-01T00:00:00Z&knownAsOf=2026-06-05T00:00:00Z
```

---

## 4. Clean Architecture Pattern

### Scope
- Label: `Hybrid`
- Stack context: Python packages under `engine/packages/` and `neuron/packages/`

### Decision
- Layer boundaries: `brain_domain` (frozen dataclasses, enums, invariants, no I/O) → application packages (`brain_security`, `brain_temporal`, `brain_review`, `brain_content` ports) → infrastructure adapters (`brain_persistence`, local filesystem content adapter) → `brain_api` and `brain_worker`.
- Dependency direction: inward only; adapters implement `Protocol` ports declared in application packages; `brain_api` wires them in `create_app()`.
- `neuron/` mirrors the split: `brain_interpretation` (models, ports) → `brain_ingestion` (bundle writer and durable publication callback) and `brain_extraction` (the upstream Graph pipeline adapter, compiled templates, and result/evidence translation). This is the ADR-0060 target; F0001 currently uses Docling plus a direct-vLLM adapter. Keep upstream graph IDs and output directories outside domain contracts.

### Rationale
- Master blueprint section 114.3 (package list as code boundaries); BLUEPRINT 2.3 boundary rules.

### Applied In
- `engine/`: as above
- `neuron/`: as above; writes to canonical truth only through engine commit services (section 64)

### Enforcement Level
- `MUST`

### Example

```text
brain_domain -> brain_temporal (port: CanonicalFactRepository) -> brain_persistence (SQLAlchemy) -> brain_api
```

---

## 5. Frontend Pattern

### Scope
- Label: `Stack-Specific`
- Stack context: React, TypeScript, Vite, TanStack Query, React Hook Form, AJV (BLUEPRINT 2.1)

### Decision
- Form strategy: React Hook Form with AJV validation against the shared JSON Schemas.
- Data-fetching strategy: TanStack Query over the OpenAPI contract; no client-side permission derivation.
- Validation strategy: the same JSON Schema files the backend validates against (ADR-0013).

### Rationale
- ADR-0013, ADR-0036; the semantic-first UX in section 72.

### Applied In
- `experience/`: from F0021; feature-slice folders `src/features/<feature>/`

### Enforcement Level
- `SHOULD` until F0021 lands, then `MUST`

### Example

```text
React Hook Form + AJV (draft 2020-12) + TanStack Query, semantic theme tokens only
```

---

## 6. Data Modeling Pattern

### Scope
- Label: `Hybrid`
- Stack context: PostgreSQL 18, SQLAlchemy 2, Alembic, range types with btree_gist

### Decision
- Entity identity strategy: UUID primary keys; external identifiers scoped by namespace and version (section 107.3); every authoritative row carries `tenant_id` and `knowledge_base_id` (ADR-0030).
- Soft delete policy: canonical facts are never deleted or soft-deleted; they end with a change reason (ADR-0009); governed retention and deletion arrive with F0026 (proposed ADR-0043).
- Temporal/audit fields: canonical fact and relationship versions carry `valid tstzrange` and `recorded tstzrange` with a two-range GiST exclusion; `source_received_at`, `artifact_created_at`, `assertion_created_at`, `canonical_accepted_at` are stored separately; all rows carry `created_at`.

### Rationale
- Sections 13 to 16, 78, 109.1, 109.2; ADR-0006 to ADR-0009.

### Applied In
- Entity model docs: `planning-mds/architecture/data-model.md`
- Migrations: `engine/migrations/versions/`

### Enforcement Level
- `MUST`

### Example

```sql
canonical_fact_version(id, slot_id, tenant_id, knowledge_base_id, value jsonb, valid tstzrange, recorded tstzrange, change_reason, commit_id,
  EXCLUDE USING gist (slot_id WITH =, valid WITH &&, recorded WITH &&))
```

---

## 7. Testing Pattern

### Scope
- Label: `Hybrid`
- Stack context: pytest with coverage for `engine/` and `neuron/`; Playwright for `experience/` (from F0021)

### Decision
- Unit/integration/e2e split: unit tests own domain invariants and pure logic; integration tests run against the Compose stack (database, object store, authentik); evaluation tests run against the Golden Corpus fixtures; contract tests validate JSON Schemas and the OpenAPI document.
- Coverage targets: 80% line coverage per workspace (framework evidence contract); severe-error rate and precision/recall reported with sample sizes (section 115.2).
- Test data policy: synthetic or licensed fixtures only; no production documents; fixture text never enters telemetry.

### Rationale
- Sections 96 to 98, 115; framework feature evidence contract.

### Applied In
- Test plans: per feature under the run's `test-plan.md`
- CI checks: `.github/workflows/ci-gates.yml` product-gates job

### Enforcement Level
- `MUST`

### Example

```text
Unit: brain_domain, range splitting, context guard
Integration: verifier, commit, review round trip, stack health
Evaluation: parse once and reinterpret on the GL fixture
```

---

## 8. Workflow Pattern

### Scope
- Label: `Universal`

### Decision
- State model: three separate state families, never conflated: canonical (accepted truth), observed (what a system reports), execution (Temporal from F0050); every state transition of canonical state is a canonical commit.
- Transition constraints: proposals pass authorization, validation, and evidence requirements before commit; review decisions and commits are append-only.
- Compensation/retry rules: PostgreSQL-backed jobs with idempotency keys, attempts, lease and heartbeat, and a transactional outbox; retries never create duplicate accepted effects (section 114.1).

### Rationale
- Sections 59 to 62, 109, 114.1; ADR-0028.

### Applied In
- Workflow specs: `planning-mds/kg-source/nodes/workflows/`
- Orchestration services: `brain_temporal.commit`, `brain_worker`

### Enforcement Level
- `MUST`

### Example

```text
Interpretation: received -> parsed -> (interpreted | partial | failed)
Review: open -> task_created -> (decided | stale)
Commit: proposed -> authorized -> committed -> projected
```

---

## 9. Cross-Cutting Pattern

### Scope
- Label: `Hybrid`
- Stack context: structlog-style JSON logs, OpenTelemetry-compatible trace ids, pydantic settings

### Decision
- Observability defaults: structured logs with `trace_id`, principal id, resource ids, model id, token counts, latency, and status; never full prompts, full model responses, fixture text, or PII (section 114.2).
- Error handling standard: typed `BrainError(code)` hierarchy mapped to ProblemDetails; no stack traces in responses.
- Configuration strategy: committed, non-secret local defaults live in `config/local.yaml`; the composition root loads that file without requiring storage environment variables. Deployment-specific overrides and secrets remain outside the repository and are introduced only where a future integration requires them.

### Rationale
- Sections 110.4, 114.2; ADR-0055 client conventions.

### Applied In
- All services and runtimes

### Enforcement Level
- `MUST`

### Example

```text
{"trace_id": "…", "principal_id": "…", "model_id": "microsoft/Phi-4-mini-instruct", "prompt_tokens": 2810, "latency_ms": 412, "status": "complete"}
```

---

## 10. DevOps Pattern

### Scope
- Label: `Stack-Specific`
- Stack context: Docker Compose, custom PostgreSQL image, host-GPU vLLM, GitHub Actions

### Decision
- Container strategy: Compose for the local stack with pinned tags or digests; the PostgreSQL image is built from `docker/postgres/Dockerfile`; the inference service runs on the host per the runbook (ADR-0054, ADR-0055).
- Environment promotion model: local Compose now; the production host is an open decision settled by F0026 (section 117.1).
- Secrets handling: never in the repository; committed local configuration contains no credentials. Future deployment integrations use platform secret management.

### Rationale
- Sections 114.3, 117.1; ADR-0054.

### Applied In
- Dockerfiles: `docker/postgres/Dockerfile`
- Compose: `docker-compose.yml`; runbook `docker/local-inference-runbook.md`

### Enforcement Level
- `MUST`

### Example

```text
docker compose up -d; scripts/dev/check_pins.py; backup and restore drill per scripts/ops/
```

---

## Pattern Update Process

1. Propose changes via ADR or architecture note.
2. Review impact across backend, AI runtime, frontend, test, and devops.
3. Update this file with rationale and enforcement level.
4. Communicate changes before implementation begins.

## Change Log

- 2026-09-06: Initial project-specific pattern set created at F0001 Phase B.
