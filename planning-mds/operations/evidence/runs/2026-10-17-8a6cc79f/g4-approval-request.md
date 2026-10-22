# G4 approval request — F0004 run 2026-10-17-8a6cc79f

Status: APPROVED by the user on 2026-10-21 (explicit reply: approve).
Original request prepared 2026-10-20; pending-decision wording below is historical.

## Reviewable result

All four stories and 25 acceptance criteria are implemented and covered by
runtime evidence: versioned immutable verified bundles, observed native/OCR
origin and durable structure, attributable append-only document dates with
verified human selection, and authorized v1/v2 consumers plus isolated restore.
The approved Python product architecture governs; frontend is not in scope.

| Check | Current result |
|---|---|
| G1, rechecked first on resume | PASS |
| G2 after review corrections | PASS |
| G3 ordered review validator | PASS |
| Independent Code Reviewer | APPROVED WITH RECOMMENDATIONS; no open code findings |
| Independent Security Reviewer | PASS WITH RECOMMENDATIONS; 0 Critical, 0 High, 1 Medium, 4 Low |
| Engine tests | 229 passed |
| Neuron tests | 93 passed; 4 optional live inference/tokenizer skips |
| Actual isolated restore | 4 passed; v1/v2 database/bytes and two citations per drill |
| Changed Python runtime coverage | 2371 / 2617 = 90.60%; all 44 files measured |
| Coverage by layer | engine 91.97%, neuron 88.58%, operations 84.40% |
| Changed Python lint | all 63 files pass; changed source type checks pass |

Independent reviewers reproduced and verified corrections for the gzip/PDF
polyglot reaching archive detection and the date-read concurrency race.
Repeated whole-file JSONL splitting was also corrected. Initial reproductions,
failed diagnostics and successful regressions are retained.

## Bounded follow-ups

The security baseline planning audit still fails: baseline threat/data/secrets/
OWASP documents remain pending. Security/Architect own reconciliation before
production-readiness claims (F0026; target 2026-11-03). No waiver is recorded.

All 15 Docling advisory records remain in the raw audit. The demonstrated
archive path is closed by the initial signature guard; other reviewed families
require absent format/OCR/plugin preconditions. AI Engineer/DevOps own a fixed
converter/hook requalification before broader activation (F0005; target
2026-11-03). This is a scoped reachability judgment, not a clean package audit.

Other low recommendations cover public health/OpenAPI headers, exact OCR model
asset provenance before broader activation, and current authorization caller
bindings at mandatory G7 before closeout. The Code Reviewer also records future
PR hotspot/owner acknowledgement obligations. These are proposed follow-ups,
not completed tickets or recorded human risk acceptance.

## Decision scope and next steps

Approval authorizes the reviewed F0004 implementation to proceed to G5 role
signoffs, G6 candidate validation, G7 Architect graph reconciliation and G8 PM
closeout. The default-false v2 writer remains disabled pending deployment's
migration/backfill/reconciliation and consumer gates. ADR-0073 remains Proposed;
production Graph qualification is separate. No shared DB migration, deployment,
commit, push or merge has occurred.

The standard severity policy reports ACCEPTABLE, approval enabled, no high-risk
justification required. Allowed review decisions: approve, request fixes, reject.
No approving decision is inferred or stored yet.

## Evidence

- [Code review](code-review-report.md)
- [Security review](security-review-report.md)
- [Test execution](test-execution-report.md)
- [Coverage](coverage-report.md)
- [Deployability](g2-deployability-check.md)
- [Severity policy](artifacts/test-results/g4-severity-policy.txt)
- [Ordered G3 result](artifacts/test-results/g3-ordered-review-gate.txt)

## Required operator checkpoint

The framework feature action Step 4 requires the user's decision after combined
review. The [Code Reviewer skill](../../../../../../nebula-agents/agents/code-reviewer/SKILL.md)
states: “The user makes the final call.” G4 remains pending until that decision.
