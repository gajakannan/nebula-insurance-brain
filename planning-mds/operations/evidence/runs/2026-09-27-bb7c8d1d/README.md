# Feature Evidence README — F0002-tenancy-aware-domain-kernel-and-principal-contracts run 2026-09-27-bb7c8d1d

## Run Summary

The `feature` action for F0002 (Tenancy-aware domain kernel + verified stable principal and scope contracts) ran from the nebula-agents framework (main dde49dc) against product root nebula-insurance-brain, on branch `feature/F0002-tenancy-kernel` off origin/main 2024fc0. The run implements the approved Phase B assembly plan: structural ownership registries with composite constraints (migrations 0005/0006 and a reviewed reconciliation script), verified stable principal aliases, a pure conjunctive evaluator over complete grant slices with trusted resource hydration, bounded delegation, a transaction-aware execution facade with durable decision audit, and integration through every existing consumer (content, fact, review, commit, F0005 worker).

## Status

`in-progress`. The run is at G2 (self-review, QE, and deployability). This matches `evidence-manifest.json` `status`.

## Evidence Index

- `evidence-manifest.json`: schema v1
- `action-context.md`, `artifact-trace.md`, `gate-decisions.md`, `commands.log`, `lifecycle-gates.log`, `workstate.yaml` (recorded design decisions #0–#6)
- `g0-assembly-plan-validation.md` (Architect), `g1-runtime-preflight.md` (DevOps)
- `g2-self-review.md`, `test-plan.md`, `test-execution-report.md`, `coverage-report.md` (QE), `deployability-check.md` (DevOps)
- `artifacts/test-results/`: suite outputs, JUnit, latency sample, migration/restore/reconcile outputs
- `artifacts/coverage/`: coverage JSON/XML and per-package gates
- `artifacts/security/`: G1 baseline and G2 scans (gitleaks, semgrep, pip-audit, ZAP)

## Validation Summary

| Gate | Validator | Exit | Notes |
|---|---|---|---|
| G0 | validate-feature-evidence --stage G0 (via run-gate) | 0 | first attempt failed on the missing scm diff artifact; fixed by writing `artifacts/diffs/changed-files.txt` |
| G1 | validate-feature-evidence --stage G1 (via run-gate) | 0 | first attempt failed `security_scan_unwaived_skip_fails` because `security_sensitive_scope` was set early; resolved by running all four scan classes as a pre-change baseline |
| G2 | validate-feature-evidence --stage G2 (via run-gate) | see lifecycle-gates.log | |

Every validator run reports `validated=1`, so the deep check runs (F0002's registry section is Planned, not Active; the F0003 silent-skip finding does not apply).

## Open Follow-ups

- **Framework: deployability filename mismatch.** `feature.yaml` names `g2-deployability-check.md`; the validator requires `deployability-check.md` (first seen in F0003 run 2026-08-29-16075bda). This run writes the validator's name.
- **Framework: role-matrix heading.** The validator reads only a STATUS.md section titled exactly `Required Role Matrix`. F0002 planning used "Required Signoff Roles (Set in Planning)", which silently disabled required-role enforcement until this run added the exact heading at G2.
- **Framework: early scope booleans force scans at G1.** Setting `security_sensitive_scope=true` at G1 (correct for a security feature) makes G1 demand all four scan classes before any code exists. Baseline scans satisfied it; a spec note would help.
- **Product: BLUEPRINT §4.11 Utopia safeguards.** Ownership-immutability triggers, link-table triggers, and deferred self-references for restore are explicitly deferred to "the F0002 implementation run" as follow-ups outside the approved plan, and were not implemented here. This needs a PM decision: a follow-up story or a scope amendment.
- **Product (low, DevOps):** move the engine PostgreSQL security/integration suites to an isolated per-run database; today they reset the shared dev database's F0002 registries and policy pointer.
