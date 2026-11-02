# Gate Decisions — F0006 / 2026-11-01-7d6d19ce

NEBULA_PRODUCT_ROOT: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|---|---|---|---|---|---|---|
| G1 | PASS | Product Manager (Codex) | 2026-11-01T19:28:27.332683+00:00 | Requirements traced to authorized amendment; bounded design choices explicitly assigned to Phase B | No | G2 tracker validation |
| G2 | PASS | Product Manager (Codex) | 2026-11-01T19:28:27.332683+00:00 | Five stories pass strict validation; STORY-INDEX regenerated; trackers have zero errors/warnings; dependency audit recorded | No | G3 operator review |
| G3 | PASS | Operator token; Product Manager attestation | 2026-11-01T20:16:49.961705+00:00 | Explicit approve-phase-a recorded; checkpoint attested and approve-plan.py Phase A operation completed | No | Phase B; A+B manifest remains draft |
| G4 | PASS | Architect (Codex) | 2026-11-01T20:16:49.961705+00:00 | Authored feature/node shards compiled; drift check exited 0; all five stories mapped with planning-only bindings | No | G5 architecture review |

## Clarification Judgment

The dated feature amendment and existing accepted decisions define the business scope. Five stories contain 35 measurable ACs, explicit negative outcomes, internal entry points, source/actor access restrictions, append-only and reload evidence requirements, and no new UI. New representation support does not enable future producers. Phase B owns the explicitly listed design choices in action-context.md, under the approved requirements constraints. No unresolved business rule is invented.

F0005's final approved rejection decision supersedes older activation/proof summaries for compatibility planning. Its existing v1/direct baseline stays default. ADR-0065 is not promoted by planning. Dependency evidence references and audit-pending boundaries are recorded in artifact-trace.md.

## Approval Checkpoints

- G3 / approve-phase-a: operator token received and recorded below; attestation/publication operation follows.
- G5 / approve-phase-b: explicit operator token received after all seven pre-checkpoint exit operations passed; recorded below for final attestation and automated publication.

The initial instruction to execute plan is not a review approval. Manual checkpoint attestations will be recorded only after the operator explicitly approves the corresponding reviewable artifacts.

## G3 Review Package

Phase A is ready for review: five stories, 35 ACs, three existing personas and no new UI. Review the feature PRD, story files and acceptance checklist. The durable gate driver is paused at `approve-phase-a`; no approval operation has run. Proposed explicit operator token: `approve-phase-a`.

Validation: strict stories PASS (all five, no warnings); generated index PASS (37 total repository stories); tracker validation PASS (zero errors/warnings, feature-evidence intentionally skipped); semantic educational schema/reference checks PASS. Initial strict validation found audit expectations outside the AC section; they were made explicit in S0002/S0003/S0004 ACs and the rerun passed. Both attempts are preserved in commands.log.

Manual judgment: G3 has no PASS decision until the operator reviews and approves this set. G4/G5 are not reached. The plan manifest remains draft. Phase B will complete the KG mapping, remove the reserved exclusion, compile projections and run the required ontology/exit checks after G3 approval.

## Explicit Phase A Approval

- Checkpoint: `approve-phase-a` (G3)
- Operator token: `approve-phase-a`
- Source: operator's chat reply after reviewing the five-story, 35-AC Phase A package.
- Recorded by: Product Manager (Codex)
- Recorded at: 2026-11-01T19:55:15.165196+00:00
- Scope approved: F0006 requirements in PRD/personas/stories/acceptance checklist, with documented exclusions and Phase B design choices.
- This authorizes Phase B architecture; A+B manifest remains draft until G5.

## Phase B Design Decisions and G5 Review Package

The Architect authored the feature assembly plan, Proposed ADR-0075, three versioned JSON Schemas, 16 positive/negative contract fixtures, worked/boundary examples, feature ER/component diagrams, data-model/glossary/blueprint/API refinements, required signoff matrix and KG source/story mappings. G4 compile and drift passed. No implementation files or feature evidence package were created.

G5 reached `approve-phase-b` after these operations completed in order with exit 0: story validation, story-index regeneration, tracker-only validation, KG coverage refresh, KG drift, KG reproducibility and framework template validation. The driver is paused at the required manual checkpoint. This is not a G5 PASS or A+B approval.

Additional checks: 16 schema/example cases passed with local-only references; Brain structural plan-readiness and semantic teaching validation passed. API validation passed with six existing convention warnings, identical to HEAD baseline. Diff-impact reported zero changed/blast symbols and no affected code nodes; documentation paths have no symbol coverage. That tool does not cover untracked design files, which were separately included in local link/schema checks and KG compilation.

Review points: preserve legacy raw records and strict readers; add immutable v2 semantics and server grounding; inherit mood/origin restrictions through correction/commit; source READ plus COMMIT decisions share one transaction through an optional trusted callback. No new grants, model calls, extraction activation or UI. The current pilot's unregistered legacy evidence behaviour remains an explicit compatibility boundary; attributable v2 evidence/review/correction lineage is guarded. F0016/F0018/F0022/F0066 retain broader adoption/orchestration/display/alignment ownership. Formal ADR-0065/0075 acceptance requires runtime proofs and is not implied by plan approval.

Proposed explicit operator token: `approve-phase-b`. After receiving it: make all approval metadata edits to STATUS/README/PRD/assembly plan/ADR/feature shard and blueprint; record token; attest the checkpoint with gate-decisions.md; rerun G5 post-approval operations (compile, coverage refresh, reproducibility, plain validate, trackers, final approve-plan.py). No planning edits follow that final refresh. Resume this same run if publication is interrupted; do not manually approve the manifest.

Final pre-review integrity: plain KG validate.py exited 0 with current coverage; nonblocking existing symbol/vocabulary index warnings are in the captured output. git diff --check passed. No Phase B token, attestation or post-approval publication operation has occurred.

## Explicit Phase B Approval

- Checkpoint: `approve-phase-b` (G5)
- Operator token: `approve-phase-b`
- Source: operator's chat reply after reviewing the Phase B assembly plan, ADR-0075, schema trio and ontology package.
- Recorded by: Architect (Codex)
- Recorded at: 2026-11-01T21:19:51.701476+00:00
- Preapproval condition: all seven G5 exit operations completed in declared order with exit 0; the driver paused at approve-phase-b.
- Scope approved: the reviewed five-story/35-AC F0006 Phase B design, with existing v1 defaults, explicit pilot legacy boundary and future feature handoffs.
- Approval-status edits completed before attestation: feature STATUS/README/PRD/checklist/GETTING-STARTED/assembly plan; ADR-0075 design-review metadata; BLUEPRINT, architecture index/data model, glossary, API/schema metadata; authored feature/schema/ADR KG shards.
- ADR-0065 and ADR-0075 remain Proposed pending their runtime proofs. All stories remain Not Started.
- Final stage result and publication are determined by the durable G5 journal and approve-plan.py; no manifest status is changed manually.

This approval evidence is frozen for attestation. G5 must execute compile, coverage refresh, reproducibility, plain KG validation, tracker-only validation and approve-plan.py in order. Any failure keeps automated publication incomplete; resume this same run. No planning-source edit follows the final refresh.
