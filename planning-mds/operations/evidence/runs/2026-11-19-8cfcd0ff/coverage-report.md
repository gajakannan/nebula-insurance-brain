# Coverage Report — F0008 second remediation run 2026-11-19-8cfcd0ff

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-19
- Floor: the contract `coverage_min_pct` (profile `standard`)

## Coverage Target And Actual Per Layer

| Measure | Actual | Source |
|---|---|---|
| Changed production lines vs `origin/main` e024cd7 | **97.96%** (48 / 49) | `artifacts/coverage/changed-code-summary.txt` |
| CI no-DB gates | `brain_temporal` 97.44%; `brain_api` 82.78% | `command-output/ci-nodb-gate-*.txt` |

The one uncovered line is `repositories.py:645`, the `continue` that skips a current version starting at or after a BOUNDED window's end. It is a conservative skip, and the other window edge is covered.

## Raw Artifact Paths

- `artifacts/coverage/final-engine-coverage.json` / `.xml`
- `artifacts/coverage/measure_changed_coverage.py`

## Result

PASS
