# Coverage Report — F0008-bitemporal-canonical-facts run 2026-11-17-1a4ae2f0

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-18
- Floor: the contract `coverage_min_pct` (profile `standard`)

## Coverage Target And Actual Per Layer

| Layer / measure | Actual | Source |
|---|---|---|
| Changed production lines (new files and modified hunks, engine `src/`), final code after the G3 fixes | **98.0%** (695 / 709) | `artifacts/coverage/changed-code-summary.txt` from `g3-engine-coverage.json`; G2 measured 97.5% (691 / 709) |
| `brain_temporal`, full run | 98.0% | `artifacts/coverage/g3-engine-coverage.json` |
| `brain_temporal`, unit tests only (CI no-DB gate) | 97.4% | `commands.log` |
| `brain_domain`, full run | 99.6% | same |
| `brain_persistence`, full run | 93.8% | same |
| `brain_api`, full run / CI no-DB gate | 97.3% / 82.3% | same / `commands.log` |
| `brain_factslots`, full run | 98.6% | same |

Uncovered changed lines are defensive branches:

- `bounds.py`:
  - 46–47: a zone in the allowlist that `ZoneInfo` cannot load;
  - 151/180: a `datetime` passed as an instant, and an unreachable granularity default;
  - 240–246, 271: duplicate and non-list `ending_evidence_refs`, and a non-mapping echo. These are covered by the unit run.
- `routes/facts.py` 280–281: a non-list `ending_evidence_refs` passed to the route helper.
- `schemas/facts.py` 43: `valid_to` sent alongside `temporal`.
- `facts.py` 92: a legacy `FactVersion` with a finite upper bound reading as `BOUNDED`. This is covered by the migration test through the repository, but the line is attributed to another process.
- `temporal.py` 97: a naive bound instant constructed directly.

## Raw Artifact Paths

- `artifacts/coverage/g3-engine-coverage.json` / `.xml`: the final full run.
- `artifacts/coverage/g2-engine-coverage.json` / `.xml`: the run before the G3 fixes.
- `artifacts/coverage/changed-code-summary.txt`, produced by `artifacts/coverage/measure_changed_coverage.py` against base `origin/main` (2badb9a).

## Feature-Scoped Notes

Migration `0014` runs under Alembic, so line coverage does not measure it. The migration, immutability and v1-commit suites prove its behaviour:

- upgrade, downgrade and re-upgrade;
- preflight refusal and downgrade refusal;
- every CHECK class;
- each of the six triggers (insert guard, close-only, no-delete, no-truncate, change append-only, change no-truncate).

## Result

PASS
