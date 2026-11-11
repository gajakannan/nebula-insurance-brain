# ADR-0077: FactSlot Identity and Typed Answer Carriers

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-11-09
**Owner:** Architect
**Design review:** F0007 Phase B approved by operator token `approve-phase-b` on 2026-11-09, plan run `2026-11-09-60865e32`. Formal ADR acceptance remains pending the operator's decision on the recorded runtime proofs below.
**Formal acceptance:** requires the PostgreSQL migration, concurrent-resolution, ownership, carrier-validation and pilot-regression proofs listed in the F0007 assembly plan. Plan approval alone is not runtime acceptance.
**Proof evidence:** the current F0007 remediation run is `2026-11-09-81798e61`, which supersedes `2026-11-09-b94cfa12` and includes the regression proofs for the five gates below. The status stays Proposed because the operator has approved implementation and closeout but has not recorded formal ADR acceptance. Record acceptance, or an explicit deferral, before F0008 Phase B. ADR-0039 and ADR-0066 retain their own broader acceptance gates; F0007 does not accept them by implication.
**Refines:** [ADR-0006](ADR-0006-factslot-defines-canonical-semantic-identity.md) (Accepted) beyond its first scalar example. Implements the F0007 share of [ADR-0039](ADR-0039-typed-insurance-values-and-completeness.md) decisions 1–5 and [ADR-0066](ADR-0066-names-are-time-bounded-claims.md) §1/§1a/§2. Does not accept those Proposed ADRs and does not implement ADR-0039 decision 6 (package completeness, F0014).

## Context

The F0001 pilot `fact_slot` row is `(id, entity_id, slot_type, tenant_id, knowledge_base_id, created_at)`. `slot_type` is free text, and nothing makes two callers asking the same question land on the same row. The pilot commit writes arbitrary JSON into `canonical_fact_version.value`. The ADR-0008 GiST exclusion applies per `slot_id`.

Master blueprint §109.1 needs identity beyond one scalar: qualified limits, multi-valued sets (additional insureds), relationships and names. ADR-0039 needs one answer carrier that keeps "not read", "not on pages 1–3" and "the policy says none" apart. Three G1 operator decisions (2026-11-09) bound the design:

1. F0007 binds ownership only; F0018 enables row-level security.
2. Predicates are opaque versioned keys with a minimal system set.
3. Display-name precedence is deferred to F0017/F0023.

F0003 assigns `fact_slot` and `fact_slot_qualifier` to F0007 and `canonical_fact_version` to F0008. F0007 therefore must not change the version table's DDL.

## Decision

### D1. Slot identity is a normalized key; the hash only accelerates lookup

An identity-v1 slot is `(tenant, knowledge base, subject entity, predicate key, normalized qualifiers)`. Two extra parts apply by cardinality: a RELATIONSHIP slot adds the object entity, and a MULTI member adds its parent slot and member key.

- Normalized qualifier rows in `fact_slot_qualifier` are authoritative.
- `identity_fingerprint` is SHA-256 over the RFC 8785 (JCS) canonical JSON of the identity document, tagged `fingerprint_version = 1`. It backs a partial unique index `(tenant_id, knowledge_base_id, identity_fingerprint) WHERE identity_version IS NOT NULL`.
- Resolution uses `INSERT … ON CONFLICT DO NOTHING`, then re-reads. Concurrent resolvers converge on one row.
- On conflict the stored identity is compared field by field. A different identity under the same fingerprint fails with `FINGERPRINT_COLLISION`; slots are never merged. The same identity with a different cardinality fails with `CARDINALITY_CONFLICT`.
- Slots are KB-owned (ADR-0061, ADR-0066 §1a). The same key in two KBs is two slots.

### D2. Predicate key: opaque, namespaced, major-versioned

- **Grammar:** `<namespace>:<localName>@v<major>`, for example `sys:hasLegalName@v1`.
- **Release reference:** a pinned `predicate_release_ref` is recorded at creation. It is not identity, so an ontology release bump never splits slots. A new major version is a new predicate and therefore new slots.
- **Predicate contract:** a `PredicateContractRegistry` port supplies cardinality, value type, declared qualifiers (required or optional, with types), member-key source and basis requirement.
- **What F0007 ships:**
  - the `sys` namespace, holding the four ADR-0066 name predicates;
  - a `test` namespace, wired only in test composition.

  Any other namespace is `PREDICATE_UNREGISTERED` until F0012/F0013 register predicates. A malformed key or a missing release reference is `PREDICATE_KEY_INVALID`.
- **What F0007 does not do:** it never validates predicate semantics against an ontology.
- **Policy lookup:** the stored key is the predicate reference used by the ADR-0038 SourceAuthorityPolicy (F0018).

### D3. Qualifier rule: declared, typed, never silently coerced

- **Typed normalization:**
  - text uses Unicode NFC;
  - decimals use one canonical form: no exponent, no trailing fractional zeros, `-0` becomes `0`, so `1E+6`, `1000000.00` and `1000000` all become `1000000`;
  - codes are exact tokens;
  - money and identifiers use D5;
  - an entity reference must point to an entity associated with the slot's KB.
- **Omitted qualifier:** contributes nothing to identity.
- **Explicit null:** rejected with `QUALIFIER_NULL_REJECTED`.
- **Other rejections:**
  - an undeclared qualifier is `QUALIFIER_UNDECLARED`;
  - a missing required qualifier is `QUALIFIER_REQUIRED`;
  - a wrong type is `QUALIFIER_TYPE_INVALID`.
- **Ordering:** qualifiers are ordered by name in the canonical document. Input order is irrelevant.

### D4. Cardinality; members are child slot rows

- **Cardinality:** `SINGLE`, `MULTI` or `RELATIONSHIP`, fixed at creation from the predicate contract. An unknown value is `CARDINALITY_INVALID`.
- **Members:** a MULTI slot is a header. Each member is a child `fact_slot` row (`parent_slot_id`, `member_key`). The member key is the canonical encoding of the member value or member entity.
- **Versions:** they attach to the member row. The unchanged ADR-0008 exclusion on `slot_id` therefore applies per member, with no DDL on `canonical_fact_version`. A commit addressed to a MULTI header is rejected with `MULTI_SLOT_REQUIRES_MEMBER`.
- **Member-value invariant:** a `PRESENT` answer on a MEMBER must canonicalize under the pinned predicate contract to its immutable `member_key`. A mismatch is rejected with `MEMBER_VALUE_MISMATCH` before any write; equivalent normalized spellings are accepted. A different canonical value must resolve its own member slot.
- **Relationships:** a RELATIONSHIP slot includes `object_entity_id` in its identity. The object must be a tenant entity associated with the slot's KB; otherwise the result is `RELATIONSHIP_OBJECT_OUT_OF_SCOPE`.

```text
fact_slot (header, MULTI: sys:hasTradeName@v1, subject E, KB A)
   ├── fact_slot (member key "acme restoration")  ── canonical_fact_version …
   └── fact_slot (member key "acme storm services") ── canonical_fact_version …
fact_slot (SINGLE: sys:hasLegalName@v1, subject E, KB A) ── versions (rename = new version)
fact_slot_qualifier (slot, name, type, canonical value)  ×N per slot
```

### D5. One answer carrier inside the existing version value

- **Envelope:** identity-v1 slots store `fact-answer/v1` in `canonical_fact_version.value`, as `{answer_contract, state, value?, scope?}`.
- **States:**
  - The nine states are `PRESENT` plus ADR-0039's eight.
  - Only `PRESENT` carries a value.
  - `NOT_FOUND` and `NOT_STATED` require an absence scope: content artifact, profile release reference, and pages and/or block IDs.
  - `NOT_PROCESSED` and `NOT_APPLICABLE` carry no scope.
  - There is no access-denied state.
- **Validation:** a `FactAnswerPolicy` validates and canonicalizes the envelope inside `CanonicalCommitService` after the slot lock and before `register_commit`. Legacy slots keep their unwrapped pilot values and pilot behaviour.
- **Unread slots:** a slot with no version answers `NOT_PROCESSED` through the internal `FactAnswerReader`. F0007 materializes no state row per possible slot. `GET /facts/{factSlotId}` keeps its pilot contract, and HTTP exposure of states is F0020/F0023.
- **Money:**
  - The amount is a decimal string. A non-string amount is `MONEY_FLOAT_REJECTED`.
  - The currency must be an ISO 4217 alphabetic code from a pinned, versioned list, or the result is `CURRENCY_INVALID`.
  - A basis is required where the predicate requires it (`BASIS_REQUIRED`).
  - Any conversion marker is `CONVERTED_MONEY_UNSUPPORTED`.
- **Decimal bounds:** decimal values and money amounts have the same 64-character total limit on input and canonical output. Canonical length is checked before exponent expansion allocates padding. Every accepted canonical value can be loaded and canonicalized again unchanged.
- **Identifiers:**
  - An identifier is `(scheme, identifier_type, value[, effective])`, with server-computed `normalized_value` from a versioned normalization table.
  - `fein` strips hyphens and requires nine digits. Every other type defaults to NFC only.
  - Equality includes the scheme, so normalization never equates two schemes.
- **Reason precedence:** errors are reported in this order: contract, then state, then state/value shape, then scope, then value type, then value detail. The first reason is returned.

### D6. Names (ADR-0066)

| Predicate | Cardinality |
|---|---|
| `sys:hasLegalName@v1` | SINGLE |
| `sys:hasTradeName@v1` | MULTI |
| `sys:hasFormerName@v1` | MULTI |
| `sys:knownAs@v1` | MULTI |

- **Name value:** verbatim text, optional `name_kind`, and evidence `{assertion_id, document_version_id}`. The evidence must resolve to an admitted, eligible F0006 v2 assertion in the slot's tenant/KB; otherwise the result is `NAME_EVIDENCE_REQUIRED`.
- **Normalized form:** computed by the server (NFC, then casefold, then whitespace collapse). It is the member key for MULTI name slots.
- **Renames:** a rename is a new version in the same `hasLegalName` slot. F0008/F0019 split valid time.
- **Display hook:** `NameFactReader.current_names` returns the reader-KB's current accepted name facts in a documented non-precedence order (predicate key, normalized form, slot ID). It creates no `entity_alias` rows. Precedence is an open decision for F0017/F0023.

### D7. Authorization: derive from sources, add no grants

- **Who may create:** creating a slot or member runs inside `AuthorizationExecution.mutate` over the source content artifacts with the existing `content_artifact:interpret` action, so only ServicePrincipal holds it today. Authorization precedes every validation detail.
- **Restrictions on the new slot:** its `resource_access` row is provisioned in the same unit of work. Classifications and source ACLs are the union of its sources', and `parent_chain` and `dependency_keys` are the sources. This follows ADR-0042 decision 4, under which derived results inherit restrictions.
- **Commits:** they keep `fact_slot:commit`. Absence-scope artifacts and name-evidence assertions join the commit's `additional_reads`, so an unauthorized scope is denied before any missingness detail (threat T-08).
- **Reads:** scope-dependent reads derive their additional READ keys from the exact privately loaded answer, then authorize, recheck and audit all keys in the same current-authority unit of work before returning it. Selecting an answer separately to discover its scope is insufficient.
- **Audit:** each creation writes one operational audit event (`fact_slot_created` / `fact_slot_member_created`) naming actor, tenant, KB, slot and fingerprint version.

### D8. Ownership now, RLS in F0018; legacy preserved

- **Migration `0012`:** additive. It adds nullable identity columns to `fact_slot`, with a NULL `identity_version` marking a legacy slot, and creates `fact_slot_qualifier`.
- **Identity guard `0013`:** leaves released migration `0012` unchanged and requires the complete legacy-or-v1 identity shape to evaluate `IS TRUE`, so missing required fields cannot pass through SQL NULL semantics. It locks `fact_slot` while checking existing rows and replacing the constraint, refuses malformed rows without repair, and restores the original `0012` guard on downgrade.
- **Composite keys:**
  - qualifiers and members bind to `fact_slot (id, tenant_id, knowledge_base_id)`;
  - the subject and object of identity-v1 rows bind to `entity_knowledge_base`. The subject binding uses a generated column that is NULL for legacy rows, so legacy rows are not retro-checked.
- **Triggers:** a trigger rejects any change to identity columns, including NULL to value, so a legacy row can never acquire a fabricated identity. Qualifier rows are append-only.
- **Legacy `slot_type` values:** no mapping is created. They stay legacy-only, and a later explicit mapping belongs to F0012/F0013.
- **RLS inventory:** `fact_slot` and `fact_slot_qualifier` are handed to F0018. F0007 enables no RLS and adds no `BYPASSRLS`, superuser or owner shortcut.
- **Downgrading below `0012`:** refuses while identity-v1 or qualifier rows exist.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Hash-only identity (fingerprint is the key) | Collisions would silently merge slots, and the hash is not inspectable; ADR-0006 needs authoritative structure |
| Release reference inside identity | Every ontology release would split every slot and orphan history |
| `member_id` column on `canonical_fact_version` with a widened exclusion | Changes the F0008-owned table and its ADR-0008 constraint ahead of F0008 |
| Nullable typed columns for state/value on the version row | Same ownership problem; also forces a migration of pilot values |
| Map pilot `slot_type` strings to predicate keys in the migration | Would fabricate predicates and qualifiers the pilot never asserted (S0006 AC2) |
| New `fact_slot:create` action or KB-level grant | Adds a grant (out of scope) and detaches slot restrictions from the evidence they derive from |

## Consequences

- **Positive:**
  - Distinct questions never share a slot, and concurrent callers converge.
  - Per-member temporal integrity comes with no version-table change.
  - Absence is explicit and scoped, money is exact, and identifiers are scheme-bound.
  - Pilot data is untouched.
- **Negative / risks:**
  - The answer envelope lives in JSONB, so database-level state/value checks wait for F0008's version-row design. Until then F0007 enforces them in the service, and F0008 should add a database backstop.
  - Slot restrictions are fixed from the creating sources. Re-derivation when later evidence arrives is F0018 policy.
  - Real predicates cannot be used until F0012/F0013 register them, so F0007 activates no producer.
- **Follow-ups:**
  - F0008: per-member close, state supersession, database carrier backstop.
  - F0011: runtime schema publication.
  - F0012/F0013: predicate registry and legacy mapping.
  - F0016: producing absence scopes.
  - F0017/F0023: display precedence and aliases.
  - F0018: RLS on the handed inventory, SourceAuthorityPolicy on the predicate key, restriction re-derivation.
  - F0020: HTTP return of states.
  - F0026: isolation proof.

## Proof Gates Before Acceptance

1. Real-PostgreSQL concurrent resolution yields one slot with one qualifier set, and the forced-collision fixture rejects without merging.
2. Two members of a MULTI slot carry independent versions without tripping the exclusion, and SINGLE overlap is still rejected.
3. Every carrier and value rejection writes zero rows, and EX-OWN-003 reloads as three distinct answers.
4. Cross-tenant/KB child, subject, object and scope negatives are rejected by the database or the facade with no disclosure.
5. Pilot slots and versions are byte-equal after upgrade, downgrade and upgrade again, and existing commit, review and assertion suites pass unchanged.

## References

- Master blueprint §§13, 15, 106.3, 107.3, 107.4, 109.1
- [F0007 assembly plan](../../features/archive/F0007-factslot-model/feature-assembly-plan.md)
- Schemas: `planning-mds/schemas/fact-slot-key-v1.schema.json`, `fact-answer-v1.schema.json`, `fact-slot-resolution-result-v1.schema.json`
- Examples: EX-OWN-003, EX-SEM-008

## Review remediation history

Operator-authorized run `2026-11-09-81798e61` tightened the member-value, decimal-bound, identity-guard and protected-read rules. On 2026-11-10 those rules were folded into D4, D5, D7 and D8 in response to plan-review finding PR-M1. This clarification preserves the Proposed status and the operator's separate formal acceptance decision.
