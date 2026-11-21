# Gate Decisions — F0011 — 2026-11-20-ccb1bd39

NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`
Action: plan; phase: A+B; feature mode: new; policy: 2026-07-11.

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|------|----------|---------|-----------|-----------|----------|-----------|

| G1 | PASS | Codex / Product Manager | 2026-11-20T05:51:03.529245+00:00 | Requirements derive from existing blueprint/ADR decisions; negative cases and mutation boundaries are explicit; technical design tasks belong to Phase B | No | Operator requirements review at G3 |
| G2 | PASS | Codex / Product Manager | 2026-11-20T05:51:03.529245+00:00 | Six stories pass strict validation with zero warnings; index regenerated (60 total stories); tracker validation has zero errors/warnings; dependency references recorded | No | Architect completes KG bindings at G4 |

| G3 | PASS | Operator; recorded by Product Manager | 2026-11-21T01:01:49.062124+00:00 | Actual response approve recorded as approve-phase-a; attested and approve-plan.py G3 completed | No | Phase B design authorized only |
| G4 | PASS | Codex / Architect | 2026-11-21T01:01:49.062124+00:00 | run-gate.py completed kg-compile and kg-check-drift, both exit zero; authored shards only | No | G5 architecture checkpoint |

These are the recorded PM judgments after successful run-gate.py G1/G2 execution.
The generated example rows were removed before execution; they are not evidence.

## Approval record

Phase A approved by the operator in chat after review of the six-story, 41-AC packet.
Exact operator response: `approve`. Canonical checkpoint token: `approve-phase-a`.
Phase B approved by the operator with the exact response `approve-phase-b` on 2026-11-20.

## Reconciliation

- F0011 contained a reserved README and an excluded feature shard, with zero
  stories and no existing assembly plan. Preserve its 2026-11-08 ownership amendment.
- The explicit operator prompt controls over older action prose: edit authored
  KG shards only in the permitted role and regenerate projections; never edit
  the generated mappings or tracker tables.
- Phase A leaves the excluded feature shard intact. The Architect replaces that
  reserved mapping with full feature/story bindings at G4 after Phase A approval.
- Actual framework revision matches the product pin:
  `840e724b72fdbaf8157dacfee579488252e1a193`.

## G3 pause — historical

run-gate.py reports status `paused`, pending checkpoint `approve-phase-a`.
At the end of Phase A this was waiting for the operator; the subsequent approval is recorded below. The concrete review packet
is F0011 PRD.md, README.md (six story links), personas.md, STATUS.md and the
acceptance checklist. At that time no approval was recorded; the following operator response authorized Phase B.

## Phase A clarification disposition

- Existing baseline decisions settle the required dialect, value shapes,
  information states and ownership. No new insurance business rule was invented.
- Phase B must settle exact schema-source authority, supported subset/formats/
  references, annotation/UI metadata handling, Pydantic generation/adaptation,
  OpenAPI wiring, existing-consumer adoption, input bounds and rollback.
  These are architecture deliverables, not unresolved stakeholder requirements.
- Initial strict validation identified missing explicit negative/audit wording;
  the story prose was clarified. Final strict validation passes all six stories
  with zero warnings. No runtime case is claimed as executed.
- Severity policy profile `none` computes PASS; this never supplies the required
  user approval. Changed executable-line coverage remains a future 80% minimum.
- The initial scaffold included a feature-action assembly PASS and placeholder
  source-control branch. They were removed/corrected in the draft manifest;
  no assembly review was performed, and manifest status remains draft.

## G3 operator approval — 2026-11-20T23:05:04.235465+00:00

- Checkpoint: `approve-phase-a`.
- Operator response: `approve`, answering the immediately preceding Phase A review request.
- Decision: APPROVED for Phase A requirements only; six MVP stories and 41 ACs.
- Recorded by: Codex / Product Manager.
- Phase B is now authorized for design; its later approval remains required at G5.

## G5 pre-approval exit validation — historical review checkpoint

The gate journal records these seven operations completed in the required order,
all exit 0: validate-stories; generate-story-index; validate-trackers with
--skip-feature-evidence; kg-write-coverage; kg-check-drift-exit;
kg-check-reproducible; validate-templates.

At that checkpoint G5 waited for `approve-phase-b`; only Phase A had been
approved. The subsequent actual operator token is recorded below. All approval-
status edits precede G5 attestation; the ordered post-approval operations refresh
projections and coverage, finish plain KG/tracker checks and publish approval last.

Additional checks: six design schemas/21 payload resource closure and 74 synthetic
expectations pass with required Python format checkers; API validation passes
with six retained baseline warnings; product feature readiness is pass with no
findings; orphan check passes; tracked diff-impact has no runtime symbols.
These are planning checks, not AJV/Pydantic/install/consumer runtime proof.

The API warnings reflect existing deliberate conventions: public no-I/O health
has no credential/error catalog, denials use non-disclosing 404 rather than 403,
and the existing review endpoint's 200 receipt covers duplicate/stale outcomes.
No route/status behavior is changed to silence those warnings.

KG risk 7/10 (high) is a shared-hub diagnostic, not a severity-gate finding. The
assembly plan requires independent plan-review, all five implementation signoffs,
broader guard/compatibility tests and maintainer/additional-reviewer acknowledgement
before a future implementation merge. The plan profile remains none; no merge or
runtime acceptance is being requested here.

## G5 operator architecture approval — 2026-11-20T20:26:17.733668-05:00

- Exact operator response and checkpoint token: `approve-phase-b`.
- Decision: APPROVED for Phase B architecture of F0011, plan run `2026-11-20-ccb1bd39`.
- Scope reviewed: six stories/41 ACs; ADR-0079 design direction; 21-resource
  inventory, six design schemas and 74 synthetic expectation cases.
- Recorded by: Codex / Architect, acting on the actual operator message.
- All seven required pre-approval exit operations completed with exit 0 before
  this approval. All approval-status edits are made before checkpoint attestation.
- G5 must recompile, write coverage, pass reproducibility/plain KG/tracker checks
  and publish through approve-plan.py. No manual manifest approval is performed.
- ADR-0079 and ADR-0039 stay Proposed pending their runtime proofs and later
  explicit acceptance. No runtime completion, production activation or merge is approved.
- No further planning edit may follow the post-approval G5 run; any required repair
  must be followed by the mandated compile/coverage/plain KG refresh.
