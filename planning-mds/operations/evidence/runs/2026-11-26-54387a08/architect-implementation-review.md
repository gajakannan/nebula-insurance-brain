# Architect Implementation Review — F0012 run 2026-11-26-54387a08

- Reviewer: Claude (Opus 5.5) / Architect
- Date: 2026-11-26
- Verdict: PASS

## Conformance to the approved design

The build implements ADR-0081 D1–D8 and assembly-plan Steps 1–7 as reconciled at G0.

- **D1 identity and authoring.**
  - The authoring schema plus semantic checks reject singular `parent`.
  - The term ID grammar and `urn:nebula:ont:` mapping are applied; the tenant namespace is reserved.
  - Identity history comes from committed locks offline and from installed rows at install.
- **D2 supported semantics.**
  - Only `subClassOf`/`subPropertyOf`/`inverseOf` infer.
  - Domain, range, disjoint and cardinality are validation only.
  - Anything else is `UNSUPPORTED_CONSTRUCT`.
- **D3 compile and release identity.**
  - Normalization is JCS with deterministic ordering.
  - `ontrel:sha256-<manifest digest>`, with exact dependency locks.
  - Five committed outputs, checked in CI with `compile --check`.
- **D4 storage.** Eight append-only tables, idempotent and atomic install, refused downgrade.
- **D5 authorization.** The new resource, actions and role; six policy rows mirrored in the KG.
- **D6 predicates.** Release-backed contracts are prepared per scope. There is no active-release fallback, and slot identity is unchanged.
- **D7 temporal kinds.** ETERNAL `(,)`, EVENT as one period, STATE unchanged. There is no DDL on `canonical_fact_version`.
- **D8 impact and activation.**
  - Change classes, closure diff, constraint diff, reach with denominators, unexamined populations.
  - A review binds the report.
  - Append-only selections with sequence locking and a database guard.

## Recorded design corrections (G0–G3)

| # | Correction | Decision basis |
|---|---|---|
| 1 | The authorization resource is `ResourceKey(ontology_release, kb_id)` with a required trusted `resource_access` row; migration 0017 widens `ck_resource_access_type` | Operator, 2026-11-26 (G0-5 revised) |
| 2 | `fact-version-read-v1` `valid_start` widened to `string\|null` for ETERNAL versions | Operator, 2026-11-26 |
| 3 | New temporal wire codes are lowercase (`kind_shape_mismatch`, `eternal_conflict`); the enumeration is not schema-closed (description-only update) | Architect, G0-3 |
| 4 | RDF export uses `nebula:validationDomain`/`validationRange` instead of `rdfs:domain`/`range`, so no reasoner infers types (D2) | Architect, G2 |
| 5 | A definition change that only adds `parents`/`sub_property_of` axioms is additive without a change record (EX-ONT-003); the report shows the entailment | Architect, G2 |
| 6 | Report generation requires `ontology_release:review` (steward); reach counts are KB aggregates | Architect, G2; accepted as SEC-F0012-L2 |
| 7 | The temporal kind reaches the commit through the answer policy (`FactAnswerPolicy.temporal_kind`); `prepare` runs inside the resolver and answer policy | Architect, G0-7/G0-8 |
| 8 | `sys`/`test` predicate namespaces are reserved at authoring and install; install checks manifest/term predicate consistency | Code review CR-F0012-L1 |
| 9 | The CLI reads the API's environment variables, not `config/local.yaml` | Architect, G2 |
| 10 | The approved `contract-inventory.yaml` was invalid YAML; repaired | Architect, G2 |
| 11 | **Process deviation:** `hint.py`/`blast.py` ran after the edits, not before | See below |

**Late `hint.py`/`blast.py` (deviation 11).** I ran both afterwards over every changed code file and the shared contracts ([hint](artifacts/kg/hint-changed-files.txt), [blast](artifacts/kg/blast-shared-semantics.txt)). Neither surfaced an impact outside the suites that ran:

- the `fact-version-read-v1` radius is F0011-S0004 (conformance passed);
- the `brain_temporal/commit.py` radius is F0001/F0003/F0007/F0008/F0011/F0012, and those suites pass in the full engine run;
- `brain_domain/authx.py` touches five stories in four features, all passing.

No canonical shared semantics were redefined. The widened read contract is an additive nullability that the operator approved.

## ADR-0081 proof status

The acceptance conditions are met by observed evidence:

- byte-identical recompilation;
- refused mutations of installed rows;
- refused reuse and collision;
- the release-backed registry with `PREDICATE_UNREGISTERED` for uninstalled releases;
- ETERNAL/EVENT commits and mismatches on PostgreSQL;
- the EX-ONT-003 and EX-ONT-004 reports;
- refused activation without a matching reviewed report;
- preserved rollback history;
- security review PASS.

Status is unchanged, **Proposed**; acceptance is a separate operator decision. ADR-0045 and ADR-0070 have their evidence notes added, and their status is unchanged.

## Knowledge-graph delta (for G7)

These code bindings should be added:

| Capability | New files |
|---|---|
| `foundation-ontology-release` | `engine/packages/brain-ontology/**`, `brain_domain/ontology.py`, `brain_persistence/ontology_releases.py`, `ontology_models.py`, migration 0017, `ontology/**` |
| `release-backed-predicate-registry` | `brain_factslots/predicates.py` |
| `ontology-release-compatibility` | `brain_ontology/impact.py`, `semantics.py` |

`bitemporal-canonical-commit`, `factslot-identity-resolution` and `authorization-enforcement` already cover the modified temporal, factslot and security files. The new role node `role:ontology-steward` and four `policy_rule:ontology-release-*` nodes were added together with the policy rows; the drift check passes.

## Result

Result: PASS
