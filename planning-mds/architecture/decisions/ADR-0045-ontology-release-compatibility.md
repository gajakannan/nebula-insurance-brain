# ADR-0045: Ontology Release Compatibility

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Deciders:** Pending; becomes Accepted only when the stated tests, owners, and release gates are satisfied (master blueprint section 106 decision posture)
**Source:** `planning-mds/architecture/master-blueprint.md` section 116

## Context

Master blueprint section 112 requires immutable module releases, dependency locks, explicit semantic migration, and preservation of historical interpretation context. F0012/F0013 need the authoring and release metadata contracts before vocabulary authoring; F0015 needs an agreed release boundary before compiler implementation.

Historical reproducibility, compatibility for consumers, and conservative extension answer different questions. Reproducing a saved assessment requires its exact inputs and releases. Compatibility also includes validation, profile, evidence, and application contracts. A supported conservative-extension check only addresses whether specified conclusions over existing terms change within its declared scope.

## Decision

Pending. The following is the proposed contract, refined on 2026-10-06 and 2026-10-07. Acceptance still requires the evidence and owners below.

### Identity and release records

- Define the stable namespace, deterministic ID-to-IRI mapping, collision handling, and tenant-extension rules in F0012. Never reassign a term IRI. Renaming a label preserves identity; meaning changes require classification and migration records. Splits and merges identify their source and replacement terms without overwriting old definitions.
- Publish immutable module versions and composed releases. A release locks every module dependency to an exact version and digest, with associated profile/template/compiler and validation artifact references. Preserve the authoring schema, supported semantics, constraint execution metadata, and evidence requirements in the manifest. The [proposed data model](../data-model.md#proposed-ontology-release-records-f0012f0013-adr-0045) defines the logical records; Phase B settles their physical schema.
- Pin interpretation runs and retain the interpretation context of their assertions and facts. Rule versions and assessments retain exact release references, input fact versions, evaluator/rule versions, valid/known coordinates, and evidence/derivation lineage. Current authorization still governs historical reads.
- Record activation and rollback separately from immutable release contents. Rollback selects the release for future work and explicitly addresses work already in flight; it neither deletes history nor silently rewrites saved outcomes.
- Version the relation-to-projection mapping with the release: predicate IRI, edge/property label and direction, endpoint identity, qualifiers, rules for retaining exact canonical source/evidence references and ownership/temporal context, and explicit omitted/inverse predicates. Hash it with the other artifacts. Mapping changes drive projection rebuild/invalidation analysis; an unmapped predicate leaves impact unknown. See the [proposed GL edge mapping](../data-model.md#age-graph-labels-master-blueprint-section-79).

### Proposed clarification of ADR-0012 format scope

[ADR-0012](ADR-0012-flexible-authoring-normalized-runtime.md) remains Accepted for authoring/interchange compiled to normalized PostgreSQL. Its baseline lists undefined `OKF`. This proposal explicitly refines that list: OKF is an optional placeholder with no supported-format claim until a precise specification/version, owner, usage terms, and example round trip are selected. Acceptance of ADR-0045 will supersede only any interpretation of the ADR-0012 list as requiring OKF support; its storage boundary remains in force. Until then, record this as pending decision reconciliation, and do not claim an OKF implementation exists.

### Semantics and constraint execution

The authoring contract separates inference rules from validation constraints. Each constraint names its lifecycle stage, consumer, applicability, severity/action, and asserted or inferred data basis. Inferred validation data also identifies the provider/ruleset and supported fragment. Unsupported constructs cannot be silently approximated.

Absence of an extracted limit is not a global commit failure. Under F0065, an assessment needing that limit returns `UNKNOWN` when required inputs are missing. Shape tightening, changes to applicability or evidence obligations, and changes to missing-value handling all participate in compatibility review even if no inferred triple changes.

### Compatibility and impact gate

Classify every release change as additive, constraint tightening, rename/alias, semantic change, split, merge, or retirement. F0012/F0013 Phase B must define the consumer contracts and version policy against which each class is evaluated. A change labeled additive must still be examined for effects on existing conclusions and consumers; passing one conservativity check does not by itself establish a non-breaking release.

Before activation, a reviewed predecessor-to-candidate impact report must contain:

1. Exact release IDs, manifests, dependency locks, changed term definitions, inference rules, and validation constraints, including their execution context.
   Include the old/new projection-mapping versions and changed predicate-to-edge/property rules.
2. Reachable FactSlots, assertions, extraction profiles/templates, guideline rule versions, derived assessments, and projections. Identify the affected tenant/KB scope and explicit limits of the inventory.
3. Separate results for dependency reach, inference changes, validation/consumer changes, and replayed assessment outcomes. Record input snapshot/digests, evaluator/provider versions, counts with denominators, and any unexamined population. Reachability alone is not evidence that an outcome changed.
4. For any conservative-extension analysis: the tested signature, supported logic/ruleset, compared releases, bounds, and result. Distinguish a detected change, no change established within scope, and unsupported/incomplete/undecided analysis. Do not promote a bounded result to an unrestricted proof or treat skipped checks as passes.
5. Change classification, compatibility decision per consumer, required migration mappings or reinterpretation, risk rationale, rollback/in-flight-work handling, and reviewer ownership. Unresolved compatibility claims prevent automatic activation pending review.

Historical replay uses retained releases and deterministic assessment inputs under the original valid/known coordinates. Evaluating those inputs under a candidate release is a separate comparison. Neither operation requires rerunning an LLM to reconstruct an already stored historical assessment.

### Delivery boundaries

- F0012/F0013 settle identity, authoring semantics, constraint applicability, missingness, and release metadata. F0015 compiles packages with the corresponding profile and evidence contracts.
- Exact derivation lineage ships with the first stored assessment under ADR-0026/F0065. General invalidation and propagation remain separately phased.
- F0030/F0062 can add external mapping analysis and logical module extraction. Crosswalks retain source namespace/version, match type, evidence, and unresolved contradictions; source-phrase signature alignment is a distinct operation. A logical module is only part of a deployable package, which must also include shapes, profile requirements, and evidence obligations.
- OPEN extraction remains free of ontology prompts under F0066. Optional RDF/OWL checkers or reasoner providers may use derived stores; authoritative semantic data stays in PostgreSQL under ADR-0002. No external engine, vocabulary catalog, or proof assistant is required by this proposal. Select external vocabularies by domain need and usage rights.

### Acceptance evidence still required

The feature plans must assign stories and owners for these cases, record actual reproduction commands/results, and identify the activation gate enforcing them. The [worked examples](../../examples/ontology-release-contracts.md) are synthetic expected outcomes, not executed acceptance evidence.

| Case | Required evidence |
|---|---|
| Identity and locks | Stable ID/IRI round trip, alias rename, collision/reuse rejection, immutable published contents, exact foundation/GL dependency resolution, and rejection of unresolved or floating dependencies. |
| Missing limit | Admissible unrelated facts can be committed; an assessment requiring missing limit inputs reports `UNKNOWN`. A malformed supplied value still fails its own applicable admission check. |
| Inference change | An allegedly additive change that adds a conclusion over existing terms is reported within a stated reasoning scope. Unsupported or truncated analysis remains unresolved. |
| Constraint change | A stricter consumer requirement is reported as a compatibility impact even when the compared inference closure is unchanged. |
| Split, replay, rollback | A concept split reports affected assertions, FactSlots, profiles, rules, projections, and derived results; an old assessment retains its original meaning, a candidate comparison records any new outcome, and rollback preserves both histories. |
| Scope and lineage | Release resolution and impact/replay honor tenant/KB scope and current authorization; the first stored assessment records exact rule/input/evidence lineage. |

## Consequences

- Until accepted, implementation treats the referenced master blueprint sections as requirements to prove, not as settled contracts.
- Acceptance requires recording the executed test, the owner, and the release gate in this record.

## References

- [Master blueprint](../master-blueprint.md), sections 19, 82, 112, and 116
- [F0012](../../features/F0012-foundation-ontology/README.md), [F0013](../../features/F0013-insurance-core-gl-ontology/README.md), [F0015](../../features/F0015-extraction-profile-compiler/README.md)
- [F0065 assessment contract](../../features/F0065-grounded-gl-guideline-assessment/assessment-contract.md)
- [ADR-0002](ADR-0002-postgresql-is-the-authoritative-runtime-store.md), [ADR-0026](ADR-0026-derived-facts-have-dependency-lineage.md)
