# F0011 — JSON Schema contract system — Product Requirements

**Feature ID:** F0011
**Feature Name:** JSON Schema contract system
**Priority:** High — Now, per the 2026-11-20 roadmap review
**Phase:** MVP / v0.1A
**Status:** Done / Archived 2026-11-23 (feature run `2026-11-22-885e8734`); Phase A and Phase B approved
**Plan Run:** 2026-11-20-ccb1bd39 (A+B; feature mode new)
**Plan Revision:** 2026-11-21-e4098d22 (Phase B, existing; operator approved with `approve-phase-b` on 2026-11-22). Requirements and 41 ACs are unchanged; the revision specifies the review's compatibility proof and consumer mapping.

## Feature Statement

**As a** platform or persistence engineer integrating a semantic consumer,
**I want** a versioned JSON Schema 2020-12 structural contract consumed consistently
by Python, Pydantic, AJV and OpenAPI,
**So that** malformed payloads fail consistently while the existing meaning,
precision, access boundaries and historical versions remain intact.

## Business Objective

Publish a reproducible contract foundation for F0012/F0015 and existing consumers.
Success means all 41 acceptance criteria have runtime evidence, 100% of the
declared conformance cases agree across consumers, changed executable-line coverage
is at least 80%, and no in-scope published artifact differs from its source.
These are future feature-run acceptance targets; no runtime delivery is claimed here.

## Problem Statement

Content and assertion packages already bundle schemas and perform offline Python
validation. F0007 publishes FactSlot/answer design schemas and tests domain parsers
against cases; F0008 adds temporal schemas and responses. The schemas are not yet
one declared cross-language contract system. The current experience package has
no AJV dependency, and the blueprint's repository-root `schemas/` location is not
present. A plan must reconcile source/package authority and integrate actual consumers.

An accepting JSON Schema result establishes shape only. Ontology meaning, money
normalization, ownership, evidence and business authorization require their own
existing checks. Combining them into one boolean would conceal both failures and
compatibility boundaries.

## Personas

Reuse the scoped jobs and needs in [personas](personas.md): Dana the Platform
Engineer and Ingrid the Persistence Engineer are primary; Mateo the Document
Intelligence Engineer consumes the extraction contracts. No new application role
or grant is introduced.

## Scope & Boundaries

**In Scope — all six stories are MVP:**

- An explicit inventory of contract sources, identities, supported versions,
  packaged/generated artifacts and existing consumers; local reference closure.
- A supported JSON Schema 2020-12 subset/format policy and annotation handling,
  with no defaults insertion, type coercion or silent property removal.
- Publication and valid/invalid fixtures for the shipped information-state,
  qualified-money and scoped-identifier contracts under ADR-0039/ADR-0077.
- Actual Python JSON Schema, generated/adapted Pydantic, headless AJV and
  OpenAPI-linked conformance against the same contract definitions.
- Compatible adoption at existing content/assertion/result/FactSlot/answer/temporal
  validation boundaries, with explicit version selection and refusal behavior.
- Deterministic artifacts, clean-package proof, CI drift detection and developer handoff.

**Out of Scope — owned elsewhere:**

- Foundation or GL ontology authoring and ontology-to-profile compilation
  (F0012/F0013/F0015); ontology Workbench/release compatibility tooling (F0030).
- Interpretation execution, scope discovery or document reparse (F0016); extraction
  activation, new model/pipeline choices, and OPEN alignment execution (F0066).
- Entity resolution (F0017), full canonical orchestration (F0018), new grants,
  API routes, schema administration UI, end-user screens or form generation.
- Package completeness computation (F0014) and incomplete-package display (F0023).
- Currency conversion, universal loss formulas, historical data cleanup and
  arbitrary external/untrusted schema loading or remote schema retrieval.
- A database registry/migration by assumption. Phase B must justify any actual
  storage need and number migrations after the current 0015 head.

## Acceptance Criteria Overview

| Requirement | Owning stories | Acceptance evidence |
|-------------|----------------|---------------------|
| Versioned local contracts, supported subset and metadata | S0001 | Bundle/reference/keyword refusal cases and installed-package resolution |
| Nine information states and exact scoped absence | S0002 | Positive/negative fixtures for every state and absence boundary |
| Exact money and scoped identifiers | S0003 | Precision, namespace and malformed/semantic-boundary cases |
| Shared structural acceptance across languages | S0004 | Python/Pydantic/AJV results plus OpenAPI reference check; zero mismatches |
| Adoption without changing shipped contracts | S0005 | Real consumer entry-point integration, legacy/current versions and no partial mutations |
| Reproducible delivery and handoff | S0006 | Clean build/install, drift failure injection, CI and AC-to-evidence mapping |

## UX / Screens

No end-user screen is introduced or materially changed. Maintainers start a
documented build/conformance command; integrations enter their existing consumer
boundaries. The terminal evidence is a versioned artifact and check output, or
the established consumer transaction/refusal verified by a subsequent read.
AJV runs headlessly, so F0021's React shell is not a prerequisite.

## Screen Layouts (ASCII)

No UI — contract packaging, validation adapters and automated conformance only.
There is no editable application screen or responsive layout to specify.

## Workflows and Interaction Contract

1. Maintainer changes reviewed source definitions under a new version when
   required → bundle checks references/subset/identities → artifact generation
   and consumer conformance → review → publication through the normal repository
   process. A failed check publishes nothing as accepted output.
2. Existing authorized consumer selects a supported contract version → structural
   validation → its existing domain/evidence/policy checks → established read or
   atomic mutation. Invalid/unsupported input refuses that operation; no fallback
   reader can convert a failure to success.
3. CI regenerates/checks the declared outputs → compares them with committed or
   packaged outputs → fails on missing/stale/drifting contracts or missing cases.

Source editing is limited to repository maintainers; released versions and old
business payloads remain readable under explicit compatible readers. Contract
validation is read-only over input. Generation records artifact/check evidence,
with no business timeline event. Existing business writes retain their own audit,
principal, lifecycle and transaction requirements. No new permissions are granted.

## Data Requirements

- Identity/version/dialect and reference closure for each selected schema.
- Existing `fact-answer/v1` plus `fact-slot-key-v1` definitions, including all
  information states, typed money, scoped identifier and absence scope.
- Existing content/assertion/result and temporal response contracts in the
  Phase B inventory, including their legacy and current version selectors.
- Synthetic positive/negative case inputs with contract/version, expected
  structural result and a separate domain outcome where shape is insufficient.
- Reproducible schema/model/metadata artifacts and consumer/version/check results.

No new business entity or persistence table is required by these requirements.
Existing field shapes, maximum lengths and normalization semantics remain the
compatibility baseline. Schema-level currency shape differs from domain support;
date format differs from interval ordering; neither distinction can be hidden.

## Role-Based Access

Repository maintainer authority controls contract publication. Runtime principals
retain the existing F0002 access policy: tenant/KB scope, resource checks, source
READ and non-disclosing refusals remain prerequisites for protected operations.
Structural validity grants no authority. Diagnostics use IDs/rule locations
without embedding protected input, source text or credentials.

## Success Criteria

- Every supported validation behavior has accepting and rejecting fixtures.
- All declared cases execute in Python JSON Schema, Pydantic and AJV with identical
  expected structural acceptance; no skips count as passes.
- OpenAPI and packaged consumers resolve the same published contract definitions.
- Actual selected consumer entry points retain legacy/current wire and authorization
  behavior, and refused writes leave no partial authoritative mutation.
- Deterministic generation and installed-package operation work without access to
  planning files or network schema retrieval; intentional drift fails checks.

## Risks & Assumptions

- **Two sources for one contract:** Phase B must settle the blueprint's runtime
  `schemas/` convention against existing package resources. Independent hand copies
  do not satisfy S0001/S0004/S0006.
- **Language differences:** supported formats, regex/number behavior, conditional
  branches, defaults and coercion require explicit cross-language cases.
- **Pydantic generation:** choose and prove a supported generation/adaptation
  mechanism in Phase B. A separately maintained Python model with no conformance
  or generation relationship is insufficient.
- **Scope ordering:** F0011 supplies structural contracts before F0012's authored
  ontology and F0015's extraction compiler. It must not require those future
  features to complete its own proof.
- **ADR status:** ADR-0013 and ADR-0077 are accepted baselines. ADR-0039 stays
  Proposed until its schema fixtures and later incomplete-package display proof
  are both recorded; this plan cannot accept it.

## Dependencies

Direct prerequisites remain F0001 and F0006, as recorded by the 2026-11-08
requirement-ownership amendment. Existing F0004, F0007 and F0008 supply impacted
compatibility contracts; their approved feature evidence references are recorded
in the run's artifact-trace.md. Downstream F0012/F0015/F0013/F0017/F0016 and F0065
consume the contract foundation or its value semantics. F0009/F0010/F0018 keep
ownership of provenance/change/commit behavior; F0014/F0023 keep package completeness.
No dependency is judged complete from a KG mapping alone.

## Related Stories

| Story | Title | ACs | Status |
|-------|-------|-----|--------|
| [F0011-S0001](F0011-S0001-resolve-versioned-offline-contracts.md) | Resolve versioned offline contracts | 7 | Done |
| [F0011-S0002](F0011-S0002-validate-information-state-and-scoped-absence.md) | Validate information state and scoped absence | 7 | Done |
| [F0011-S0003](F0011-S0003-validate-qualified-money-and-scoped-identifiers.md) | Validate qualified money and scoped identifiers | 7 | Done |
| [F0011-S0004](F0011-S0004-prove-cross-language-contract-conformance.md) | Prove cross-language contract conformance | 7 | Done |
| [F0011-S0005](F0011-S0005-preserve-existing-consumer-contracts.md) | Preserve existing consumer contracts | 7 | Done |
| [F0011-S0006](F0011-S0006-verify-reproducible-contract-delivery.md) | Verify reproducible contract delivery | 6 | Done |

**Total Stories:** 6. **Numbered acceptance criteria:** 41. All are Done.

## Questions & Phase B Design Tasks

No unresolved business requirement needs an operator decision before Phase A
review. The following are required architecture outputs, not hidden business
assumptions: exact contract/adoption inventory; source and artifact authority;
supported keyword/format/reference policy; annotation/UI-metadata representation;
Pydantic generation/adaptation mechanism; OpenAPI integration and error mapping;
bounded malformed-input handling; rollout, rollback and any justified migration.
Any design that changes the shipped semantics must return to the PM/operator
for explicit reconciliation before architecture approval.

## Requirement Authority and Traceability

| Source | Requirement carried into this PRD |
|--------|----------------------------------|
| BLUEPRINT sections 2.1–2.3, 3.4.1 and 6 | Stack, authored/runtime schema boundary, semantic examples and Now lane |
| Master blueprint sections 25–27 and 112 | JSON Schema structural authority, Pydantic/AJV parity, annotations and supported subset |
| Master blueprint section 98 | Compile parity and schema/model conformance checks |
| F0011 README amendment 2026-11-08; master blueprint 106.3 | F0001/F0006 dependencies and ADR-0039 schema fixture ownership |
| ADR-0039 decisions 1–5 | Information state, scoped absence, money, identifiers and authorization separation |
| ADR-0077 and shipped F0007 schema examples | Existing value/answer shape and domain-validation compatibility |
| ADR-0078 and shipped F0008 contracts | Temporal-result boundary and historical version compatibility |

The examples in [personas.md](personas.md) and the existing EX-OWN/EX-GL library
illustrate requirements. Plan review and implementation proof remain separate gates.

## Architecture Traceability — Phase B Approved

The operator approved the six stories and 41 ACs at G3 with `approve`. The
Architect's [assembly plan](feature-assembly-plan.md) maps every AC range to exact
files, interfaces and proof obligations. [Contract design](contract-design.md),
[inventory](contract-inventory.yaml) and [profile](schema-validation-profile.yaml)
settle the Phase B design tasks without changing the requirements above.

The 21-resource bundle uses authored planning schemas and generated root/package
snapshots. Additive information-state/money/identifier aliases reference shipped
definitions; a fact-read schema documents the existing flat timestamp response.
New generic wire use is explicitly portable; existing readers retain a fixed
native compatibility policy and never retry a failed reader as fallback.
Pydantic remains source-gated; AJV, metadata and OpenAPI use the same definitions.
No new database table, migration, route, grant, deployable, screen or reparse.

The [proposed ADR-0079](../../../architecture/decisions/ADR-0079-offline-schema-bundle-and-cross-language-conformance.md)
lists runtime proof and later acceptance conditions. The operator approved Phase B
with `approve-phase-b` on 2026-11-20; this approves the plan, not formal ADR acceptance.
ADR-0039 still needs its independent package-completeness/display proof.
