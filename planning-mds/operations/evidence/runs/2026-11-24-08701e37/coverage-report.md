# Coverage Report — F0009-provenance-and-human-correction-lineage run 2026-11-24-08701e37

Owner: Claude (Opus 5.5) / Quality Engineer. Date: 2026-11-24.

Result: PASS

## Scope

This report covers the changed authored executable code against base `3729dbee528ce27a3a939b24abe5b8efca3aeb9e`: the tracked diff plus untracked engine source, including migration 0016. Tests, generated Pydantic models, schemas and configuration are excluded. The floor is `coverage_min_pct` (80) from `nebula-agents/agents/actions/spec/_contract.yaml`. Coverage was measured over the final full engine run, including the PostgreSQL integration suites ([g2-engine.coverage.json](artifacts/coverage/g2-engine.coverage.json)).

## Coverage target and actual per layer

| Layer | Target | Actual | Source |
|-------|------:|------:|--------|
| Changed executable lines, all layers | 80% | **94.41%** (912/966) | [changed-line-coverage.json](artifacts/coverage/changed-line-coverage.json) |
| brain_provenance package, own unit tests (CI gate) | 80% | 100.00% | [brain-provenance-gate.txt](artifacts/coverage/brain-provenance-gate.txt) |
| brain_domain package, own tests (CI gate) | 80% | 91.11% | same |
| brain_review package, own tests (CI gate) | 80% | 98.73% | same |
| brain_security package, own tests (CI gate) | 80% | 93.09% | same |
| Frontend | n/a | n/a | No experience source changed (generated contract copies only) |
| AI / Neuron | n/a | n/a | No Neuron source changed; shared-bundle callers pass 8/8 |

## Per file (changed executable lines)

| File | Covered / changed |
|---|---|
| brain_api/deps.py | 3/4 |
| brain_api/routes/reviews.py | 30/30 |
| brain_api/schemas/review.py | 5/5 |
| migrations/versions/0016_f0009_provenance_hooks.py | 59/60 |
| brain_domain/provenance.py | 241/257 |
| brain_persistence/lineage_contracts.py | 10/10 |
| brain_persistence/models.py | 2/2 |
| brain_persistence/provenance.py | 382/414 |
| brain_persistence/provenance_models.py | 38/38 |
| brain_persistence/repositories.py | 33/36 |
| brain_provenance/__init__.py, ports.py, service.py | 57/57 |
| brain_review/decisions.py | 32/32 |
| brain_security/execution.py | 20/21 |

The uncovered lines fall into three groups. First, defensive refusals for corrupt or impossible stored states: a missing run or document row behind a present FK, a missing mandatory v2 semantics row, and an ambiguous commit actor. Second, error branches in the domain query parser. Third, the composition-root body of `get_provenance_reader`, which is exercised through the equivalent `qe.provenance` composition instead. None of them is an untested AC path.

## Waivers

None.
