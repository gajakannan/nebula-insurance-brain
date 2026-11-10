# F0007 — FactSlot model

**Feature ID:** F0007
**Feature Name:** FactSlot model
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Phase A and Phase B approved 2026-11-09 (`approve-phase-a`, `approve-phase-b`); implementation not started
**Plan Run:** `2026-11-09-60865e32` (A+B, new)

## Feature Statement

**As a** persistence engineer, business reviewer and GL underwriter
**I want** every semantic question the Brain answers about a subject to have one stable, typed identity whose answer states its information state separately from its value
**So that** distinct limits, insureds and names never share or split an answer, and "not found here" is never read as "does not exist".

## Business Objective

- Goal: define canonical semantic identity (ADR-0006) beyond the first scalar example (master blueprint §109.1), carry ADR-0039 information state, qualified money and scoped identifiers, and define the ADR-0066 name FactSlots.
- Baseline: the F0001 pilot `fact_slot` row holds only `entity_id` plus a free-text `slot_type`. It has no predicate key, qualifiers, cardinality, member identity, information state or typed value. The pilot commit and `GET /facts/{factSlotId}` paths work on it today.
- Target: all 39 story acceptance criteria pass, every negative fixture yields its named outcome with zero prohibited rows, and every pilot slot and fact version reads back unchanged.
- Evidence: real PostgreSQL round trips, concurrent-resolution and ownership negative cases, carrier/value validation fixtures, and pilot regression tests in the later feature run. Planning checks do not establish runtime delivery.

## Problem Statement

A canonical fact is only as trustworthy as the question it answers. If the each-occurrence and general-aggregate limits share a slot, one silently overwrites the other. If two additional insureds share one single-valued slot, the database rejects the second. If one null stands for "not read yet", "not on pages 1–3" and "the policy says none", an underwriter can be told an exclusion is absent when the endorsement was never supplied. If a policy number is stored without the carrier that issued it, two carriers' policies merge.

## Scope & Boundaries

**In Scope (Must, MVP):**

1. **Slot identity.** Subject (tenant entity identity) + predicate key + typed qualifiers resolve deterministically to one knowledge-base-owned slot. The rules cover typed qualifier normalization, Unicode and identifier normalization, omitted versus explicit-null qualifiers, deterministic ordering, canonical decimal encoding and a versioned fingerprint. Normalized qualifier rows are authoritative and the hash only accelerates lookup (§13, §109.1).
2. **Predicate key (G1 decision).** An opaque, namespaced predicate key with a pinned ontology-release reference. F0007 owns only a minimal system-predicate set: the four ADR-0066 name predicates plus test fixtures. F0012/F0013 register and validate real predicates later. The key is the predicate reference used by the ADR-0038 SourceAuthorityPolicy (F0018).
3. **Cardinality and shapes.** `SINGLE`, `MULTI` with member identity, and `RELATIONSHIP` (subject, predicate, object entity, qualifiers). The overlap unit is per slot for single-valued slots and per member for multi-valued slots, so the §15 constraint is never applied unchanged to a set.
4. **Information state carrier (ADR-0039 1–3).** `PRESENT` plus the eight absence/quality states. Only `PRESENT` carries a value. `NOT_FOUND`/`NOT_STATED` carry their exact scope. There is no access-denied state.
5. **Typed values (ADR-0039 4–5).** Qualified money (exact decimal, ISO 4217 currency, basis where required) and scoped identifiers (scheme or issuer, type, value, optional effective interval).
6. **Name FactSlots (ADR-0066).** `hasLegalName` (single-valued per valid time), `hasTradeName`, `hasFormerName`, `knownAs` (multi-valued), name-kind qualifier, evidence-bound name values and a display-name hook with **no precedence rule** (G1 decision).
7. **Compatibility and ownership.** Pilot slots, fact versions, commit and read paths are preserved. New rows bind tenant/KB ownership through composite keys and immutability (the F0002/0007 pattern). An RLS table inventory is handed to F0018 (G1 decision).

**Out of Scope:**

- Bitemporal version storage, supersession/closing algorithms, unknown-end representation and valid-time precision (F0008, F0019, ADR-0064). F0007 defines the identity unit those versions attach to.
- Provenance/derivation lineage (F0009), change/retraction reasons (F0010), and JSON Schema publication as runtime contracts (F0011).
- Ontology predicates, properties, GL limit bases, name-property kinds and temporal kinds as vocabulary (F0012/F0013). The name predicates here are system keys, not an ontology release.
- Package completeness, expected versus received (F0014), and production of `NOT_FOUND` scopes by interpretation runs (F0016).
- Entity resolution, `entity_alias` projection, shared-name review pairs and display-name precedence (F0017, F0023). Display-name precedence is a recorded open decision.
- SourceAuthorityPolicy storage and evaluation, full commit orchestration, and PostgreSQL row-level security enablement (F0018). Isolation proof (F0026).
- Return and display of states to end users (F0020/F0023), currency conversion and exchange-rate provenance, new HTTP routes, UI, or new permission grants.

## Personas

See [personas.md](personas.md). Ingrid owns durable slot identity and ownership. Mateo needs extracted claims to land in the right slot. Rosa needs absence to stay distinguishable. Priya needs limits and identifiers she can trust. These are existing personas, not new access roles.

## Acceptance Criteria Overview

- The same question always resolves to one slot, including under concurrent resolution. Questions that differ only by a qualifier never share a slot. The same key in two knowledge bases is two slots.
- Multi-valued and relationship slots have explicit member/relationship identity, so two insureds coexist and each membership can be closed independently by F0008.
- An answer is `PRESENT` with a value, or one of eight states with no value. Absence states name their scope. Access denial never surfaces as missingness.
- Money is exact and qualified. Identifiers are scoped. Binary floats, unknown currencies and unscoped identifiers are rejected.
- Name slots exist with fixed cardinalities. A rename keeps the entity and the slot, and no name crosses knowledge bases.
- Pilot facts read back byte-for-byte equal. No predicate or qualifier is fabricated for legacy rows. Cross-tenant/KB child rows are rejected by the database.

The [acceptance checklist](acceptance-criteria-checklist.md) maps each criterion to its story and required runtime evidence.

## UX / Screens

No new or materially changed UI. The surface is an internal slot-resolution and value-validation contract used by the existing commit path and by later features. F0020/F0023 own the return and display of states, names and typed values.

## Screen Layouts (ASCII)

No UI: slot identity, value carriers, and storage/compatibility contracts only. No screen, zone, or user editing flow is introduced.

## Data Requirements

- **Slot identity:** tenant ID, knowledge base ID, subject entity identity (tenant-scoped, ADR-0061), predicate key + pinned release reference, cardinality, normalized qualifier rows, fingerprint + fingerprint algorithm version, creation actor/time.
- **Qualifiers:** typed (text, decimal, money, identifier, code, date, entity reference). Text uses Unicode NFC. Decimals use one canonical encoding. Ordering is deterministic. The omitted versus explicit-null rule is documented in Phase B and must not coerce silently.
- **Members/relationships:** member key derived from the normalized member value or member entity identity. Relationship object is a tenant entity identity visible in the slot's KB.
- **Information state:** `PRESENT`, `NOT_PROCESSED`, `NOT_FOUND`, `NOT_STATED`, `ILLEGIBLE`, `AMBIGUOUS`, `CONFLICTING`, `EXPLICIT_NEGATIVE`, `NOT_APPLICABLE`. Absence scope is content artifact version, profile release reference and page/block list.
- **Money:** decimal amount (no binary float), ISO 4217 alphabetic code, basis qualifier where the predicate requires it. **Identifier:** scheme/issuer, identifier type, value, optional effective interval.
- **Names:** verbatim text, normalized comparison form, name kind, reference to the admitted F0006 name claim/quote.
- Every new authoritative row carries `tenant_id`, `knowledge_base_id` and audit fields. Child rows bind to the parent slot's ownership through composite foreign keys.

## Role-Based Access

Use the verified principal and typed resource scope from F0002. Slot creation requires the caller's existing write authority for the knowledge base; reads require existing read authority. Cross-tenant/KB subject, object, scope or slot references are denied with zero rows written. A denial does not reveal whether the target exists. Existing authorization-decision audit stays in force; slot creation emits an audit event. No broker/MGA access or new grants are introduced.

## Success Criteria

- All 39 ACs pass with observed evidence in the later feature run.
- Zero duplicate slots under the concurrent-resolution fixture. Zero cross-tenant/KB rows or disclosures in the negative fixtures. Zero precision loss in money round trips.
- Every pilot slot and fact version is unchanged after upgrade/downgrade/upgrade.
- At least 80% changed-code coverage, with real PostgreSQL tests in addition to unit checks. No latency threshold is invented here.

## Risks & Assumptions

- ADR-0006 is Accepted. ADR-0039, ADR-0066, ADR-0038 and ADR-0042 are Proposed with operator decisions recorded (2026-11-08 / 2026-09-25). F0007 implements its assigned carriers and identities and does not formally accept those ADRs.
- **G1 decisions (2026-11-09):** (1) F0007 adds ownership binding only; F0018 Phase B designs and enables RLS on all tenant-owned tables, including F0007's. (2) The predicate key is opaque and versioned, with a minimal F0007 system-predicate set. (3) The display-name precedence rule is deferred to F0017/F0023.
- **Assumption:** slots are knowledge-base-owned semantic content (ADR-0061, ADR-0066 §1a). The same subject/predicate/qualifiers in two KBs are two slots.
- **Assumption:** an unread slot answers `NOT_PROCESSED`. F0007 does not materialize a state row for every possible slot.
- **Assumption:** money is original-currency only in F0007. A value marked as converted is rejected until a feature owns exchange-rate provenance (§107.3).
- Risk: pilot `slot_type` strings may not map cleanly to predicate keys. Phase B defines an explicit, reversible mapping or keeps them labelled legacy and never fabricates qualifiers.

## Dependencies

Direct delivered foundations: [F0002](../archive/F0002-tenancy-aware-domain-kernel-and-principal-contracts/README.md) (tenant entity identity, principals, authorization, audit), [F0003](../archive/F0003-postgresql-persistence/README.md) (PostgreSQL, table ownership, safe schema evolution), [F0006](../archive/F0006-assertion-plane-origin-and-interpretation-basis/README.md) (assertion and name-claim admission). The F0001 pilot supplies the existing `fact_slot`, commit and read paths.

Downstream consumers: F0008, F0013, F0017, F0018, F0065 (direct `depends_on`), plus F0011, F0014, F0016, F0020, F0023, F0024 under ADR-0039. Their undelivered implementations do not block F0007. Dependency evidence and audit-pending notes live in the plan run's `artifact-trace.md`.

## Related Stories

| Story | Outcome | ACs |
|---|---|---|
| [F0007-S0001](F0007-S0001-resolve-stable-factslot-identity.md) | One stable, KB-owned identity per semantic question | 7 |
| [F0007-S0002](F0007-S0002-distinguish-single-multi-and-relationship-slots.md) | Cardinality with member and relationship identity | 6 |
| [F0007-S0003](F0007-S0003-carry-information-state-separately-from-value.md) | Eight states plus a present value, with scoped absence | 7 |
| [F0007-S0004](F0007-S0004-type-money-and-identifiers.md) | Exact qualified money and scoped identifiers | 7 |
| [F0007-S0005](F0007-S0005-define-name-factslots.md) | Name slots, rename continuity and KB isolation | 5 |
| [F0007-S0006](F0007-S0006-preserve-pilot-slots-and-ownership.md) | Pilot compatibility and structural ownership | 7 |

## Rollout & Enablement

Phase B must specify the additive migration, legacy-slot handling, slot-resolution service contract, value validation at the existing commit boundary, rollback, and the RLS inventory handoff before implementation. No producer is activated and no route is added. Reuse the synthetic EX-GL-001, EX-OWN-003 and EX-SEM-008 cases and keep development fixtures outside the frozen holdout.

## Source Traceability

[BLUEPRINT](../../BLUEPRINT.md) §§0–4.12; [master blueprint](../../architecture/master-blueprint.md) §§12, 13, 15, 106.3, 107.3, 107.4, 109.1; Accepted [ADR-0006](../../architecture/decisions/ADR-0006-factslot-defines-canonical-semantic-identity.md); Proposed with decisions recorded [ADR-0038](../../architecture/decisions/ADR-0038-semantic-authority-and-source-ownership.md), [ADR-0039](../../architecture/decisions/ADR-0039-typed-insurance-values-and-completeness.md), [ADR-0042](../../architecture/decisions/ADR-0042-resource-and-derivation-authorization.md); Proposed [ADR-0066](../../architecture/decisions/ADR-0066-names-are-time-bounded-claims.md); accepted-for-scope [ADR-0061](../../architecture/decisions/ADR-0061-tenant-identity-and-structural-ownership.md); the dated amendments in [README](README.md); examples [EX-OWN-003](../../examples/source-authority-and-information-state.md#ex-own-003--three-kinds-of-no-value) and [EX-SEM-008](../../examples/statements-time-and-governance.md#names). No external business authority or new insurance rule is asserted.
