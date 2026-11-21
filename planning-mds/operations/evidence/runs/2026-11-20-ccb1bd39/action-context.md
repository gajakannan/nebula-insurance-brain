# Action Context — F0011 plan

## Run Identity

- NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`
- Source: shell environment, normalized by the framework resolver with explicit absolute argument.
- Framework: `/home/gajap/uSandbox/repos/nebula/nebula-agents`
- Framework revision/product pin: `840e724b72fdbaf8157dacfee579488252e1a193`
- Action: plan; FEATURE_ID: F0011; PHASE: A+B; FEATURE_MODE: new.
- FEATURE_SLUG: json-schema-contract-system.
- FEATURE_PATH: `planning-mds/features/F0011-json-schema-contract-system` under product root.
- PLAN_RUN_ID: `2026-11-20-ccb1bd39`, minted once by init-run.py.
- PLAN_RUN_FOLDER: `planning-mds/operations/evidence/runs/2026-11-20-ccb1bd39` under product root.
- Contract version/effective date: 2026-07-11; evidence scope: base-run-only.
- FEATURE_INDEX_ROOT is resolved for identity only; it is not created during plan.

## Inputs and context

Operator prompt; project_context.py product instructions; framework ROUTER,
agent-map, AGENT-USE, PROJECT-EXTENSIONS, plan action and Product Manager skill;
registry/roadmap/blueprint; KG routing; F0011 reserved README; ADR-0013/0039;
master blueprint 25–27/98/106.3/107.3–4/112; existing typed contracts and personas.
Raw contracts govern over KG routing. No current-run pointer is used.

## Assumptions and design tasks

No new business rules. Existing value/answer/temporal shapes are the compatibility
baseline; the headless AJV consumer creates no screen. Phase B must choose exact
source/artifact authority, subset/formats/references, annotations, Pydantic
generation/adaptation and existing consumer adoption. It cannot silently change
the approved PRD. Database persistence is not assumed necessary.

## Scope Boundaries

Six MVP stories, 41 ACs; no runtime implementation in this action. F0012/F0013
own vocabulary, F0015 extraction compilation, F0016 searched scope execution,
F0014/F0023 completeness/display, F0018 full commit orchestration. ADR-0039 stays
Proposed until all proofs are satisfied. Only Architect authors KG shards under
the strict operator prompt. Phase A retains the excluded F0011 stub until G4.

## Lifecycle Stage at Phase A review (historical)

Phase A prepared; G1 clarification and G2 tracker sync passed. G3 is paused
at checkpoint approve-phase-a and requires an actual operator response before
attestation, approve-plan.py G3 publication or any Phase B work.
Severity profile none; runtime changed-code coverage floor 80% in the feature run.

## Resume

Run resume-brief.py with this absolute product root and run ID, reload product
instructions, then inspect gate-state.json and workstate digest. Do not mint a new run.

## Phase A approval and Architect handoff

Operator response `approve` authorized Phase A. G3 attestation and approve-plan.py
completed; PHASE=A approval was published while the A+B manifest stays draft.
Active role: Architect. Root remains
`/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`.
The assembly plan, contract design, ADR-0079, six new design schemas, 21-resource
inventory/profile, 74 synthetic expectations and authored KG shards are prepared.
Next: G4 ontology compile/drift, then G5 ordered exit checks and separate operator
architecture approval. No runtime implementation or new feature evidence index.

## Phase B review packet (historical)

G1–G4 completed. G5 pre-approval exit operations all returned zero, now waiting
for operator approve-phase-b. Phase B and formal ADR acceptance are not approved.
After the actual response, complete all approval-status edits before attesting
and rerunning G5; its post-approval plain KG check and approve-plan.py are required.
Root and run ID stay fixed. The risk/compatibility controls are in the assembly plan.

## Current position — operator-approved A+B planning

Phase B token `approve-phase-b` received on 2026-11-20, following Phase A's `approve`.
All approval-status changes precede G5 attestation and final regeneration. The
G5 journal/manifest record final publication; only approve-plan.py may set the
manifest approved after all required post-approval checks. Independent plan-review
is next; no feature run, implementation or formal ADR acceptance is included.
Recorded absolute root and run ID remain unchanged. Active role: Architect.
