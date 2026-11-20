# Gate Decisions — F0008-bitemporal-canonical-facts run 2026-11-19-8cfcd0ff

One row per gate evaluated. Executed validator results are in `lifecycle-gates.log` and `gate-state.json`.

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|------|----------|---------|-----------|-----------|----------|-----------|
| G0 | PASS | Architect (Claude Opus 5.5) | 2026-11-19T22:26:45-05:00 | Second remediation of review 2026-11-19-b21ec2de (SEC-F8-NEW-01 High plus 4 Low). Operator decision: refuse the whole commit with 404. Plan section "Second Remediation". | No | - |
| G1 | PASS | DevOps (Claude Opus 5.5) | 2026-11-19T22:26:37-05:00 | Preflight recorded before every test (commands.log line 1); PG 18.6 healthy; fresh DB at 0015 | No | - |
| G2 | PASS | Quality Engineer (Claude Opus 5.5) | 2026-11-19T22:36:54-05:00 | Final regression 1101/0/0; changed-line coverage 97.96%; no-DB gates pass (brain_api 82.78% after helper tests); concurrency 3/3 | No | - |
| G3 | PASS | Code Reviewer / Security (Claude Opus 5.5) | 2026-11-19T22:36:54-05:00 | Code APPROVED; Security PASS WITH RECOMMENDATIONS; SEC-F8-NEW-01 fixed with 404, 409-race and non-overlap tests; scans dependency clean, secrets triaged, SAST 0, DAST 0/0 | No | SEC-F8-02 to F0018 |
| G4 | APPROVED | Operator; recorded by Claude (Opus 5.5) / Product Manager | 2026-11-19T22:39:42-05:00 | Explicit operator decision "Approve"; gate_policy ACCEPTABLE (code 0/0, security 0/0); no mitigation token required. Supersedes 2026-11-18-bce4909b at G8. | No | - |
| G5 | PASS | Product Manager (Claude Opus 5.5) | 2026-11-19T22:40:07-05:00 | Five required roles signed for all seven stories (35 rows for this run); Security WITH RECOMMENDATIONS meets §15 (SEC-F8-02); no waiver | No | - |
| G6 | PASS | Quality Engineer (Claude Opus 5.5) | 2026-11-19T22:40:07-05:00 | Pre-closeout candidate: G0–G5 evidence present and passing; NUL-safe changed_paths (all paths exist); booleans match path classes; validate-trackers PASS | No | - |
| G7 | PASS | Architect (Claude Opus 5.5) | 2026-11-19T22:40:20-05:00 | New route-helper test bound to temporal-fact-resolution; compile, symbols/decisions and drift exit 0 | No | - |
| G8 | APPROVED | Product Manager (Claude Opus 5.5) | 2026-11-19T22:41:15-05:00 | The PM verified the G7 graph and the Story x Role matrix; trackers and BLUEPRINT synced; prior run 2026-11-18-bce4909b superseded by patch-prior-manifest; the ordered G8 checks govern publication | No | ADR-0078 acceptance is an operator decision |

Decisions: `PASS`, `PASS WITH RECOMMENDATIONS`, `FAIL`, `SKIP`. Blocking values: `Yes` / `No`.

## G4 Approval Record

- **Presented:**
  - the SEC-F8-NEW-01 fix and how it behaves: 404, full response for an authorized reader, no check without overlap, 409 on a race;
  - the four Low fixes with errata;
  - regression 1101/0/0 and coverage 97.96%;
  - the scan results and the gate-policy outcome ACCEPTABLE;
  - the effect of approving: it supersedes `2026-11-18-bce4909b` at G8.
- **Operator choice:** **Approve**, 2026-11-19.
- **High findings open:** none, so no mitigation token is recorded.
