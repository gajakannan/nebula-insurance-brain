# Action Context

> Seeded by init-run.py; judgment sections filled at FR0 (2026-11-18).

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain (source: NEBULA_PRODUCT_ROOT environment, resolved by `_product_root.py`)
- **action:** feature-review
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0008
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts
- **feature_slug:** bitemporal-canonical-facts
- **mode:** clean
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-18-a3709ba0
- **run_id:** 2026-11-18-a3709ba0
- **run_id_prior:** 2026-11-17-1a4ae2f0

## Inputs

- **FEATURE_ID:** F0008 (operator)
- **MODE:** closeout-audit (operator). Consistent with PR #55 state `MERGED`.
- **PR_URL:** not supplied. The target was located through `gh pr view 55`: "feat(F0008): bitemporal canonical facts — fact-temporal/v1 contract and migration 0014". Head `feature/F0008-bitemporal-canonical-facts` (4da9f4e), base `main`, squash-merge commit `339c920`.
- **FEATURE_RUN_ID:** 2026-11-17-1a4ae2f0, the default from `features/F0008-bitemporal-canonical-facts/latest-run.json` (`status: approved`). latest-run.json and FEATURE_RUN_ID agree.
- **FEATURE_PATH:** planning-mds/features/archive/F0008-bitemporal-canonical-facts. This matches the manifest's `feature_path_at_closeout`.
- **FEATURE_RUN_FOLDER:** planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0 (read-only)
- **DIFF_RANGE:** `2badb9a..339c920`, i.e. main before the PR to the squash-merge commit. `git diff --quiet 4da9f4e 339c920` shows the PR head tree is identical to the merge commit tree.
- **Changed-file set:** 135 paths. The resolved list is `artifacts/diffs/changed-files.txt` in this run (`git diff --name-only 2badb9a 339c920`). It covers 29 engine/CI paths, 37 planning/KG/tracker paths, and 69 feature-run evidence paths.
- **Changed-set reconciliation against manifest `changed_paths[]` (133 entries):**
  - Three paths are in the diff but missing from the manifest: `planning-mds/knowledge-graph/coverage-report.yaml`, `planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts/latest-run.json`, and `.../runs/2026-11-17-1a4ae2f0/token-usage.json`.
  - One path is in the manifest but missing from the diff and from disk: `.../artifacts/security/sast/sast-semgrep-20261117-052012.sarif`. It belongs to the first SAST attempt, whose log is 0 bytes.
  - All four are recorded as evidence-drift findings in FR1.
- **RUN_DEVOPS:** auto resolves to **yes**. `.github/workflows/ci-gates.yml` changed, migration `0014` was added, and the manifest sets `deployment_config_changed: true` and `runtime_bearing: true`.
- **Framework:** nebula-agents HEAD d90bbb6, which equals the BLUEPRINT pin. The working tree has one uncommitted change, `agents/templates/prompts/evidence-contract/feature-review-operator-friendly.md`. It was not made by this run, and this run neither touches nor relies on it.

## Assumptions

- Review target is the merged `main` state (`339c920`), checked out on the local branch `review/F0008-closeout-audit` so that only this run folder is written.
- No live runtime re-execution (Docker/Postgres) is required for a closeout audit. Raw test/coverage/scan artifacts in the feature run are inspected directly. Code is read at `339c920`. Engine unit tests that need no DB may be re-run as spot checks.

## Scope Boundaries

- Read-only audit of F0008. Nothing is written under the feature run folder, the feature docs, the trackers, the KG, or the code.
- Cross-feature impact (F0001 bindings, F0007 harness, F0018 deferrals) is recorded only.

## Lifecycle Stage

- FR0 diff lock complete; FR1 next.
