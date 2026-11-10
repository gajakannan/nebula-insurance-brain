# Coverage Report — F0007-factslot-model run 2026-11-09-b94cfa12

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-09
- Floor: the contract `coverage_min_pct` (profile `standard`)

## Coverage Target And Actual Per Layer

| Layer / measure | Actual | Source |
|---|---|---|
| Changed production lines (new files + modified hunks, engine `src/`), final code after G3 fixes | **99.0%** (1211 / 1223) | `artifacts/coverage/changed-code-summary.json` (from `g3-engine-full.json`; the G2 measurement was 98.9%, 1174 / 1187) |
| `brain_factslots` (unit + PostgreSQL suites, the new CI gate) | 98.6% (G2: 98.25%) | `artifacts/test-results/command-output/g3-f0007-ci-step.txt` |
| `brain_factslots` (unit tests alone, the runtime-suites gate) | 87% | unit run in `commands.log` |
| `brain_domain` package gate | 92% (new modules 99%) | full engine run |
| Full engine run, selected packages (factslots, domain, persistence, temporal, api, testing) | 96% | `artifacts/coverage/g3-engine-full.xml` |

Uncovered changed lines are listed per file in `changed-code-summary.json`. They are defensive branches:

- `fact_values.py` 126, 152, 361: JCS non-int scalar, `InvalidOperation` and date fallbacks;
- `fact_answers.py` 168: a non-string block ID;
- `answers.py` 88-89: a predicate key that the registry cannot parse;
- `service.py` 64, 82, 118-119: the empty source list, the mixed-owner guard, and missing-slot handling in `read_answer`;
- `fact_slots.py` 119: a missing source access row;
- `brain_testing/factslots.py` 151: the empty-KB guard.

## Raw Artifact Paths

- `artifacts/coverage/g3-engine-full.json` / `.xml` (final owned-DB full run); `g2-engine-full.*` (pre-fix run)
- `artifacts/coverage/changed-code-summary.json`, produced by `artifacts/coverage/measure_changed_coverage.py` against base `ff0a619`

## Feature-Scoped Notes

- Migration `0012` runs under Alembic, so line coverage does not measure it. Its behaviour is proven by the migration and ownership suites: upgrade, downgrade, re-upgrade, refusal, every constraint and every trigger.
- `scripts/ops/verify_content.py` runs as a subprocess of the backup drill and is outside line coverage. The drill passes at revision 0009 and at head.

## Result

PASS
