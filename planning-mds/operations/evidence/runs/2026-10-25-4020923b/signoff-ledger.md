# Signoff Ledger — F0005-one-time-docling-ingestion run 2026-10-25-4020923b

Recorded by Claude in the Product Manager role on 2026-10-28, after the operator's G4 approval (2026-10-28) to close F0005 on the S0004-AC7 rejection branch. The verdicts are agent role reviews from the cited reports, not additional human reviewer identities.

- **Review independence:** Code Review, Security, QA and the Architect each ran as a fresh session without the authors' context. G3 round 1 (Code Review REJECTED) is preserved under `-round1` names.
- **Post-G4 changes:** the independent delta review `delta-review-report.md` (APPROVED WITH RECOMMENDATIONS) covers them.

## Required Role Matrix

| Role | Required |
|---|---|
| Quality Engineer | Yes |
| Code Reviewer | Yes |
| Security Reviewer | Yes |
| DevOps | Yes |
| Architect | Yes |

## Current Signoff State

- F0005-S0001 / Quality Engineer: PASS WITH RECOMMENDATIONS by Claude (Quality Engineer role; independent QA qualification session for S0004) on 2026-10-28 (test-execution-report.md)
- F0005-S0001 / Code Reviewer: APPROVED WITH RECOMMENDATIONS by Claude (independent Code Reviewer session, G3 round 2; independent delta review) on 2026-10-28 (code-review-report.md)
- F0005-S0001 / Security Reviewer: PASS WITH RECOMMENDATIONS by Claude (independent Security Reviewer session, G3 round 2; independent delta review) on 2026-10-28 (security-review-report.md)
- F0005-S0001 / DevOps: PASS WITH RECOMMENDATIONS by Claude (DevOps role) on 2026-10-28 (deployability-check.md)
- F0005-S0001 / Architect: PASS WITH RECOMMENDATIONS by Claude (independent Architect qualification session, G3 round 2) on 2026-10-28 (architect-qualification-verdict.md)
- F0005-S0002 / Quality Engineer: PASS WITH RECOMMENDATIONS by Claude (Quality Engineer role; independent QA qualification session for S0004) on 2026-10-28 (test-execution-report.md)
- F0005-S0002 / Code Reviewer: APPROVED WITH RECOMMENDATIONS by Claude (independent Code Reviewer session, G3 round 2; independent delta review) on 2026-10-28 (code-review-report.md)
- F0005-S0002 / Security Reviewer: PASS WITH RECOMMENDATIONS by Claude (independent Security Reviewer session, G3 round 2; independent delta review) on 2026-10-28 (security-review-report.md)
- F0005-S0002 / DevOps: PASS WITH RECOMMENDATIONS by Claude (DevOps role) on 2026-10-28 (deployability-check.md)
- F0005-S0002 / Architect: PASS WITH RECOMMENDATIONS by Claude (independent Architect qualification session, G3 round 2) on 2026-10-28 (architect-qualification-verdict.md)
- F0005-S0003 / Quality Engineer: PASS WITH RECOMMENDATIONS by Claude (Quality Engineer role; independent QA qualification session for S0004) on 2026-10-28 (test-execution-report.md)
- F0005-S0003 / Code Reviewer: APPROVED WITH RECOMMENDATIONS by Claude (independent Code Reviewer session, G3 round 2; independent delta review) on 2026-10-28 (code-review-report.md)
- F0005-S0003 / Security Reviewer: PASS WITH RECOMMENDATIONS by Claude (independent Security Reviewer session, G3 round 2; independent delta review) on 2026-10-28 (security-review-report.md)
- F0005-S0003 / DevOps: PASS WITH RECOMMENDATIONS by Claude (DevOps role) on 2026-10-28 (deployability-check.md)
- F0005-S0003 / Architect: PASS WITH RECOMMENDATIONS by Claude (independent Architect qualification session, G3 round 2) on 2026-10-28 (architect-qualification-verdict.md)
- F0005-S0004 / Quality Engineer: PASS WITH RECOMMENDATIONS by Claude (Quality Engineer role; independent QA qualification session for S0004) on 2026-10-28 (test-execution-report.md)
- F0005-S0004 / Code Reviewer: APPROVED WITH RECOMMENDATIONS by Claude (independent Code Reviewer session, G3 round 2; independent delta review) on 2026-10-28 (code-review-report.md)
- F0005-S0004 / Security Reviewer: PASS WITH RECOMMENDATIONS by Claude (independent Security Reviewer session, G3 round 2; independent delta review) on 2026-10-28 (security-review-report.md)
- F0005-S0004 / DevOps: PASS WITH RECOMMENDATIONS by Claude (DevOps role) on 2026-10-28 (deployability-check.md)
- F0005-S0004 / Architect: PASS WITH RECOMMENDATIONS by Claude (independent Architect qualification session, G3 round 2) on 2026-10-28 (architect-qualification-verdict.md)
- F0005-S0005 / Quality Engineer: PASS WITH RECOMMENDATIONS by Claude (Quality Engineer role; independent QA qualification session for S0004) on 2026-10-28 (test-execution-report.md)
- F0005-S0005 / Code Reviewer: APPROVED WITH RECOMMENDATIONS by Claude (independent Code Reviewer session, G3 round 2; independent delta review) on 2026-10-28 (code-review-report.md)
- F0005-S0005 / Security Reviewer: PASS WITH RECOMMENDATIONS by Claude (independent Security Reviewer session, G3 round 2; independent delta review) on 2026-10-28 (security-review-report.md)
- F0005-S0005 / DevOps: PASS WITH RECOMMENDATIONS by Claude (DevOps role) on 2026-10-28 (deployability-check.md)
- F0005-S0005 / Architect: PASS WITH RECOMMENDATIONS by Claude (independent Architect qualification session, G3 round 2) on 2026-10-28 (architect-qualification-verdict.md)

S0004 is signed off as **evaluated and rejected**:
- S0004-AC3: thresholds missed; activation blocked.
- S0004-AC4: QA, Architect and Security verdicts recorded; operator decision recorded at G4.
- S0004-AC7: `direct-baseline` and the v1 writer remain default, verified by `artifacts/test-results/post-decision-check.log`.
- S0004-AC5/AC6 and S0005-AC5 are not reachable on the rejection branch. That is the outcome the PRD prescribes, not a gap.

## Recommendation Acceptances

All reviewer verdicts pass with recommendations; no Critical or High recommendation is open. The operator's G4 decisions:
- **Fixed in this run:** N1, L5 and the Lows. Verified by the delta review and the final live lanes.
- **Retained as owned follow-ups:** each one, with its owner and target, gets an explicit PM acceptance line in `pm-closeout.md` at G8. Activation preconditions:
  - SEC-F5-M1: converter OS isolation;
  - Docling ≥ 2.132 / pillow ≥ 13 requalification;
  - SEC-F5-L4 residual: name-based program check and minimal restart environment.
- **Retained limitations:** the queue-race orphan sweep; the ADR-0073 OCR-bearing restore-drill proof gate; QA's process findings (corpus not committed; batched `commands.log`; predicted values not retained); and the pre-existing F0004 failures.

## Waivers And Omissions

None. No required artifact, scan class or coverage waiver: changed-line coverage is 83.5% against an 80% floor, and all four scan classes ran.
