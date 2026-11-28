# Plan Review Action Context

- Action: plan-review; contract: read-only-audit, policy 2026-07-11.
- PLAN_SCOPE: feature (operator supplied FEATURE_ID=F0021).
- TARGET: F0021.
- DIFF_RANGE: omitted; inspect current working-tree planning package, not a change-only review.
- NEBULA_PRODUCT_ROOT: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain; source: shell environment, explicitly passed to resolver and all subsequent product-aware invocations.
- Session starting directory: /home/gajap/uSandbox/repos/nebula.
- Framework: /home/gajap/uSandbox/repos/nebula/nebula-agents.
- FEATURE_SLUG: native-react-semantic-shell-and-oidc-session (REGISTRY.md row F0021).
- FEATURE_PATH: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/features/F0021-native-react-semantic-shell-and-oidc-session.
- PLAN_REVIEW_RUN_ID: 2026-11-27-d1148686; generated once using secrets.token_hex(4).
- PLAN_REVIEW_RUN_FOLDER: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-27-d1148686.
- Review scope: F0021 raw requirements, all nine stories and associated acceptance criteria, UI/screens, API/schema/session/migration design, identity/security dependencies, authorization, ADRs, current planning approval history, tracker and KG alignment, role handoffs and proof plan. Shared artifacts are inspected only for F0021 and prerequisite compatibility.
- Routing: lookup.py F0021 resolves exact feature and its concrete planning folder; routing is subordinate to raw evidence.
- Reviewers: product-manager owns Product Readiness; architect owns Architecture Readiness; code-reviewer owns Buildability Challenge. Three parallel lanes required by PR1.
- Write boundary: this base run only (plus temporary orchestration helpers in /tmp). No plan, source, KG, tracker, approval or feature evidence edits. No evidence-manifest.json.
- Runtime proof is future feature work. feature-assembly-plan.md is not required as a plan deliverable; its existing design content may be read.
- Required project check: plan-readiness at PR2 before_stage_complete via run-gate.py, in addition to every core PR2 validator.
- Framework and product instruction sources: agents/ROUTER.md, agent-map.yaml, AGENT-USE.md, PROJECT-EXTENSIONS.md, plan-review.md, plan.md, feature.md; role SKILLs; planning-mds/BLUEPRINT.md; docs/agent-instructions.md; docs/plan-review-checklist.md.
