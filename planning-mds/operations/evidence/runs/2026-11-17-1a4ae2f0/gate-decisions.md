# Gate Decisions — F0008-bitemporal-canonical-facts run 2026-11-17-1a4ae2f0

One row per gate evaluated. Executed validator results are in `lifecycle-gates.log` and `gate-state.json`.

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|------|----------|---------|-----------|-----------|----------|-----------|
| G0 | PASS | Architect (Claude Opus 5.5) | 2026-11-17T04:49:40-05:00 | The approved plan (PR #54) was reconciled. Head 0013 confirmed, and ten implementation details were recorded in the assembly plan. Two reconcile decisions were logged: the F0007 harness request shape, and the refusal audit deferred to F0018 with an ADR-0078 D8 note. Five required roles set. | No | No plan-review run preceded this feature run (recorded) |
| G1 | PASS | DevOps (Claude Opus 5.5) | 2026-11-17T04:52:15-05:00 | Docker Desktop restored; `brain-postgres` healthy (PG 18.6). The shared DB at 0010 is left untouched, and a disposable DB was migrated to head. Baseline 74/74. Both tzdata versions recorded. | No | - |
| G2 | PASS | Quality Engineer (Claude Opus 5.5) | 2026-11-18T07:09:40-05:00 | 46/46 ACs mapped and passing. Full engine run 1076/1076 at G2 and 1081/1081 after the G3 fixes; changed-line coverage 98.0%. Deployability PASS (0014 up/down/up, guards, CI step). Booleans reconciled. | No | - |
| G3 | PASS | Code Reviewer / Security (Claude Opus 5.5) | 2026-11-18T07:09:51-05:00 | Code APPROVED; Security PASS WITH RECOMMENDATIONS. CR-L1 and SEC-F8-01 (Low) fixed and re-tested. SEC-F8-02 (Low) deferred to F0018. Open: critical 0, high 0, medium 0. Scans: dependency and secrets clean, SAST triaged, DAST 0 FAIL / 0 WARN (operator-approved run). | No | SEC-F8-02 to F0018 (Architect + DevOps) |
| G4 | APPROVED | Operator; recorded by Claude (Opus 5.5) / Product Manager | 2026-11-18T07:46:40-05:00 | Explicit operator decision "Approve" at the G4 prompt, accepting SEC-F8-02 as a deferred non-blocking Low. `gate_policy.py --profile standard`: ACCEPTABLE (code 0/0, security 0/0); allowed outcomes approve or fix issues; no mitigation token required. | No | - |
| G5 | PASS | Product Manager (Claude Opus 5.5) | 2026-11-18T07:48:18-05:00 | Five required roles signed for all seven stories (35 provenance rows), each with a named reviewer, ISO date and run-folder evidence. The Security WITH RECOMMENDATIONS verdict meets the five §15 conditions (SEC-F8-02 Low, owner and follow-up, operator-accepted at G4). No waiver or required-role omission. | No | - |
| G6 | PASS | Quality Engineer (Claude Opus 5.5) | 2026-11-18T07:48:47-05:00 | Pre-closeout candidate: G0–G5 evidence present and passing. changed_paths populated (103), and the booleans match the path classes (engine runtime, migration and CI, security scope from the G0 risk call). Non-required artifacts are in omissions[]. validate-trackers PASS. | No | - |
| G7 | PASS | Architect (Claude Opus 5.5) | 2026-11-18T07:50:23-05:00 | As-built code bound by literal path: reader, routes and schemas to temporal-fact-resolution; commit-side code merged into the existing bitemporal-canonical-commit record; models to canonical-fact-version; new migration node. compile, symbols/decisions and drift all exit 0. Coverage regeneration deferred to G8. | No | - |
| G8 | APPROVED | Product Manager (Claude Opus 5.5) | 2026-11-18T21:13:15-05:00 | The PM verified the G7 graph and the Story x Role matrix: 35 signoff rows, seven Done stories. Archive move complete with links repaired; trackers, BLUEPRINT, story index and feature shard synced; SEC-F8-02 PM acceptance line recorded. The ordered G8 automated checks govern publication. | No | ADR-0078 acceptance is an operator decision |

Decisions: `PASS`, `PASS WITH RECOMMENDATIONS`, `FAIL`, `SKIP`, `APPROVED`. Blocking values: `Yes` / `No`.

## G4 Approval Record

- **Presented:**
  - the combined review summary: verdicts, severity counts, fixed Lows, the final regression 1081/0/0, 46/46 ACs and the six proof gates, coverage 98.0%, and the four scan results;
  - the recorded reconciliations: two F0007 tests aligned to approved F0008 semantics, the F0007 harness v1 block, and refusal reason persistence deferred to F0018;
  - the deferred Low SEC-F8-02;
  - the options Approve / Fix issues.
- **Operator choice:** **Approve**.
- **Severity evidence:** `artifacts/test-results/g4-gate-policy.txt` (status ACCEPTABLE, requires_justification false).
- **High findings:** none, so no mitigation token is recorded.
- **Recommendation acceptance:** SEC-F8-02 (Low, superuser application connection can bypass the triggers). Owner Architect + DevOps; follow-up is the F0018 application role. Accepted by the operator at G4 on 2026-11-18.
- **DAST:** the operator approved running the ZAP API scan on 2026-11-18, after auto mode had denied the test-server bind at G2.
