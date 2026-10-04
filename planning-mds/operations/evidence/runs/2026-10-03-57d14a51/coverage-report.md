# Coverage Report — F0003-postgresql-persistence run 2026-10-03-57d14a51

## Coverage Target And Actual Per Layer

| Layer | Target | Actual | Source |
|---|---:|---:|---|
| Engine persistence unit | Contract floor | Not measured | No run-scoped coverage artifact produced |
| PostgreSQL integration | Contract floor | Not measured | Integration run did not complete |

## Raw Artifact Paths

No current-run coverage artifact exists. The repository's existing `engine/.coverage` predates this run and is not cited as feature evidence.

## Feature-Scoped Notes

The database-independent contract tests passed, but that run did not collect coverage. The required live PostgreSQL integration and migration lanes could not finish because this sandbox denies host socket creation and Docker API access. This report records the missing measurement; it does not request or imply a coverage waiver.

## Result

Result: FAIL
