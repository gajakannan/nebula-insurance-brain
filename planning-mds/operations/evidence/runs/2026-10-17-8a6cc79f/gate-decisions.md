# Gate decisions — F0004

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G0 | PASS | Codex (Architect role) | 2026-10-17 | g0-assembly-plan-validation.md; actual stage validator must also pass | No | G1 preflight |
| G1 | FAIL | Codex (DevOps role) | 2026-10-18T00:54:43.636673+00:00 | Docker Desktop WSL integration is unavailable; no local daemon/socket. See g1-runtime-preflight.md. | Yes | Restore runtime and resume this run at G1. |
| G1 | PASS | Codex (DevOps role) | 2026-10-19 | Final locked runtime healthy; ordered G1 validator passes. | No | G2 |
| G2 | PASS | Codex (QE and DevOps roles) | 2026-10-19 | Self review, actual tests, changed coverage and isolated restore pass; ordered G2 validator required. | No | G3 review |
| G3 | PASS WITH RECOMMENDATIONS | Independent Code and Security Reviewers | 2026-10-20 | Both reports pass after corrected date race and PDF polyglot; current open critical/high zero. Ordered G3 validator passed. | No | G4 operator approval pending |
| G4 | APPROVED | User | 2026-10-21T04:13:22Z | User explicitly replied approve to the concrete G4 review packet; code/security open critical/high zero; bounded recommendations retained. | No | G5 signoff |
| G5 | PASS | Codex (required role reports / PM ledger) | 2026-10-21 | All four stories have passing QE, Code, Security, DevOps and Architect rows with concrete report evidence. | No | G6 candidate validation |
| G6 | PASS | Codex (QE / PM roles) | 2026-10-21 | G0–G5 evidence complete; candidate manifest in-progress; ordered evidence and tracker checks required. | No | G7 semantic graph |
| G7 | PASS | Codex (Architect role) | 2026-10-21 | As-built bindings, new migration node and generated symbols/decisions/drift/reproducibility pass. Static caller limits explicitly recorded. | No | G8 PM closeout |
| G8 | PASS | Codex (Product Manager role) | 2026-10-21 | All four stories Done; twenty role rows; archive, named recommendation acceptances and synchronized trackers prepared. Ordered driver must complete all final checks and patch-then-publish. | No | Final validation / publication |

The original G1 failures below are historical and superseded by the later G1
PASS. No feature-completion approval or delivery signoff is recorded.

## G1 runtime stop

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1 | FAIL | Codex (DevOps role) | 2026-10-18T00:55:25.417409+00:00 | Docker/Compose report missing WSL integration; no daemon/socket available. g1-runtime-preflight.md records evidence. | Yes | Restore host Docker Desktop WSL integration, then resume this same run at G1. |

## Resumed runtime and Step 1a exit decision

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1 | PASS | Codex (DevOps role) | 2026-10-18T01:56Z | Healthy dependencies and locked-workspace application jobs; model-cache restoration; both ordered G1 executions exit 0. See g1-runtime-preflight.md. | No | Step 1a |
| Step 1a | PASS | Codex (Architect role) | 2026-10-18T01:59Z | All three actual conversions pass; native 2/2 STATED with observed backend, scanned 1/1 OCR with observed engine, mixed 3/3 singly attributed with 0 ORIGIN_UNAVAILABLE. Reproduction script exits 0 and retained regression test passes. See step1a-provenance-spike.md and its per-cell receipts. | No | Proceed to Step 1b under the approved contracts; keep v2 writer disabled until Step 4 compatibility passes. |

Architect review confirms the evidence uses positive producer receipts and the
actual converter cells-to-item relation. The early native observer diagnostic
was corrected before this decision; its missing producer receipt is not treated
as a final converter limitation. Hooks are instance-local, pinned-version
integration points. Unsupported/mixed origins still require explicit
ORIGIN_UNAVAILABLE and per-document v1 fallback. This decision authorizes the
planned implementation sequence, not writer activation or ADR-0073 acceptance.

## G2 self-review and deployment evidence

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1 | PASS | Codex (DevOps role) | 2026-10-19 | Final locked jobs healthy; four scan classes recorded; ordered G1 replay passes. Earlier replay failed evidence completeness while scan records were pending, not runtime readiness. | No | G2 |
| G2 | PASS | Codex (Quality Engineer / DevOps roles) | 2026-10-19 | g2-self-review.md, test-execution-report.md, coverage-report.md, g2-deployability-check.md; all required behavior tests pass and each changed-runtime layer exceeds 80%. Actual stage validator must pass before G3. | No | Code and Security review; no implementation approval is inferred. |


## G4 awaiting operator decision — 2026-10-20

G1 was rechecked first and passed. G2 replayed after the independent review
corrections and passed; G3 passed with both reports finalized. Current open
code Critical/High: 0/0; security Critical/High: 0/0. Security retains one Medium
and four Low recommendations. See g4-approval-request.md and the two reports.
The standard severity policy enables approval without a high-risk mitigation.
No operator decision has been recorded; do not advance to G5 on a generic
resume instruction or infer acceptance from the prior planning approvals.


## Operator approval recorded — 2026-10-21

The user explicitly replied `approve` to the G4 request after reviewing the
combined results. This approves the implementation and continuation through
G5–G8 with the recorded bounded follow-ups. It does not activate the v2 writer,
accept Proposed ADRs or approve a deployment/merge. Earlier awaiting-approval
prose is historical.
