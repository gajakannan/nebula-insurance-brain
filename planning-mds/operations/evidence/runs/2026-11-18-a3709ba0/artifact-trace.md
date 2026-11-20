# Artifact Trace — F0008-bitemporal-canonical-facts review run 2026-11-18-a3709ba0

## Artifacts Read

- Framework:
  - `agents/actions/feature-review.md`
  - `agents/scripts/run-gate.py --list`
  - `project_context.py` output: `BLUEPRINT.md` and `docs/agent-instructions.md`
- Feature index:
  - `planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts/latest-run.json`
- Feature run `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/` (manifest-cited only):
  - `evidence-manifest.json`, `gate-decisions.md`, `signoff-ledger.md`, `pm-closeout.md`, `test-plan.md`, `code-review-report.md`, `security-review-report.md`, `deployability-check.md`, `commands.log`
  - raw `artifacts/test-results/{g1-baseline-regression,g2-full-engine-regression,g3-full-engine-regression}.xml`, `g1-tzdata-versions.txt`, `g4-gate-policy.txt`, `command-output/g2-migration-cycle.txt`
  - raw `artifacts/security/{sast/sast-semgrep-20261117-052326.sarif, secrets/secrets-gitleaks-20261117-052326.sarif, dast/api-scan.json, dependency-engine.json}`
  - `artifacts/diffs/changed-files.txt`
- Feature folder `planning-mds/features/archive/F0008-bitemporal-canonical-facts/`:
  - `STATUS.md`, `acceptance-criteria-checklist.md`, `F0008-S0005-guard-succession-by-start-basis-and-state.md`
- Architecture and contracts:
  - `planning-mds/architecture/decisions/ADR-0078-bitemporal-version-contract-and-close-only-immutability.md`
  - `planning-mds/api/brain-api.yaml` (diff and grep)
- Cross-feature:
  - `planning-mds/features/F0018-canonical-commit-service-and-action-authorization/README.md`
  - `planning-mds/kg-source/features/F0018.yaml`
  - `kg-source/features/F0007.yaml`
  - `ADR-0077` (grep)
- Code at `339c920`:
  - `engine/migrations/versions/0014_f0008_bitemporal_contract.py`
  - `brain_temporal/{bounds,attestation,commit,reader}.py`
  - `brain_domain/temporal.py`, plus the `brain_domain/facts.py` diff
  - `brain_persistence/{models,repositories}.py` diff
  - `brain_api/{routes/facts.py, schemas/facts.py, errors.py}` diff
  - `.github/workflows/ci-gates.yml` diff
  - `engine/tests/integration/test_temporal_immutability.py` (S0004 AC6)
- KG:
  - `planning-mds/knowledge-graph/code-index.yaml` (grep)
  - `planning-mds/kg-source/**` (grep)
- SCM and CI:
  - `gh pr view 55`
  - `gh pr checks 55`
  - `gh run view 44445935719 --log` (F0008 step)
  - `gh run view 44449326859` (main)

## Artifacts Created Or Updated

This run folder is the only write location.

- `action-context.md` (FR0), `feature-review-report.md`, `README.md`, `artifact-trace.md`, `gate-decisions.md`: created or filled.
- `commands.log`, `lifecycle-gates.log`, `gate-state.json`: appended by the operator session and by `run-gate.py`.
- Local branch `review/F0008-closeout-audit` in nebula-insurance-brain, cut from `origin/main` (`339c920`) to hold this run folder.

## Generated Evidence

- `artifacts/diffs/changed-files.txt`: `git diff --name-only 2badb9a 339c920`, 135 paths.
- `artifacts/diffs/fr2-story-index-currency.diff`: 0 lines. `generate-story-index.py` was run against a scratch copy of `planning-mds/features`, and the product file was not touched.
- `artifacts/test-results/fr1-unit-spot-check.xml`: 107 passed.
- `artifacts/test-results/fr1-ci-step-rerun.xml` and `fr1-ci-step-rerun.txt`: 234 passed, `brain_temporal` 97.99%. The run used owned PostgreSQL databases on local `brain-postgres`, which the tests create and drop.
- `artifacts/test-results/fr1-pr55-ci-f0008-step-excerpt.txt`: PR CI step log excerpt.
- `artifacts/test-results/fr2-validate-feature-evidence-closeout.txt` and `fr2-validate-trackers.txt`.
- `artifacts/test-results/fr4-gate-policy.txt`.

## External Or Global Evidence References

- GitHub Actions run `44445935719` (PR #55, CI Gates): success.
- GitHub Actions run `44449326859` (main push, `339c920`): success.

## Omissions And Waivers

- There is no `evidence-manifest.json`, because feature-review is not feature-bound.
- These artifact subdirectories are empty by design: `artifacts/coverage/`, `artifacts/security/`, `artifacts/screenshots/`. Coverage and scans were verified against the feature run's raw artifacts and the CI re-run console. The scope has no UI.
- Full engine regression was not re-run (1081 tests). The F0008 CI step and the post-merge main CI cover the merged tree.

## Run Environment (conditional)

- Absolute cwd: none. `commands.log` cwd values are repo labels (`nebula-agents` / `nebula-insurance-brain`).
- Exception: `run-gate.py` wrote the literal placeholder `{NEBULA_PRODUCT_ROOT}` for product-cwd ops. This is recorded as FR-X-I1.
