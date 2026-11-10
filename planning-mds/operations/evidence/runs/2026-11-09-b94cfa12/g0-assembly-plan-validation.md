# G0 Assembly Plan Validation — F0007

- Run: `2026-11-09-b94cfa12`
- NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`
- Reviewer: Claude (Opus 5.5) / Architect
- Review date: 2026-11-09
- Verdict: PASS
- Scope: assembly readiness only. No runtime implementation or final signoff is claimed.

## Source and approval baseline

The feature-local `feature-assembly-plan.md` is the primary implementation specification. It was authored and approved in plan run `2026-11-09-60865e32` (`approve-phase-a`, `approve-phase-b`, 2026-11-09), so G0 reconciles it rather than re-authoring it. Six story files carry 39 ACs (7/6/7/7/5/7). The plan was read with the PRD, README diagrams, worked examples, Proposed ADR-0077, the three design schemas (`fact-slot-key-v1`, `fact-answer-v1`, `fact-slot-resolution-result-v1`), `contract-examples.json` and the API contract. The commit 422 description already lists the ADR-0077 D5 lowercase codes. Tier-1 KG lookup routed context; raw artifacts govern.

## Assembly checks

| Check | Judgment and concrete handoff |
|---|---|
| Scope split | Backend owns pure domain (`brain_domain.fact_slots/fact_values/fact_answers`), the new `brain-factslots` application package, persistence (migration 0012, store), and the commit/API hook. Frontend and AI are out of scope: no `experience/` or `neuron/` path, model, prompt or MCP change. |
| Dependency order | Step 0 pilot snapshot, then the pure domain, the application package, persistence, commit integration and proof. The domain has no I/O; the commit hook depends only on a protocol in `brain_temporal`. |
| Integration checkpoints | Real PostgreSQL migration 0012 up/down/up with seeded pilot rows; two-session concurrent resolve; composite-FK and trigger negatives as the service role; EX-OWN-003 through `POST /facts/{id}/commits` and reload; non-disclosing denial before any reason; existing commit, review and assertion suites unchanged. |
| Ownership | Architect: plan, ADR-0077, schemas, this report and G7. Backend: engine code. QE: independently authored expectations, test plan, execution and coverage reports. DevOps: preflight, migration cycle and CI wiring. Code and Security reviewers: separate verdict reports. PM: signoff, trackers, archive and publication. No conflicting owner. |
| Migration lineage | Static AST inspection finds the sole head `0011`, so `0012_f0007_factslot_identity.py` keeps `down_revision="0011"`. Evidence: `artifacts/test-results/g0-migration-lineage.json`. No migration has run at G0. |
| Signoff and progress | STATUS.md already holds the Phase B required-role matrix: QE, Code Reviewer, Security Reviewer, DevOps and Architect are all Yes. The manifest `required_roles` now matches. Story × Role cells use the contract vocabulary; every story is still Not Started. |
| Scope booleans | Set now and re-checked at G2: `runtime_bearing` (engine runtime), `deployment_config_changed` (migration and CI workflow), `security_sensitive_scope` (ownership keys, derived restrictions, non-disclosing denial). `frontend_in_scope` stays false. |
| KG handoff | The plan's binding prediction stands: two capabilities, the refined `entity:fact-slot`, the new `entity:fact-slot-qualifier`, three schema nodes and `adr:0077`. G7 reconciles as-built bindings; coverage regeneration waits for G8. |

## Reconciliations recorded in the plan

Section "Feature-Action G0 Reconciliation" in the plan records six implementation details: the commit-hook protocol shape, source-access proof isolation, owned per-test databases, `ANSWER_CONTRACT_UNSUPPORTED` for an unregistered predicate at commit, the name-evidence eligibility rule, and CI wiring. None changes a story outcome, reason code, schema or API shape, so no `plan-story-reconcile` decision is needed.

## Contract constraints retained for implementation

- The fingerprint only accelerates lookup. On conflict, stored qualifier rows are compared, and a mismatch is `FINGERPRINT_COLLISION`. Slots are never merged.
- An omitted qualifier contributes nothing to identity, and an explicit null is `QUALIFIER_NULL_REJECTED`.
- MULTI members are child `fact_slot` rows. No DDL touches `canonical_fact_version`, which F0008 owns.
- Resolution runs as the operation of `AuthorizationExecution.mutate` over source artifacts with `INTERPRET`, so denial precedes every reason. A rejection after any insert rolls back its savepoint, leaving zero rows.
- The answer policy applies to identity-v1 slots only. Legacy slots keep the pilot values and behaviour.
- Money amounts must be strings, and a JSON number is `MONEY_FLOAT_REJECTED` before any conversion.
- No new grant, route, Casbin row, model call, RLS policy, `BYPASSRLS` role or `SECURITY DEFINER` function.

No open G0 finding or recommendation. This pass does not substitute for the 39-AC runtime proof, G3 reviews, the G4 operator decision, G5 signoff or the G7/G8 checks.
