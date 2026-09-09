# Feature Assembly Plan — F0001: Repository and Engineering Foundation

**Created:** 2026-09-06
**Author:** Architect Agent
**Status:** Draft (Phase B, plan run `2026-09-06-cdb5d8cb`)
**Feature type:** infrastructure plus four proof harnesses; the template's entity/endpoint sections are adapted accordingly

## Overview

F0001 creates the `engine/` and `neuron/` runtime roots, the local dependency stack, and four proof harnesses whose measured results settle the Proposed ADRs the v0.1 kernel depends on. Nothing exists in the runtime roots today, so there is no existing code to modify; every path below is new. The proofs are deliberately narrow: one GL package, one FactSlot, one review task, two principals. They are not the production services (F0004, F0005, F0018, F0022 build those) but they establish the package boundaries, the contracts, and the test harness those features extend.

## Governing Decisions

- Runtime roots and topology: `engine/` (API, worker, kernel packages), `neuron/` (AI runtime), `experience/` (proof-scope Review Panel here; the full shell is F0021); one uv workspace per Python root; modular monolith of API plus worker over PostgreSQL 18, MinIO, authentik, and a host-GPU vLLM service (ADR-0054 as amended by ADR-0057, BLUEPRINT 2.3).
- Local inference profile: `microsoft/Phi-4-mini-instruct` on vLLM as an OpenAI-compatible service with a 4,096-token context and bearer auth, outside Compose, aligned with the CRM's ADR-035; context enforced client-side; no PII or tokens to the model server (ADR-0055).
- Parse once with a lossless bundle including `docling-document.json`; evidence precision declared per binding; failed pages are partial, never negative (ADR-0003, ADR-0004, proposed ADR-0040 settled by S0003).
- Two-range bitemporal commit with a multi-column GiST exclusion constraint, facts plus audit plus outbox in one transaction, idempotent projector (ADR-0007, ADR-0008, ADR-0009, proposed ADR-0041 settled by S0005).
- Nebula owns the review surface as well as ReviewItem, ReviewDecision, lineage, and audit; adjudication is not approval; unresolved evidence blocks a decision rather than misplacing it (ADR-0057, ADR-0037, proposed ADR-0044 and ADR-0058 settled by S0004).
- Credentials verified before any storage read; verified `(issuer, subject)` maps to a stable internal principal; native Casbin adapter with typed resource attributes; every decision audited with policy hash and grant revision (proposed ADR-0049 and ADR-0050 settled by S0006).
- Python packages use the `brain_` import prefix; distribution directories keep `brain-*` names (BLUEPRINT 2.2). Pydantic v2 models are the wire and manifest contracts; SQLAlchemy 2 models are persistence only.
- AI scope: yes. S0003 runs an LLM through Docling-Graph; the ai-engineer owns `neuron/`.
- Frontend scope: none.

## Build Order

| Step | Scope | Stories | Rationale |
|------|-------|---------|-----------|
| 1 | Runtime roots, workspaces, API skeleton, health endpoint, CI | S0001 | Everything else needs a place to live and a gate to pass |
| 2 | Compose stack, PostgreSQL 18 image with pgvector and AGE, MinIO, authentik, inference runbook, dependency matrix | S0002 | Every proof runs on this stack |
| 3 | Identity and authorization core: credential verifier, principal resolver, Casbin adapter, authorization audit, protected resource reads | S0006 (access part) | S0004 needs verified reviewer principals; S0005 needs an authorized actor |
| 4 | Content artifact bundle, Docling adapter, Docling-Graph adapter, interpretation runs, counters | S0003 | Produces the assertion S0004 reviews and the evidence S0006 restores |
| 5 | FactSlot, canonical fact versions, commit service, outbox, projector stub | S0005 | Independent of review; needed before the restore drill |
| 6 | ReviewItem, review batch, Review Panel with its renderers and anchor resolution, ReviewDecision with lineage | S0004 | Consumes S0003's assertion and evidence locators, and S0006's principals |
| 7 | Backup and restore drill, revocation propagation measurement, DAST run | S0006 (hosting part) | Needs S0003 to S0005 data in place |
| 8 | Record outcomes, settle ADRs, complete the dependency matrix | S0007 | Closes the feature |

## Existing Code (Must Be Modified)

None. `engine/`, `neuron/`, `docker/`, and `docker-compose.yml` do not exist. `planning-mds/` artifacts modified by this plan are listed in the run's `artifact-trace.md`.

## New Files

| File | Layer | Purpose |
|------|-------|---------|
| `engine/pyproject.toml`, `engine/uv.lock` | Backend workspace | uv workspace root: members `apps/api`, `apps/worker`, `packages/*` |
| `engine/apps/api/pyproject.toml`, `engine/apps/api/src/brain_api/{__init__,app,health,deps,errors}.py` | API | FastAPI app factory, `/health`, dependency wiring, ProblemDetails handler |
| `engine/apps/worker/src/brain_worker/{__init__,main,outbox_projector}.py` | Worker | Ingestion job runner (Step 4) and idempotent outbox projector stub (Step 5) |
| `engine/packages/brain-domain/src/brain_domain/{principal,content,assertion,review,facts,audit,errors}.py` | Domain | Frozen dataclasses and enums shared by every package; no I/O |
| `engine/packages/brain-persistence/src/brain_persistence/{base,models,session,repositories}.py`, `engine/migrations/` | Infrastructure | SQLAlchemy 2 async models, Alembic environment, migrations 0001 to 0004 |
| `engine/packages/brain-content/src/brain_content/{manifest,store,object_store}.py` | Infrastructure | Artifact manifest model, `ContentArtifactStore` port, MinIO adapter |
| `engine/packages/brain-security/src/brain_security/{verification,principals,authorization,audit,casbin_adapter}.py` | Application | Credential verifier, principal resolver, Casbin adapter, decision audit |
| `engine/packages/brain-temporal/src/brain_temporal/{commit,ranges,outbox}.py` | Application | Bitemporal commit algorithm, range helpers, outbox writer |
| `engine/packages/brain-review/src/brain_review/{items,batches,decisions}.py` | Application | ReviewItem routing, review batch assembly, ReviewDecision persistence and idempotency |
| `experience/src/review-panel/**` | Frontend | Review Panel: renderers (pdf.js, fflate, `TextDecoder`), anchor resolution, decision batch submission |
| `engine/tests/{unit,integration,security,contract}/` | Tests | pytest suites per step |
| `neuron/pyproject.toml`, `neuron/uv.lock` | AI workspace | uv workspace root: members `packages/*` |
| `neuron/packages/brain-ingestion/src/brain_ingestion/{docling_adapter,bundle_writer}.py` | AI | Parse once: Docling conversion, bundle assembly, manifest hashing |
| `neuron/packages/brain-extraction/src/brain_extraction/{profiles,docling_graph_adapter,context_guard}.py` | AI | Extraction profiles, Docling-Graph OpenAI-compatible backend, context enforcement |
| `neuron/packages/brain-interpretation/src/brain_interpretation/{result,runs,counters}.py` | AI | InterpretationResult model, run recording, conversion and OCR counters |
| `neuron/tests/{unit,integration,evaluation}/` | Tests | pytest suites for Step 4 |
| `docker-compose.yml`, `docker/postgres/Dockerfile`, `docker/postgres/init/*.sql`, `docker/authentik/`, `.env.example` | Runtime | Dependency stack (Step 2) |
| `docker/DEPENDENCY-MATRIX.md`, `docker/local-inference-runbook.md` | Runtime docs | Pinned matrix; vLLM runbook adapted from the CRM |
| `planning-mds/api/brain-api.yaml` | Contract | OpenAPI 3.1 for `/health`, protected reads, review decisions, commit (authored in this plan run) |
| `planning-mds/schemas/*.schema.json` | Contract | Manifest, interpretation result, review decision, commit request and response, problem details (authored in this plan run) |
| `planning-mds/security/policies/{model.conf,policy.csv}` | Authorization | Casbin model and proof policy (authored in this plan run) |

---

## Step 1 — Runtime roots and toolchain skeleton (S0001)

### New Files

| File | Layer |
|------|-------|
| `engine/pyproject.toml` | workspace (`[tool.uv.workspace] members = ["apps/*", "packages/*"]`, `requires-python = ">=3.13"`) |
| `engine/apps/api/src/brain_api/app.py` | API |
| `engine/apps/api/src/brain_api/health.py` | API |
| `engine/apps/api/src/brain_api/errors.py` | API |
| `engine/ruff.toml`, `engine/mypy.ini`, `neuron/ruff.toml`, `neuron/mypy.ini` | tooling |
| `.github/workflows/ci-gates.yml` | CI (extend the existing product-gates job) |

### Code

```python
# engine/apps/api/src/brain_api/app.py
from fastapi import FastAPI
from brain_api.errors import install_problem_details_handlers
from brain_api.health import router as health_router

def create_app(*, settings: "Settings | None" = None) -> FastAPI:
    app = FastAPI(title="Nebula Insurance Brain API", version="0.1.0", openapi_url="/openapi.json")
    install_problem_details_handlers(app)
    app.include_router(health_router)
    return app
```

```python
# engine/apps/api/src/brain_api/health.py
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str                      # "ok"
    git_sha: str                     # injected at build time via BRAIN_GIT_SHA
    versions: dict[str, str]         # {"fastapi": ..., "sqlalchemy": ..., "docling": ...}

@router.get("/health", response_model=HealthResponse, operation_id="getHealth")
async def get_health() -> HealthResponse: ...
```

```python
# engine/apps/api/src/brain_api/errors.py
class ProblemDetails(BaseModel):
    type: str; title: str; status: int; detail: str | None = None
    instance: str | None = None; code: str; traceId: str   # camelCase extension member per the framework API validator
```

### Logic Flow

`create_app()` → registers handlers that map `BrainError(code)` subclasses and validation errors to `ProblemDetails` with `application/problem+json`; `/health` performs no I/O.

### HTTP Responses

| Status | Body | Condition |
|--------|------|-----------|
| 200 | `HealthResponse` | Always, no credentials required |

### Mutation Traceability

N/A — read-only.

---

## Step 2 — Local runtime containers and dependency matrix (S0002)

### New Files

| File | Change |
|------|--------|
| `docker-compose.yml` | services `postgres` (built from `docker/postgres/Dockerfile`: PostgreSQL 18 base, `pgvector`, `age` compiled and `CREATE EXTENSION` in init SQL, `btree_gist`), `objectstore` (MinIO, bucket `content` created by an init job), `authentik` (server, worker, its own PostgreSQL and Redis per the CRM pattern), healthchecks on all |
| `docker/local-inference-runbook.md` | vLLM on the host GPU: Python 3.12 venv, `vllm` pinned, `--model microsoft/Phi-4-mini-instruct --dtype auto --max-model-len 4096 --gpu-memory-utilization 0.90 --port 8000 --api-key $BRAIN_INFERENCE_API_KEY`; WSL2 flags `VLLM_WSL2_ENABLE_PIN_MEMORY=1`, `VLLM_USE_FLASHINFER_SAMPLER=0`; secrets from `~/.brain-secrets` (0600) |
| `docker/DEPENDENCY-MATRIX.md` | Python, PostgreSQL 18.x, AGE build, pgvector, btree_gist, Docling, Docling-Graph, Node and the `experience/` toolchain, `pdf.js`, `fflate`, authentik, MinIO, vLLM, model id and Hugging Face revision, context length; each row cites its verification source |
| `.env.example` | `BRAIN_DATABASE_URL`, `BRAIN_OBJECT_STORE_ENDPOINT`, `BRAIN_OBJECT_STORE_ACCESS_KEY`, `BRAIN_OBJECT_STORE_SECRET_KEY`, `BRAIN_OBJECT_STORE_BUCKET`, `BRAIN_OIDC_ISSUER`, `BRAIN_OIDC_AUDIENCE`, `BRAIN_INFERENCE_BASE_URL`, `BRAIN_INFERENCE_MODEL`, `BRAIN_INFERENCE_API_KEY_ENV`, `BRAIN_INFERENCE_CONTEXT_LIMIT=4096` |

### Logic Flow

`docker compose up -d` → postgres init runs `CREATE EXTENSION IF NOT EXISTS vector; ... age; ... btree_gist;` → MinIO init job creates `content` → authentik healthy → `scripts/dev/seed_principals.py` provisions two tenants, two users, one service client in authentik (Step 3 consumes them).

### Edge cases resolved here

- AGE build failure on 18 → the Dockerfile build fails naming the extension; the matrix records the failure and the 17 fallback; no silent downgrade.
- `latest` tags → `scripts/dev/check_pins.py` fails CI when any compose image lacks a pinned tag or digest.

---

## Step 3 — Identity and authorization core (S0006, access part)

### New Files

| File | Layer |
|------|-------|
| `engine/packages/brain-domain/src/brain_domain/principal.py` | Domain |
| `engine/packages/brain-security/src/brain_security/verification.py` | Application |
| `engine/packages/brain-security/src/brain_security/principals.py` | Application |
| `engine/packages/brain-security/src/brain_security/authorization.py` | Application |
| `engine/packages/brain-security/src/brain_security/casbin_adapter.py` | Infrastructure |
| `engine/packages/brain-security/src/brain_security/audit.py` | Application |
| `engine/migrations/versions/0001_principals_and_audit.py` | Infrastructure |
| `engine/apps/api/src/brain_api/deps.py` | API (bearer extraction → verify → resolve → request principal) |
| `engine/apps/api/src/brain_api/routes/{content,reviews,facts}.py` | API (protected reads used by the proof) |

### Code

```python
# brain_domain/principal.py
class PrincipalKind(StrEnum): USER = "user"; SERVICE = "service"; AGENT = "agent"
class PrincipalStatus(StrEnum): ACTIVE = "active"; DISABLED = "disabled"

@dataclass(frozen=True, slots=True)
class Principal:
    id: UUID; kind: PrincipalKind; issuer: str; subject: str; status: PrincipalStatus

@dataclass(frozen=True, slots=True)
class Membership:
    principal_id: UUID; tenant_id: UUID; knowledge_base_id: UUID; role: str; grant_revision: int; revoked_at: datetime | None
```

```python
# brain_security/verification.py
@dataclass(frozen=True, slots=True)
class VerifiedCredential:
    issuer: str; subject: str; audience: str; expires_at: datetime; not_before: datetime | None; key_id: str

class CredentialError(BrainError):      # code in {"invalid_signature","wrong_issuer","wrong_audience","expired","not_yet_valid","malformed","disabled_principal"}
    ...

class CredentialVerifier(Protocol):
    async def verify(self, bearer_token: str) -> VerifiedCredential: ...

class OidcJwksVerifier(CredentialVerifier):
    def __init__(self, issuer: str, audience: str, jwks_cache: JwksCache) -> None: ...
```

```python
# brain_security/principals.py
class PrincipalResolver:
    async def resolve(self, credential: VerifiedCredential) -> Principal:  # (issuer, subject) → stable id; creates on first sight; raises CredentialError("disabled_principal")
    async def memberships(self, principal: Principal) -> tuple[Membership, ...]:  # current grants only; revoked rows excluded
```

```python
# brain_security/authorization.py
@dataclass(frozen=True, slots=True)
class ResourceRef:
    type: str                 # "content_artifact" | "review_task" | "fact_slot"
    id: UUID; tenant_id: UUID; knowledge_base_id: UUID; classification: str = "internal"

@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool; reason_code: str; policy_hash: str; grant_revision: int; trace_id: str

class AuthorizationService:
    async def authorize(self, principal: Principal, resource: ResourceRef, action: str, *, trace_id: str) -> Decision:
        # 1 memberships → 2 structural tenancy conjunction → 3 Casbin evaluate(role, resource type, action, attrs) → 4 audit → 5 return
```

### Logic Flow

`request → deps.current_principal()`:
1. Extract bearer; missing or malformed → 401 `malformed` (no storage touched).
2. `CredentialVerifier.verify` → issuer, audience, signature, `exp`, `nbf` checked against the cached JWKS; failure → 401 with the reason code in the audit event only.
3. `PrincipalResolver.resolve` → stable principal; disabled → 401 `disabled_principal`.
4. Route handler builds `ResourceRef` from the row's tenant and knowledge base (server-hydrated, never from the client), calls `authorize`.
5. Denied → 404 `not_found` (existence not disclosed); audit event carries `reason_code`.
6. Allowed → the read proceeds with the query already scoped by `knowledge_base_id`.

### Casbin Enforcement

- Model: `planning-mds/security/policies/model.conf` (request `sub, obj, act`; policy `role, resource, action, cond`; matcher on role, resource type, action, and `eval(cond)`).
- Policy rows: `planning-mds/security/policies/policy.csv` — `TenantMember` reads `content_artifact`, `review_task`, `fact_slot` when `r.obj.knowledge_base_id == r.sub.knowledge_base_id`; `Reviewer` annotates `review_task` under the same condition; `ServicePrincipal` commits `fact_slot` under the same condition.
- Hydrated attributes: `sub.role`, `sub.knowledge_base_id` (from the membership matched to the resource's tenant), `obj.type`, `obj.knowledge_base_id`, `obj.classification`.
- `policy_hash` = sha256 of the loaded `policy.csv` bytes, recorded on every decision.

### Audit Event

- `audit_event(id, occurred_at, actor_principal_id, delegate_principal_id, resource_type, resource_id, action, decision, reason_code, policy_hash, grant_revision, trace_id)`; append-only table; written in the same transaction as the read's request log.

### HTTP Responses

| Status | Body | Condition |
|--------|------|-----------|
| 200 | resource DTO | Allowed |
| 401 | ProblemDetails (`unauthenticated`) | Verification failed; reason code only in audit |
| 404 | ProblemDetails (`not_found`) | Denied or absent; indistinguishable to the caller |

### Mutation Traceability

N/A — read-only endpoints; the audit event is a system record, not a user mutation.

---

## Step 4 — Parse once, reinterpret twice, evidence resolves (S0003)

### New Files

| File | Layer |
|------|-------|
| `engine/packages/brain-content/src/brain_content/manifest.py` | Contract (pydantic) |
| `engine/packages/brain-content/src/brain_content/store.py`, `object_store.py` | Port and MinIO adapter |
| `engine/migrations/versions/0002_content_and_interpretation.py` | `source_document`, `document_version`, `content_artifact`, `semantic_interpretation_run`, `assertion`, `assertion_evidence` |
| `neuron/packages/brain-ingestion/src/brain_ingestion/docling_adapter.py`, `bundle_writer.py` | AI |
| `neuron/packages/brain-extraction/src/brain_extraction/profiles.py`, `docling_graph_adapter.py`, `context_guard.py` | AI |
| `neuron/packages/brain-interpretation/src/brain_interpretation/result.py`, `runs.py`, `counters.py` | AI |
| `profiles/extraction/gl-limits-a.yaml`, `profiles/extraction/gl-limits-b.yaml` | Profiles (two hand-selected profiles for the proof) |
| `neuron/tests/integration/test_parse_once_reinterpret.py` | Tests |

### Code

```python
# brain_content/manifest.py — matches planning-mds/schemas/content-artifact-manifest.schema.json
class ArtifactFile(BaseModel): path: str; sha256: str; size_bytes: int
class DoclingDocumentRef(BaseModel): path: str; schema_version: str; sha256: str
class ExecutionRecord(BaseModel): parser_package_version: str; model_artifact_digests: list[str]; configuration_hash: str; environment_digest: str
class ExtractionQuality(BaseModel): status: Literal["complete", "partial", "failed"]; failed_pages: list[int]; warnings: list[str]
class ArtifactManifest(BaseModel):
    artifact_contract_version: Literal[1]
    tenant_id: UUID; knowledge_base_id: UUID; document_id: UUID; version_id: UUID; artifact_id: UUID
    source_sha256: str; artifact_sha256: str
    docling_document: DoclingDocumentRef; files: list[ArtifactFile]
    execution: ExecutionRecord; extraction_quality: ExtractionQuality
    page_count: int; coordinate_origin: Literal["top_left"]; offset_encoding: Literal["unicode_code_points"]
    created_at: datetime
```

```python
# brain_content/store.py
class ContentArtifactStore(Protocol):
    async def put_bundle(self, manifest: ArtifactManifest, files: Mapping[str, bytes]) -> ArtifactManifest: ...   # immutable; second put of the same artifact_id raises ArtifactExists
    async def get_manifest(self, artifact_id: UUID) -> ArtifactManifest: ...
    async def open_file(self, artifact_id: UUID, path: str) -> bytes: ...
```

```python
# brain_interpretation/result.py — matches planning-mds/schemas/interpretation-result.schema.json
Precision = Literal["span", "table_cell", "block", "page", "document", "unresolved"]
class BoundingBox(BaseModel): page: int; x0: float; y0: float; x1: float; y1: float
class EvidenceBinding(BaseModel): artifact_id: UUID; block_id: str | None; page: int | None; bbox: BoundingBox | None; char_start: int | None; char_end: int | None; precision: Precision
class CandidateAssertion(BaseModel): id: UUID; subject_type: str; slot_type: str; value: dict; evidence: list[EvidenceBinding]; model_confidence: float | None; interpretation_basis: Literal["EXPLICIT", "INFERRED", "AMBIGUOUS"]
class RunConfiguration(BaseModel): backend: Literal["openai_compatible"]; model_id: str; model_revision: str | None; endpoint_hash: str; prompt_hash: str; schema_hash: str; context_limit: int; profile_id: str; profile_version: str
class Counters(BaseModel): conversion_calls: int; ocr_calls: int; model_calls: int; prompt_tokens: int; completion_tokens: int
class InterpretationResult(BaseModel):
    run_id: UUID; artifact_id: UUID; status: Literal["complete", "partial", "failed"]
    entities: list[CandidateEntity]; assertions: list[CandidateAssertion]; relationships: list[CandidateRelationship]
    quality_signals: dict[str, float]; warnings: list[str]; failed_chunks: list[str]
    run_configuration: RunConfiguration; counters: Counters; provenance_ledger_ref: str | None; created_at: datetime
```

```python
# brain_extraction/context_guard.py
class ContextLimitExceeded(BrainError): code = "context_limit_exceeded"
class ContextGuard:
    def __init__(self, limit: int, reserve_for_output: int = 512) -> None: ...
    def check(self, prompt_tokens: int) -> None:   # raises before the call; never truncates
```

### Logic Flow

`ingest(document_bytes)`:
1. `sha256(source)`; if a `document_version` with this hash exists for the tenant and knowledge base, return the accepted artifact (no reparse; counter unchanged).
2. Docling converts once; `counters.conversion_calls += 1`, `ocr_calls += pages_ocr`.
3. `bundle_writer` writes `docling-document.json`, `normalized.md`, `blocks.jsonl`, `tables.jsonl`, `layout.jsonl`, `manifest.json`; per-file sha256; manifest `artifact_sha256` over the sorted file hashes.
4. `ContentArtifactStore.put_bundle` (immutable). Failed pages → `extraction_quality.status = partial`, `failed_pages` listed; the run is still persisted.

`interpret(artifact_id, profile)`:
1. Load manifest and `docling-document.json` only; assert `conversion_calls == 0` for this run.
2. Chunk per profile; `ContextGuard.check` each chunk; exceeded → record `failed_chunks`, status `partial`, continue.
3. Docling-Graph via the OpenAI-compatible backend at `BRAIN_INFERENCE_BASE_URL` with `BRAIN_INFERENCE_MODEL`; schema-validate each chunk result; invalid → `failed_chunks`, no assertion emitted.
4. Map external grounding to `EvidenceBinding` with declared precision; store the external provenance ledger with the run.
5. Persist `semantic_interpretation_run` and `assertion` rows; never delete or overwrite a prior run.

### Mutation Traceability

N/A — harness-driven; no user-facing mutation. Runs and assertions are append-only records.

---

## Step 5 — Bitemporal commit under retroactive and concurrent change (S0005)

### New Files

| File | Layer |
|------|-------|
| `engine/packages/brain-domain/src/brain_domain/facts.py` | Domain |
| `engine/packages/brain-temporal/src/brain_temporal/commit.py`, `ranges.py`, `outbox.py` | Application |
| `engine/migrations/versions/0003_fact_slots_and_commits.py` | `fact_slot`, `canonical_fact_version`, `canonical_fact_change`, `outbox_event` |
| `engine/apps/worker/src/brain_worker/outbox_projector.py` | Worker (records processed events; no graph or vector yet) |
| `engine/apps/api/src/brain_api/routes/facts.py` | API (`GET /facts/{factSlotId}`, `POST /facts/{factSlotId}/commits`) |
| `engine/tests/integration/test_bitemporal_commit.py`, `test_commit_concurrency.py`, `test_outbox_replay.py` | Tests |

### Code

```python
# brain_domain/facts.py
class ChangeReason(StrEnum): SUPERSEDED = "superseded"; CORRECTED = "corrected"; RETRACTED = "retracted"; EXPIRED = "expired"; INVALIDATED = "invalidated"; MERGED = "merged"; SPLIT = "split"

@dataclass(frozen=True, slots=True)
class CommitProposal:
    slot_id: UUID; value: Mapping[str, Any]; valid_from: datetime; valid_to: datetime | None
    change_reason: ChangeReason | None; evidence_refs: tuple[UUID, ...]; review_decision_id: UUID | None
    source_received_at: datetime; artifact_created_at: datetime; assertion_created_at: datetime
    expected_current_version_id: UUID | None; idempotency_key: str

@dataclass(frozen=True, slots=True)
class CommitResult:
    commit_id: UUID; fact_version_ids: tuple[UUID, ...]; canonical_accepted_at: datetime
```

```python
# brain_temporal/commit.py
class CanonicalCommitService:
    async def commit(self, actor: Principal, proposal: CommitProposal, *, trace_id: str) -> CommitResult:
        # steps 1-7 of master blueprint section 109.2, one transaction
```

```sql
-- migration 0003 (excerpt)
CREATE TABLE canonical_fact_version (
  id uuid PRIMARY KEY, slot_id uuid NOT NULL REFERENCES fact_slot(id),
  tenant_id uuid NOT NULL, knowledge_base_id uuid NOT NULL,
  value jsonb NOT NULL, valid tstzrange NOT NULL, recorded tstzrange NOT NULL,
  change_reason text, evidence jsonb NOT NULL, review_decision_id uuid, commit_id uuid NOT NULL,
  source_received_at timestamptz NOT NULL, artifact_created_at timestamptz NOT NULL,
  assertion_created_at timestamptz NOT NULL, canonical_accepted_at timestamptz NOT NULL,
  CHECK (NOT isempty(valid) AND NOT isempty(recorded)),
  EXCLUDE USING gist (slot_id WITH =, valid WITH &&, recorded WITH &&)
);
```

### Logic Flow

`commit(actor, proposal)`:
1. `authorize(actor, ResourceRef("fact_slot", ...), "commit")`; denied → 404 as above.
2. `SELECT ... FOR UPDATE` the slot; if `expected_current_version_id` is set and differs → 409 `stale_version`.
3. Validate ranges non-empty and non-null; `valid_to` may be null (open); `recorded` starts at `now()` = `canonical_accepted_at`.
4. For each current version overlapping the new valid range: close its `recorded` upper bound at `now()`; insert the split remainders (before and after) as new versions carrying the old value and `change_reason = split`; insert the new version.
5. Insert `canonical_fact_change(reason, from_version, to_version)`, `audit_event`, `outbox_event(commit_id, payload)`.
6. `COMMIT`; a concurrent transaction on the same slot serializes on the row lock and then fails the exclusion constraint if still overlapping → 409 `concurrent_commit`.
7. Return `CommitResult`.

`GET /facts/{factSlotId}?validAsOf=&knownAsOf=` → single version where `valid @> validAsOf AND recorded @> knownAsOf`; defaults now and now.

### Mutation Traceability

| Screen / Entry Point | User Action | Endpoint | Service Method | Entity / Carrier | Authorization | Concurrency | Validation Failure | Audit / Timeline | Test Expectation |
|----------------------|-------------|----------|----------------|------------------|---------------|-------------|--------------------|------------------|------------------|
| Proof harness (service principal) | commit endorsement, then correction | `POST /facts/{factSlotId}/commits` | `CanonicalCommitService.commit` | `canonical_fact_version` | `fact_slot:commit` | `expected_current_version_id` plus GiST exclusion | 400 `invalid_range`, 409 `stale_version` or `concurrent_commit` | `audit_event` + `outbox_event` in the commit transaction | `test_bitemporal_commit.py` answers the section 87 matrix after reload; `test_commit_concurrency.py` leaves one winner |

### HTTP Responses

| Status | Body | Condition |
|--------|------|-----------|
| 201 | `CanonicalCommitResponse` | Committed |
| 200 | `FactVersion` | `GET` resolved at both coordinates |
| 400 | ProblemDetails (`invalid_range`) | Empty or null range |
| 401 / 404 | ProblemDetails | As in Step 3 |
| 409 | ProblemDetails (`stale_version` or `concurrent_commit`) | Optimistic check or exclusion constraint |

---

## Step 6 — Native review round trip (S0004)

### New Files

| File | Layer |
|------|-------|
| `engine/packages/brain-domain/src/brain_domain/review.py` | Domain |
| `engine/packages/brain-review/src/brain_review/items.py`, `batches.py`, `decisions.py` | Application |
| `engine/migrations/versions/0004_review.py` | `review_item`, `review_batch`, `review_event`, `review_decision` |
| `engine/apps/api/src/brain_api/routes/reviews.py` | API (`GET /reviews/{reviewItemId}`, `POST /reviews/batches/{reviewBatchId}/decisions`) |
| `experience/src/review-panel/{Panel,ArtifactRail,FieldList}.tsx` | Frontend shell (ADR-0057) |
| `experience/src/review-panel/renderers/{pdf,ooxml,text}.ts` | Frontend renderers: pdf.js, fflate over the OOXML parts, `TextDecoder` |
| `experience/src/review-panel/anchors/{resolve,selectors}.ts` | Frontend anchor resolution against the stored locator (ADR-0058) |
| `engine/tests/integration/test_review_round_trip.py`, `engine/tests/security/test_review_authority.py`, `experience/tests/review-panel/anchors.spec.ts` | Tests |

### Code

```python
# brain_domain/review.py
class ReviewItemType(StrEnum): LOW_CONFIDENCE_ASSERTION = "LOW_CONFIDENCE_ASSERTION"; EXTRACTION_CORRECTION = "EXTRACTION_CORRECTION"; PROVENANCE_CORRECTION = "PROVENANCE_CORRECTION"; ENTITY_CORRECTION = "ENTITY_CORRECTION"; RELATIONSHIP_CORRECTION = "RELATIONSHIP_CORRECTION"
class ReviewAction(StrEnum): ACCEPT = "ACCEPT"; CORRECT = "CORRECT"; REJECT = "REJECT"; BLOCKED = "BLOCKED"
class ReviewItemStatus(StrEnum): OPEN = "open"; IN_REVIEW = "in_review"; DECIDED = "decided"; STALE = "stale"; BLOCKED = "blocked"
class EvidencePrecision(StrEnum): EXACT_SPAN = "exact-span"; TABLE_CELL = "table-cell"; BLOCK = "block"; PAGE = "page"; DOCUMENT = "document"; UNRESOLVED = "unresolved"

@dataclass(frozen=True, slots=True)
class ReviewDecision:
    id: UUID; review_item_id: UUID; review_batch_id: UUID; action: ReviewAction
    reason_code: str | None; corrected_value: Mapping[str, Any] | None; evidence: EvidenceLocator | None
    reviewer_principal_id: UUID; decided_at: datetime; assertion_version: int; stale: bool
    corrected_assertion_id: UUID | None; event_sha256: str
```

```python
# brain_review/decisions.py
class ReviewDecisionService:
    async def submit(self, batch_id: UUID, body: DecisionBatch, principal: Principal, *, trace_id: str) -> Receipt:
        # 1 authorize principal for review:annotate on every item's knowledge base → else 404 (no existence leak)
        #   the reviewer is `principal`, never a payload field (ADR-0049, ADR-0057)
        # 2 sha256(canonical(body)); INSERT review_event ... ON CONFLICT DO NOTHING; if not inserted → duplicate → 200 {"duplicate": true}
        # 3 one transaction for the whole batch:
        #     if item.assertion_version != current assertion version → decision stored with stale=True, item.status=STALE, new item opened
        #     if action == BLOCKED → require reason_code EVIDENCE_UNRESOLVED; no assertion created; item stays OPEN
        #     if action == CORRECT → create corrected assertion linked to the original, carrying the evidence target
        #                            and precision the reviewer saw (original untouched)
        # 4 audit_event per decision; item.status = DECIDED for applied adjudications
        # 5 canonical commit is never reachable from here — review:approve is a separate permission (section 111.2)
```

### Mutation Traceability

| Screen / Entry Point | User Action | Endpoint | Service Method | Entity / Carrier | Authorization | Concurrency | Validation Failure | Audit / Timeline | Test Expectation |
|----------------------|-------------|----------|----------------|------------------|---------------|-------------|--------------------|------------------|------------------|
| Nebula Review Panel, opened on a review batch | inspect the anchored region, edit value, submit batch | `POST /reviews/batches/{reviewBatchId}/decisions` | `ReviewDecisionService.submit` | `review_decision`, corrected `assertion` | `review_task:annotate` for the session principal on every item's knowledge base | decision event sha256 unique per item; assertion version check | 404 unauthorized; duplicate → 200 no-op; stale → decision flagged, not applied; unresolved evidence → BLOCKED, no assertion | `audit_event` per decision | `test_review_round_trip.py`: decision queryable after restart; original assertion unchanged; resubmission no-op; `anchors.spec.ts`: quote recovery and unresolved cases |

### HTTP Responses

| Status | Body | Condition |
|--------|------|-----------|
| 200 | `{"decision_ids": [...], "applied": n, "duplicate": false, "stale": 0, "blocked": 0}` | Applied |
| 200 | `{"duplicate": true}` | Resubmission of an already-decided batch |
| 401 | ProblemDetails (`unauthenticated`) | Credentials missing or invalid |
| 404 | ProblemDetails (`not_found`) | Batch not visible to this principal, or an item outside their scope |
| 422 | ProblemDetails (`decision_invalid`) | BLOCKED without EVIDENCE_UNRESOLVED, or CORRECT without a corrected value |

---

## Step 7 — Restore drill, revocation, DAST (S0006, hosting part)

- `scripts/ops/backup.sh`: `pg_dump` (custom format) plus MinIO `content` bucket mirror plus `docker/DEPENDENCY-MATRIX.md` snapshot into one timestamped directory with a manifest of sha256s.
- `scripts/ops/restore.sh`: fresh Compose project name → restore database → mirror bucket → run `scripts/ops/verify_citations.py` (every S0003 evidence binding resolves to a block in the restored artifact) → print measured restore duration.
- Revocation: `scripts/dev/revoke_membership.py` advances `grant_revision` and sets `revoked_at`; `test_revocation_propagation.py` polls until denied and records the elapsed time (JWKS and membership caches bounded by `BRAIN_GRANT_CACHE_SECONDS`, default 30).
- DAST: ZAP baseline against the API in Compose; dependency, secrets, and SAST scans via the framework security scripts; outputs under the feature run's `artifacts/security/`.

---

## Step 8 — Record outcomes (S0007)

Documentation-only step: per-ADR result tables citing `artifacts/` paths; dependency matrix completion; BLUEPRINT 2.1 and 4.8 updates. No code.

---

## Scope Breakdown

| Layer | Required Work | Owner | Status |
|------|----------------|-------|--------|
| Backend (`engine/`) | Steps 1, 3, 5, 6, 7 | backend-developer | Not started |
| AI (`neuron/`) | Step 4 | ai-engineer | Not started |
| Frontend (`experience/`) | None (F0021) | — | N/A |
| Quality | Test plan; AC matrix below; coverage ≥ 80% per workspace | quality-engineer | Not started |
| DevOps/Runtime | Steps 2 and 7 (stack, matrix, runbook, backup and restore, CI) | devops | Not started |
| Security | Step 3 review; review authority and evidence scope; four scan classes | security | Not started |

## Dependency Order

```
Step 0 (Architect):   this plan approved at G5; ADR-0054/0055 Accepted
Step 1 (Backend):     workspaces, app factory, /health, CI
Step 2 (DevOps):      compose stack, matrix, inference runbook
  ──── Runtime checkpoint: stack healthy, extensions created, /v1/models lists the model ────
Step 3 (Backend):     verifier, resolver, Casbin adapter, audit, protected reads
Step 4 (AI):          parse once, two interpretations, evidence bindings
Step 5 (Backend):     bitemporal commit, outbox, projector stub
Step 6 (Backend + Frontend): review items and batches, Review Panel, anchor resolution, decisions
  ──── Proof checkpoint: S0003, S0004, S0005 acceptance criteria green ────
Step 7 (DevOps+Sec):  backup/restore drill, revocation timing, DAST
Step 8 (Architect):   ADR results, matrix, blueprint updates
```

## Integration Checkpoints

### Checkpoint A — After Step 2

- [ ] `docker compose up -d` healthy within 120 s; `CREATE EXTENSION` for vector, age, btree_gist succeeds on PostgreSQL 18
- [ ] `GET /v1/models` on the inference service lists `microsoft/Phi-4-mini-instruct`; max model length 4096
- [ ] Two tenants, two users, one service client seeded in authentik

### Checkpoint B — After Step 3

- [ ] Wrong audience, expired, wrong signature, malformed → 401; no storage read (asserted by a repository spy)
- [ ] Same subject, different issuer → different principal ids
- [ ] Cross-tenant read → 404; audit event has `reason_code` and `policy_hash`

### Checkpoint C — After Step 4

- [ ] Second interpretation: `conversion_calls == 0`, `ocr_calls == 0`, `artifact_sha256` unchanged
- [ ] Every assertion has at least one binding with declared precision; scanned variant yields `page` where no tighter grounding exists
- [ ] Truncated page → `partial` with `failed_pages`; no assertion for that page; a review item exists

### Checkpoint D — After Step 5

- [ ] Section 87 matrix answered at four coordinates after reload
- [ ] Concurrency test: one winner, one 409, no ambiguous state
- [ ] Worker killed after commit → outbox replay processes once; canonical readable throughout

### Checkpoint E — After Step 6

- [ ] Correction produces one decision and one corrected assertion; original unchanged
- [ ] Duplicate delivery → no second decision; stale version → flagged, not applied; bad secret → 401
- [ ] Out-of-scope reviewer behavior on the Community edition recorded for ADR-0044

### Checkpoint F — After Step 7

- [ ] Restore drill: relational, content, manifests, review evidence present; every S0003 citation resolves; duration and data-loss window recorded
- [ ] Revocation propagation time recorded and under `BRAIN_GRANT_CACHE_SECONDS`
- [ ] Four scan classes recorded in the manifest `security_scans{}`

### Cross-Story Verification

- [ ] Full lifecycle: ingest → interpret twice → route low-confidence assertion → correct in the Review Panel → commit corrected value → query at four time coordinates → backup → restore → citations resolve
- [ ] All three roles enforced; revoked principal denied
- [ ] ProblemDetails format consistent across every endpoint (`code` + `traceId`)

## Acceptance-Criteria Test Matrix

| Story | Criterion | Test |
|-------|-----------|------|
| S0001 | `uv sync`, `/health` 200 with sha and versions, ruff and mypy clean, CI runs suites | `engine/tests/unit/test_health.py`; CI job |
| S0002 | Stack healthy, extensions created, object round trip, model listed, matrix pinned, no `latest` tags | `engine/tests/integration/test_stack_health.py`; `scripts/dev/check_pins.py` |
| S0003 | Bundle files and manifest; zero conversion on second run; binding precision; partial page; invalid model output | `neuron/tests/integration/test_parse_once_reinterpret.py`; `neuron/tests/unit/test_context_guard.py` |
| S0004 | Batch rendered and anchored; decision with lineage; original preserved; resubmission; stale; unresolved evidence blocked; annotate cannot commit | `engine/tests/integration/test_review_round_trip.py`; `engine/tests/security/test_review_authority.py`; `experience/tests/review-panel/anchors.spec.ts` |
| S0005 | Four-coordinate matrix; correction split; concurrency; transactional outbox; separate timestamps | `engine/tests/integration/test_bitemporal_commit.py`, `test_commit_concurrency.py`, `test_outbox_replay.py` |
| S0006 | Verification before storage; cross-scope 404; revocation timing; extension build; restore with citations | `engine/tests/security/test_credential_verification.py`, `test_scope_isolation.py`, `test_revocation_propagation.py`; `scripts/ops/restore.sh` output |
| S0007 | ADR status and results; matrix complete; blueprint updated | Link check in the feature run; Architect signoff |

## Security and Runtime Evidence

- `security_sensitive_scope = true` (Steps 3, 6, 7): Security Reviewer required; scan classes dependency, secrets, SAST, and DAST all apply because the API listens on a port in Compose.
- No secret in the repository; `.env.example` only; the inference key lives in `~/.brain-secrets` (0600) or CI secrets.
- The model server receives chunk text only; never a user token, principal id, or tenant identifier.
- Authorization denials never disclose existence; reason codes live in `audit_event` only.

## Knowledge-Graph Binding Plan

At feature G7 the Architect binds as-built source to the ten capabilities, ten entities, three workflows, six endpoints, one API contract, six schemas, three roles, and five policy rules declared in `planning-mds/kg-source/features/F0001.yaml` and `kg-source/nodes/**` by this plan. Intended binding globs (authored as `kg-source/bindings/**` shards at G7, never hand-edited into `code-index.yaml`):

| Node | Intended paths |
|------|----------------|
| `capability:runtime-roots-and-toolchain` | `engine/apps/api/src/brain_api/{app,health,errors}.py`, `engine/pyproject.toml`, `neuron/pyproject.toml` |
| `capability:local-dependency-stack` | `docker-compose.yml`, `docker/postgres/**`, `docker/DEPENDENCY-MATRIX.md` |
| `capability:local-inference-service` | `docker/local-inference-runbook.md`, `neuron/packages/brain-extraction/src/brain_extraction/docling_graph_adapter.py` |
| `capability:parse-once-content-artifact` | `neuron/packages/brain-ingestion/src/**`, `engine/packages/brain-content/src/**` |
| `capability:semantic-interpretation-run` | `neuron/packages/brain-extraction/src/**`, `neuron/packages/brain-interpretation/src/**` |
| `capability:evidence-review-round-trip` | `engine/packages/brain-review/src/**`, `experience/src/review-panel/**` |
| `capability:bitemporal-canonical-commit` | `engine/packages/brain-temporal/src/**`, `engine/migrations/versions/0003_*.py` |
| `capability:credential-verification-and-principal-resolution` | `engine/packages/brain-security/src/brain_security/{verification,principals}.py` |
| `capability:authorization-enforcement` | `engine/packages/brain-security/src/brain_security/{authorization,casbin_adapter,audit}.py`, `planning-mds/security/policies/**` |
| `capability:backup-and-restore` | `scripts/ops/**` |

Feature status moves `architecture-complete → in-progress` in the shard at feature G0 and `→ done` at G8.

## Risks and Blockers

| Item | Severity | Mitigation | Owner |
|------|----------|------------|-------|
| Phi-4-mini-instruct's 4,096-token context is short for document chunks | High | Client-side guard; chunk sizing in the profile; adequacy result recorded in ADR-0040; alternative backend proposed at Phase B of F0005 if needed | ai-engineer |
| AGE build on PostgreSQL 18 fails | Medium | Fallback to 17 recorded in the matrix; no silent downgrade | devops |
| Real documents defeat the panel's renderers: no text layer, rotated pages, fragmented text items, multi-row spreadsheet headers | Medium | Precision is declared and unresolved anchors block the decision (ADR-0058); S0004 proves that path deliberately and the gaps are recorded for ADR-0058 | frontend-developer, ai-engineer, QA |
| Docling-Graph grounding coarser than expected | Medium | Precision recorded per binding; page-level accepted and displayed honestly | ai-engineer |
| GL policy package not available in time | Medium | Operator supplies; otherwise a synthetic package selected and recorded | product-manager |
| Restore drill omits content objects | High | `verify_citations.py` fails the drill; failure recorded, not waived | devops |

## JSON Serialization Convention

snake_case keys (the single exception is the ProblemDetails `traceId` extension member, camelCase because the framework API contract validator requires that name); RFC 3339 UTC timestamps with `Z`; UUIDs as strings; monetary amounts as `{"amount": "2000000.00", "currency": "USD"}` with the amount as a decimal string; ranges as `{"start": ..., "end": ... | null}`; enums as their exact string values. All schemas under `planning-mds/schemas/` set `additionalProperties: false`.

## DI Registration Changes

`brain_api.app.create_app()` builds `Settings` from environment, then the adapters (`OidcJwksVerifier`, `PrincipalResolver`, `CasbinAuthorizationService`, `MinioContentArtifactStore`, `CanonicalCommitService`, `ReviewDecisionService`) and exposes them through FastAPI dependencies in `brain_api.deps`. The worker (`brain_worker.main`) builds the same `Settings` and only the ingestion runner and outbox projector.

## Casbin Policy Sync

`planning-mds/security/policies/policy.csv` is the authored source; `brain_security.casbin_adapter` loads it at startup from `BRAIN_POLICY_PATH` (default: the planning path) and records its sha256 as `policy_hash`. `scripts/kg/validate.py --check-drift` cross-checks the `policy_rule` nodes against the CSV.

## Run and Release Checklist

- [ ] `python3 scripts/run-lifecycle-gates.py` green
- [ ] `uv run --directory engine pytest --cov` and `uv run --directory neuron pytest --cov` ≥ 80%
- [ ] `docker compose config` valid; `scripts/dev/check_pins.py` clean
- [ ] Inference runbook executed once on the developer host; `GET /v1/models` captured under `artifacts/`
- [ ] Restore drill output captured under `artifacts/`
- [ ] ADR-0040, 0041, 0044, 0049, 0050 status updated by S0007
