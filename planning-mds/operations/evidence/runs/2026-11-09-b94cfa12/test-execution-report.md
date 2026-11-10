# Test Execution Report — F0007-factslot-model run 2026-11-09-b94cfa12

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-09 (executions 2026-11-10T01:35Z to 02:20Z)
- Runtime: local Compose `brain-postgres` (PostgreSQL 18.6, pgvector 0.8.6, AGE 1.8.0, btree_gist 1.8), `engine/.venv` (Python 3.14.4, `uv sync --locked`)

## Commands Executed

Every command is in `commands.log` with its artifact path. The final passing executions:

1. **F0007 CI step:** `BRAIN_MIGRATION_ADMIN_URL=… engine/.venv/bin/python -m pytest engine/packages/brain-factslots/tests engine/tests/integration/test_factslot_{migration,resolution,ownership,answers,names}.py engine/tests/integration/test_assertion_migration.py engine/tests/integration/test_job_event_reason_migration.py --cov=brain_factslots --cov-fail-under=80`. This is the same command added to the CI `runtime-stack` job.
2. **Full engine suite:** `artifacts/runtime/owned_regression_db.sh bash -c 'cd engine && .venv/bin/python -m pytest -q --cov=…'`. It runs every engine test (unit, API, integration, security) against a fresh owned database at head, then drops it.
3. **Neuron suite:** `neuron/.venv/bin/python -m pytest -q`. The 41 skips are the live and PostgreSQL lanes, as in the CI `runtime-suites` job.
4. **Static checks:** `ruff check .`, `ruff format --check .` and `mypy` over the CI package list plus `packages/brain-factslots/src`.
5. **Pre-change baseline (G1):** five pilot regression suites.

## Pass/Fail Counts

| Execution | Tests | Passed | Failed | Skipped | Artifact |
|---|---|---|---|---|---|
| F0007 CI step | 148 | 148 | 0 | 0 | `artifacts/test-results/g2-f0007-ci-step.xml` |
| Full engine suite (owned DB) | 816 | 816 | 0 | 0 | `artifacts/test-results/g2-engine-full.xml` |
| Neuron suite | 305 | 264 | 0 | 41 | `artifacts/test-results/g2-neuron-suite.xml` |
| G1 pilot baseline | 27 | 27 | 0 | 0 | `artifacts/test-results/g1-baseline-regression.xml` |
| ruff / format / mypy | — | clean (186 files formatted; mypy 98 files, 0 issues) | 0 | — | `commands.log` |

The F0007-specific tests break down as follows:

- 55 unit and contract tests in `brain-factslots`;
- 67 PostgreSQL acceptance tests: resolution 19, answers 34, names 6, ownership 5, migration 3;
- 26 F0006 migration-drill tests that F0007 touched.

The 14 new domain tests in `brain-domain` run inside the full engine suite.

## Skipped Tests And Rationale

The F0007 and engine executions skipped nothing, because PostgreSQL and `BRAIN_MIGRATION_ADMIN_URL` were available. The neuron suite skipped 41 tests: its live-model and PostgreSQL lanes need `BRAIN_TEST_POSTGRES_URL` and a model service, and F0007 changes no neuron code. The neuron skip count matches the CI `runtime-suites` job.

## Raw Test Artifact Paths

- `artifacts/test-results/g2-f0007-ci-step.xml`, `g2-engine-full.xml`, `g2-neuron-suite.xml`, `g1-baseline-regression.xml`
- Console output per command: `artifacts/test-results/command-output/g2-f0007-ci-step.txt`, `g2-engine-full.txt`, `g2-neuron-suite.txt`, `g2-deployability-static.txt`, `g2-dev-clone-migration.txt`, `g1-baseline-regression.txt`
- `artifacts/coverage/g2-engine-full.{xml,json}`, `artifacts/coverage/changed-code-summary.json`
- `engine/tests/fixtures/factslots/pilot-before.json` (the committed pilot snapshot the migration test compares byte for byte)

## Failed / Retried Command History

All failures below were fixed and their commands re-run; none was waived.

1. **First F0007 resolution run.** `fact_slot.created_at` is a naive timestamp column, and the store passed an aware datetime. Fix: rely on the column's server default. Classified as a code defect and fixed.
2. **Test-authoring errors, fixed in the tests:**
   - The member-overlap check copied a row onto a slot that already held an overlapping version. It was replaced with a direct cross-member overlap query.
   - A unit test resolved under a forced fingerprint, then expected the real fingerprint to find that slot.
   - A migration test asserted `or True`. The vacuous assertion was removed.
   - The pilot seed's workspace disagreed with `protect()`'s derived workspace.
3. **First full engine run: 3 failures.**
   - `test_assertion_migration.py::test_occupied_downgrade_stops_without_erasing_semantics` hard-coded head `0011`. The test now asserts that the head is unchanged after the refused downgrade.
   - `test_job_event_reason_migration.py::test_backup_and_isolated_restore…` was already failing on `main` (a worktree at `ff0a619` reproduced `UndefinedColumn assertion.semantic_contract_version`). The backup inventory `scripts/ops/verify_content.py` selected every mapped column, including columns that later migrations add, so it failed on older revisions. 0012 would have caused the same failure for `fact_slot`. Fix: hash only the columns present at the database's revision; at head the hash is identical.
   - `test_content_restore_v2.py`: connection refused to the test's own temporary server during the parallel full run. It passed alone (4/4) and in the final full run, so it is classified as transient.
4. **DAST.** The first attempt could not reach host loopback from the container. The second attempt scanned a stale server whose database was gone; that output was discarded and the script hardened. The third attempt is the recorded result.

## AC Coverage Result

All 39 ACs map to passing tests or a named review check (`test-plan.md`). S0006 AC5 (RLS inventory, no bypass path) is a documentation and DDL-review item for G3 Security.

## Post-G3 Delta (final code)

The G3 security fixes (SEC-F7-01/02/03) changed `brain_factslots/{service,resolution,answers,ports}.py`, `brain_persistence/fact_slots.py` and `engine/apps/api/src/brain_api/routes/facts.py`, and added two tests. All evidence was re-run on the final code:

| Execution | Tests | Passed | Failed | Skipped | Artifact |
|---|---|---|---|---|---|
| F0007 CI step | 151 | 151 | 0 | 0 | `artifacts/test-results/g3-f0007-ci-step.xml` (`brain_factslots` 98.6%) |
| Full engine suite (owned DB) | 819 | 819 | 0 | 0 | `artifacts/test-results/g3-engine-full.xml` |
| ruff / format / mypy | — | clean | 0 | — | `artifacts/test-results/command-output/g3-static.txt` |

Changed-line coverage on the final code is 99.0% (1211/1223; `artifacts/coverage/changed-code-summary.json` from `g3-engine-full.json`).

## Result

PASS

## Post-Closeout CI Fix (PR #43)

The PR's CI `runtime-stack` job failed in `neuron/tests/integration/test_document_process_recovery.py` (PostgreSQL lanes). Those neuron lanes need `BRAIN_TEST_POSTGRES_URL`, so they were among the 41 neuron tests skipped in this run.

- **Cause:** schemas built from the ORM metadata could not create `fact_slot_qualifier`. Two tests excluded `fact_slot`, and the `FactSlotRow` model did not declare `uq_fact_slot_owner`, the key migration 0005 created, which the qualifier's composite foreign key references.
- **Fix:** declare `uq_fact_slot_owner` on `FactSlotRow` to mirror the database; no DDL change. Exclude `fact_slot_qualifier` together with `fact_slot` in the two neuron tests.
- **Re-run on owned PostgreSQL databases:**
  - neuron `test_worker_cli_enqueue`, `test_document_process_recovery` and `test_document_delivery`: 27/27, 0 skipped (`artifacts/test-results/command-output/pr43-neuron-postgres.txt` for the first two-file run);
  - full engine suite: 819/819. One intermediate run had a single transient failure that did not reproduce in two re-runs.
