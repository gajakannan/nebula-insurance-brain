# Coverage Report — F0008 review remediation run 2026-11-18-bce4909b

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-18
- Floor: the contract `coverage_min_pct` (profile `standard`)

## Coverage Target And Actual Per Layer

| Measure | Actual | Source |
|---|---|---|
| Changed production lines vs `origin/main` 339c920 | **100%** (24 / 24) | `artifacts/coverage/changed-code-summary.txt` |
| `brain_temporal` unit-only (CI gate) | 97.40% | `command-output/ci-nodb-gate-brain_temporal.txt` |
| `brain_api` unit-only (CI gate) | 81.78% | `command-output/ci-nodb-gate-brain_api.txt` |

## Raw Artifact Paths

- `artifacts/coverage/engine-coverage.json` / `.xml`
- `artifacts/coverage/measure_changed_coverage.py`

## Feature-Scoped Notes

Migration `0015` runs under Alembic, so line coverage does not measure it. `test_0015_*` and `test_fr_arch_l2_*` prove its behaviour.

## Result

PASS
