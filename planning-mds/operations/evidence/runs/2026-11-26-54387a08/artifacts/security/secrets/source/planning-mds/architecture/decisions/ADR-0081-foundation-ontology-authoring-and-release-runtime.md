# ADR-0081: Foundation Ontology Authoring and Release Runtime

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-11-25
**Deciders:** Architect (F0012 plan run `2026-11-25-120320e9`); operator decisions D1–D8 at G1 and Phase A approval `approve-phase-a` (2026-11-25)
**Refines:** [ADR-0045](ADR-0045-ontology-release-compatibility.md) (Proposed) for the F0012 share: namespace, authoring schema, physical release storage, activation gate and consumer policy. [ADR-0012](ADR-0012-flexible-authoring-normalized-runtime.md) and [ADR-0011](ADR-0011-ontology-is-versioned-and-modular.md) stay Accepted and unchanged.
**Activates:** the [ADR-0078](ADR-0078-bitemporal-version-contract-and-close-only-immutability.md) D10 temporal kinds through [ADR-0077](ADR-0077-factslot-identity-and-typed-answer-carriers.md) D2 predicate contracts.
**Plan approval:** Phase B approved 2026-11-25 by operator token `approve-phase-b` (approves the plan, not formal ADR acceptance).
**Feature:** [F0012](../../features/F0012-foundation-ontology/README.md); [assembly plan](../../features/F0012-foundation-ontology/feature-assembly-plan.md).

## Context

F0013–F0016 need a release they can pin. ADR-0045 proposes the contract but leaves namespace, authoring schema, storage and consumer policy to F0012. The operator settled the scope at F0012 G1: offline authoring and compile, immutable PostgreSQL releases, release-backed predicate contracts, a gated activation, URN identities, a small inference subset and `parents:` as the only parent field.

## Decision

### D1. Authoring files and identity

- Authored modules live under `ontology/modules/<module>/` as YAML validated by the design schema `ontology-module-authoring/v1`. `parents:` is a list; `parent:` is refused with `AUTHORING_FIELD_RETIRED`.
- Term ID grammar: `^[a-z][a-z0-9-]{0,47}(\.[a-z][a-z0-9-]{0,47}){1,7}$`, ASCII only, so case and Unicode normalization cannot create distinct spellings of one ID. Term IRI = `urn:nebula:ont:` + ID. `urn:nebula:tenant:` is reserved; no shared module may use it, and no install path for tenant extensions exists (`TENANT_EXTENSION_UNSUPPORTED`).
- Identity history is the union of the term IRIs in every committed release lock under `ontology/releases/**` and, at install, every release installed in the target tenant/KB. A candidate may reuse an IRI only with the same definition digest or under a change record. Change records (`semantic_change`, `split`, `merge`, `retirement`) live in the module's `changes.yaml` and become immutable release content.
- Labels: BCP 47 tags; exactly one preferred `en-US` label; labels and aliases are excluded from the definition digest, so a rename never looks like a semantic change.

### D2. Supported semantics

| Construct | Role | Executed by |
|---|---|---|
| `subClassOf`, `subPropertyOf`, `inverseOf` | Inference over the terminology | Deterministic in-house fixpoint in `brain_ontology.semantics`; used by the impact report and RDF export checks |
| `domain`, `range`, `disjoint`, `minCardinality`, `maxCardinality` | Validation constraint only; never infers a type | Its named consumer at its named stage |
| Anything else (`symmetric`, `transitive`, `equivalentClass`, …) | Refused with `UNSUPPORTED_CONSTRUCT` | — |

Every constraint carries `stage` (`authoring` \| `canonical-admission` \| `example-validation` \| `assessment-preconditions` \| `consumer-defined`), `consumer`, `applicability`, `severity` (`violation` \| `warning`), `on_nonconformance` and `data_basis` (`asserted`, or `inferred` with `ruleset: nebula-tbox-subset/v1`). F0012 executes only `authoring` and `example-validation` constraints. `canonical-admission` constraints are declared contracts that F0017/F0018 execute.

### D3. Compile and release identity

- The compiler (`brain_ontology.compiler`) normalizes modules to canonical JSON (RFC 8785 JCS), sorts terms by IRI and computes SHA-256 digests. A module version digest covers its normalized content; the release manifest digest covers module digests, the dependency lock, the projection mapping digest and the declared semantics.
- **Release reference** = `ontrel:sha256-<manifest digest>` (71 characters, valid under the ADR-0077 `_RELEASE_REF` grammar). It is content-addressed, so a release can never be republished with different content.
- Dependencies are exact `module@version#sha256`. Ranges, `latest`, a missing member or two versions of one module refuse the compile with `DEPENDENCY_UNRESOLVED`.
- Compiled output is committed under `ontology/releases/<name>/<n>/`: `manifest.json`, `normalized.json`, `projection-mapping.json`, `release.ttl`, `release.jsonld`. CI recompiles from source and compares bytes.
- The projection mapping lists every property as mapped (label, direction, endpoint types, required context) or omitted with a reason. Inverse properties are omitted (derived). F0012 writes no projection; F0034 consumes the mapping.

### D4. Physical storage (migration 0017)

Append-only, tenant/KB-owned tables (ADR-0030): `ontology_module_version`, `ontology_release`, `ontology_release_module`, `ontology_term`, `ontology_change_record`, `ontology_impact_report`, `ontology_release_review`, `ontology_release_selection`. UPDATE, DELETE and TRUNCATE are refused by triggers on every table. `ontology_term` stores one normalized row per term with its definition digest and, for FactSlot properties, its predicate key, cardinality, value type and `temporal_kind`. Install writes all rows for one release in one transaction; an identical `release_ref` already installed in the tenant/KB is an idempotent no-op. The exact DDL is in [migration-design.sql](../../features/F0012-foundation-ontology/migration-design.sql). Downgrade is refused while any ontology row exists.

### D5. Authorization

A new resource type `ontology_release` with actions `install`, `review`, `activate` and `read`, scoped to tenant/KB, evaluated by the existing `AuthorizationExecution` and audited with the policy hash. Proposed policy rows (added by the feature run, not by this plan):

```text
p, ServicePrincipal, ontology_release, install
p, ServicePrincipal, ontology_release, read
p, OntologySteward, ontology_release, review
p, OntologySteward, ontology_release, activate
p, OntologySteward, ontology_release, read
p, TenantMember, ontology_release, read
```

`OntologySteward` is a new role for the human steward (Sameer). It is granted through existing memberships; no existing role gains review or activation. The reviewer and the activator may be the same steward principal; review and activation remain separate audited records. Rollback uses `activate`.

Command-line entry points (`python -m brain_ontology.cli`) take a bearer token verified by the existing F0002 credential verification. No HTTP route or UI is added.

### D6. Release-backed predicate contracts

- Each FactSlot-bearing property declares `predicate: {namespace, local_name, major}` explicitly; the module declares its namespace (`fnd` for foundation). The key is validated against the ADR-0077 grammar and must be unique in the release. The term-IRI-to-key map is part of the release manifest.
- `PredicateContract` gains `temporal_kind` (default `STATE`, so `sys` predicates are unchanged).
- `ReleasePredicateRegistry` keeps the synchronous `PredicateContractRegistry` port. Before a FactSlot resolution or commit, the service calls `prepare(scope, release_refs)`, which loads contracts only for releases installed in that tenant/KB within the same unit of work; `contract()` then reads that snapshot. Unknown keys and uninstalled release references stay `PREDICATE_UNREGISTERED`. There is no fallback to the active release; an existing slot uses its recorded `predicate_release_ref`.
- New releases keep the slot identity of a predicate whose major is unchanged (release reference is not identity). A changed major is a new predicate and requires a `semantic_change` record.

### D7. Temporal kinds

`brain_temporal.commit` takes `kind` from the predicate contract instead of the constant `STATE`:

- `ETERNAL`: the request must carry no valid-time bounds; the version is written with valid `(,)` and NULL bound columns. A second, different value in a SINGLE `ETERNAL` slot is refused with `ETERNAL_CONFLICT`. Correcting an `ETERNAL` value is F0010 retraction/correction scope.
- `EVENT`: one bounded granularity period, using the existing placement path.
- A shape that does not match the kind is refused with `KIND_SHAPE_MISMATCH` before any write. The existing `ck_cfv_v1_kind_shape` CHECK remains the database backstop; no DDL changes.

The foundation module declares no `EVENT` property; `EVENT` is proven with a test-composition release.

### D8. Impact report and activation

- `brain_ontology.impact` produces `ontology-impact-report/v1`: predecessor and candidate references, per-term change classes, closure diff over the D2 inference subset restricted to predecessor terms, per-consumer constraint diff, reach counts with denominators (identity-v1 FactSlots by predicate key, assertions by `predicate_id`) and an explicit `unexamined` list (profiles/templates F0015, assessments F0065, projections F0034). A change it cannot classify, or an analysis exceeding its bound (default 100,000 entailments), marks the report `incomplete` with the reason.
- A review binds the report digest and both release digests. Activation requires a `complete` report with an `approve` review whose digests match the installed candidate. Each activation and rollback appends one `ontology_release_selection` row with a per-tenant/KB sequence under `SELECT … FOR UPDATE` on the tenant/KB selection head; a concurrent loser is refused with `SELECTION_CONFLICT`. Rollback may select only a release that was previously activated in that tenant/KB.
- Selections govern future work only. No slot, version, assertion or report is rewritten.

## Consequences

- F0013 authors GL modules against `ontology-module-authoring/v1`, pins `foundation@1` by digest and registers GL predicates the same way.
- F0015 fills the reserved manifest artifact slots; F0016 records `release_ref` on interpretation runs; F0017/F0018 execute the declared `canonical-admission` constraints; F0034 consumes the projection mapping; F0030 owns the workbench and extended reasoning.
- A new role and resource type need security review in the feature run.
- ADR-0045 remains Proposed. F0012 supplies its identity/locks, inference-change, constraint-change, split/rollback and scope evidence; acceptance is a separate operator decision.

## Alternatives Considered

| Alternative | Why not |
|---|---|
| HTTPS namespace | Needs a domain the project does not own; operator chose URNs (D4 at G1). |
| Derive predicate local names from term IDs | Kebab-to-camel conversion can collide and hides a breaking rename; explicit names are reviewable. |
| Make the registry port async and tenant-aware | Changes every F0007 caller; a prepare step keeps the port and reuses the unit of work. |
| Store releases only as files | ADR-0012 requires normalized runtime structures, and activation history must be audited (operator D1). |
| Use an external OWL reasoner | Not needed for the three supported rules; F0062 owns optional providers. |

## Acceptance (separate from Phase B approval)

Accept when the F0012 feature run records: byte-identical recompilation; refused mutations of installed rows; refused reuse/collision; the release-backed registry with `PREDICATE_UNREGISTERED` for uninstalled releases; ETERNAL/EVENT commits and mismatches on PostgreSQL; an EX-ONT-003 entailment change and an EX-ONT-004 constraint tightening each reported; refused activation without a matching reviewed report; and rollback history preserved. Security review of `OntologySteward` and `ontology_release` passes.

## Implementation notes (feature run 2026-11-26-54387a08)

Status is unchanged: **Proposed**. The feature run implemented D1–D8 and recorded these refinements as Architect decisions. Each is in the [assembly plan G0 reconciliation](../../features/F0012-foundation-ontology/feature-assembly-plan.md#g0-reconciliation--feature-run-2026-11-26-54387a08) or the [architect implementation review](../../operations/evidence/runs/2026-11-26-54387a08/architect-implementation-review.md).

- **D5:** the authorization resource is `ResourceKey(ontology_release, knowledge_base_id)`. It requires a trusted `resource_access` row, and migration 0017 widens `ck_resource_access_type`. Report generation requires `review`, not `read`.
- **D1:** a definition change that only adds `parents`/`sub_property_of` axioms is additive and needs no change record (EX-ONT-003). The impact report shows its entailment change.
- **D3:** RDF export writes domain and range as `nebula:validationDomain`/`nebula:validationRange`, so no RDFS/OWL reasoner infers a type from them (D2).
- **D7:** an ETERNAL version reads with `valid_start: null` (`fact-version-read-v1` widened). The new wire codes are lowercase: `kind_shape_mismatch`, `eternal_conflict`.

## References

- [Master blueprint](../master-blueprint.md) §§19–22, 67, 79, 82, 112
- [F0012 PRD](../../features/F0012-foundation-ontology/PRD.md), [assembly plan](../../features/F0012-foundation-ontology/feature-assembly-plan.md)
- [ADR-0045](ADR-0045-ontology-release-compatibility.md), [ADR-0070](ADR-0070-account-party-and-role-model.md), [ADR-0077](ADR-0077-factslot-identity-and-typed-answer-carriers.md), [ADR-0078](ADR-0078-bitemporal-version-contract-and-close-only-immutability.md), [ADR-0079](ADR-0079-offline-schema-bundle-and-cross-language-conformance.md)
