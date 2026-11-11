# Backend remediation — values and member consistency

Scope: FR-C1, FR-H1, FR-M2 and plan PR-H1. Parent Architect approved the 64-total-character numeric limit and MEMBER_VALUE_MISMATCH contract before implementation. Original completion/audit runs were not modified.

## Implementation

- `brain_domain/fact_values.py`: input/canonical limit is 64 total characters (sign and point included). Canonical length is calculated from bounded digits and exponent before any exponent-sized allocation. Every newly emitted canonical value is a valid subsequent input. No stored value, identity key or fingerprint was rewritten.
- `brain_domain/fact_answers.py`: named `MEMBER_VALUE_MISMATCH` answer reason.
- `brain_factslots/answers.py` `FactAnswerPolicy`: after existing evidence and entity/KB checks, derive the PRESENT member key under the pinned predicate contract and require equality with the immutable stored member key. Non-PRESENT states, SINGLE legal-name renames, and existing out-of-scope rejection precedence retain their contracts.

## Regression evidence

`artifacts/values-members-red.txt`: before source fixes, 12 targeted tests failed and eight boundary positives passed. Failing cases cover both signs/decimal directions exceeding the common cap, both exponent-allocation directions under a capped child process, and entity/name/identifier mismatches.

`artifacts/values-members-unit-green.txt` and `values-members-unit.xml`: 138 domain/application/contract tests passed after the fixes. No unit skips.

`artifacts/values-members-static-final.txt`: scoped Ruff checks passed. Formatting unchanged after the function signature line-length correction. Primary coordinator owns full static/type/coverage and combined database validation.

## PostgreSQL/API tests delivered for the combined run

- `test_factslot_answers.py::test_numeric_answer_canonical_bound_round_trips_or_rejects_without_writes` (money and decimal): four exact 64-character canonical boundaries round-trip through real commit/internal read/HTTP GET; six oversized forms receive `decimal_invalid` and preserve business row counts.
- `test_factslot_answers.py::test_member_commit_rejects_another_entity_before_writing`: unauthorized caller sees 404 first; authorized mismatched member receives 422 `member_value_mismatch`, no business write; matching entity commits/reloads.
- `test_factslot_answers.py::test_identifier_member_commit_accepts_equivalence_but_rejects_issuer_change`: issuer mismatch writes nothing; equivalent FEIN formatting commits/reloads.
- `test_factslot_names.py::test_trade_name_member_commit_keeps_its_normalized_identity`: real F0006 admitted evidence; mismatched name 422 with no business write, equivalent case/spacing commits and reads back.
- Corrected existing `test_multi_header_and_unregistered_contract_are_rejected` to commit the entity that actually defined its member, rather than asserting success for a different entity.

Unit counterparts verify entity, normalized system-name and scoped identifier identity, including another identifier value and another issuer. The baseline tests remain responsible for evidence eligibility and cross-KB precedence.

## Limits and handoff

These edits do not repair any prior malformed canonical facts. The parent coordinator owns read-only existing-data inventory and reports any discovered historical rows rather than rewriting evidence. This lane did not run concurrent database suites or modify schema, planning, KG or tracker artifacts. The protected-read worker owns FactAnswerReader in the same answers.py file; this lane changed only the policy/import section.
