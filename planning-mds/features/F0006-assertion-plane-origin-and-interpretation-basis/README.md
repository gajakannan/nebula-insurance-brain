# F0006 — Assertion plane + origin + interpretation basis

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

The assertion plane records what sources claim before anything becomes truth; origin and interpretation basis are first-class from the first extraction (section 11).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0005](../../architecture/decisions/ADR-0005-three-plane-knowledge-model.md), [ADR-0035](../../architecture/decisions/ADR-0035-interpretation-basis-is-first-class.md).

## Documents

- [PRD](PRD.md) — Phase A approved by operator `approve-phase-a` on 2026-11-01; five stories and 35 ACs.
- [Personas](personas.md), [acceptance checklist](acceptance-criteria-checklist.md), [status](STATUS.md), [getting started](GETTING-STARTED.md).
- Plan run: `2026-11-01-7d6d19ce` (A+B, new). Phase A+B approved by operator on 2026-11-01. Architecture contracts and ontology bindings are complete for planning; implementation has not started.
- Feature shard: `planning-mds/kg-source/features/F0006.yaml`; Architect-authored planning mappings cover all five stories; G4 compile and drift validation passed. Registry status remains Planned and roadmap remains Next.
- [Assembly plan](feature-assembly-plan.md) — Phase B design approved 2026-11-01; implementation files, signatures, migration constraints, authorization, consumer guards and verification matrix.
- [ADR-0075](../../architecture/decisions/ADR-0075-versioned-assertion-semantics-and-admission.md) — Proposed; bounded versioned semantics and admission design. [Worked examples](worked-examples.md), [structured contract examples](contract-examples.json).

## Stories

| ID | Title | Status |
|----|-------|--------|
| [F0006-S0001](F0006-S0001-preserve-typed-source-claims.md) | Preserve typed source claims | Not Started |
| [F0006-S0002](F0006-S0002-retain-open-statements-and-version-contracts.md) | Retain open statements and version contracts | Not Started |
| [F0006-S0003](F0006-S0003-check-structural-admission-and-evidence.md) | Check structural admission and evidence | Not Started |
| [F0006-S0004](F0006-S0004-guard-mood-and-described-evidence.md) | Guard mood and described evidence | Not Started |
| [F0006-S0005](F0006-S0005-preserve-existing-consumer-boundaries.md) | Preserve existing consumer boundaries | Not Started |

**Total Stories:** 5

## Phase B design: feature ERD

Proposed storage; no runtime migration has been applied by plan. The original Assertion and AssertionEvidence identities survive. Document-local references and admission name claims do not establish canonical entities or name FactSlots.

```mermaid
erDiagram
    DOCUMENT_VERSION ||--o{ ASSERTION_DOCUMENT_REFERENCE : scopes
    ASSERTION_DOCUMENT_REFERENCE ||--o{ ASSERTION_NAME_CLAIM : claims_name
    ASSERTION_DOCUMENT_REFERENCE ||--o{ ASSERTION_SEMANTICS : subject
    ASSERTION ||--o| ASSERTION_SEMANTICS : extends_v2
    ASSERTION ||--o{ ASSERTION_EVIDENCE : supports
    ASSERTION ||--o{ ASSERTION : corrected_from
    ASSERTION ||--o{ REVIEW_ITEM : reviewed
    ASSERTION {
        uuid id PK
        uuid original_assertion_id FK
        smallint semantic_contract_version
        string origin
    }
    ASSERTION_SEMANTICS {
        uuid assertion_id PK,FK
        uuid subject_ref FK
        uuid object_ref FK
        string assertion_kind
        string fact_mode
        string predicate_id
        string ontology_release
        json record
    }
    ASSERTION_DOCUMENT_REFERENCE {
        uuid id PK
        uuid document_version_id FK
        string entity_type
        string label
    }
    ASSERTION_NAME_CLAIM {
        uuid document_version_id PK,FK
        string normalized_name PK
        uuid entity_ref FK
    }
    ASSERTION_EVIDENCE {
        uuid id PK
        uuid assertion_id FK
        uuid artifact_id FK
        string precision
    }
```

```text
document version -> local references -> unique document name claims
                         | subject/object
assertion 1 -------- 0..1 semantics (required exactly once for version 2)
    | 1..n evidence          | full record + verified selectors/origins
    +----- review item       +----- eligibility guard
    +----- corrected assertion (additive; restrictions inherited)
```

## Phase B component design

```mermaid
flowchart LR
    Legacy[Existing v1 result importer] --> Carrier[Assertion/evidence store]
    Caller[Authorized internal v2 caller] --> Auth[Current authorization facade]
    Auth --> Admission[Structural admission]
    Source[Verified immutable F0004 content] --> Admission
    Admission --> Writer[Atomic assertion writer]
    Writer --> Carrier
    Writer --> Extension[Semantics/local references/name claims]
    Writer --> Hook[Existing review hook]
    Carrier --> Guard[Source eligibility guard]
    Extension --> Guard
    Guard --> Commit[Existing pilot commit service]
    Admission --> Outcomes[Protected outcome contract to F0016]
```

Existing [C4 context](../../architecture/c4-context.md) and [container topology](../../architecture/c4-container.md) remain unchanged. Engine owns this application contract and storage; neuron keeps the v1 producer path. No model, new service or UI is added by the design. See the assembly plan for direct backend/QE/security/DevOps/Architect handoffs.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Persist both assertion kinds: `OPEN_STATEMENT` (subject, source relation phrase, object or literal, role-word qualifiers, time-mention references, mandatory quote, nullable predicate) and `TYPED_ASSERTION` (ontology property and release). v0.1 acceptance runs on the template route; open extraction and alignment ship in F0066 (ADR-0063).
- Define the admission service contract: quote-in-block, name-in-quote, time-words-in-quote, and name-claimed-by-another checks; server-computed selectors; drop reasons (ADR-0065).
- Add the `mood` qualifier. Mood-bearing statements are never eligible for canonical facts; an issued policy's operative provisions remain contract facts (ADR-0065, EX-SEM-007).
- **v0.1 scope guard (validate finding P-2):** this feature's Phase A admits only the storage fields, contract checks, and review/display hooks listed here. Alignment, automated deciders, fingerprint-driven scheduling, and time-mention resolution that replaces template fields stay in v0.2+ unless the operator amends the scope (BLUEPRINT §4.11).
- **Schema versioning (validate finding A-5):** `schemas/interpretation-result.schema.json` sets `additionalProperties: false`. Assertion kind, source phrase, quote and selector, role-word qualifiers including mood, and time-mention references need a versioned schema addition with compatible readers; existing results stay valid.
