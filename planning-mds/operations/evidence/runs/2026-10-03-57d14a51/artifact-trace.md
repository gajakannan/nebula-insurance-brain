# Artifact Trace — F0003-postgresql-persistence run 2026-10-03-57d14a51

> Required per §8. Captures what was read, written, generated, referenced externally, and explicitly omitted/waived.

## Artifacts Read

- Product architecture: BLUEPRINT, master-blueprint §78, SOLUTION-PATTERNS, feature README/PRD/assembly plan/STATUS/acceptance checklist, GETTING-STARTED, personas, and stories S0001–S0004.
- Prior plan run `2026-09-30-6632006b`: resume summary and fields used to distinguish planning from feature-completion scope.
- Framework routing, action, project-extension, agent-use, evidence-contract, Quality Engineer, and Architect instructions.
- KG lookup for F0003, tier 1, recorded with this run ID. Raw feature artifacts remain authoritative.
- Current hosted CI runtime-suites and runtime-stack results for run `37251703741`, including the persistence package coverage step on PR head `1e9db3381d63c8634b52d8e172ccd36a1e3cdf73`.

## Artifacts Created Or Updated

- Run base files, evidence manifest, G0–G5 reports, G3 role reviews, signoff ledger, and gate state under `planning-mds/operations/evidence/runs/2026-10-03-57d14a51/`.
- `planning-mds/features/F0003-postgresql-persistence/STATUS.md` — QA/DevOps progress, per-story Code Review and Security results, 20 formal role signoffs, and the accepted security follow-up recorded.
- `engine/tests/integration/test_persistence_contract.py` — direct PostgreSQL exclusion-constraint test added for F0003-S0003.
- `artifacts/test-results/f0003-postgres.xml` and `f0003-postgres-run.md` — live PostgreSQL acceptance results and clean upgrade through `0007`.
- `artifacts/test-results/f0003-migration-run-record.md` — operator account, logged timestamps, migration revisions, and outcomes for both migration attempts.
- `code-review-report.md` and `security-review-report.md` — G3 reviews; code review approved after the migration-run record was added, security review passed with recommendations.
- `signoff-ledger.md` — Required=Yes role signoffs and Product Manager acceptance of the non-blocking medium security recommendation.
- `feature-action-execution.md` — G6 pre-closeout candidate summary.
- `kg-reconciliation.md` — G7 Architect reconciliation record and graph validation outcomes.
- `planning-mds/kg-source/bindings/f0003.yaml` and `planning-mds/kg-source/nodes/capabilities/postgresql-persistence-contract.yaml` — stable code-path binding and evidence note.
- Generated graph projections and tracker regions — regenerated only by `scripts/kg/compile.py` from `kg-source/**`.
- `artifacts/test-results/f0003-migration-run-record.md` — operator account, logged timestamps, migration revisions, and outcomes for both migration attempts.
- `artifacts/coverage/f0003-postgres.xml` — line coverage for the focused acceptance selection.
- `artifacts/coverage/brain-persistence-ci-coverage.log` — captured persistence package coverage gate from hosted run `37251703741`, on the current PR head.
- Earlier G2 logs remain in `artifacts/test-results/` to preserve failed/retried command history.

## Generated Evidence

The local PostgreSQL acceptance command passed 12 tests with no skips. A clean disposable PostgreSQL database upgraded through revision `0007`. The same PR head passed the hosted persistence package coverage gate at 87.78%. G3 approved the code review and recorded the Security review's non-blocking recommendation; G4 and G5 passed with the PM acceptance and follow-up owner/date recorded. The focused acceptance command's line-coverage diagnostic is retained as supplemental evidence and is not substituted for the package-level coverage gate.

## External Or Global Evidence References

- Hosted Actions run: https://github.com/gajakannan/nebula-insurance-brain/actions/runs/37251703741 (runtime-suites job `111580493891`; runtime-stack job `111580494061`).
- The implementation depends on accepted F0001 persistence proofs and F0002 ownership contracts as cited by the F0003 planning artifacts. No global frontend evidence lane is used.

## Omissions And Waivers

No waiver is requested. Four conditional security scan outputs are omitted because `security_sensitive_scope=false` and the changed paths do not touch dependencies, secrets/configuration, runtime policy, or deployable endpoints. Their reasons and Product Manager approval are listed in manifest.omissions[] and signoff-ledger.md. Required test and coverage reports cite current-run artifacts. Earlier sandbox-limited attempts remain as history but are superseded by completed local PostgreSQL and hosted package-coverage results.

## Run Environment (conditional)

Required only when `commands.log` carries an absolute `cwd`. One bullet per justified absolute path:

```text
- Absolute cwd: /workspace/some/path — sandboxed CI runner; NEBULA_PRODUCT_ROOT not stable
```
