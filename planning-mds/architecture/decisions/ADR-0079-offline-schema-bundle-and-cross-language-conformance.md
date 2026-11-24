# ADR-0079: Offline Schema Bundle and Cross-Language Conformance

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-11-20
**Owner:** Architect
**Deciders:** Operator approved the Phase B plan with `approve-phase-b` on 2026-11-20; formal ADR acceptance remains pending the runtime proofs below.
**Proving feature:** F0011 — JSON Schema contract system.
**Plan run:** 2026-11-20-ccb1bd39 (Phase A and Phase B approved by the operator).

Architecture plan approval authorizes implementation of this direction. It does
not accept this ADR or ADR-0039; the runtime proofs below remain required.

## Context

Accepted ADR-0013 makes JSON Schema 2020-12 the shared structural contract;
Pydantic provides Python runtime models and AJV validates JavaScript inputs.
F0004/F0006 already package local contracts. F0007/F0008 add typed answers and
temporal metadata. Existing copies, a planning-directory fallback and a stale
nested FactVersion OpenAPI description prevent a reliable shared release.

F0011 has six approved MVP stories and 41 ACs. It must publish information-state,
money and identifier definitions without redefining their shipped shapes or
weakening source READ, evidence admission, atomic commits or version dispatch.

## Decision

1. **One authored definition, explicit runtime publication.** Retain authored
   definitions in planning-mds/schemas. Build a deterministic runtime snapshot
   under schemas/contracts/v1 and package it in brain_contracts/resources/v1.
   Existing package resources become generated copies/delegates. Every resource
   has an identity, explicit selected version and content digest. No runtime
   planning-directory lookup, network schema retrieval or mutable schema registry.
2. **A declared supported subset.** nebula-json-schema/1 admits the exact
   validation/core keywords, four asserted formats and eight x-nebula annotation
   names in the feature profile. Unknown/dynamic/recursive references and unknown
   instructions fail admission. Coercion, inserted defaults and property removal
   are disabled; annotations convey no authorization or evidence authority.
3. **Source-gated Pydantic, headless AJV, shared OpenAPI.** Build-only
   datamodel-code-generator emits Pydantic v2 models. The source JSON Schema gates
   original input and serialized output so a generator approximation cannot
   weaken validation. Preserve unset-versus-null and open/closed object behavior.
   AJV uses its 2020-12 class and declared options/formats. Generate metadata and
   self-contained OpenAPI components from the same resources; retain the existing
   inline ProblemDetails only with a structural equality check.
4. **Versioned wire policy, no implicit fallback.** New generic consumers use
   portable-json/v1 with explicit finite/safe numeric, Unicode and resource limits.
   Existing callers are selected as native-compat/v1 before parsing and retain
   their established acceptance and reason semantics. Both reuse the same schema
   source. A portable failure never retries through a native/older reader.
5. **Preserve the service boundary.** Content/assertion loaders delegate to the
   shared installed bundle. FactSlot/answer/temporal services validate normalized
   canonical carriers within current authorized transactions and before effects
   commit, retaining existing domain guards and refusal precedence. Domain code
   remains I/O-free. Legacy pilot payloads are never fabricated as identity-v1.
6. **Document the shipped API.** Add a fact-version-read-v1 description using the
   actual flat timestamps and the existing optional temporal metadata. This
   corrects documentation; it does not change the runtime response. The installed
   generated OpenAPI snapshot must match the real route table and payload fixtures.
7. **No new persistent registry or deployable.** Use immutable package artifacts
   and an in-process immutable cache. No database table, migration, HTTP route,
   grant, workbench, model activation or document reparse belongs to this change.

```text
authored JSON Schemas + explicit source manifest
                    |
           deterministic generator
                    |
        root runtime snapshot + digest manifest
          /          |          |          \
 Python bundle   Pydantic     AJV      OpenAPI/metadata
          \          |          |          /
              shared expected case inventory
```

The Mermaid component/artifact views are in the feature README. Existing C4 L1/L2
deployables and communications are unchanged.

## Alternatives Considered

- **Pydantic-generated schemas as authority:** rejected because it reverses
  ADR-0013 and can lose conditional/composition semantics and source annotations.
- **One independently authored schema per package/language:** rejected because
  ordinary checks cannot make divergent copies a single structural contract.
- **General-purpose ontology compiler now:** deferred to F0012/F0015. F0011
  compiles/publishes structural artifacts without requiring future vocabulary.
- **Database/HTTP schema registry:** unnecessary for the approved scope; adds
  tenancy, mutation, retention and rollout behavior without a user requirement.
- **Silently tighten every legacy parser to a portable wire policy:** rejected.
  Existing callers retain a fixed native compatibility boundary and differential
  tests. New reader-version adoption is explicit rather than fallback-driven.

## Consequences

- Adds build-time code generation, a JS conformance consumer and dependency locks;
  production Python uses the installed local bundle, not the generator.
- Pydantic output is useful typed code, but never the final authority on structural
  validity. Unsupported generation, missing cases or lossy serialization blocks release.
- Package version and bundle must be deployed together. Rollback restores a prior
  coherent immutable package set; existing facts and evidence are untouched.
- Validation diagnostics are internal IDs/locations only; existing public domain
  reasons and non-disclosing authorization behavior remain controlling contracts.
- Runtime capability/binding claims wait for the feature run. New KG bindings
  point to real planning/contract artifacts, not proposed implementation paths.

## Required Proof Before Acceptance

1. All 41 F0011 ACs are observed; every supported keyword/format has positive and
   negative cases and every selected conditional branch is exercised.
2. Python JSON Schema, source-gated generated Pydantic and headless AJV agree on
   100% of portable cases with no skips, and round trips retain declared metadata,
   money precision, scoped identifier identity and absence-versus-null behavior.
3. Native compatibility readers preserve current/legacy acceptance, refusal codes,
   F0006 dispatch, F0007 scope/name READ order and F0008 attestation/source checks;
   refused writes leave no partial business mutation.
4. Installed packages work without a checkout or network schema retrieval. Missing
   refs, duplicate identities, bad hashes, unknown profiles and generated drift
   fail rather than select alternate resources/readers.
5. OpenAPI/route/payload checks and clean reproducible builds pass; changed
   executable-line coverage is at least 80%; required reviewers sign every story.

Acceptance requires a later explicit operator decision citing those proofs.
ADR-0039 independently remains Proposed until its F0011 schema and F0023
incomplete-package display acceptance conditions are both met.

## References

- [Approved requirements](../../features/archive/F0011-json-schema-contract-system/PRD.md)
- [Assembly plan](../../features/archive/F0011-json-schema-contract-system/feature-assembly-plan.md)
- [Detailed design and checked primary technical sources](../../features/archive/F0011-json-schema-contract-system/contract-design.md)
- Accepted ADR-0013, ADR-0077, ADR-0078; proposed ADR-0039.
