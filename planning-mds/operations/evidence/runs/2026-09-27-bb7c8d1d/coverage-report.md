# Coverage Report — F0002 run 2026-09-27-bb7c8d1d

**Owner:** Quality Engineer
**Floor:** `coverage_min_pct` from the framework contract (80%), plus the product's per-package CI gates (≥ 80%).

## Changed-kernel line coverage (cycle 2, full engine suite, PostgreSQL enabled)

| Module | Statements | Covered |
|---|---|---|
| brain_domain/authx.py | 338 | 100.0% |
| brain_domain/tenancy.py | 63 | 100.0% |
| brain_domain/audit.py | 22 | 100.0% |
| brain_security/evaluation.py | 135 | 98.5% |
| brain_security/execution.py | 158 | 98.7% |
| brain_security/identity_profile.py | 52 | 98.1% |
| brain_security/delegation.py | 25 | 96.0% |
| brain_security/verification.py | 93 | 88.2% |
| brain_security/principals.py | 23 | 100.0% |
| brain_security/casbin_adapter.py | 38 | 100.0% |
| brain_security/audit.py | 15 | 86.7% |
| brain_persistence/authx.py | 120 | 95.8% |
| brain_persistence/tenancy.py | 144 | 95.1% |
| brain_persistence/grants.py | 99 | 99.0% |
| brain_persistence/identity.py | 95 | 96.8% |
| brain_persistence/models.py | 319 | 100.0% |
| brain_persistence/repositories.py | 139 | 96.4% |
| brain_api/deps.py | 94 | 89.4% |
| brain_api/errors.py | 62 | 100.0% |
| brain_api/routes/content.py | 36 | 86.1% |
| brain_api/routes/facts.py | 51 | 96.1% |
| brain_api/routes/reviews.py | 65 | 93.8% |
| brain_temporal/commit.py | 53 | 100.0% |
| brain_jobs/queue.py | 145 | 92.4% |
| brain_worker/document_delivery.py | 132 | 40.9% engine-only / 89% from the neuron suite that drives it |
| **Changed kernel total** | **2516** | **94.04% (2366 lines)** |

Cycle 1 measured 93.74% over 2621 lines. The difference is the synthetic fixtures moving to the dev-only `brain-testing` package, plus the shared `decide` orchestration. The engine-wide total across the measured packages is 94%. The worker adapter is exercised by the neuron integration suite (delivery, recovery, CLI enqueue), which reports `brain_worker/document_delivery.py` at 89% and `brain_ingestion/worker_cli.py` at 69%.

## CI-equivalent per-package gates (each package's own tests only)

| Package | Coverage | Gate |
|---|---|---|
| brain_api | 91.04% | pass |
| brain_content | 96.21% | pass |
| brain_persistence | 87.78% | pass |
| brain_domain | 98.78% | pass |
| brain_security | 92.95% | pass |
| brain_review | 99.21% | pass |
| brain_temporal | 99.01% | pass |
| brain_jobs | 92.41% | pass (PostgreSQL proofs included) |

Coverage percentage never substitutes for negative-case outcomes. All scoped negative cases pass (test-execution-report.md).

## Evidence artifacts

artifacts/coverage/g3r-engine-coverage.json
artifacts/coverage/g3r-engine-coverage.xml
artifacts/coverage/g3r-package-coverage-gates.txt
artifacts/test-results/g3r-neuron-pytest.txt

Cycle 1:

artifacts/coverage/g2-engine-coverage.json
artifacts/coverage/g2-engine-coverage.xml
artifacts/coverage/g2-package-coverage-gates.txt
artifacts/test-results/g2-neuron-pytest.txt

Result: PASS
