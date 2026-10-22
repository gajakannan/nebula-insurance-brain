# Coverage Report — F0004 run 2026-10-17-8a6cc79f

Owner: Codex, Quality Engineer role. Refreshed after G3 corrections, 2026-10-20.

## Coverage Target And Actual Per Layer

| Changed Python runtime layer | Target | Covered / statements | Actual |
|---|---:|---:|---:|
| Engine, including migration wrapper | 80% | 1683 / 1830 | 91.97% |
| Neuron, including operator CLI | 80% | 504 / 569 | 88.58% |
| Local operations Python | 80% | 184 / 218 | 84.40% |
| Combined changed runtime | 80% | 2371 / 2617 | 90.60% |

## Raw Artifact Paths

- artifacts/coverage/changed-runtime.json — per-file changed statement coverage.
- artifacts/coverage/changed-lines.json — tracked HEAD diff plus untracked runtime lines.
- artifacts/coverage/combined.json and combined.xml — combined executed statements.
- the current engine, neuron, restore, migrations and integritycli JSON reports — measured lane sources.
- artifacts/test-results/g3-current-coverage-threshold.txt — threshold exit 0.
- artifacts/runtime/changed-coverage.py — reproducible denominator calculation.

## Feature-Scoped Notes

The denominator includes 44 changed Python runtime files. Changed executable
statements come from coverage's Python parser, intersected with git diff HEAD
and every untracked runtime file. Unmeasured statements count as misses; none
of these files is unmeasured. Existing unchanged declarations and unrelated
outbox_projector code do not inflate the changed-runtime percentage.

The raw engine/neuron lane totals differ because each intentionally includes
common modules also executed in another job. Combining those lanes avoids
misreporting date services as untested merely because neuron does not call them.
Engine, neuron, restore and operator CLI measurements were rerun after the G3
source corrections; the denominator was regenerated from the current diff.
The table-index case is now included in the full engine lane, so its earlier
source map is excluded rather than combined after source line shifts.
Subprocess coverage captures the actual backup/restore verifier processes.
The unchanged migration-specific measurement covers the dynamically loaded
revision wrapper. Fresh source maps and original raw failures remain retained.

The frozen SQL revision and Bash scripts are not Python statement coverage.
Actual PostgreSQL upgrade/downgrade/constraint/fault cases and actual
pg_dump/pg_restore plus inventory/citation checks validate those surfaces.
Tests and run-only tooling are not runtime denominator files.

## Waiver Block

None. Every measured changed-runtime layer exceeds the required floor.

## Result

PASS
