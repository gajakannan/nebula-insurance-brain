# Gate Decisions — F0011 run 2026-11-22-885e8734

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|------|----------|---------|-----------|-----------|----------|-----------|
| G0 | PASS | Codex / Architect | 2026-11-22 | Approved plan, all 21 source identities/hashes and 68 mappings reconciled; ordered validator passed after diff-list repair | No | Runtime preflight at G1 |
| G1 | PASS | Codex / DevOps | 2026-11-22 | Healthy application containers; Engine/Node locked tools and both existing databases at0015 ready; report scopes current readiness accurately | No | Refresh Neuron readiness after its candidate lock sync before Neuron checks; both candidate history sweeps still required |
| G2 | PASS | Claude / Quality Engineer + DevOps (orchestrator) | 2026-11-23 | Canonical Node pnpm-selection fix applied; all three canonical images rebuild and pass offline; 1237 unit, 81 PostgreSQL, 8 Neuron, 19 Node, 12 UI, 1329 conformance results pass; coverage Python 86.0% / JS 98.5%; clean context matches current source; all four scan classes ran | No | SoupSieve 2.9.2 (pre-existing, Low) disposition and SAST WARNING at G3 Security; PR-L3 read-audit disposition at G3 |
| G3 | PASS | Claude / Code Reviewer + Security Reviewer | 2026-11-23 | Code: APPROVED WITH RECOMMENDATIONS (0C/0H/0M/1L; CR-F0011-01..04 closed and replayed on current source). Security: PASS WITH RECOMMENDATIONS (0C/0H/0M/2L; PR-L3 accepted; SAST warning informational; 4/4 scan classes ran) | No | G4 user decision; Lows: facts.py mismatch test, SoupSieve upgrade, invariant-500 logging |
| G4 | FIX ISSUES | User (operator) | 2026-11-23 | Gate policy ACCEPTABLE (0C/0H). Operator chose "Fix all 3 Lows first", then approve: SoupSieve upgrade, 500-handler traceId logging, facts.py mismatch test. Returned to G2/G3 per Step 4 | Yes (until fixes re-pass G2/G3) | Re-run G2 and G3 on current source |
| G2 | PASS | Claude / Quality Engineer + DevOps (re-run after G4 fixes) | 2026-11-23 | Unit 1239, PostgreSQL 83, full Neuron 265/0 fail, Node 19, 1329 conformance results; images rebuilt; coverage 86.4%/98.5%; DevOps PASS | No | — |
| G3 | PASS | Claude / Code Reviewer + Security Reviewer (re-run after G4 fixes) | 2026-11-23 | Code: APPROVED (0 open; CR-F0011-05 fixed). Security: PASS (0 open; SEC-F0011-01/02 fixed; dependency/secrets/SAST re-run) | No | G4 approval per operator's prior instruction |
| G4 | APPROVED | User (operator) | 2026-11-23 | Operator's G4 answer: fix all three Lows, then approve. Fixes landed and G2/G3 re-passed with 0 open findings in any severity (Code APPROVED, Security PASS); gate policy ACCEPTABLE, no justification required | No | ADR-0079 acceptance remains a separate operator decision |
| G5 | PASS | Claude (Opus 5.5) / Product Manager | 2026-11-23 | All 5 required roles × 6 stories (30 rows) signed with PASS/APPROVED; each verdict cross-checked against its role report; STATUS provenance and signoff-ledger.md consistent | No | G6 candidate validation |
| G6 | PASS | Claude (Opus 5.5) / Quality Engineer | 2026-11-23 | G0–G5 evidence present with passing verdicts; manifest is a pre-closeout candidate; feature-action-execution.md timeline written; scoped tracker validation recorded | No | G7 KG reconciliation |
| G7 | PASS | Claude (Opus 5.5) / Architect | 2026-11-23 | 114 new source files bound by literal path to the two F0011 capabilities; capability notes updated to as-built; no new canonical nodes; compile, symbol/decision regen and drift checks green | No | G8 PM closeout |
| G8 | APPROVED | Claude (Opus 5.5) / Product Manager | 2026-11-23 | All six stories Done; feature archived with links repaired; trackers synchronized; G7 graph verified; no carried recommendations or waivers | No | ADR-0079 acceptance is a separate operator decision |

All gates G0–G8 are recorded. Template example decisions were removed before further gates;
only actual decisions are recorded here. G4 requires review of the concrete result.
