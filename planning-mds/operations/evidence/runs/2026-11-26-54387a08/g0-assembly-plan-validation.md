# F0012 G0 — Assembly plan validation

Reviewer: Claude (Opus 5.5) / Architect
Date: 2026-11-26
Verdict: PASS
Run: 2026-11-26-54387a08
Product: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain

Result: PASS

The approved Phase B plan from plan run `2026-11-25-120320e9` (PR #68, `main` 87fe31c) is the implementation baseline. No new plan was authored. I reconciled the existing plan instead: see [feature-assembly-plan.md § G0 Reconciliation](../../../../features/archive/F0012-foundation-ontology/feature-assembly-plan.md#g0-reconciliation--feature-run-2026-11-26-54387a08).

I read the following and checked them against the shipped code at 87fe31c:

- the PRD and all seven stories (46 ACs);
- ADR-0081;
- `migration-design.sql`;
- `contract-inventory.yaml`;
- the three design schemas.

Requirements are unchanged.

**Process deviation:** no plan-review run preceded this feature action, although the PRD and plan expect one. The operator was asked on 2026-11-26 and chose to resolve plan gaps at G0 (workstate `.kg-state/workstate/F0012-2026-11-26-54387a08.yaml`, decision #0, topic `plan-story-reconcile`). G3 reviewers should read the two gap resolutions (G0-5, G0-6) as plan-level design, not only as code.

## Scope split and dependencies

The seven build steps keep their order and checkpoints:

1. authoring validation and identity;
2. foundation content;
3. compiler and release locks;
4. migration 0017, release store, install and grants;
5. the release-backed registry and temporal kinds;
6. impact report and gated activation;
7. delivery proof.

Ownership:

- **Backend** owns `brain-ontology`, the release store, the registry, the commit path and the CLI.
- **QE** owns the negative fixtures per rejection rule, the PostgreSQL proofs (atomic install, concurrency, immutability, activation race) and the ADR-0045 case log.
- **DevOps** owns migration ordering, the refused downgrade, the CI `compile --check` and the package install.
- **Security** owns the new `OntologySteward` role, the `ontology_release` resource and scoped reach counts.
- **Code Reviewer** owns compiler determinism and regressions in the registry and commit path.
- **Architect** owns shared semantics (ADR-0081/0045/0070 proofs) and the KG bindings.

Frontend and AI are out of scope: there is no UI, model, parse or producer. The five-role signoff matrix in STATUS.md is reconfirmed.

Dependencies are all shipped:

- **F0002:** authority and audit.
- **F0007:** registry port and slot identity.
- **F0008:** `fact-temporal/v1` and the `ck_cfv_v1_kind_shape` CHECK.
- **F0011:** offline bundle and AJV conformance.

`brain-ontology` depends on brain-contracts and brain-domain only. The release store lives in brain-persistence, and the CLI composes both, so there is no package cycle.

## Verified plan claims against code

| Plan claim | Code evidence | Result |
|---|---|---|
| Migration head is 0016 | `engine/migrations/versions/0016_f0009_provenance_hooks.py` is the latest revision | Confirmed; 0017 needs no rebase |
| Commit writes the constant `TemporalKind.STATE` | `brain_temporal/commit.py` `_commit_v1` builds `VersionTemporal(kind=TemporalKind.STATE, …)` | Confirmed |
| `PredicateContract` has no `temporal_kind` | `brain_domain/fact_slots.py` `PredicateContract` | Confirmed; additive field, default STATE |
| Registry port is synchronous; production = `sys` only | `brain_factslots/ports.py` `PredicateContractRegistry`; `predicates.production_registry` | Confirmed |
| API composes one module-level registry | `brain_api/deps.py` `_predicate_registry = production_registry()` | Confirmed; replaced by a per-request registry (G0-8) |
| DB already enforces ETERNAL/EVENT shapes | 0014 `ck_cfv_v1_kind_shape` and the EVENT one-period trigger branch | Confirmed; no DDL on `canonical_fact_version` |
| ETERNAL valid `(,)` fits the domain types | `TimeRange.start: datetime`; `_from_pg_range` asserts a lower bound | **Gap** → G0-6 |
| Authorization on `ontology_release@tenant/KB` | `brain_persistence/authx.hydrate` needs a `resource_access` row per instance | **Gap** → G0-5 |
| Temporal reasons schema-closed? | `brain-api.yaml` 422 lists codes in its description; ProblemDetails `code` is open | Not closed; description-only update (G0-3) |
| Audit can carry release ref/digest | `audit_event.event_type` + `payload` (F0002 v1 additions) | Confirmed (G0-9) |
| Composite FK target `knowledge_base(id, tenant_id)` | Used by 0005/0006 FKs | Confirmed |

## Integration checkpoints (feasible)

1. After Step 3, the committed release locks recompile byte-identically (`compile --check`).
2. After Step 4, install, idempotence, concurrency and immutability pass on PostgreSQL 18, and the Casbin drift check passes with six new policy rows plus kg-source policy nodes.
3. After Step 5, the F0007/F0008/F0009 suites pass unchanged, and ETERNAL/EVENT/STATE commits and mismatches are proven on PostgreSQL.
4. After Step 6, the activation refusal matrix, the concurrent-activation race and the rollback history pass.
5. Feature complete: 46/46 ACs, coverage ≥ 80% on changed lines, and security review of `OntologySteward` and `ontology_release`.

## Artifact ownership and knowledge graph

There is no ownership conflict. The design schemas, `migration-design.sql` and ADR-0081 are Architect-owned and unchanged at G0, apart from filling the hashes in `contract-inventory.yaml`. Generated contract artifacts come only from the F0011 toolchain.

Predicted KG delta:

- The existing planned capabilities `foundation-ontology-release`, `release-backed-predicate-registry` and `ontology-release-compatibility` gain code bindings for `engine/packages/brain-ontology/**`, `brain_persistence/ontology_releases*.py`, migration 0017 and `ontology/**`.
- `bitemporal-canonical-commit`, `factslot-identity-resolution` and `authorization-enforcement` already cover the modified temporal, factslot and security files.
- No generated KG YAML is hand-edited.

## Validation limits

This verdict approves the assembly and its checkpoints only. Runtime readiness and all 46 ACs remain unproven until G1/G2. ADR-0081, ADR-0045 and ADR-0070 remain Proposed.
