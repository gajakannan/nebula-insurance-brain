# F0009 Plan Action Context

## Run Identity

- NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` — shell environment, resolved once with `_product_root.py` and passed explicitly thereafter.
- Action: plan; feature: F0009; slug: provenance-and-human-correction-lineage.
- PHASE: A+B; FEATURE_MODE: new; PLAN_RUN_ID: `2026-11-24-bfdbbf04` (minted once by init-run.py using the contract scheme).
- Feature path: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/features/F0009-provenance-and-human-correction-lineage`.
- Run folder: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-24-bfdbbf04`.
- Contract: 2026-07-11, base-run-only; severity profile none, computed PASS; implementation coverage floor 80%.
- Starting workspace: `/home/gajap/uSandbox/repos/nebula`; framework: `/home/gajap/uSandbox/repos/nebula/nebula-agents`.

## Inputs and loaded context

Operator plan prompt plus framework router/map/use/extensions/action, product project_context.py output (BLUEPRINT and docs/agent-instructions.md), registry/roadmap, scoped KG lookup/canonical refs, F0009 dated amendments and raw dependency contracts. Project context loaded successfully; no required product check is declared for action plan.

## Assumptions / requirement decisions to review

PRD A1–A3: bounded internal reader and existing routes; exactly one reserved future candidate identity per new effective CORRECT; honest incomplete legacy/undelivered provenance. The operator approved these Phase A scope interpretations with approve-phase-a at G3. Architecture details are now specified in the Phase B assembly plan and proposed ADR-0080; Phase B was explicitly approved with approve-phase-b, recorded 2026-11-25T02:16:33.637463+00:00.

## Scope Boundaries

Phase A writes PRD, personas, six stories/41 ACs, checklist, STATUS and index/setup skeletons, worked examples and authored tracker prose. PM does not edit KG source or generated projections. The existing reserved F0009 shard supplies the initial id/path/status/dependencies stub; its planned exclusion is removed by the Architect at Phase B/G4, as the shard explicitly requires.

Phase B may start only after explicit G3 approval. It authors assembly plan/ADR/contracts, final KG source bindings and role matrix. Future feature action owns runtime implementation/evidence; F0010/F0018/F0020/F0022/F0023/F0026/F0041 keep their delegated scope.

## Lifecycle Stage

Phase A artifacts validated; G1/G2/G3 passed via the gate driver after exact operator token approve-phase-a. Architect Phase B approved by the operator; G4 ontology sync passed on its first attempt. All seven G5 pre-approval operations passed in order; exact operator token approve-phase-b has now been recorded. Approval-status edits precede checkpoint attestation and the G5 post-approval refresh. The authoritative gate journal and automated manifest publication record completion; there is no feature evidence index, role report or latest-run pointer for F0009.
