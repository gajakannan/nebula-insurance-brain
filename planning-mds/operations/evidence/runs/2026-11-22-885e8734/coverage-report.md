# Coverage Report — F0011-json-schema-contract-system run 2026-11-22-885e8734

Owner: Claude / Quality Engineer. Date: 2026-11-23.

Scope is the changed authored executable code of this feature against base
`bf78e111934570f83439057ea3c73a1eaefbb022`: tracked diff plus untracked source.
Tests, generated Pydantic models, schema/data resources and non-executable
configuration are excluded. The contract floor is `shared.coverage_min_pct` = 80
from `nebula-agents/agents/actions/spec/_contract.yaml`.

## Coverage Target And Actual Per Layer

| Layer | Target | Actual | Source |
|-------|------:|------:|--------|
| Changed Python (engine packages, API, `scripts/contracts`, Neuron) — changed statements | 80% | 86.4% (1166/1350) | `artifacts/coverage/changed-line-coverage.json` |
| Changed JavaScript (`experience/scripts/contracts/{case-data,check,runtime}.mjs`) — lines | 80% | 98.5% (453/460) | `artifacts/coverage/js-line-coverage.json` |

Per-file Python rows, including missing line numbers and the file hash measured,
are in `changed-line-coverage.json`. No changed file is unmeasured.

## Raw Artifact Paths

- Combined Python data: `artifacts/coverage/combined.coverage`, reported as
  `artifacts/coverage/combined-python.json` and `artifacts/coverage/combined-python.xml`.
- Combined inputs (each recorded after the last change to the source it measures; the G4 Low fixes were re-measured at 2026-11-23 21:34–21:35 -05:00):
  `core.coverage` (full Engine/package/API/tool unit run, 1239 tests),
  `conformance.coverage`, `generation.coverage`, `consumer-closeout.coverage`
  (PostgreSQL consumer integration, 83 tests), `consumer-cli-review-final.coverage`,
  `neuron-smoke.coverage`, `install.coverage`.
- Measurement method: `artifacts/coverage/measure_changed_coverage.py`
  (changed-statement intersection with `git diff --unified=0`; untracked files count in full).
- JavaScript raw V8 data: `artifacts/coverage/js-review-final-v8/` (recorded
  2026-11-23 10:42 -05:00, after the last `.mjs` change at 10:41); summarised by
  `artifacts/coverage/summarize_v8.mjs`, which takes the innermost V8 block range at
  each line's first non-blank character, using the maximum across processes.

## Feature-Scoped Notes

- This refresh supersedes the 2026-11-22 18:56 figure (85.5%, 1102/1289). That
  figure predated the portable-parity remediation (workstate decision 6). The
  per-suite data had already been regenerated on current source, but the combine
  and changed-line measurement had not.
- `scripts/contracts/installed_probe.py` (52 statements) and
  `scripts/contracts/run_installed_probe.py` (35) show 0% because they run only
  inside the isolated installed-distribution container, which has the checkout hidden
  and no coverage tracer. Their behaviour is evidenced by
  `artifacts/install-final/installed-distribution-results.json` (wheel and sdist both pass).
  Coverage still clears the floor even with them counted as uncovered.
- G4 follow-up (2026-11-23): two direct PostgreSQL tests now cover the
  `facts.py` `ValueError/TypeError` → `CONTRACT_MODEL_MISMATCH` translations, for
  commit (with rollback) and read. Two unit tests cover the new 500-handler logging.
  `routes/facts.py` (22/22) and `brain_api/errors.py` (10/10) changed statements are
  now fully covered. The remaining uncovered application lines are bare re-raises
  (`contracts.py:91`, `assertions.py:148`) and an accessor no caller exercises
  (`contracts.py:77`).
- No cross-feature coverage regression: existing F0007/F0008 consumer suites run
  inside `consumer-closeout.coverage` and pass.

## Result

Result: PASS
