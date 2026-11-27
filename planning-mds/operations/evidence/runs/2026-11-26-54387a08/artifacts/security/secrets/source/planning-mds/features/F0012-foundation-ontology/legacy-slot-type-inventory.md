# Legacy pilot slot-type inventory (F0012-S0005 AC5)

Feature run `2026-11-26-54387a08`. A legacy pilot slot has `identity_version IS NULL` and a free-text `slot_type`; it never had a predicate contract. This inventory maps each known value to a foundation predicate key, or marks it unmapped with its future owner. **No legacy row is backfilled or rewritten**; `test_ac5_no_legacy_row_rewritten` proves install leaves `fact_slot` unchanged, and `fact_slot` is immutable by migration 0013.

## Sources

1. The G0-4 query, run at G1: `SELECT slot_type, count(*) FROM fact_slot WHERE identity_version IS NULL GROUP BY 1`. It ran on the local `brain`, `brain_f0009` and `brain_f0012` databases and returned 0 rows in each ([artifact](../../operations/evidence/runs/2026-11-26-54387a08/artifacts/test-results/g1-legacy-slot-types.txt)).
2. A source scan of `engine/` and `neuron/` for slot-type literals in code, SQL fixtures and tests.

## Inventory

| Legacy `slot_type` | Where it appears | Foundation predicate | Owner / disposition |
|---|---|---|---|
| `limit` | F0001 pilot commit path and tests | Unmapped | F0013 (GL limit predicates) |
| `each_occurrence_limit` | F0001/F0007 pilot fixtures and tests | Unmapped | F0013 (GL limit predicates) |
| `general_aggregate_limit` | `engine/tests/fixtures/factslots/pilot-seed.sql` | Unmapped | F0013 (GL limit predicates) |
| `document_date` | `engine/tests/integration/test_content_restore_v2.py` (test fixture only) | Unmapped; not a foundation concept | F0004 restore proof only; no runtime producer |
| `__OPEN_STATEMENT_V2__` | F0006 assertion semantics | Not a predicate: the OPEN-statement sentinel | F0066 |

None of these is a party, account, ownership or role concept, so no legacy value maps to a `fnd:` key.
