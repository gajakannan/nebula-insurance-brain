# G0 Assembly Plan Validation — F0008 second remediation

- Run: `2026-11-19-8cfcd0ff`
- NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` (source: environment)
- Reviewer: Claude (Opus 5.5) / Architect
- Review date: 2026-11-19
- Verdict: PASS

## Source and approval baseline

The approved run is `2026-11-18-bce4909b` (merged #56, e024cd7). Review `2026-11-19-b21ec2de` returned CONDITIONALLY DONE with 1 High (SEC-F8-NEW-01) and 4 Low findings. Operator decision (2026-11-19): refuse the whole commit with the non-disclosing 404 when the committer cannot read a predecessor's attesting document. The change set is recorded in the assembly plan section "Second Remediation". This run supersedes `2026-11-18-bce4909b` at G8.

## Assembly checks

| Check | Judgment |
|---|---|
| Scope split | Backend: commit-service disclosure hook, repository query, route checks and tests. Architect: ADR-0078 D4 sentence and plan wording. PM: STATUS, BLUEPRINT and errata. No frontend or AI. |
| Dependency order | Service hook, repository, route, tests, docs, then the regression and reviews. |
| Migration lineage | No migration; head stays 0015. |
| Ownership | Unchanged. |
| Scope booleans | `runtime_bearing`, `deployment_config_changed` (CI pin unchanged; no deploy config in this diff) and `security_sensitive_scope` true; `frontend_in_scope` false. They are re-checked at G2 against `changed_paths`. |
| Race design | Up-front READ checks cover documents of overlapping current versions. After the lock, a concurrently committed predecessor returns 409 `stale_version`, so no date is returned without a check. |
