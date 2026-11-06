# Action Context

## Run Identity

- action: feature
- feature_id: F0006
- run_id: 2026-11-02-5a00b0ff
- NEBULA_PRODUCT_ROOT: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- framework_root: /home/gajap/uSandbox/repos/nebula/nebula-agents
- mode: clean
- slice_order_source: assembly-plan
- run_id_prior: null
- rerun_of: null
- contract_version: 2026-07-11

## Inputs

- Environment-supplied product root, normalized once with the framework resolver.
- Product context loaded by `project_context.py --action feature`.
- Framework ROUTER, agent map, AGENT-USE, PROJECT-EXTENSIONS and feature action.
- Tier-1 F0006 lookup, approved assembly plan, STATUS, GETTING-STARTED and five stories.
- Concurrent manifest check found no other F0006 feature-completion run.

## Assumptions

The approved plan governs the five stories and 35 ACs. It adds versioned assertion
storage, structural admission and consumer guards; no UI or live extraction activation.
Runtime, deployment and security booleans agree with the implemented code, migration
and authorization consumers; frontend remains out of scope. Actual changed paths and
source hashes are recorded in the manifest and diff/coverage/security inventories.

## Scope Boundaries

Only the approved F0006 five-story assertion contracts/storage/admission/consumer
guard slice is authorized. No UI, producer activation, new grants or deferred
F0016/F0018/F0022/F0066 work is introduced. Required roles remain the five listed
in STATUS.md. Runtime/deployment/security scope booleans remain true after reconciliation.

## Lifecycle Stage

G0 through G8 completed through run-gate.py. Operator G4 approval with the exact SEC-01 mitigation is recorded in gate-decisions.md. G5 verifies all required signoffs; G6 candidate validation passed; G7 as-built source reconciliation passed; G8 PM archive, patch-before-publication, post-archive coverage/drift and final plain KG validation passed. Manifest approved; feature archived at `planning-mds/features/archive/F0006-assertion-plane-origin-and-interpretation-basis`. Original runtime/validator failures are retained as history.

## Resume Update — 2026-11-03T00:06:32+00:00

The operator resumed this same run after changing Codex permissions. Actual G0
execution created gate-state.json. G0 readiness judgment is recorded; base evidence
shape and a premature security-scan validator check are being repaired before
stage completion. The earlier runtime-blocked lifecycle text is historical.

### G0 completed — 2026-11-03T00:07:47+00:00

Assembly judgment and validate-g0 pass. The journal now supports normal resume; no new run was created.
