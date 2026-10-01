# Artifact Trace — F0002 run 2026-09-27-bb7c8d1d

## Artifacts Read

- `planning-mds/BLUEPRINT.md`, `docs/agent-instructions.md` (via `project_context.py --action feature`)
- `planning-mds/features/F0002-tenancy-aware-domain-kernel-and-principal-contracts/`: PRD.md, README.md, STATUS.md, GETTING-STARTED.md, feature-assembly-plan.md, acceptance-criteria-checklist.md, worked-examples.md, contract-examples.json, six story files
- `planning-mds/architecture/decisions/ADR-0061-tenant-identity-and-structural-ownership.md`, `ADR-0062-current-authorization-and-durable-decisions.md`
- `planning-mds/schemas/authx-kernel.schema.json`, `planning-mds/security/policies/{model.conf,policy.csv}`, `planning-mds/architecture/SOLUTION-PATTERNS.md`
- `planning-mds/operations/evidence/runs/2026-09-25-3c64470a/` (plan run manifest and gate decisions) and `runs/2026-09-12-855d2b93/` (F0001 approved run: scan precedent)
- Existing engine/neuron code for every file in the assembly plan's "Existing code and concrete gaps" table
- KG lookup `scripts/kg/lookup.py F0002 --tier 1`; `scripts/kg/hint.py` on the edited runtime paths

## Artifacts Created Or Updated

- `evidence-manifest.json`: created by init-run; updated at G0 (required roles), G1 (status in-progress, scope booleans, runtime preflight, baseline scans), and G2
- `action-context.md`, `g0-assembly-plan-validation.md`, `g1-runtime-preflight.md`, `g2-self-review.md`, `test-plan.md`, `test-execution-report.md`, `coverage-report.md`, `deployability-check.md`, `gate-decisions.md`, `README.md`, `workstate.yaml`
- Feature folder: `STATUS.md` (progress matrix, Required Role Matrix, checklists), `GETTING-STARTED.md` (implemented files, runbook, verification)
- Runtime and code: see `artifacts/diffs/changed-files.txt` (engine, neuron worker CLI, scripts/dev, config)

## Generated Evidence

- artifacts/test-results/ (G1 preflight and baseline; G2 engine/neuron suites, JUnit, static gates, latency, migration, restore drill, round trip, reconciliation, lock check)
- artifacts/coverage/ (engine coverage JSON/XML, per-package gate output)
- artifacts/security/ (G1 baseline and G2 gitleaks, semgrep, pip-audit, ZAP reports and logs)
- artifacts/diffs/changed-files.txt

## External Or Global Evidence References

- None. No frontend scope, so the global frontend lanes do not apply.

## Omissions And Waivers

- None. No required artifact is omitted, and every scan class ran.
