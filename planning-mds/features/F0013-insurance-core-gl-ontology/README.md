# F0013 — Insurance Core GL ontology

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

The General Liability module of the insurance core ontology supplies the coverage, limit, and trigger concepts the v0.1 slice extracts (sections 23, 24, 107).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0011](../../architecture/decisions/ADR-0011-ontology-is-versioned-and-modular.md), [ADR-0039](../../architecture/decisions/ADR-0039-typed-insurance-values-and-completeness.md).

## GL authoring prerequisites (2026-10-06)

This feature depends on [F0012](../F0012-foundation-ontology/README.md), in addition to F0001. Author the GL vocabulary against its stable identity, semantics, constraint execution, and release contracts. [ADR-0045](../../architecture/decisions/ADR-0045-ontology-release-compatibility.md) remains Proposed.

- Pin the exact foundation module version in each GL release. Define GL terms, typed values, applicability, qualifiers, and missing-value behavior with worked and boundary cases.
- State which GL rules infer conclusions and which validate data for a named consumer and lifecycle stage. The section 82 `min_cardinality` example is a completeness requirement for the consumer requesting a complete limit; it does not reject every commit with no extracted limit. F0065 returns `UNKNOWN` when required limit inputs are missing.
- Include constraint and profile/evidence requirements in release metadata. A logical ontology module alone is insufficient to package a GL extraction profile. Ontology material stays out of OPEN extraction prompts under F0066; F0015 governs TEMPLATE compilation.
- Specify the GL relation-to-AGE projection mapping with F0012's release contract; `hasLimit`, `hasForm` and `hasTrigger` need declared predicate IDs, edge labels, direction and source lineage. Review the [interchange examples](../../examples/ontology-interchange/README.md) before freezing vocabulary or mappings.

Contracts and examples: [release records](../../architecture/data-model.md#proposed-ontology-release-records-f0012f0013-adr-0045), [assessment contract](../F0065-grounded-gl-guideline-assessment/assessment-contract.md), and [ontology release cases](../../examples/ontology-release-contracts.md). The PRD must assign the owning stories; this amendment does not change feature status or delivery phase.

## Documents

### Commercial P&C teaching expansion (2026-10-08)

The [Cedar Bridge example](../../examples/commercial-pc-account/README.md) compares standalone GL with a BOP's liability and property sections, alongside auto/umbrella and unissued WC/inland-marine requests. Carry its distinction between product/package and coverage line, scoped party roles, carrier-qualified policy identity, qualified money and source lineage into the insurance-core/GL plan. The additional lines are illustrative future breadth, with runtime owners/releases still to be assigned; they do not widen F0013's GL delivery commitment or F0065's operation. See [the planning handoff](../../architecture/commercial-pc-example-handoff.md).

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0013.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md), [ADR-0066](../../architecture/decisions/ADR-0066-names-are-time-bounded-claims.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Declare `temporal_kind` on every GL property, and declare the name properties and name kinds (ADR-0064, ADR-0066).
- Model policy-period time-of-day and time-zone conventions so that documents can declare them in their time context.
- **v0.1 scope guard (validate finding P-2):** this feature's Phase A admits only the storage fields, contract checks, and review/display hooks listed here. Alignment, automated deciders, fingerprint-driven scheduling, and time-mention resolution that replaces template fields stay in v0.2+ unless the operator amends the scope (BLUEPRINT §4.11).
