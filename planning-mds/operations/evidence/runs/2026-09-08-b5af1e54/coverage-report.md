# Coverage Report — F0001-repository-and-engineering-foundation run 2026-09-08-b5af1e54

## Coverage Target And Actual Per Layer (engine/, per-package gates — matches CI exactly)

| Package | Target | Actual | Source |
|---|---:|---:|---|
| `brain_domain` | 80% | 100% | `uv run pytest packages/brain-domain/tests --cov=brain_domain` |
| `brain_content` | 80% | 96.11% | `uv run pytest packages/brain-content/tests --cov=brain_content` |
| `brain_persistence` | 80% | 87.68% | `uv run pytest packages/brain-persistence/tests --cov=brain_persistence` (sqlite-scoped; `canonical_fact_version`/`canonical_fact_change` excluded by design, see below) |
| `brain_security` | 80% | 98.55% | `uv run pytest packages/brain-security/tests --cov=brain_security` |
| `brain_review` | 80% | 99.12% | `uv run pytest packages/brain-review/tests --cov=brain_review` |
| `brain_temporal` | 80% | 99.06% | `uv run pytest packages/brain-temporal/tests --cov=brain_temporal` |
| `brain_api` | 80% | 91.88% | `uv run pytest apps/api/tests --cov=brain_api` |

## Coverage Target And Actual Per Layer (neuron/, informational — no per-package CI gate exists for neuron)

| Package | Actual (offline run) | Notes |
|---|---:|---|
| `brain_ingestion` | 94–100% | `docling_adapter.py` 100%, `bundle_writer.py` 94% |
| `brain_interpretation` | 100% | |
| `brain_extraction` | 25–82% (`docling_graph_adapter.py` 25%) | Low because its structured-extraction call path only executes against a live vLLM endpoint; that endpoint was unreachable during this specific coverage pass. The live path executed and passed during S0003 development (2026-09-09) — see `docker/DEPENDENCY-MATRIX.md`. Recommendation filed in `g2-self-review.md` to add an offline-mockable unit test. |

## Coverage Target And Actual Per Layer (experience/)

| Layer | Actual | Source |
|---|---:|---|
| Component (Vitest) | 3 files / 11 tests, all passing | `pnpm exec vitest run` |

No coverage percentage is gated for `experience/` in this proof-scope run (the full
frontend toolchain, including coverage thresholds, is F0021's).

## Raw Artifact Paths

Per-package coverage output is reproduced verbatim in `test-execution-report.md`; this
run's evidence package does not include a separate coverage-artifacts subdirectory (CI's
`runtime-suites` job instead uploads `engine/coverage/coverage.xml` as its own workflow
artifact — see run `34554563562`).

## Feature-Scoped Notes

- `brain_persistence`'s 87.68% excludes `canonical_fact_version`/`canonical_fact_change`
  by design — those tables use `tstzrange` columns and a `gist` exclusion constraint with
  no sqlite equivalent, and are instead proven against live Postgres in
  `engine/tests/integration/`. This is documented in `brain_persistence.base.sqlite_test_tables()`.
- `brain_api`'s missed lines (`routes/content.py` 73%, `routes/reviews.py` 87%,
  `routes/facts.py` 85%) are almost entirely exception-handling branches for
  infrastructure failures (object-store misses, malformed manifests) not exercised by the
  sqlite-scoped unit suite — the corresponding happy/denial paths are covered live in
  `engine/tests/security/` and `apps/api/tests/test_facts.py`.
- No coverage waiver is requested; every gated package meets or substantially exceeds the
  80% target.

## Result

PASS
