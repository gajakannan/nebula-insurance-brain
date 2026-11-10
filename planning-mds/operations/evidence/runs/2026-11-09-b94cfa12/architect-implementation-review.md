# Architect Implementation Review — F0007 run 2026-11-09-b94cfa12

- Role: Architect
- Reviewer: Claude (Opus 5.5) / Architect
- Date: 2026-11-09
- Scope: the as-built conformance to ADR-0077 and the approved assembly plan, the identity and legacy compatibility, and the RLS handoff. This review grants no product approval; the operator approved at G4.

## Conformance to ADR-0077

| Decision | As built | Evidence |
|---|---|---|
| D1 normalized identity; the hash only accelerates lookup | Qualifier rows are authoritative. The SHA-256/JCS fingerprint (version 1) backs the partial unique index. On conflict the stored identity is compared field by field, and a forced collision is rejected without a merge. | `test_s0001_ac1…`, `test_s0001_ac3_forced_collision…`, `brain_domain/fact_slots.py` |
| D2 opaque major-versioned predicate keys | Grammar enforced in the domain and in the DB check. The release reference is recorded but excluded from identity. Production registers only `sys`; `test` exists only in test composition. | `predicates.py`, `deps.get_predicate_registry`, `test_s0001_ac6…` |
| D3 declared, typed qualifiers | NFC text, exact canonical decimals. An omitted qualifier contributes nothing; explicit null is `QUALIFIER_NULL_REJECTED`. | `test_s0001_ac3/ac4…`, domain tests |
| D4 cardinality; members are child slots | The ADR-0008 exclusion applies per member slot, with no DDL on `canonical_fact_version`. A commit addressed to a MULTI header is refused. | `test_s0002_*`, ownership suite |
| D5 one carrier in the existing value | `fact-answer/v1` with nine states, scoped absence, exact original-currency money and scheme-scoped identifiers. Reason precedence follows the ADR. Legacy slots bypass the carrier. | answers suite, domain precedence tests |
| D6 names | Four `sys` predicates with fixed cardinalities. Names require same-KB admitted F0006 v2 evidence. The display hook applies no precedence and writes no alias. | names suite |
| D7 authorization derived from sources | INTERPRET over the source artifacts. Restrictions are the union of the sources, and since the G3 fix the name-evidence artifacts too. No new grants. Scope and evidence reads come before any reason (T-08), on commit and since G3 on read. | resolution, answers and names suites; `security-review-report.md` |
| D8 ownership now, RLS in F0018; legacy preserved | Additive 0012: composite owner keys, generated subject-KB key, immutability and append-only triggers, a deferred integrity trigger, and a refusing downgrade. | migration and ownership suites |

## ADR-0077 Proof Gates

1. **Concurrent resolution:** 6 sessions on real PostgreSQL produce one slot with one qualifier set. The forced collision rejects without merging. **Evidenced.**
2. **Members and SINGLE overlap:** two members carry overlapping versions without tripping the exclusion, and a SINGLE overlap is still rejected. **Evidenced.**
3. **Zero rows on rejection:** every carrier and value rejection writes zero rows, and EX-OWN-003 reloads as three distinct answers. **Evidenced.**
4. **Cross-owner negatives:** child, subject, object and scope cases across tenants and KBs are rejected by the database or the facade with no disclosure. **Evidenced**, including the G3 read-path scope fix.
5. **Pilot compatibility:** pilot rows are byte-equal across upgrade, downgrade and re-upgrade. The existing commit, review and assertion suites pass, with 819 engine tests on the final code. **Evidenced.**

All five proof gates now have runtime evidence in this run. ADR-0077 status is unchanged here (Proposed). Marking it Accepted is a separate decision for the operator, consistent with how the 2026-11-08 ADR decisions were handled.

## Identity and Legacy Compatibility

- Legacy rows keep NULL identity columns and no qualifiers. A trigger refuses any NULL-to-value change. Resolution never matches a legacy slot (`test_s0006_ac1_ac2…`).
- The pilot `GET /facts/{id}` contract is unchanged. Identity-v1 slots return the stored envelope, with the scope gated by READ.
- The backup inventory change hashes only present columns, so older-revision backups keep working.

## RLS Handoff

The inventory (`fact_slot`, `fact_slot_qualifier`, both owned by `(tenant_id, knowledge_base_id)`) is recorded in the feature GETTING-STARTED and the assembly plan. Migration 0012 adds no policy, role, grant, `BYPASSRLS` or `SECURITY DEFINER`.

## Handoffs Confirmed

These remain with their owning features and are not reported as delivered:

- **F0008:** temporal close, state supersession, the carrier backstop.
- **F0011:** runtime schema publication.
- **F0012/F0013:** registry and legacy mapping.
- **F0016:** producing absence scopes.
- **F0017/F0023:** display precedence. The hook's per-slot authorization cost is a design note for them.
- **F0018:** RLS, restriction re-derivation, SourceAuthorityPolicy.
- **F0020:** HTTP states.
- **F0026:** isolation.

## Result

PASS
