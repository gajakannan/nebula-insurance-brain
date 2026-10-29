# Feature Action Execution — F0005 run 2026-10-25-4020923b

## Gate

G6 candidate validation. The feature closes on the **S0004-AC7 rejection branch**:
- Graph dense is not activated. `direct-baseline` with the v1 writer stays the committed default.
- The execution controls ship for every pipeline under ADR-0074, Accepted.
- ADR-0060 stays Proposed, with the failed gates and a reopen deadline.

Nothing is committed to git; commits and pushes wait for the operator.

## Execution Timeline

| Date | Gate / step | Outcome |
|---|---|---|
| 2026-10-25 | G0 assembly plan validation | PASS |
| 2026-10-25 | G1 runtime preflight | FAIL (no GPU, loopback blocked, credential absent), then PASS after the environment was restored |
| 2026-10-25/26 | Implementation, assembly-plan Steps 0a–7 | Host guard and quiescence, supervised conversion, failure reasons (migration 0009), pipeline selection, OCR provenance, queue bound, qualification corpus (independent author), harness |
| 2026-10-26 | Measured comparison | `report.json`, `void: false`; Graph dense misses the PRD thresholds (5, like for like); activation blocked |
| 2026-10-26 | G2 round 1 | PASS WITH RECOMMENDATIONS |
| 2026-10-26 | G3 round 1 | **FAIL**: Code Review REJECTED (C1 OCR page count/engine; H1 rejected/fallback calls); Security, QA and Architect pass with recommendations |
| 2026-10-27 | G4 (operator) | Fix critical. Graph dense rejected; ADR-0060 Proposed with a reopen deadline; controls ADR-0074; Medium fixes; pypdf 6.21.2; kill-lane re-run |
| 2026-10-27 | Rework (round 2) | C1 (ADR-0073 §6 OCR block), H1, M1–M6, SEC-F5-L1–L3, S0003-AC3/AC4, migration 0010 |
| 2026-10-27 | G2 round 2 | PASS WITH RECOMMENDATIONS (live attempt 1 blocked by a 10 s test timeout; fixed; all lanes pass) |
| 2026-10-28 | G3 round 2 (fresh sessions) | PASS: Code Review APPROVED WITH RECOMMENDATIONS; Security, QA and Architect PASS WITH RECOMMENDATIONS |
| 2026-10-28 | G4 round 2 (operator) | Approved the rejection branch. Fix N1, L5, the ADR text and the Lows; ADR-0074 accepted once N1/L5 are verified |
| 2026-10-28 | Round 3 | N1, SEC-F5-L4/L5/L6, Code Review/Architect/QA Lows, delta-review D-1–D-5, litellm 1.100.4. Independent delta review APPROVED WITH RECOMMENDATIONS. One D-1 regression caught live and fixed. All 7 live lanes pass |
| 2026-10-28 | Post-decision check | PASS: committed config `direct-baseline`/v1, no Graph call |
| 2026-10-28 | ADR-0074 | Accepted |
| 2026-10-28 | G4 conditions met; G5 signoff | PASS |

## Evidence and commands

- **Commands:** `commands.log`, written in batches after execution.
- **Test results:** `test-execution-report.md`; `artifacts/test-results/g2r3-*` (current), `g2r-*`, `live-*`, the attempt folders, `post-decision-check.log`, and the HEAD baselines.
- **Coverage:** `coverage-report.md`; 83.5% changed-line.
- **Deployability:** `deployability-check.md`; `artifacts/runtime/`.
- **Security scans:** `artifacts/security/g2r3/` (current), `g2r/`, round 1.
- **Measurement:** `artifacts/qualification/` (`report.json` immutable; `report-summary.md` with G3 corrections inline).
- **Reviews:**
  - G3 round 2: `code-review-report.md`, `security-review-report.md`, `qa-qualification-verdict.md`, `architect-qualification-verdict.md`;
  - G3 round 1: `*-round1.md`;
  - post-G4 delta: `delta-review-report.md`.
- **Records:** `gate-decisions.md`, `signoff-ledger.md`.
- **ADRs:** ADR-0060 (outcome section), ADR-0073 §6 (amendment), ADR-0074 (Accepted).

## Result

PASS WITH RECOMMENDATIONS
