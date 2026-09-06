## Story Header

**Story ID:** F0001-S0002
**Feature:** F0001 — Repository and engineering foundation
**Title:** Local runtime containers and dependency matrix
**Priority:** Critical
**Phase:** Infrastructure

## User Story

**As a** Dana the Platform Engineer
**I want** Docker Compose to start PostgreSQL with pgvector and Apache AGE, an S3-compatible object store for content artifacts, Label Studio, and authentik, plus the local vLLM inference service serving Phi-4-mini-instruct on the host GPU, all from one pinned dependency matrix
**So that** the four pre-build proofs run against the exact combination the pilot will deploy instead of generic compatibility claims

## Context & Background

Master blueprint section 114.3 requires a tested dependency matrix (exact Python build, Docling and Docling-Graph releases, PostgreSQL major and minor, AGE build, pgvector, Label Studio edition and version) and a modular-monolith topology of API, worker, web, PostgreSQL, object storage, and Label Studio. Section 111.1 requires proving the Label Studio workflow with the intended edition. This story delivers the stack and records the matrix.

## Acceptance Criteria

**Happy Path:**
- **Given** `docker compose up -d`
- **When** the services start
- **Then** every service reports healthy within 120 seconds and `CREATE EXTENSION vector` and `CREATE EXTENSION age` succeed on PostgreSQL 18

- **Given** the object store
- **When** the engine health check runs
- **Then** it writes and reads back a 1 KB object in the `content` bucket using the credentials from `.env.example`

- **Given** Label Studio
- **When** it starts
- **Then** the API answers `GET /api/version` with the pinned Community edition version and an API token can be created for the proof user

- **Given** authentik
- **When** it starts
- **Then** the OIDC discovery document is served and two test principals in two tenants exist from the seed script

- **Given** the local inference service started per `docker/local-inference-runbook.md` (adapted from the CRM's `neuron/neuron-local-phi-vllm-wsl2-runbook.md`)
- **When** `GET /v1/models` is called with the bearer key
- **Then** it lists `microsoft/Phi-4-mini-instruct` and the server reports a 4,096-token maximum model length

- **Given** `docker/DEPENDENCY-MATRIX.md`
- **When** reviewed
- **Then** it pins Python, PostgreSQL major and minor, AGE build, pgvector, Docling, Docling-Graph, Label Studio edition and version, authentik version, vLLM version, the model id `microsoft/Phi-4-mini-instruct` with its Hugging Face revision, and the context length, each with the source it was verified against

**Alternative Flows / Edge Cases:**
- AGE build fails on the chosen PostgreSQL major → the postgres image build fails with the extension name in the error; the matrix records the incompatibility and the fallback major
- Port already in use → compose fails naming the port; GETTING-STARTED lists the override variables
- `docker compose down -v` then `up -d` → the stack recreates from scratch with no manual steps

## Interaction Contract

N/A — infrastructure story; no user-facing mutation of business data.

## Data Requirements

**Required Fields:**
- `docker-compose.yml` with services `postgres`, `objectstore`, `labelstudio`, `authentik`
- `docker/local-inference-runbook.md`: vLLM OpenAI-compatible server on the host GPU (outside Compose, as in the CRM's ADR-035), `--max-model-len 4096`, bearer `--api-key`, secrets sourced from a gitignored file, never from the repo
- `docker/postgres/Dockerfile` building the pinned PostgreSQL with pgvector and AGE
- `.env.example` with every endpoint, port, bucket, and credential variable
- `docker/DEPENDENCY-MATRIX.md`

**Optional Fields:**
- `docker-compose.override.yml` (ignored by git) for local port overrides

**Validation Rules:**
- Every image reference pins a tag or digest; `latest` is rejected by a CI grep check
- Credentials in `.env.example` are development-only and documented as such

## Role-Based Visibility

**Roles that can execute:**
- Developer — local stack
- CI runner — ephemeral stack for integration tests

**Data Visibility:**
- InternalOnly content: none (fixture data only)
- ExternalVisible content: none

## Non-Functional Expectations

- Performance: cold start with cached images completes within 3 minutes on a developer machine and within 5 minutes on the CI runner
- Security: no production credentials; authentik and Label Studio bind to localhost by default
- Reliability: two consecutive `down -v` and `up -d` cycles reach healthy without intervention

## Dependencies

**Depends On:**
- F0001-S0001 — repository skeleton and CI job

**Related Stories:**
- F0001-S0003 to F0001-S0006 — every proof runs on this stack

## Business Rules

1. Pin one exact combination (master blueprint section 114.3); do not rely on generic compatibility claims. PostgreSQL 18 is not excluded by AGE, but the exact build must be tested.

## Out of Scope

- Production hosting, Kubernetes, managed database services (section 117.1 item 3 decides the host later)
- Temporal (F0050), Qdrant (F0061)

## UI/UX Notes

- N/A

## Questions & Assumptions

**Open Questions:**
- [x] PostgreSQL major version — decided at the F0001 clarification gate (2026-09-06): PostgreSQL 18; fall back to 17 only if the AGE build fails, and record the outcome in the dependency matrix
- [x] Label Studio edition — decided: Community, self-hosted; the proof records missing governed-review features for ADR-0044
- [x] Local model — decided at the F0001 clarification gate (2026-09-06), aligned with the CRM's validated profile (nebula-insurance-crm ADR-035): `microsoft/Phi-4-mini-instruct` served by vLLM 0.25.1 as an OpenAI-compatible service on the host GPU; not Mistral, not Ollama
- [ ] Object store — Architect to decide at Phase B; assumption below applies until then

**Assumptions (to be validated):**
- MinIO as the local S3-compatible store behind a storage interface (section 5 says the object store is replaceable; the artifact contract is not)
- authentik is included here because the access proof (S0006) needs verified identities from the same stack; the authentik version is pinned by the Architect in the dependency matrix

## Definition of Done

- [ ] Acceptance criteria met
- [ ] Edge cases handled
- [ ] Permissions enforced (N/A — infrastructure story)
- [ ] Audit/timeline logged (N/A — no business mutation)
- [ ] Tests pass (compose health checks and object round trip in CI)
- [ ] Documentation updated (GETTING-STARTED, dependency matrix)
- [ ] Story filename matches `Story ID` prefix
- [ ] Story index regenerated

## Review Provenance

Recorded in `STATUS.md` (Required Signoff Roles, Story Signoff Provenance).
