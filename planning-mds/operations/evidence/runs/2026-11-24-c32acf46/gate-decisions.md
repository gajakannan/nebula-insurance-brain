# Gate Decisions — F0009 / 2026-11-24-c32acf46 (plan, PHASE=B, existing)

NEBULA_PRODUCT_ROOT: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1–G3 | SKIP | Architect (Claude) | 2026-11-24 | PHASE=B. Phase A requirements were approved in run 2026-11-24-bfdbbf04 and are unchanged. | No | - |

## Reconciliation With Existing Assembly Plan

This run amends, and does not overwrite, the approved F0009 assembly plan from run 2026-11-24-bfdbbf04.

**PR-H1 (High): refused-attempt replay.** Operator chose "Always re-evaluate".
- Replay identity now comes only from ReviewDecision rows. A stored refused attempt never short-circuits a request; a matching resubmission is evaluated against current state, so a BATCH_REFUSED sibling resubmitted alone applies.
- Attempt rows are get-or-create on the unique key (review_item_id, event_sha256, outcome), under the item locks. Reused rows are unchanged (append-only), and a changed outcome appends a new row.
- Each refused request writes one review_submission_refused audit per attempt it refused.
- An attempt and a later decision with the same (item, event) coexist. The decision governs replay.
- Changed: assembly plan Step 3 items 3–5, the Mutation Traceability row and the S0002 AC6 proof; migration-design.sql unique key; ADR-0080 Decision §5 and proof row.

**PR-H2 (High): edge semantics.**
- Edges read `<source> <kind> <target>`.
- A closed per-kind (source kind, target kind) table is in the new Edge Semantics section of the assembly plan, with the stored basis for each kind. provenance-result-v1 enforces it through a per-kind oneOf plus uniqueItems.
- `reviewed_by` is retired. `reviews` runs from review_decision or review_attempt to the reviewed assertion, which gives refused attempts their linking edge.
- New kinds: located_in (evidence→content_artifact), interprets (interpretation_run→content_artifact), recorded_decision (fact_version→review_decision, needed for S0001 AC2 and S0003 AC5).
- Domain invariants: endpoints present, root connectivity ignoring direction, acyclic corrected_from/split_of, one edge per stored link.
- contract-examples.json gains one valid correction-lineage graph and four negative cases (reversed direction, retired kind, duplicate edge, wrong endpoint kind). All 21 cases validate locally with Draft202012 and a closed registry.

No other design element changed. PR-M1, PR-M2 and PR-L1–L5 remain routed to feature G0.

| G4 | PASS | Architect (Claude) | 2026-11-24 | kg compile and drift checks exit 0. Only a shard note was added; no binding semantics changed | No | G5 |

## G5 Review Package

All seven pre-checkpoint exit operations passed in order: validate-stories, story index, trackers, coverage refresh, drift, reproducibility and templates. `git diff --check` is clean. contract-examples.json passes 21/21 (artifacts/phase-b-rework-examples.log). The driver is paused at `approve-phase-b`. No approval token has been received; this is not a G5 PASS.

Review points:

1. **PR-H1.** Refused attempts are history, never a replay key. A BATCH_REFUSED sibling resubmitted alone is re-evaluated and can apply. Attempts are get-or-create on (item, event, outcome), and each refused request writes its own refusal audit.
2. **PR-H2.** The closed 17-kind edge table (source kind → target kind, stored basis) is enforced in provenance-result/v1. `reviewed_by` becomes `reviews` (decision or attempt → assertion). New kinds: located_in, interprets, recorded_decision. Domain invariants: endpoints present, connected to root, acyclic ancestry.
3. Phase A requirements are unchanged. PR-M1, PR-M2 and PR-L1–L5 stay routed to feature G0.

Proposed operator token: `approve-phase-b`.

## Explicit Phase B Approval

The operator replied with the exact token `approve-phase-b` on 2026-11-24, after reviewing the G5 package above.

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G5 | PASS | Operator (approve-phase-b) + Architect (Claude) | 2026-11-24T21:53:16-05:00 | The Phase B rework resolving PR-H1 and PR-H2 is approved. Pre-approval exit validation was green. Post-approval refresh and approve-plan.py supersede plan run 2026-11-24-bfdbbf04 | No | PR-M1, PR-M2, PR-L1–L5 at feature G0; optional plan-review re-check |
