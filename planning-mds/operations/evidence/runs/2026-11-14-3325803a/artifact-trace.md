# Artifact Trace — F0064-repository-instructions-and-planning-check-adoption run 2026-11-14-3325803a

## Artifacts Read

- `planning-mds/features/F0064-repository-instructions-and-planning-check-adoption/` — README, STATUS, PRD, GETTING-STARTED, feature-assembly-plan, S0001–S0004
- `planning-mds/BLUEPRINT.md` (section 0 pin), `docs/agent-instructions.md`, `docs/plan-review-checklist.md`, `.nebula-project.yaml`
- `scripts/validation/validate_plan_readiness.py`, `scripts/validation/tests/test_plan_readiness.py`, `scripts/kg/validate_plan_compliance.py`
- `.github/workflows/ci-gates.yml` (`framework-validators`), `CONTRIBUTING.md`, `nebula.code-workspace`, `docs/framework-adoption.md`, `planning-mds/framework-adoption-plan.md`
- Framework at `d90bbb6`: `agents/actions/feature.md`, `agents/scripts/project_checks.py` (input matching), `agents/product-manager/scripts/validate-feature-evidence.py` (artifact contract)
- Model evidence: `runs/2026-11-09-81798e61/` (F0007 approved feature run)
- KG: `scripts/kg/lookup.py F0064 --tier 2`, `lookup.py capability:project-check-ci-enforcement`, `hint.py` on the three doc targets

## Artifacts Created Or Updated

- Run folder: `evidence-manifest.json`, `README.md`, `action-context.md`, `artifact-trace.md`, `gate-decisions.md`, `g0-assembly-plan-validation.md`, `g1-runtime-preflight.md`, `g2-self-review.md`, `test-plan.md`, `test-execution-report.md`, `coverage-report.md`, `deployability-check.md`, `g2-deployability-check.md`, plus later-gate reports as each gate runs
- Source (doc repairs): `docs/framework-adoption.md`, `planning-mds/framework-adoption-plan.md`, `CONTRIBUTING.md`
- Feature trackers: F0064 `STATUS.md` (Story × Role Progress, story status), `README.md` story table, S0001–S0004 status lines
- Generated: `planning-mds/knowledge-graph/coverage-report.yaml` (freshness after the doc edits)

## Generated Evidence

- `artifacts/test-results/` — S0001 (`s0001-*`), S0002 (`s0002-*`), S0003 (`s0003-*`, including AC7 tree hashes), S0004 (`s0004-*`, including `s0004-ac3-copy-run/` from the executor run on the broken copy), `g1-preflight.txt`, `tree-hash.py`, the post-edit and pre-commit validator outputs, and the `hint.py` output
- `artifacts/coverage/` — combined (88.36%: 83.87% branch, 90.55% statement) and fixture-only (68% combined) coverage of `validate_plan_readiness.py`, with the reproducible script
- `artifacts/diffs/changed-files.txt`, `artifacts/diffs/doc-repairs.diff`
- `artifacts/gates/` — `run-gate.py` output per stage
- CI: PR #49 checks (S0004 AC4), URL recorded in `test-execution-report.md`

## External Or Global Evidence References

None. No global frontend or UX lane applies, since there is no UI scope.

## Omissions And Waivers

Mirrors manifest `omissions[]`:
- `frontend-developer-report.md`, `ux-audit-report.md` — no UI scope.
- `backend-developer-report.md` — no `engine/**` runtime code.
- `ai-engineer-report.md` — no `neuron/**`, prompt, model or MCP change.
- `security-review-report.md` — Security Reviewer not required (STATUS.md, Phase B); `security_sensitive_scope=false`. Security scans are recorded as not run, each with a reasoned waiver.

No coverage or validator-defect waiver.

## Run Environment (conditional)

Not required: every `commands.log` entry uses the stable labels `{NEBULA_PRODUCT_ROOT}` or `nebula-agents`. Negative-case copies live in the session scratchpad, and only their outputs were copied into `artifacts/`.
