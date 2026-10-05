# Artifact Trace — F0003-postgresql-persistence run 2026-10-03-57d14a51

> Required per §8. Captures what was read, written, generated, referenced externally, and explicitly omitted/waived.

## Artifacts Read

- `planning-mds/BLUEPRINT.md` and `planning-mds/architecture/SOLUTION-PATTERNS.md`
- `planning-mds/architecture/master-blueprint.md` (§78 inventory)
- `planning-mds/features/F0003-postgresql-persistence/README.md`
- `planning-mds/features/F0003-postgresql-persistence/PRD.md`
- `planning-mds/features/F0003-postgresql-persistence/feature-assembly-plan.md`
- `planning-mds/features/F0003-postgresql-persistence/STATUS.md`
- `planning-mds/features/F0003-postgresql-persistence/acceptance-criteria-checklist.md`
- `planning-mds/features/F0003-postgresql-persistence/GETTING-STARTED.md`, `personas.md`, and stories S0001–S0004
- `planning-mds/operations/evidence/README.md` and this run's initialized base files and manifest
- Prior plan run `2026-09-30-6632006b`: `resume-brief.py` summary and the single `run_scope`/status fields needed to distinguish base-run-only from feature-completion scope; no feature evidence was reused.
- Framework routing, action, project-extension, agent-use, evidence-contract, and Architect skill instructions.
- KG lookup result for F0003, tier 1, recorded with this run ID. Raw feature artifacts remain authoritative.

## Artifacts Created Or Updated

- `planning-mds/operations/evidence/runs/2026-10-03-57d14a51/README.md` — initialized with current draft state
- `planning-mds/operations/evidence/runs/2026-10-03-57d14a51/action-context.md` — run inputs and scope
- `planning-mds/operations/evidence/runs/2026-10-03-57d14a51/artifact-trace.md` — this trace
- `planning-mds/operations/evidence/runs/2026-10-03-57d14a51/gate-decisions.md` — initialized for this run
- `planning-mds/operations/evidence/runs/2026-10-03-57d14a51/evidence-manifest.json` — initialized by `init-run.py`
- `planning-mds/operations/evidence/runs/2026-10-03-57d14a51/evidence-manifest.json` — G0 recorded PASS; status advanced to `in-progress`
- `planning-mds/operations/evidence/runs/2026-10-03-57d14a51/gate-decisions.md` — Architect G0 decision recorded
- `planning-mds/features/F0003-postgresql-persistence/STATUS.md` — Story × Role Progress matrix to be initialized at G0
- `planning-mds/operations/evidence/runs/2026-10-03-57d14a51/g0-assembly-plan-validation.md` — Architect assembly-plan review
- `planning-mds/operations/evidence/runs/2026-10-03-57d14a51/g1-runtime-preflight.md` — DevOps runtime preflight
- `planning-mds/operations/evidence/runs/2026-10-03-57d14a51/g2-self-review.md`, `test-plan.md`, `test-execution-report.md`, `coverage-report.md`, `g2-deployability-check.md`, and `deployability-check.md` — G2 quality and deployability evidence
- `engine/tests/integration/test_persistence_contract.py` — direct PostgreSQL exclusion-constraint test added for F0003-S0003
- `artifacts/test-results/g2-contract.log`, `g2-persistence-contract.log`, `g2-persistence-integration.log`, `g2-uv-offline.log`, `g2-environment-blocker.md`, `g2-validator.log`, and `g2-diagnostic.json` — G2 test outputs, validator result, and environment limitation record

## Generated Evidence

The contract test run passed 15 tests. PostgreSQL integration attempts did not complete; command outcomes and environment restrictions are recorded in the G2 reports and `commands.log`. The G2 gate returned exit 1, consistent with the failing QE verdicts. No current-run coverage artifact was produced.

## External Or Global Evidence References

The implementation depends on accepted F0001 persistence proofs and F0002 ownership contracts as cited by the F0003 planning artifacts. Existing F0001/F0002 tests were inspected as source but were not treated as run evidence. No global frontend evidence lane is used.

## Omissions And Waivers

No waiver is requested. The required coverage report exists and records that current-run coverage was not measured; a stale repository `.coverage` file is intentionally not used. Mirror any later manifest entries here; only non-required artifacts may be omitted.

## Run Environment (conditional)

Required only when `commands.log` carries an absolute `cwd`. One bullet per justified absolute path:

```text
- Absolute cwd: /workspace/some/path — sandboxed CI runner; NEBULA_PRODUCT_ROOT not stable
```
