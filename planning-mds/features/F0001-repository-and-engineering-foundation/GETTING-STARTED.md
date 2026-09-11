# F0001 — Repository and engineering foundation — Getting Started

## Prerequisites

- [ ] Docker with Compose v2
- [ ] Python 3.13 and `uv`
- [x] Node and pnpm — used both for the KG TypeScript symbol extractor and, from S0004, the proof-scope `experience/` Review Panel (host tested: Node 24.16.0, pnpm 11.17.0)
- [x] A GL policy package for the proofs: no operator-supplied package was available before S0003, so a synthetic one was generated (`neuron/fixtures/make_gl_fixture.py` → `gl-policy-declarations.pdf` + `-scanned.pdf`), per the story's own contingency
- [ ] Framework session: `nebula-agents` checked out as a sibling with `NEBULA_PRODUCT_ROOT` exported

## Services to Run

```bash
cp .env.example .env   # fill AUTHENTIK_SECRET_KEY / AUTHENTIK_BOOTSTRAP_PASSWORD; never commit .env
docker compose up -d   # postgres (18 + pgvector v0.8.6 + AGE PG18/v1.8.0-rc0) and authentik; artifacts use config/local.yaml
# inference service on the host GPU, per docker/local-inference-runbook.md (vLLM 0.25.1, microsoft/Phi-4-mini-instruct, :8000)
uv run --directory engine fastapi dev apps/api/src/brain_api/app.py   # API on :8100
uv run --directory engine python -m brain_worker.outbox_projector     # outbox projector (S0005, done; polls every 1s)
```

authentik is reachable at `http://localhost:9010` (server) — remapped off its stock 9000/9443
because this host may already run `nebula-insurance-crm`'s own authentik there (F0001-G1
finding). `python3 scripts/dev/seed_principals.py` verifies the dev seed (`alice.tenant-a`,
`bob.tenant-b`, `brain-service`) via ROPC; **on a fresh `up -d` it can fail once with
`HTTP 400`** for ~10–15s after authentik reports healthy — the custom blueprint applies
asynchronously just after the healthcheck passes. Retry once; CI retries automatically.

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `BRAIN_DATABASE_URL` | PostgreSQL 18 connection | compose default |
| `config/local.yaml` | Local filesystem content-artifact store | committed default; runtime bytes under ignored `./content/` |
| `BRAIN_OIDC_ISSUER`, `BRAIN_OIDC_AUDIENCE` | authentik verification | compose defaults |
| `BRAIN_INFERENCE_BASE_URL`, `BRAIN_INFERENCE_MODEL`, `BRAIN_INFERENCE_API_KEY_ENV`, `BRAIN_INFERENCE_CONTEXT_LIMIT` | vLLM endpoint, `microsoft/Phi-4-mini-instruct`, key name, `4096` | see runbook |
| `BRAIN_GRANT_CACHE_SECONDS` | Bound on revocation propagation | `30` |

## Seed Data

- Proof fixture: one GL policy package with a deliberately low-confidence limit extraction and one endorsement effective June 1, received June 12 (sections 86, 87)
- Two principals in two tenants for the access proof (section 115.4)

## How to Verify

1. `python3 scripts/run-lifecycle-gates.py` passes.
2. **S0001 (done):** `cd engine && uv sync && uv run ruff check . && uv run ruff format --check . && uv run mypy apps/api/src && uv run pytest apps/api/tests --cov=brain_api --cov-fail-under=80` — 5 tests, 100% coverage. `cd neuron && uv sync && uv run ruff check . && uv run mypy && uv run pytest` — 1 smoke test (neuron/packages/ is empty until S0003). `uv sync --python 3.12` in either workspace fails closed, naming `>=3.13`, proving the version gate.
3. `uv run --directory engine fastapi dev apps/api/src/brain_api/app.py` then `curl localhost:8100/health` (or run uvicorn directly, as CI does) returns `{"status": "ok", "git_sha": ..., "versions": {...}, "storage": "ok"}` — `storage` proves the `LocalFilesystemObjectStore` round trip against `config/local.yaml` with no storage environment variables.
4. **S0002 (done):** `python3 scripts/dev/check_pins.py` (no `latest`/bare tags); `docker compose build postgres` (pgvector v0.8.6 + AGE PG18/v1.8.0-rc0 build clean against PG18 headers); `docker compose up -d` reaches healthy in ~30s (postgres) / ~30–60s (authentik, well under the 120s ceiling); `docker exec brain-postgres psql -U brain -d brain -c "\dx"` lists `vector`, `age`, `btree_gist`; OIDC discovery served at `:9010`; `python3 scripts/dev/seed_principals.py` verifies all three seeded principals via ROPC, including the `tenant_id` claim in the token; two consecutive `docker compose down -v && up -d` cycles both reach healthy with no manual steps.
5. **S0003 (done):** `python3 neuron/fixtures/make_gl_fixture.py` regenerates the synthetic GL fixture pair (no operator-supplied package was available; the Architect selected a synthetic one per the story's own contingency). With `docker/local-inference-runbook.md`'s vLLM server running, `BRAIN_INFERENCE_API_KEY=<key> uv run --directory neuron pytest tests/integration/test_parse_once_reinterpret.py` runs the full live proof: parse once (real Docling, real OCR on the scanned variant only), persist the six-file bundle, interpret twice under two independent profiles from the persisted artifact alone (`assert_no_reparse` on both), and resolve each extracted value's evidence to a page/block/bbox/char-span with declared precision. The test is skipped automatically (not failed) when vLLM isn't reachable. `docker/DEPENDENCY-MATRIX.md`'s ADR-0040 section records why `docling-graph` itself is not used for extraction. `cd engine && alembic -c migrations/alembic.ini upgrade head` (with the compose `postgres` service up) applies the F0001-S0003 schema (`source_document`, `document_version`, `content_artifact`, `semantic_interpretation_run`, `assertion`, `assertion_evidence`); `downgrade base` reverses it cleanly.
6. **S0004 (done):** Backend — `cd engine && uv run pytest -q` (84 tests: identity/authorization core in `brain-security`, the review decision transaction in `brain-review` covering every acceptance-criterion edge case — duplicate-by-hash, stale reopens a new item, unresolved evidence forces BLOCKED, corrected assertion created with `origin=HUMAN_REVIEW` — and a real HTTP round trip through `brain_api` with a genuine RSA-signed JWT and the real Casbin policy files). `uv run ruff check . && uv run ruff format --check . && uv run mypy apps/api/src packages/brain-content/src packages/brain-persistence/src packages/brain-domain/src packages/brain-security/src packages/brain-review/src` all exit 0. Frontend — `cd experience && pnpm install && pnpm exec tsc -b && pnpm exec eslint . && pnpm exec vitest run && pnpm exec vite build` (11 component tests; production build succeeds, pdf.js worker bundled).
7. **S0005 (done):** `cd engine && alembic -c migrations/alembic.ini upgrade head` (with compose `postgres` up) applies `0003_fact_slots_and_commits` (`fact_slot`, `canonical_fact_version` with its `EXCLUDE USING gist (slot_id WITH =, valid WITH &&, recorded WITH &&)`, `canonical_fact_change`, `outbox_event`); `downgrade 0002` reverses it cleanly. `uv run pytest -q` (112 tests total: 21 pure-algorithm tests in `brain-temporal` against an in-memory fake repository — the section 87 matrix, retroactive split-into-two, stale-version rejection, empty-range rejection, missing-slot/no-membership denial-as-404 — plus, when the compose `postgres` service is reachable, 7 live tests that are skipped rather than failed otherwise: `tests/integration/test_bitemporal_commit.py` answers the section 87 matrix after a real reload from Postgres, `test_commit_concurrency.py` races two real `asyncio` tasks against the same slot through independent sessions and leaves exactly one winner (the loser's row lock blocks on `SELECT ... FOR UPDATE`, then rejects on a stale `expected_current_version_id`), `test_outbox_replay.py` proves a simulated worker-kill-then-restart processes each outbox event exactly once, and `apps/api/tests/test_facts.py` proves the HTTP contract end to end — 201/200 happy path, 400 `invalid_range`, 409 `stale_version`, 404 for a slot outside the caller's membership — over a real `httpx.AsyncClient`/ASGI transport rather than the synchronous `TestClient`, because `asyncpg` connections are bound to the event loop that created them and break across `TestClient`'s worker-thread portal). A manual `psql` probe additionally confirmed the exclusion constraint itself rejects two rows for the same slot with disjoint `valid` ranges but overlapping `recorded` ranges — the database-level backstop behind the row lock. `uv run python -m brain_worker.outbox_projector` (or `run_once` directly) drains `outbox_event` and is idempotent on replay.
8. **S0006 (done):** `docker exec brain-postgres psql -U brain -d brain -c "\dx"` re-confirms `vector 0.8.6`, `age 1.8.0`, `btree_gist 1.8` against server `PostgreSQL 18.6` (see `docker/DEPENDENCY-MATRIX.md` for the base-image tag drift note). `cd engine && uv run pytest tests/security -q` (10 tests, live against the compose Postgres, skipped not failed if unreachable): `test_credential_verification.py` (missing/malformed/garbage/expired/wrong-audience bearer all 401, reason never disclosed), `test_scope_isolation.py` (principal A: 200 on A's own content/review/fact, 404 on B's, across all three resource types; a membership-less principal is 404 not 401), `test_revocation_propagation.py` (revoke via `scripts/dev/revoke_membership.py`'s SQL, denied on the very next request — measured 12.41ms — and a revoked grant cannot be reinstated by querying an earlier bitemporal coordinate). `packages/brain-security/tests/test_verification.py` and `test_principals.py` gained `not_yet_valid` and "different issuer → different principal" cases. Restore drill: `python3 scripts/dev/seed_restore_drill_fixture.py` (from the repo root, via `uv run --directory engine`) seeds one real S0003/S0004/S0005-shaped fixture, then `bash scripts/ops/backup.sh` followed by `bash scripts/ops/restore.sh <backup-dir>` restores into a fresh, throwaway Postgres container (not the dev stack) plus a fresh content root and runs `scripts/ops/verify_citations.py` — four consecutive runs all passed in ~3.1s with both citations (block-level and page-level) resolving identically each time; a backup with an empty content snapshot correctly fails the citation check (exit 1) instead of passing silently.
9. **S0007 (done):** documentation-only — no code, no tests to run. Verify by reading: `planning-mds/architecture/decisions/ADR-0040-*.md`, `ADR-0041-*.md`, `ADR-0044-*.md`, `ADR-0049-*.md`, `ADR-0050-*.md`, `ADR-0058-*.md` are all Accepted (ADR-0058 accepted-as-amended) with a "Results" section citing the exact test paths above; `docker/DEPENDENCY-MATRIX.md` is marked complete; `planning-mds/BLUEPRINT.md` sections 2.1 and 4.8 name the pinned host image/PostgreSQL build/model-provider data policy and mark master blueprint section 117.1 items 3 and 4 answered; `planning-mds/architecture/master-blueprint.md` section 116.1's reconciliation table is annotated for rows 14, 47–49, 75, 80–81, and 104, each pointing at the ADR that settled it instead of silently rewriting the original baseline text.

## Key Files

| Layer | Path | Purpose |
|-------|------|---------|
| Backend | `engine/apps/api/src/brain_api/` | app factory, `/health` (S0001/S0002), `deps.py` (bearer→verify→resolve→authorize), `routes/reviews.py`, `routes/content.py` (streamed authorized artifact reads) (S0004, done); `routes/facts.py` — `GET /facts/{factSlotId}`, `POST /facts/{factSlotId}/commits` (S0005, done) |
| Backend | `engine/packages/brain-content/` | `ContentArtifactStore`/`ObjectStore` ports + local filesystem adapter (S0002, done) |
| Backend | `engine/packages/brain-persistence/` | SQLAlchemy 2 async models + migrations `0001_content_and_interpretation` (S0003), `0002_principals_audit_and_review` (S0004), `0003_fact_slots_and_commits` (S0005); repository adapters for every port `brain-security`/`brain-review`/`brain-temporal` declare |
| Backend | `engine/packages/brain-domain/` | `Principal`/`Membership`, `AuditEvent`, `ReviewItem`/`ReviewBatch`/`ReviewDecision`/`EvidenceLocator` (S0004), `FactSlot`/`CommitProposal`/`CommitResult`/`FactVersion`/`ChangeReason` (S0005) — pure dataclasses, no I/O |
| Backend | `engine/packages/brain-security/` | `OidcJwksVerifier`, `PrincipalResolver`, `CasbinAuthorizationAdapter`, `AuthorizationService`, audit sink (S0004/S0006-access, done) |
| Backend | `engine/packages/brain-review/` | routing policy, batch assembly, the `ReviewDecisionService` transaction, the interpretation→review evidence-locator bridge (S0004, done) |
| Backend | `engine/packages/brain-temporal/` | `TimeRange`/`split_remainder`, `CanonicalCommitService` (bitemporal commit algorithm, master blueprint section 109.2), `OutboxProjector` (S0005, done) |
| Backend | `engine/apps/worker/src/brain_worker/` | `outbox_projector.py` — polls and marks `outbox_event` rows processed; idempotent on replay (S0005, done; no graph/vector projection yet — F0033/F0034) |
| Backend | `engine/tests/security/` | `test_credential_verification.py`, `test_scope_isolation.py`, `test_revocation_propagation.py` — live-Postgres access-boundary proof (S0006, done) |
| Ops | `scripts/ops/backup.sh`, `restore.sh`, `verify_citations.py` | Backup/restore drill: sha256-manifested backup, restore into a throwaway Postgres container, citation verification against S0003 evidence bindings (S0006, done) |
| Dev | `scripts/dev/revoke_membership.py`, `seed_restore_drill_fixture.py` | Revocation-propagation and restore-drill proof fixtures (S0006, done) |
| Frontend | `experience/src/review-panel/` | proof-scope Review Panel: `Viewport.tsx` (real `pdf.js`), `FieldList.tsx`, `ReviewPanel.tsx`, `api.ts`/`types.ts` (S0004, done; ADR-0057) |
| AI runtime | `neuron/packages/brain-ingestion/` | real Docling parse-once adapter + bundle writer, now with optional original-source-byte retention (S0003, extended at S0004) |
| AI runtime | `neuron/packages/brain-extraction/` | extraction profiles, context guard, OpenAI-compatible/vLLM adapter — not `docling-graph` (S0003, done; see ADR-0040 input in `docker/DEPENDENCY-MATRIX.md`) |
| AI runtime | `neuron/packages/brain-interpretation/` | `InterpretationResult` model, counters, run recorder port (S0003, done) |
| Containers | `docker/`, `docker-compose.yml` | Dependency stack and pinned matrix |

## Notes

- Section 114.3: pin one exact combination of Python, PostgreSQL, AGE, pgvector, Docling, Docling-Graph, `pdf.js`, and `fflate`; do not rely on generic compatibility claims.
- Sections 111.1 and 125: prove the native review workflow, including the anchoring and unresolved-evidence paths, before estimating anything that depends on it.
