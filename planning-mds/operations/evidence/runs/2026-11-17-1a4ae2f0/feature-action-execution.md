# Feature Action Execution — F0008 (run 2026-11-17-1a4ae2f0)

- Role: Quality Engineer (G6 candidate validation)
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-18
- Result: PASS

## Gate timeline

| Gate | When | Outcome | Key evidence |
|---|---|---|---|
| Setup | 2026-11-17 04:3x | Run created (`init-run.py`); branch `feature/F0008-bitemporal-canonical-facts` cut from `origin/main` 2badb9a. No concurrent F0008 feature-completion run; the approved base-run-only plan manifest is independent. | `action-context.md` |
| G0 | 2026-11-17T04:49:40-05:00 | PASS, at the second validator attempt: the first was missing the Architect role result and the diff artifact | `g0-assembly-plan-validation.md`, plan "Feature-Action G0 Reconciliation" |
| G1 | 2026-11-17T04:52:15-05:00 | PASS after the runtime was restored (Docker Desktop); baseline 74/74 | `g1-runtime-preflight.md` |
| Implementation | 2026-11-17 | Migration 0014, domain, bounds, attestation, commit v1, reader, repository, API, tests and CI | `artifacts/diffs/changed-files.txt` |
| G2 | 2026-11-18T07:09:40-05:00 | PASS, at the second attempt: the self-review was missing required headings. Full run 1076/1076; changed-line coverage 97.5% | `g2-self-review.md`, `test-plan.md`, `test-execution-report.md`, `coverage-report.md`, `deployability-check.md` |
| G3 | 2026-11-18T07:09:51-05:00 | PASS. Code APPROVED; Security PASS WITH RECOMMENDATIONS. Two Lows fixed; final run 1081/0/0; coverage 98.0%. DAST ran after operator approval | `code-review-report.md`, `security-review-report.md`, `artifacts/security/**` |
| G4 | 2026-11-18T07:46:40-05:00 | APPROVED by the operator (gate policy ACCEPTABLE; SEC-F8-02 accepted) | `gate-decisions.md`, `artifacts/test-results/g4-gate-policy.txt` |
| G5 | 2026-11-18T07:48:18-05:00 | PASS, at the second attempt: the ledger headings and the G5 row were missing. 35 signoff rows | `signoff-ledger.md`, STATUS.md provenance |
| G6 | 2026-11-18 | This report; validate-feature-evidence G6 and validate-trackers | `lifecycle-gates.log` |

## Candidate checks

- The G0–G5 artifacts exist, and each verdict passes.
- Manifest:
  - `status: in-progress`;
  - `gate_results` cover `assembly_plan_validation` through `signoff`;
  - there is no `pm_closeout`, no `tracker_sync` and no `latest-run.json`.
- `changed_paths[]` is populated from `git diff origin/main` plus the untracked files, and mirrored in `artifacts/diffs/changed-files.txt`.
- Booleans cross-checked against the path classes:
  - `engine/**` gives `runtime_bearing`;
  - `engine/migrations/**` and `.github/workflows/**` give `deployment_config_changed`;
  - `security_sensitive_scope` was set by the G0 risk call;
  - no `experience/**` path, so `frontend_in_scope` is false.
- Non-required absent artifacts are in `omissions[]`: frontend, UX audit and AI reports.

## Operator interactions during the run

1. **G3 DAST:** the operator chose "Allow ZAP scan" after auto mode denied the test-server bind.
2. **G4:** the operator chose "Approve".

## Open follow-ups

- **SEC-F8-02 → F0018.** The application role is not a superuser.
- **Refusal reason-code persistence → F0018.** ADR-0078 D8 note.
- **CR-I1:** `brain-api.yaml` `FactVersion` `valid`/`recorded` drift, which predates F0008.
- **CR-I2:** align the ADR-0078 D4 clear wording at acceptance.
- **CR-I3:** pin tzdata for PostgreSQL and Python together.
- **Plan-review:** none was run before this feature action. Recorded at G0.
- **Shared development DB:** the `brain` database is at revision 0010; operators run `alembic upgrade head` when ready.
