# Gate decisions — F0005 Phase B rework

## Phase selection and prior approval

PM inspected raw S0001, S0002 and S0004 requirements and the prior base-run approval manifest. Requirements remain unchanged. Prior run 2026-10-23-9a04b327 has approved_phases A/B; its raw gate-decisions records operator decisions. The new run is PHASE=B, existing feature, rework of current design in response to the independently recorded three high findings. G1/G2/G3 are not applicable to this Phase B run; no new Phase A checkpoint is asserted.

## Reconciliation basis

The approved design has concrete gaps despite the historical approval. Replace its rejection selector with the required direct baseline, add enforceable conversion supervision, and enforce the existing single-worker qualification topology. Preserve the older plan and review evidence. The architecture revision and exact proof changes will be recorded below before G5 approval.

## Gate status

- G4: pending architecture repair and ontology synchronization.
- G5: pending ordered exit validation and explicit operator architecture approval. No approval token is recorded.

## Phase B reconciliation and owning-role verification

Architect replaced the three conflicting/insufficient controls in the existing assembly plan; the earlier approval and independent review remain preserved. No requirements or thresholds changed. All new protocols are future implementation obligations.

| Finding | Revised source | Resolution at planning level |
|---|---|---|
| PM-1 | feature-assembly-plan.md Steps 6–7; rejection/acceptance/rollback table | Initial and rejected ordinary jobs select direct-baseline/v1. Candidate configs and queues are isolated. New submission identities include pipeline; legacy keys/payloads retain graph-direct meaning. Drain/cancel candidate jobs before branch proof. Restart/new-source assertions verify actual selection. PM confirms this satisfies unchanged S0004 AC7. |
| ARCH-1 | Step 2, Supervised conversion and checkpoint handshake | A spawned conversion-only process cannot infer or publish ready; durable ownership/start ACK closes the orphan window. Parent watchdog/latch selects failure at the unchanged 300-second bound, rejects late handoff, and fences publication. Bounded group kill/reap, orphan cleanup and late/hung-converter tests are specified. |
| BLD-1 | Steps 0a and 4 | One host processing worker per canonical dedicated endpoint, shared fixed directory/inode, noninherited flock and internal semaphore 1. A competitor exits before work. Durable pre-HTTP marker prevents overlap after uncertain outcomes; controlled provider group exit and pinned restart precede marker clear. Two-process refusal, SIGKILL, ambiguous timeout, health-only bypass rejection and fsync-failure zero-send tests are explicit. |

Architect owns the revised design and KG notes. Code Reviewer independently read the landed revision and found no residual blocker for these targeted repairs; specifically challenged new-engine idempotency, orphan launch registration, fixed guard sharing, late deadline acceptance and provider requests surviving a worker. Those challenges were resolved in the written protocols/test inventory before freeze. This is a planning challenge disposition, not a runtime signoff or feature role report.

Raw supporting metadata updated consistently: ADR-0060 control rationale (still Proposed), feature README/GETTING-STARTED/STATUS (pending approval), BLUEPRINT §4.8/§6, and the F0005 authored KG shard. Required story signoff roles now agree with the design's existing five-role requirement. No new canonical concept, endpoint, permission or shared schema is introduced.

## Gate execution results

- **G4 PASS:** kg-compile and kg-check-drift each exited 0 through run-gate.py. Only the F0005 authored shard was edited; projections/ROADMAP were generated. No new shared canonical node was needed.
- **G5 pre-approval validation PASS:** all seven operations completed in order with exit 0: validate-stories, generate-story-index, validate-trackers --skip-feature-evidence, kg-write-coverage, kg-check-drift-exit, kg-check-reproducible, validate-templates. Evidence: lifecycle-gates.log, artifacts/validation/ and gate-state.json.
- **Supplementary checks PASS:** F0005 product plan-readiness returned findings=[]; git diff --check clean. Raw Phase A PRD/stories/checklist and historical review report are unchanged; prior plan approval remains intact (artifacts/preserved-inputs.txt).
- **G5 architecture approval PENDING:** run-gate.py stopped normally at approve-phase-b after validation. The operator has not yet reviewed/approved this concrete revision. No token, attestation, supersession or approval publication is invented. The plan manifest remains draft. The old approval does not approve this amended design.

## Next gate

Present the revised architecture and passing checks to the operator. On explicit Phase B approval: record the actual response/timestamp here, make all approval-status planning edits, attest approve-phase-b against gate-decisions.md, then rerun G5 so its required post-approval compile/coverage/plain-KG/trackers/approve-plan operations run in order. Make no product planning edits afterward without refreshing coverage again. Only approve-plan.py may supersede the earlier planning approval. Until then, the rework is a validated draft awaiting approval, not an approved implementation handoff.

## Explicit operator Phase B approval — 2026-10-25T22:17:25.637087+00:00

The operator replied verbatim **`approve`** to “Do you approve the revised Phase B plan?” after the concrete repairs and passing seven pre-approval validations were presented. This is explicit approval of the amended F0005 architecture in run `2026-10-25-50fcf658`, mapped to checkpoint `approve-phase-b`; it is not a claim that the operator literally typed the checkpoint ID.

Decider: operator. Recorded by: architect role. Scope: the three design repairs, aligned metadata and unchanged approved requirements/thresholds. No runtime implementation, ADR acceptance or activation is authorized by this planning approval. Approval-status text was updated in the assembly plan, README, GETTING-STARTED, STATUS, BLUEPRINT, ADR-0060 design note and authored F0005 KG shard before attestation. Formal ADR-0060 status remains Proposed.

G5 architecture decision: APPROVED by operator. The procedural journal and manifest record the required post-approval refresh and automated publication result. Only approve-plan.py may publish/supersede; this approval record is retained unchanged after attestation.
