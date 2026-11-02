# Gate Decisions — F0006 / 2026-11-01-512e9303 (plan, PHASE=B, existing)

NEBULA_PRODUCT_ROOT: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1–G3 | SKIP | Architect (Claude) | 2026-11-01 | PHASE=B. Phase A requirements were approved in run 2026-11-01-7d6d19ce and are unchanged. | No | - |

## Reconciliation With Existing Assembly Plan

This run amends, and does not overwrite, the approved F0006 assembly plan from run 2026-11-01-7d6d19ce:

- **AR-1 (High)** — interpretation basis on corrections. Operator chose "Inherit; v1 unchanged". v2 correction children copy the original basis into both the carrier and the record. v1 corrections keep the existing hard-coded EXPLICIT as a documented legacy boundary (S0005 AC3); they stay version 1 and confer no v2 eligibility. A reviewer-supplied basis is deferred to a later contract amendment.
- **AR-2 (Medium)** — persistence mapping. Now specified:
  - v2 carrier `subject_type` comes from the admitted subject reference's `entity_type`.
  - A correction child is v2, with its own extension (record/snapshots copied, origin HUMAN_REVIEW).
  - The child gets its own evidence rows, `UUID5(child, ordinal)`, copied from the original or from re-admitted evidence.
  - `raw_item_sha256` hashes the validated correction input; `admission_sha256` hashes the child record plus its lineage.
  - The integrity trigger accepts NULL-run HUMAN_REVIEW v2 children only with a matching v2 original.

No other design element changed.
| G4 | PASS | Architect (Claude) | 2026-11-01 | kg compile + drift exit 0; no shard semantics changed | No | G5 |

## G5 Review Package

All seven pre-checkpoint exit operations passed in order: validate-stories, story index, trackers, coverage refresh, drift, reproducibility and templates. `git diff --check` and the API YAML parse also pass. The driver is paused at `approve-phase-b`. No approval token has been received; this is not a G5 PASS.

Review points:

1. v2 corrections inherit the original basis. v1 corrections keep EXPLICIT as a legacy boundary, read under S0005 AC3. S0001 AC4 is enforced for v2 claims; the AC text itself is unchanged.
2. A v2 correction child is a full v2 record, with its own extension, evidence rows and hashes.
3. v2 `subject_type` comes from the subject reference's `entity_type`.
4. The trigger enforces matching lineage for HUMAN_REVIEW v2 children.

Proposed operator token: `approve-phase-b`.

## Explicit Phase B Approval

- Checkpoint: `approve-phase-b` (G5)
- Operator token: `approve-phase-b`
- Source: operator's chat reply after reviewing the AR-1/AR-2 Phase B rework package above.
- Recorded by: Architect (Claude), 2026-11-01
- Preapproval condition: all seven G5 exit operations completed in declared order with exit 0; the driver paused at approve-phase-b.
- Scope approved: v2 corrections inherit the original interpretation basis; v1 corrections keep EXPLICIT as a legacy boundary; v2 correction child persistence (carrier, extension, evidence rows, hashes, trigger lineage); v2 `subject_type` mapping. Phase A requirements are unchanged.
- Approval-status edits completed before attestation: STATUS, README, PRD plan-run line, assembly plan run line, ADR-0075 design-review line, and the kg-source F0006 shard notes and validation_gate.
- ADR-0065/0075 remain Proposed. All stories remain Not Started. Publication is by the G5 journal and approve-plan.py; no manual manifest change is made.
