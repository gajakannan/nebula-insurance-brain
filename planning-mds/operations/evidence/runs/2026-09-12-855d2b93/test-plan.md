---
template: test-plan
version: 2.0
applies_to: quality-engineer
---

# Test Plan — F0001-repository-and-engineering-foundation run 2026-09-12-855d2b93

## Remediation Test Plan

The remediation adds a pure structured-log contract test plus HTTP-layer assertions for
malformed, invalid-signature, expired, and wrong-audience credentials. The security
fixture has a bounded host-connect preflight so unavailable Postgres is reported as a
skip, never as a hung test process.

## Story-to-AC Mapping

| Story | AC | Lane | Test ID | Owner |
|-------|----|------|---------|-------|
| S0001 | `uv sync` green, version gate fails closed | Unit/CI | `apps/api/tests/test_health.py`; CI `runtime-suites` | backend-developer |
| S0001 | `/health` returns sha/versions/storage | Integration | `apps/api/tests/test_health.py::test_health_ok` | backend-developer |
| S0002 | Extensions create on PostgreSQL 18 | Integration (live) | CI `runtime-stack` job; manual `\dx` at S0006 | devops |
| S0002 | Two `down -v`/`up -d` cycles both reach healthy | Integration (live) | CI `runtime-stack` job | devops |
| S0003 | Zero conversion/OCR on reinterpretation | Integration (live, vLLM) | `neuron/tests/integration/test_parse_once_reinterpret.py::test_parse_once_reinterpret_twice_evidence_resolves` | ai-engineer |
| S0003 | Evidence precision declared per binding | Integration (live, vLLM) | same test, Step 3 assertions | ai-engineer |
| S0003 | Context-limit rejection edge case | Unit/Integration | `test_reinterpretation_over_context_limit_is_rejected_client_side` | ai-engineer |
| S0004 | Duplicate-by-hash no-op | Unit | `packages/brain-review/tests/test_decisions.py` | backend-developer |
| S0004 | Stale reopens a new item | Unit | `packages/brain-review/tests/test_decisions.py` | backend-developer |
| S0004 | Unresolved evidence forces BLOCKED | Unit | `packages/brain-review/tests/test_decisions.py` | backend-developer |
| S0004 | Correction preserves the original | Unit | `packages/brain-review/tests/test_decisions.py` | backend-developer |
| S0004 | Reviewer cannot commit canonical truth | API/Security | `apps/api/tests/test_reviews.py::test_tenant_member_without_annotate_permission_cannot_submit_a_decision` | backend-developer |
| S0004 | Page-level ground renders honestly | Component | `experience/src/review-panel/__tests__/Viewport.test.tsx` | frontend-developer |
| S0004 | BLOCKED action surfaced, no accept/correct | Component | `experience/src/review-panel/__tests__/FieldList.test.tsx` | frontend-developer |
| S0005 | Section 87 matrix after reload | Integration (live) | `engine/tests/integration/test_bitemporal_commit.py` | backend-developer |
| S0005 | Concurrency leaves exactly one winner | Integration (live) | `engine/tests/integration/test_commit_concurrency.py` | backend-developer |
| S0005 | Outbox replay processes once | Integration (live) | `engine/tests/integration/test_outbox_replay.py` | backend-developer |
| S0006 | Verify before any protected read | API/Security | `engine/tests/security/test_credential_verification.py` | backend-developer |
| S0006 | Cross-scope denial across 3 resource types | API/Security (live) | `engine/tests/security/test_scope_isolation.py` | backend-developer |
| S0006 | Revocation propagation measured | API/Security (live) | `engine/tests/security/test_revocation_propagation.py` | backend-developer |
| S0006 | Restore drill, citations resolve | Integration (live, manual) | `scripts/ops/backup.sh`/`restore.sh`/`verify_citations.py` | devops |
| S0007 | ADRs record measured results | Documentation | ADR files under `planning-mds/architecture/decisions/` | architect |

## Test Strategy

- **Unit tests** (developer-owned): pure-Python algorithm/domain tests, no I/O — `brain-domain`, `brain-temporal` (algorithmic layer via in-memory fake), `brain-review`, `brain-security` (except live-JWT round trips).
- **Component tests** (developer-owned): Vitest + Testing Library for the Review Panel, pdf.js mocked (jsdom cannot render `<canvas>`).
- **Integration tests** (developer + QE-owned): live-Postgres tests under `engine/tests/integration/` and `engine/tests/security/`, skip (not fail) when the compose stack is unreachable; live-vLLM tests under `neuron/tests/integration/`, same skip convention.
- **API tests** (developer-owned): real HTTP round trips via `httpx.AsyncClient`/ASGI transport with genuine RSA-signed JWTs and the real Casbin policy files — `apps/api/tests/`.
- **E2E tests**: not built in this proof-scope run — the harder, more critical proof (backend decision transaction, real JWT/Casbin) was prioritized; full Playwright E2E deferred to F0021 (the full frontend toolchain).
- **Accessibility tests**: not in scope for this proof-scope run; F0021 owns the full UX rule-set toolchain.

## Developer-vs-QE Test Ownership

This run had one implementer executing both developer and QE responsibilities (proof-scope feature, no dedicated QE headcount allocated at Phase B). All unit/component/integration/API test lanes above were authored by the implementer as each story landed, self-reviewed at `g2-self-review.md`, and are re-verified here as the QE pass.

## Test Data / Fixtures

- Synthetic GL policy declarations fixture, native + scanned variants (`neuron/fixtures/`), generated by `neuron/fixtures/make_gl_fixture.py` since no operator-supplied package was available (S0003's own documented contingency).
- Two tenants, two users, one service client seeded in authentik (`docker/authentik/blueprints/nebula-brain-dev.yaml`).
- Real RSA-signed JWTs generated per-test (not against live authentik) for credential-verification and API-layer tests — same pattern used consistently from S0004 onward.
- `scripts/dev/seed_restore_drill_fixture.py` — one real S0003/S0004/S0005-shaped fixture (content bundle + review decision + committed fact) for the S0006 restore drill.

## Happy / Edge / Error / Auth / Accessibility / Regression Cases

- **Happy**: parse→interpret→review→correct→commit→query-at-four-coordinates chain proven piecewise per story.
- **Edge**: dense-block extraction (ADR-0040), retroactive correction splitting into two pieces (S0005), stale reviewer correction (S0004), a backup missing content objects (S0006, confirmed the drill correctly fails).
- **Error**: expired/malformed/wrong-audience/wrong-signature/not-yet-valid tokens all 401 with no storage read; empty/null commit ranges 400; concurrent commit 409.
- **Auth**: cross-tenant denial (404, never 403) across content/review/fact; revoked-membership denial; issuer-namespaced identity.
- **Accessibility**: not covered — deferred to F0021.
- **Regression**: the full `uv run pytest -q` suite (129 tests) and CI's per-package coverage gates run on every change; the framework's own KG reproducibility and tracker-validation gates cover planning-doc regressions.

## Risks And Mitigations

- **Risk**: proof-scope harness code (this feature) may not generalize to production load/scale. **Mitigation**: this feature's explicit purpose is de-risking the pre-build contracts before v0.1A construction begins; F0002 onward builds the production-shaped kernel on these settled contracts.
- **Risk**: no E2E/accessibility coverage for the Review Panel. **Mitigation**: backend decision transaction (the higher-risk surface) is thoroughly tested; residual risk accepted for this proof-scope run, tracked for F0021.
- **Risk**: `docling-graph`'s live-only extraction path has low unit coverage (25%, see `coverage-report.md`). **Mitigation**: the real live proof executed successfully during development (recorded in `docker/DEPENDENCY-MATRIX.md`); an offline-mockable unit test is recommended for F0002 (see `g2-self-review.md`).

## Result

PASS WITH RECOMMENDATIONS
