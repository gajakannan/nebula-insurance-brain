# Gate Decisions — F0009 plan 2026-11-24-bfdbbf04

Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`. Action plan, PHASE=A+B, FEATURE_MODE=new, contract 2026-07-11.

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1 | PASS | Product Manager | 2026-11-25T00:35:41.502579+00:00 | Raw blueprint/accepted contracts resolve scope; technical design is assigned to Phase B; six stories/41 testable ACs, no open business-rule question | No | Operator reviews explicit A1–A3 assumptions at G3 |
| G2 | PASS | Product Manager | 2026-11-25T00:35:41.502579+00:00 | STORY-INDEX regenerated; strict story, tracker, semantic-example and local-link checks pass; approved direct dependency metadata recorded | No | Architect completes the reserved KG stub at G4 |

Current position: G1–G4 completed through run-gate.py. G3 records the operator’s exact approve-phase-a token and attestation. All seven G5 pre-approval operations passed; G5 has received the explicit operator token approve-phase-b; approval-status edits precede attestation and the post-approval refresh.

## Requirements reconciliation

1. Current BLUEPRINT §4.10 and F0018 ownership override ADR-0044's old F0002 orchestration sequencing shorthand. Review submission creates a correction, never canonical acceptance; F0009 reads stored commit links only.
2. ADR-0077/0078 as built (including migration 0015 and both F0008 remediation runs) control split remainders, ending evidence and source READ. No F0010 retraction amendment is made here.
3. A reserved LearningCandidate reference is the only §88 hook: PRD A2 proposes one identity per new effective CORRECT, with no learning/benchmark/holdout behavior. The operator reviews this at G3.
4. S0002 requires auditable attributed losing/stale submissions under ADR-0044. The Architect must reconcile the current already-decided rejection/stale payload retention in Phase B, without silently expanding reviewer authority.
5. No earlier F0009 assembly plan exists. F0009's existing KG reserved stub remains pending Architect completion at G4; no shared node/projection is edited by PM.

## Dependency audit

See artifact-trace.md for exact approved F0006/F0008/F0011 manifest references and future-consumer audit-pending notes. This is a targeted planning audit, not repo-wide feature-evidence validation.

## Operator approvals

Phase A: operator approved with exact token `approve-phase-a` in the current conversation, recorded 2026-11-25T00:49:49.474930+00:00. Phase B: operator approved with exact token `approve-phase-b`, recorded 2026-11-25T02:16:33.637463+00:00. Phase A attestation follows this record.

## Validation and pending checkpoint

- `artifacts/phase-a-stories-repaired.log`: strict story validation, all six pass with zero warnings. The first attempt flagged heuristic wording (not found/denied and audit) despite existing negative scenarios; clarified wording and explicit edge-case notes are retained in the final stories, and the failed attempt is preserved in `artifacts/phase-a-stories.log`.
- `artifacts/phase-a-story-index.log`: generator found 66 stories, including the new six.
- `artifacts/phase-a-trackers.log`: zero errors, zero warnings; feature-evidence validation explicitly skipped.
- `artifacts/phase-a-examples.log`: semantic teaching artifacts pass; this is not runtime proof.
- `artifacts/phase-a-links.log`: feature/base-run Markdown references resolve; six stories/41 ACs and absence of a feature evidence index confirmed.
- `artifacts/phase-a-severity.log`: profile none computes PASS.
- `artifacts/gate-g1.log` and `artifacts/gate-g2.log`: driver reports pass for each ordered stage.

G3 requires the user's approval of the concrete PRD/stories. The operator prompt says: “No gate may be passed without an explicit approval token recorded in gate-decisions.md.” The suggested response token is `approve-phase-a`. After that response, record the exact token/actor/time, make Phase A approval-status edits, attest approve-phase-a as product-manager and rerun G3. Do not attest before the response.

## G3 explicit Phase A approval

- Stage: G3
- Checkpoint: approve-phase-a
- Approval token: `approve-phase-a`
- Actor: user (operator)
- Recorded at: 2026-11-25T00:49:49.474930+00:00
- Scope: F0009 Phase A requirements, six stories/41 ACs, PRD assumptions A1–A3; run 2026-11-24-bfdbbf04.
- Decision: APPROVED. Architecture proceeds in this same A+B run; the manifest remains draft until G5 publication.

## Architecture gates and reconciliation

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G3 | PASS | Operator / Product Manager | 2026-11-25T01:04:13.415373+00:00 | Exact user token approve-phase-a recorded and checkpoint attested; approve-plan Phase A operation passed in the existing A+B run | No | Manifest remains draft until G5 |
| G4 | PASS | Architect | 2026-11-25T01:04:13.415373+00:00 | Source shards compiled and kg --check-drift passed on first attempt through run-gate.py | No | Ordered G5 exit validation and explicit Phase B review |

Architect design uses four new schema sources and two new tables plus a nullable server-owned decision marker. This avoids inventing historical candidate links or using a timestamp/transaction-ID guess. New decisions persist their domain decided_at explicitly so reservation actor/time agrees with the stored decision. All 41 ACs are mapped; runtime proofs remain Not Started. G5 architecture approval has not been supplied.

## G5 pre-approval exit validation — PASS, architecture checkpoint pending

The gate journal records these completed operations in order, each exit 0: validate-stories, generate-story-index, validate-trackers (skip-feature-evidence), kg-write-coverage, kg-check-drift-exit, kg-check-reproducible, validate-templates. `artifacts/gate-g5-exit-validation.log` records pending-checkpoint approve-phase-b. This is not a Phase B approval or completed G5.

Additional local structural checks pass: four authored schemas, 16 positive/negative examples, 139 feature/ADR links and the exact 41-AC assembly map; the product feature-readiness structure validator also passes (`artifacts/phase-b-local-readiness.log`). These are planning validation, not independent plan-review or runtime proof.

Await the operator's explicit architecture approval token `approve-phase-b`. Record its exact text/actor/time, make every approval-status edit in planning docs/KG source, attest the checkpoint as Architect, then rerun G5 so post-approval compile/coverage/reproducibility/plain validation/tracker checks and approve-plan.py publish the manifest last. The operator approval is now recorded below; attest only after finishing all approval-status edits and retain automated publication last.

## G5 explicit Phase B architecture approval

- Stage: G5
- Checkpoint: approve-phase-b
- Approval token: `approve-phase-b`
- Actor: user (operator)
- Recorded at: 2026-11-25T02:16:33.637463+00:00
- Decision: APPROVED for the Phase B architecture of F0009, run 2026-11-24-bfdbbf04.
- Scope: five-step assembly plan, four schema sources, two append-only hook tables, nullable server-owned decision marker, current-authority lineage and all 41 approved ACs.
- Prerequisite: all seven ordered pre-approval G5 operations have exited 0.
- Formal ADR status: ADR-0080 remains Proposed; this token approves the plan, not runtime proof or separate ADR acceptance.
- All planning approval-status edits are finished before checkpoint attestation. Rerun G5 for post-approval compile, fresh coverage, reproducibility, plain validation, tracker validation and approve-plan.py publication last. The journal/manifest supplies the procedural completion record; no manual manifest approval.
