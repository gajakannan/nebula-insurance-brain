# G0 Assembly Plan Validation — F0008

- Run: `2026-11-17-1a4ae2f0`
- NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` (source: environment)
- Reviewer: Claude (Opus 5.5) / Architect
- Review date: 2026-11-17
- Verdict: PASS
- Scope: assembly readiness only. This pass claims no runtime implementation and no final signoff.

## Source and approval baseline

The feature-local `feature-assembly-plan.md` is the primary implementation specification. Plan run `2026-11-16-208a1193` authored and approved it with `approve-phase-a` on 2026-11-16 and `approve-phase-b` on 2026-11-17, and PR #54 merged it. G0 therefore reconciles the plan; it does not re-author it.

Seven story files carry 46 ACs, split 6/7/7/6/7/7/6. G0 read the plan alongside:

- Proposed ADR-0078;
- `fact-temporal-v1.schema.json` and the `canonical-commit-request` `temporal` branch;
- `brain-api.yaml` 0.5.0 (`FactVersion.temporal`, `FactValidityUnknown`, the 422 codes);
- `contract-examples.json` (20 cases);
- the existing engine code the plan extends.

The tier-1 KG lookup routed this context, and the raw artifacts govern. Before any planned code edit, `hint.py` ran on the five edit targets and `blast.py` on `entity:canonical-fact-version` and `brain_temporal/commit.py`.

Process note: BLUEPRINT §6 lists `plan` → `plan-review` → `feature`. No `plan-review` run exists for F0008, and the operator invoked the feature action directly. This report records that order and does not substitute for a plan review.

## Assembly checks

| Check | Judgment and concrete handoff |
|---|---|
| Scope split | Backend owns everything: the domain types (`brain_domain.temporal`), the `brain_temporal` bounds/attestation/commit/reader, persistence (migration 0014, repository) and the API mapping. Frontend and AI are out of scope because no `experience/` or `neuron/` path, model, prompt or MCP surface changes. |
| Dependency order | Migration 0014 comes first, then pure domain and bounds, attestation, the commit path, the reader, the API, the contract-example check and the PostgreSQL suites. The domain has no I/O, and the service depends only on repository protocols. |
| Integration checkpoints | Owned PostgreSQL 18 databases: 0014 up/down/up on seeded pilot and F0007 rows; the §87 grid; the race with 8 or more tasks; direct-insert, UPDATE, DELETE and TRUNCATE negatives; the EX-SEM-004 and EX-PC-014 A–D reads; the GET with a revoked grant; the existing F0001/F0007/F0002 suites. |
| Ownership | Architect: the plan, ADR-0078, schemas, this report and G7. Backend: engine code. QE: the test plan, execution and coverage reports. DevOps: preflight, the migration cycle and CI wiring. Code and Security reviewers: separate reports. PM: signoff, trackers, archive. No owner conflicts. |
| Migration lineage | Static AST inspection finds the single head `0013`, and no remote branch has a `0014`. Evidence: `artifacts/test-results/g0-migration-lineage.json`. |
| Signoff and progress | STATUS.md holds the Phase B role matrix, with QE, Code Reviewer, Security Reviewer, DevOps and Architect all set to Yes. The manifest `required_roles` now matches. Every story's Story × Role cells are `not-started`. |
| Scope booleans | Set now and re-checked at G2. `runtime_bearing` comes from `engine/**`. `deployment_config_changed` comes from the migration and the CI workflow. `security_sensitive_scope` comes from the attestation-date disclosure, triggers under application roles, and non-disclosing refusals; the reason is the Phase B risk call, not a path glob. `frontend_in_scope` stays false. |
| KG handoff | The binding prediction stands: `capability:temporal-fact-resolution` (new), `capability:bitemporal-canonical-commit`, `entity:canonical-fact-version`, `schema:fact-temporal-v1`, `adr:0078`. G7 binds the code paths, and coverage regeneration waits for G8. |

## Reconciliations recorded in the plan

The plan section "Feature-Action G0 Reconciliation" lists ten details:

- owned test databases;
- `session_replication_role` in the shared-database truncate cleanups;
- the F0007 harness request shape (S0007 AC3 vs AC5), logged as a `plan-story-reconcile` decision in `artifacts/workstate.json`;
- trigger names and firing order;
- refusal audit through the F0002 failed-outcome decision, with durable reason persistence moving to F0018 (ADR-0078 D8 note added);
- optional read timestamps (S0006 AC5);
- remainder review linkage;
- the fault-injection method;
- migration lineage;
- CI wiring.

None of them changes a reason code, route, grant or story outcome.

## Contract constraints retained for implementation

- `valid` and `recorded` stay `tstzrange`, and the exclusion DDL is unchanged. An `UNKNOWN` end is a finite upper bound at the end of the `attested_to` period.
- The only UPDATE permitted is the single close of an open recorded interval. DELETE and TRUNCATE are refused, and `canonical_fact_change` is append-only.
- Remainders copy the predecessor's value, evidence, review linkage, four timestamps, kind, basis and attestation. Only the cut bound comes from the successor.
- Attestation dates come only from current F0004 date selections, never from clocks.
- Guards run after the lock and before any effect. An end revision is not a succession (D8).
- Legacy pilot slots keep the pilot request shape and behaviour, plus the remainder timestamp fix.
- There is no new grant, route, Casbin row, model call, RLS policy, `BYPASSRLS` role or `SECURITY DEFINER` function.

There are no open G0 findings. This pass does not stand in for the 46-AC runtime proof, the G3 reviews, the G4 operator decision, G5 signoff or the G7/G8 checks.
