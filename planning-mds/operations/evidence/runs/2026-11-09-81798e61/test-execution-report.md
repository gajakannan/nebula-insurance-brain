# Test Execution Report — F0007 remediation

Role: Quality Engineer / Codex primary coordinator. Date: 2026-11-10.

## Commands Executed

Exact commands, timestamps, exit codes and output artifacts are in commands.log. Container composition: artifacts/runtime/compose.yaml. Preflight evidence precedes validation. Current source is mounted read-only into the project's existing engine/neuron images; unchanged third-party dependencies remain image-owned and the current workspace package is exposed through PYTHONPATH.

## Pass/Fail Counts

| Execution | Tests | Passed | Failed/errors | Skipped | Raw artifact |
|---|---:|---:|---:|---:|---|
| Combined domain/application/security + F0007 PostgreSQL | 319 | 319 | 0 | 0 | artifacts/test-results/remediation.xml |
| Full engine including backup/restore | 868 | 868 | 0 | 0 | artifacts/test-results/engine-full-final.xml |
| Affected Neuron PostgreSQL worker/recovery/delivery | 27 | 27 | 0 | 0 | artifacts/test-results/neuron-postgres-final.xml |

The combined319 and migration16 cases are subsets of the full868, not additive unique-test counts. All commands exited0. Static checks: Ruff passes189 files; mypy passes72 sources (artifacts/static-final.txt). New source tests first reproduced12 failing member/numeric cases before fixes; migration red execution failed because0013 was absent, then16 real PostgreSQL cases passed.

## Skipped Tests And Rationale

No tests skipped in the executions above. No unrelated live-model/UI/OIDC flows were claimed. No broad Neuron behavior changed; the three affected PostgreSQL suites were deliberately run rather than inheriting the old41-skip rationale.

## Failed / Retried Command History

- Initial native PostgreSQL migration red test needed network escalation, then failed for the intended missing0013 reason. Original output retained.
- Static runtime setup initially used a login shell that omitted the virtual-environment path, then a read-only cache path. These were corrected without source semantics changes. Final formatting correction shortened the scope helper signature; all final static checks passed.
- First full engine run:865pass/3fail, each backup.sh Docker command missing in the validation image. Classified runtime-blocked; no application fix made. Exposed the existing Docker CLI/socket to the isolated validation runner with its Docker group and dedicated restore network, rechecked Docker/PostgreSQL readiness, reran the full same suite:868pass. Initial failure remains artifacts/engine-full.txt/XML.
- First Neuron runner could not migrate because the Neuron image does not contain Alembic. The engine image now creates/migrates its owned database, and the unchanged Neuron image runs the27 tests against it; all pass, database dropped afterward.
- Dependency-audit tool initially lacked a writable home. Tool/cache paths were moved to container/tmp; final audit reports no known vulnerabilities. SAST exit1 reports two audit flags, independently classified constant-SQL false positives; raw results and reviewer triage are preserved.

## AC Coverage Result

All39 original AC tests/review checks were freshly covered by the engine run and current DDL/security review, augmented by the audit-specific counterexamples. Original incorrect member acceptance assertion now uses the resolved insured value; a separate negative proves mismatch rejects with no commit/version/outbox effects. New coverage is derived from current source and actual raw reports; no waiver.

## Result

PASS


## Explicit In-Progress Run Validation

The pinned framework CLI returns success with validated=0 for nonterminal Active Features, even when --run-id is explicit. We detected this in the summary rather than treating it as run validation. The preserved artifacts/validate_selected_run.py invokes the pinned module's unchanged validate_governed_row with the actual registry row and selected run; no rule is skipped, changed or waived. Both selected-g2-evidence-validation-final.txt and selected-g3-evidence-validation-final.txt report validated=1 with zero errors. The CLI's normal terminal closeout path remains required after final approval/archive. An advisory absolute-cwd warning is retained; command/environment roots are explicitly documented. Framework eligibility behavior is a framework-owned follow-up, not a waived product finding.
