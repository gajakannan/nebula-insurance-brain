# Self Review — F0001-repository-and-engineering-foundation run 2026-09-08-b5af1e54

**Role:** Backend Developer / AI Engineer / Frontend Developer / DevOps (combined; one implementer executed all seven stories in this run)
**Date:** 2026-09-10

## Scope Review

Implemented scope matches `feature-assembly-plan.md`'s eight steps exactly: engine/neuron workspace skeletons (S0001), the local dependency stack (S0002), the parse-once/reinterpret-twice proof (S0003), the native review round trip (S0004), the bitemporal commit proof (S0005), the access-boundary/restore proof (S0006), and ADR settlement (S0007). No scope drift from the assembly plan's Step 1–8 sequence.

One deliberate architecture deviation from the plan's assumptions, recorded rather than silently absorbed: `docling-graph` (named in the plan as the semantic/graph extraction engine) was evaluated live at S0003 and rejected — its API always reconverts the source, conflicting with the parse-once requirement. Extraction instead calls the OpenAI-compatible vLLM endpoint directly. Recorded in ADR-0040 and `docker/DEPENDENCY-MATRIX.md`'s "ADR-0040 input" section, and reconciled into `BLUEPRINT.md` §2.1/§4.8 and `master-blueprint.md` §116.1 row 104 at S0007.

## Acceptance Criteria Review

Each story's acceptance criteria and the test/evidence that validates them:

- **S0001** (runtime roots): `uv sync` green on both workspaces, `/health` returns git sha + versions + storage round trip, `uv sync --python 3.12` fails closed — `apps/api/tests/test_health.py`, CI `runtime-suites` job.
- **S0002** (dependency stack): extensions create on PostgreSQL 18, two `down -v`/`up -d` cycles both reach healthy, no `latest`/bare tags — `scripts/dev/check_pins.py`, CI `runtime-stack` job, re-verified live at S0006 (`\dx`: vector 0.8.6, age 1.8.0, btree_gist 1.8, server 18.6).
- **S0003** (parse once, reinterpret twice): zero conversion/OCR calls on reinterpretation, evidence precision declared per binding — `neuron/tests/integration/test_parse_once_reinterpret.py`.
- **S0004** (native review round trip): duplicate-by-hash no-op, stale reopens a new item, unresolved evidence forces BLOCKED, corrected assertion links to the untouched original — `engine/packages/brain-review/tests/`, `engine/apps/api/tests/test_reviews.py`, `experience/src/review-panel/__tests__/`.
- **S0005** (bitemporal commit): section 87 matrix after reload, concurrency leaves exactly one winner, outbox replay processes once — `engine/tests/integration/test_bitemporal_commit.py`, `test_commit_concurrency.py`, `test_outbox_replay.py`.
- **S0006** (access boundaries, extension build, restore): verify-before-read, cross-scope denial across all three resource types, revocation propagation measured, restore drill with citation verification — `engine/tests/security/`, `scripts/ops/backup.sh`/`restore.sh`/`verify_citations.py`.
- **S0007** (ADR settlement): all six ADRs updated with measured results and artifact citations — see the ADR files themselves under `planning-mds/architecture/decisions/`.

## Implementation Risks

- **ADR-0058's selector shape is narrower than proposed** (single `nebula:BoxSelector`, PDF-only, vs. the proposed W3C multi-selector redundant model). Mitigation: recorded as an explicit ADR amendment rather than silently shipped; the fuller model is demoted to future scope for whichever feature first adds a non-PDF fixture. Not a defect — a scope call made and disclosed.
- **Scanned-variant OCR path lacks an automated regression test** — verified manually at S0007 (2026-09-10) but not asserted by pytest. Mitigation: tracked in `STATUS.md` Deferred Non-Blocking Follow-ups for F0002.
- **`docling_graph_adapter.py` has only 25% unit-test coverage** in the offline coverage run (its live-integration proof requires a reachable vLLM endpoint, skipped when unavailable — see `coverage-report.md`). The actual live proof ran successfully during S0003 development (real model calls, real token counts recorded).
- **CI never actually exercised the runtime-bearing jobs before this run** (previous CI history was framework/planning-only, ~17s runs) — several real gaps surfaced only once real code landed: a coverage gate on `brain_domain.facts` (fixed), a pytest import-mode collision unique to per-package invocation (fixed across all 7 engine packages), a documented-but-unimplemented retry race in the OIDC discovery check (fixed), and a stale KG coverage-report.yaml (regenerated). All four are now fixed and verified green on `main`.

## Validation Evidence

- `engine`: 129 tests passing (unit + live-Postgres integration/security, skip not fail when infra unreachable); ruff/mypy clean across all 8 src trees; per-package coverage gates all ≥80% (see `coverage-report.md`).
- `neuron`: 18 passed, 2 skipped (vLLM-dependent, skip-not-fail); ruff/mypy clean.
- `experience`: 11 component tests passing; `tsc -b`/`eslint`/`vite build` all clean.
- CI (`main`, run `34554563562`): all 5 jobs green — `product-gates`, `runtime-suites`, `runtime-stack`, `experience`, `framework-validators`.
- Backup/restore drill: 4 consecutive runs, ~3.1s each, citations resolved identically every time (`scripts/ops/`).

## Recommendations

- [medium] Add an automated test exercising the scanned/OCR fixture in `neuron/tests/integration/test_parse_once_reinterpret.py` rather than relying on a manual check — owner: ai-engineer; follow-up: F0002.
- [medium] `docling_graph_adapter.py`'s live-only code paths (structured extraction call, response parsing) should get an offline unit test with a mocked HTTP client so coverage doesn't depend on a reachable vLLM endpoint — owner: ai-engineer; follow-up: F0002.
- [low] Add a Playwright E2E pass for the Review Panel (currently 11 Vitest/Testing-Library component tests only, pdf.js mocked) — owner: quality-engineer; follow-up: F0021 (full frontend toolchain).

## Result

PASS WITH RECOMMENDATIONS
