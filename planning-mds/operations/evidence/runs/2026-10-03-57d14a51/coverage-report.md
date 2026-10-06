# Coverage Report — F0003-postgresql-persistence run 2026-10-03-57d14a51

## Coverage Target And Actual Per Layer

| Layer | Target | Actual | Source |
|---|---|---:|---|
| Persistence business logic (brain_persistence) | Contract coverage_min_pct | 87.78% — PASS | See raw coverage artifact list below |
| PostgreSQL acceptance lane | Feature acceptance criteria verified by live database behavior; line coverage is supplementary | 12/12 tests passed; focused-run line coverage diagnostic: 79% | See raw coverage artifact list below |

## Raw Artifact Paths

- artifacts/coverage/brain-persistence-ci-coverage.log
- artifacts/coverage/f0003-postgres.xml
- artifacts/test-results/f0003-postgres.xml

## Feature-Scoped Notes

The persistence package suite is the line-coverage gate for the business-logic package and passed in CI on this run's PR head. The 79% value is from the narrower PostgreSQL acceptance selection run by itself; it is retained as a diagnostic, while acceptance of that lane is measured by its 12 passing live-database cases. No implementation source files changed in this feature run. The earlier missing measurement is superseded by these current, artifact-backed results. No coverage waiver is requested.

## Result

Result: PASS

