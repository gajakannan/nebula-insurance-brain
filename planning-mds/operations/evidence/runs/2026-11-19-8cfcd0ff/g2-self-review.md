# G2 Self-Review — F0008 second remediation (run 2026-11-19-8cfcd0ff)

- Roles: Backend Developer, Quality Engineer, DevOps
- Reviewer: Claude (Opus 5.5)
- Date: 2026-11-19
- Verdict: PASS

## Scope Review

The change is limited to the findings of review `2026-11-19-b21ec2de`, under the operator's decision of 2026-11-19. There is no route, grant, table, migration or UI. Scope booleans: `runtime_bearing` and `security_sensitive_scope` true; `deployment_config_changed` kept true as declared at G0 (conservative; this diff changes no deploy config); `frontend_in_scope` false.

## Acceptance Criteria Review

All 46 ACs (as amended) are re-verified by the final regression. The SEC-F8-NEW-01 behaviours are covered by five new tests and the helper unit tests.

## Implementation Risks

- **Over-checking.** The up-front window is a superset of the real overlap, so a committer may be asked to READ a document of a version that in fact would not split. This errs toward denial, matching D4.
- **Race path.** It returns 409 rather than 404, by design: the denial case is caught up front, and the 409 tells the caller to retry, which re-checks.
- **Coverage gate.** The `brain_api` no-DB gate initially fell to 79.44%. Pure helper tests restored it to 82.78%.

## Validation Evidence

- Final regression 1101/0/0; changed-line coverage 97.96%.
- No-DB gates pass; concurrency 3/3.
- `ruff`, `format` and the CI `mypy` set are clean.
- Scans: dependency clean; secrets 5 false positives (review hash manifest); SAST 0; DAST 0/0.
