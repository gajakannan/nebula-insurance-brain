# F0012 — Foundation ontology

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

The foundation ontology module is the versioned base that every insurance module composes on (sections 19 to 22).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0011](../../architecture/decisions/ADR-0011-ontology-is-versioned-and-modular.md), [ADR-0012](../../architecture/decisions/ADR-0012-flexible-authoring-normalized-runtime.md).

## Ontology authoring and release prerequisites (2026-10-06)

Carry these requirements into the F0012 PRD before authoring the foundation vocabulary. [ADR-0045](../../architecture/decisions/ADR-0045-ontology-release-compatibility.md) remains Proposed; its release contract and proof obligations must be settled before compiler implementation.

- Specify the stable term namespace and deterministic ID-to-IRI mapping, including collision handling and tenant extensions. Labels and aliases may change; an IRI is never reassigned. Meaning changes, splits, merges, and retirement follow explicit change classes and migration mappings.
- Distinguish inference semantics from validation constraints in the authoring schema. Each constraint declares its lifecycle stage, consumer, applicability, severity/action, and whether it examines asserted data or a named inferred closure. Unsupported constructs are explicit errors.
- Resolve the existing authoring inconsistency: master blueprint section 20 uses `parents:` as a list, while section 82 uses singular `parent:`. The new interchange example uses `parents:`; the PRD must select the canonical field/cardinality and define whether legacy spelling is migrated or rejected. Neither example is a finalized schema.
- Preserve missing, unknown, explicit negative, conflicting, and not-applicable states. A consumer's need for a complete limit does not become a universal canonical-commit requirement; see the [F0065 assessment contract](../F0065-grounded-gl-guideline-assessment/assessment-contract.md).
- Define immutable module versions and composed ontology releases with exact dependency locks, artifact hashes, supported semantics, and constraint metadata. Interpretation and assessment records retain their exact release references; see the [proposed release records](../../architecture/data-model.md#proposed-ontology-release-records-f0012f0013-adr-0045).
- Include versioned relation-to-projection mappings in each release: predicate IRI, edge label/direction, endpoints, qualifiers, exact canonical source/evidence references and temporal/ownership context. Explicitly declare unprojected predicates and rebuild impact. The [GL interchange example](../../examples/ontology-interchange/README.md) demonstrates proposed mappings for `hasLimit`, `hasForm`, and `hasTrigger`.
- Derived assessments need exact input and rule lineage from their first stored result, as already required by ADR-0026 and F0065. Full change propagation and external reasoning remain separately phased work.

Worked and boundary cases: [ontology release contracts](../../examples/ontology-release-contracts.md). This amendment defines planning inputs; feature status and the existing v0.1 scope guard are unchanged.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0012.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Every ontology property declares `temporal_kind` (`STATE`, `EVENT`, `ETERNAL`) (ADR-0064).
- Properties and classes carry a definition, examples, and regression cases, which alignment and the workbench rely on (ADR-0063).
- **v0.1 scope guard (validate finding P-2):** this feature's Phase A admits only the storage fields, contract checks, and review/display hooks listed here. Alignment, automated deciders, fingerprint-driven scheduling, and time-mention resolution that replaces template fields stay in v0.2+ unless the operator amends the scope (BLUEPRINT §4.11).
