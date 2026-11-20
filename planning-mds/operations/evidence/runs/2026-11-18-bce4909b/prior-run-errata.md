# Errata for superseded run 2026-11-17-1a4ae2f0

- Recorded by: Claude (Opus 5.5) / Product Manager
- Date: 2026-11-18
- Basis: review `2026-11-18-d34a095e` and audit `2026-11-18-a3709ba0`
- Result: PASS

The prior run is approved history, and this run supersedes it at G8. Its files are not rewritten; these corrections apply when reading them.

| ID | Prior statement | Correction |
|---|---|---|
| PM-L1 | `evidence-manifest.json` `changed_paths` matched the merged diff | It omits `planning-mds/knowledge-graph/coverage-report.yaml`, `planning-mds/operations/evidence/features/F0008-bitemporal-canonical-facts/latest-run.json` and `…/2026-11-17-1a4ae2f0/token-usage.json`. Those were written at G8 after the last sync. It lists `…/artifacts/security/sast/sast-semgrep-20261117-052012.sarif`, which was deleted at the operator's request and is absent from the merged diff (2badb9a..339c920). |
| PM-L2 | Feature `STATUS.md` **Last Updated:** 2026-11-17 | Closeout was recorded on 2026-11-18. The current STATUS date is maintained by this run. |
| SEC-L1 | `security_scans.sast.result: "clean"` | The raw SARIF (`sast-semgrep-20261117-052326.sarif`) has 7 `avoid-sqlalchemy-text` findings in migration 0014, triaged as false positives (module constants only) in `security-review-report.md`. The accurate label is "findings-triaged". |
| QE-L1 | `test-execution-report.md` claims the concurrency suite passed three repeat runs and that the CI no-DB package gates passed (97.4% / 82.3% / 90.8% / 87.7%) | Those executions happened in-session, but no raw output was kept in the run folder, so they are unsupported by the evidence package. This run re-executes and keeps raw output for both (`artifacts/test-results/command-output/`). |
| S0002 AC7, S0004 AC1 | 46/46 criteria verified | Only 44/46 were met as written. The commit response lacked AC7 metadata, and AC1's "no audit row" clause contradicted the F0002 audit. Both are resolved in this run, by implementation and an operator-approved amendment respectively. |
