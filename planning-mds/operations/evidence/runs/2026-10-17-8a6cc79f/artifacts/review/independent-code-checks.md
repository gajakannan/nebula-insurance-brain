# Independent Code Reviewer checks — 2026-10-20

Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`.
All application execution used the run-scoped Compose application jobs. These
checks are supplemental review evidence, not another feature run.

## Original date-read counterexample

Command (exit 0 means the counterexample was reproduced):

```text
docker compose -f planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/artifacts/runtime/compose.yaml exec -T -e PYTHONDONTWRITEBYTECODE=1 engine-validation python /app/brain/planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/artifacts/review/date_read_race_probe.py
```

Actual PostgreSQL 0001→0008 migration, authority/audit and controlled human
verifiers were used in a uniquely named disposable database. Result is retained
in `date-read-race-result.json`: the concurrent selection committed; its candidate
was absent from the returned candidate set; `selected_date=null`; a stable reread
returned `2025-03-01`. The database was dropped by the fixture's finalizer. This
is historical pre-remediation evidence. The original probe intentionally expects
the defective behavior and is not a current acceptance test.

## Current pure contracts / table / asset / geometry checks

```text
docker compose -f planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/artifacts/runtime/compose.yaml exec -T -e PYTHONDONTWRITEBYTECODE=1 engine-validation python -m pytest -q -p no:cacheprovider --basetemp=/app/brain/planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/artifacts/review/content-unit-temp /app/brain/engine/packages/brain-content/tests/test_versioned_content.py /app/brain/engine/packages/brain-content/tests/test_document_dates.py
```

Exit 0: **54 passed in 0.72s**. Includes table bounds/overlap/header/reference/
continuation-cycle rejection, exact retained bytes, native resource closure,
symlink/extra-file rejection, Unicode/multi-region/unavailable geometry,
schema/model parity, date precision, exact-line basis and default-deny verifiers.

## Current PostgreSQL correction and durable table checks

```text
docker compose -f planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/artifacts/runtime/compose.yaml exec -T -e PYTHONDONTWRITEBYTECODE=1 -e BRAIN_MIGRATION_ADMIN_URL=postgresql://brain:brain@postgres:5432/brain engine-validation python -m pytest -q -p no:cacheprovider --basetemp=/app/brain/planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/artifacts/review/date-regression-temp /app/brain/engine/tests/integration/test_content_migration_states.py::test_date_read_keeps_selected_candidate_consistent_during_concurrent_write /app/brain/engine/tests/integration/test_content_migration_states.py::test_durable_table_cells_headers_and_continuations_round_trip
```

Exit 0: **2 passed, 2 warnings in 3.03s**. Warnings concern Alembic's existing
`path_separator` configuration. The date regression starts a real writer after
the candidate query and observes `pg_blocking_pids` at its `FOR UPDATE`, then
checks the old coherent read, writer completion after audit commit, and a later
coherent new read. The table regression verifies reopen/exact retry, retained
ordinals/hashes, headers/continuation/cell links, cross-owner FK denial and
missing-link rejection. Each test owns and drops a fresh database.

## Framework / routing checks

`check-code-quality.py` on `brain-content/src/brain_content`: no TODO/FIXME,
no file over 500KB; seven line-length advisories occur only in exact packaged
JSON schema copies. No source-style finding is inferred from schema descriptions.

`validate-trackers.py --product-root <product> --skip-feature-evidence`: PASS,
zero errors/warnings. The explicit skip prevents prematurely invoking G6 during
G3; it does not assert feature evidence completion.

`review_routing_checks.py` retains `kg-diff-impact.json`, per-node risk JSON,
define lookups and `routing-summary.json`. All risk commands executed read-only.
Tracked HEAD diff resolves six existing capabilities; new untracked runtime
surfaces are included through the canonical changed-file list and manual review.
Zero scores for new planning nodes reflect absent runtime signals, not safety
proof. G7 binding/symbol/decision regeneration is still pending.
