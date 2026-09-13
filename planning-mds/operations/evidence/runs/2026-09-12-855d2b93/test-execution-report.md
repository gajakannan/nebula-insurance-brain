# Test Execution Report — F0001-repository-and-engineering-foundation run 2026-09-12-855d2b93

**Date:** 2026-09-12

## Remediation Validation

```text
$ .venv/bin/ruff check apps/api/src/brain_api/deps.py tests/security/test_credential_verification.py tests/security/conftest.py
All checks passed!
$ .venv/bin/python -m pytest tests/security/test_credential_verification.py -q
1 passed, 5 skipped in 0.03s
$ .venv/bin/python -m pytest packages/brain-security/tests/test_verification.py -q
6 passed in 0.08s
```

The five skips are the live HTTP cases whose Postgres endpoint is inaccessible from the
managed sandbox; `docker compose ps` separately confirmed the services healthy. The
pure logging-contract test passed and proves the failure reason is emitted without the
credential value.
**Executed by:** Quality Engineer pass (combined with implementer per `test-plan.md` ownership note)

## Engine Workspace (`engine/`)

```text
$ uv run ruff check .                         -> All checks passed!
$ uv run ruff format --check .                -> 83 files already formatted
$ uv run mypy apps/api/src apps/worker/src packages/brain-content/src \
    packages/brain-persistence/src packages/brain-domain/src \
    packages/brain-security/src packages/brain-review/src packages/brain-temporal/src
                                               -> Success: no issues found in 46 source files
$ uv run pytest -q                            -> 129 passed in 2.30s
```

129 tests break down as: unit tests across `brain-domain` (12), `brain-security` (22),
`brain-review` (20), `brain-temporal` (21), `brain-content` (18), `brain-persistence` (4
sqlite-scoped), `apps/api` (19 sqlite-scoped) — plus live-Postgres integration tests
(`engine/tests/integration/`, 3) and live-Postgres security tests
(`engine/tests/security/`, 10). All live-infrastructure tests are `skipif`-gated to skip
(not fail) when the compose Postgres is unreachable; this run had it reachable, so all
129 executed.

Per-package coverage gates (`--cov-fail-under=80`, matching CI's `runtime-suites` job
exactly): see `coverage-report.md` for the full table — all six gated packages pass.

## Neuron Workspace (`neuron/`)

```text
$ uv run ruff check .          -> All checks passed
$ uv run mypy                  -> Success
$ uv run pytest -q --cov=brain_ingestion --cov=brain_extraction --cov=brain_interpretation
                                -> 18 passed, 2 skipped in 24.87s
```

The 2 skips are `test_parse_once_reinterpret.py`'s live-vLLM integration tests
(`pytest.mark.skipif` on endpoint reachability) — no local vLLM server was running for
this specific execution pass. These two tests were executed live and passed during S0003
development (2026-09-09; see `docker/DEPENDENCY-MATRIX.md`'s "ADR-0040 input" section for
the measured extraction results from that run) and are re-verified live again whenever
`docker/local-inference-runbook.md`'s vLLM server is running.

## Experience Workspace (`experience/`) — frontend

```text
$ pnpm exec tsc -b              -> clean
$ pnpm exec eslint .            -> clean
$ pnpm exec vitest run          -> 3 test files, 11 tests passed (900ms)
$ pnpm exec vite build          -> clean, pdf.js worker bundled
```

## CI (GitHub Actions, `main`, run `34554563562`)

| Job | Result |
|---|---|
| product-gates | success |
| runtime-suites | success |
| runtime-stack | success |
| experience | success |
| framework-validators | success |
| kg-reproducibility | success |

## Live-Infrastructure Drills (manual, not part of the pytest suites above)

- **Backup/restore drill** (`scripts/ops/`): 4 consecutive runs, ~3.1s duration each, both
  citations (block-level + page-level) resolved identically every run; a backup with an
  empty content snapshot correctly failed the citation check (exit 1) rather than passing
  silently.
- **Revocation propagation**: measured 12.41ms end to end through the HTTP layer
  (`engine/tests/security/test_revocation_propagation.py`, printed via `-s`).
- **Extension build re-verification**: `\dx` against the running S0002 image confirmed
  `vector 0.8.6`, `age 1.8.0`, `btree_gist 1.8` on `PostgreSQL 18.6`.
- **OIDC discovery timing** (found while diagnosing a CI failure): authentik's Docker
  healthcheck passes at t=35s from a fresh boot; OIDC discovery isn't actually served
  until t=50s. CI's retry loop (added this run) covers the gap.

## Result

PASS
