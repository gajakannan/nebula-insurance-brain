# Action Context

## Run Identity

- NEBULA_PRODUCT_ROOT: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- Root source: shell environment, normalized by the framework resolver with explicit --product-root.
- Framework: /home/gajap/uSandbox/repos/nebula/nebula-agents
- Action: plan; FEATURE_ID: F0006; PHASE: A+B; FEATURE_MODE: new.
- PLAN_RUN_ID: 2026-11-01-7d6d19ce; minted once by init-run.py, active contract 2026-07-11.
- FEATURE_SLUG: assertion-plane-origin-and-interpretation-basis
- FEATURE_PATH: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/features/F0006-assertion-plane-origin-and-interpretation-basis
- PLAN_RUN_FOLDER: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-01-7d6d19ce
- Feature evidence index root: not created (base-run-only plan).

## Inputs

Operator plan prompt; project_context.py product instructions; framework router/map/use/extensions/plan; REGISTRY, ROADMAP and BLUEPRINT; routed KG F0006 and Assertion lookup; raw ADR-0005/0035/0063/0065/0074, master blueprint sections 11/17/28, glossary, existing result schema and F0005 final STATUS.

## Assumptions

The existing reserved folder is not an existing plan: it contained only README and the dated authorized amendment, so FEATURE_MODE=new creates Phase A artifacts without overwriting prior requirements or architecture. Existing personas and permission grants are reused. Representing future origins/kinds does not activate their producers.

Architect-owned bounded decisions: normalization and original-selector mapping (including the EX-SEM-005 case/spacing example); schema version/reader dispatch; compatible MACHINE_EXTRACTION origin transition; transaction and rollout/rollback design; exact existing consumer call sites. These bounded design choices were resolved in ADR-0075 and the approved assembly plan; no unresolved insurance business rule was invented.

## Scope Boundaries

Five stories, 35 ACs: typed claims; open storage/versioned contract; structural admission; mood/origin safeguards and review hooks; existing-consumer compatibility. No new screen or permission grants. No pipeline activation, open extraction/alignment, durable drops/full run orchestration, normative execution or full canonical orchestration. Preserve F0005 final direct-baseline/v1 defaults and F0004 legacy provenance honesty. ADR-0065 remains Proposed.

Strict role sequence: Product Manager authors Phase A; Architect authors feature/node shards, contracts, ADRs and assembly plan only after G3 explicit approval. No compiled KG or generated tracker regions are hand-edited. The Architect completed the feature/node/story bindings and removed the reserved exclusion; G4 passed. Roadmap remains Next.

## Lifecycle Stage

G1–G4 passed. Operator explicitly approved Phase A with approve-phase-a and Phase B with approve-phase-b after the G5 preapproval checks passed. Both tokens are in gate-decisions.md. All approval metadata edits are complete before the G5 checkpoint attestation. The durable G5 journal records execution of the postapproval compile/coverage/reproducibility/plain-KG/tracker/publication operations; evidence-manifest.json is authoritative for automated publication status. Do not change its status manually. No planning-source edits may follow the final G5 refresh.

This is planning approval only: five stories and 35 ACs are unstarted, no feature evidence package exists, and Proposed ADRs still require runtime proof. Roadmap remains Next. Implementation is a separate feature action.

Durable working state: workstate.yaml in this run folder; use workstate.py --state-file explicitly. Gate journal and gate-decisions.md remain authoritative for approval and position.
