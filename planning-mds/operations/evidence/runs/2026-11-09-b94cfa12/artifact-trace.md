# Artifact Trace — F0007-factslot-model run 2026-11-09-b94cfa12

## Artifacts Read

- `planning-mds/features/F0007-factslot-model/`: PRD, the six stories, the assembly plan, STATUS, GETTING-STARTED, worked examples, `contract-examples.json`
- `planning-mds/architecture/decisions/ADR-0077-factslot-identity-and-typed-answer-carriers.md`
- `planning-mds/schemas/fact-slot-key-v1.schema.json`, `fact-answer-v1.schema.json`, `fact-slot-resolution-result-v1.schema.json`
- `planning-mds/api/brain-api.yaml` (commit 422 contract); `planning-mds/security/policies/policy.csv`
- `planning-mds/BLUEPRINT.md`, `docs/agent-instructions.md` (through `project_context.py`)
- Delivered prerequisite evidence: plan run `2026-11-09-60865e32` (approved A+B); F0006 feature run `2026-11-02-5a00b0ff` (report shapes, harness)
- Engine sources touched or reused: migrations 0003/0005/0006/0007/0011; `brain_persistence` models, repositories, tenancy and assertions; `brain_security.execution`; `brain_temporal.commit`; `brain_api` routes, errors and deps; `brain_testing.fixtures`; the F0006 test harness

## Artifacts Created Or Updated

- **Run folder:** `evidence-manifest.json`, `README.md`, `action-context.md`, `artifact-trace.md`, `gate-decisions.md`, `g0-assembly-plan-validation.md`, `g1-runtime-preflight.md`, `g2-self-review.md`, `test-plan.md`, `test-execution-report.md`, `coverage-report.md`, `deployability-check.md`, `g2-deployability-check.md`, `code-review-report.md`, `security-review-report.md`, `architect-implementation-review.md`, `signoff-ledger.md`, `feature-action-execution.md`
- **Feature folder:** `feature-assembly-plan.md` (G0 reconciliation section); `STATUS.md`; `GETTING-STARTED.md`; `acceptance-criteria-checklist.md`; the six story files (Status)
- **Code, migration, CI and tests:** the 47 paths in `artifacts/diffs/changed-files.txt`, which also include the operator's pre-run Now-lane edits to `ROADMAP.md` and `kg-source/features/F0007.yaml`

## Generated Evidence

- `artifacts/test-results/`: `g1-baseline-regression.xml`, `g2-*.xml`, `g3-*.xml`, `command-output/*.txt` (named files), `g0-migration-lineage.json`, `g4-gate-policy.json`, `g2-prior-hints.txt`
- `artifacts/coverage/`: `g2-engine-full.{xml,json}`, `g3-engine-full.{xml,json}`, `changed-code-summary.json`, `measure_changed_coverage.py`
- `artifacts/security/`: `sast/*.sarif`, `secrets/*.sarif`, `dependency-engine.json`, `engine-requirements.txt`, `dast/api-scan.{json,html}`, `dast/run-dast.sh`, `scan-targets.txt`
- `artifacts/runtime/`: `owned_regression_db.sh`, `dev_clone_migration.sh`

## External Or Global Evidence References

None. F0007 has no frontend scope, so no global frontend lane is cited.

## Omissions And Waivers

- Omitted (non-required): `frontend-developer-report.md` and `ux-audit-report.md` (`frontend_in_scope=false`); `ai-engineer-report.md` (no neuron code, model or prompt change).
- Waivers: none.
