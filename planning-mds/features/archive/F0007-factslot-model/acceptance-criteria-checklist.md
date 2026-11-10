# F0007 acceptance criteria checklist

**Status:** All 39 criteria evidenced in feature run `2026-11-09-b94cfa12`; code review APPROVED, security PASS, operator approval at G4, closed at G8 (2026-11-09).
**Total:** 39 acceptance criteria across six stories. A checkbox records observed implementation evidence, not planning completeness. The per-AC test mapping is in the run's `test-plan.md`.

| Story | Criteria | Observed runtime evidence (run `2026-11-09-b94cfa12`) | State |
|---|---|---|---|
| S0001 | AC1–AC7 (7) | `test_factslot_resolution.py`: 6-way concurrent resolve gives one slot and one qualifier set; order and normalization fixtures; forced collision rejected without merge; omitted vs null; cross-KB slots and 404 denial; predicate-key rejection with zero rows; creation audit; identity UPDATE rejected | Evidence recorded |
| S0002 | AC1–AC6 (6) | `test_factslot_resolution.py` and `test_factslot_ownership.py`: cardinality conflict and invalid; SINGLE overlap still hits the ADR-0008 exclusion; two insureds give two members and a duplicate resolves; out-of-KB relationship object; member A change leaves member B untouched; named rejections | Evidence recorded |
| S0003 | AC1–AC7 (7) | `test_factslot_answers.py`: nine states accepted, others rejected; state/value mismatch; scope required and owned; unread slot is `NOT_PROCESSED`; EX-OWN-003 through `POST /facts/{id}/commits`; unreadable scope gives 404 before any reason; audit and zero versions on rejection | Evidence recorded |
| S0004 | AC1–AC7 (7) | `test_factslot_answers.py` and `test_factslot_resolution.py`: float, currency, basis and conversion rejections; `1000000`/`1000000.00`/`1E+6` equal; exact PostgreSQL round trips; two-carrier `GL-1001`; FEIN forms equal; money qualifier identity; denial before detail | Evidence recorded |
| S0005 | AC1–AC5 (5) | `test_factslot_names.py` with a real admitted F0006 v2 assertion: system cardinalities; EX-SEM-008 same-slot rename; evidence required; KB A trade name invisible in KB B; precedence-free hook with no alias rows | Evidence recorded |
| S0006 | AC1–AC7 (7) | `test_factslot_migration.py` and `test_factslot_ownership.py`: `pilot-before.json` byte-equal across up/down/up; legacy rows unfabricated; existing suites pass (816 engine tests); composite-FK and trigger negatives as the application role; RLS inventory (this folder's GETTING-STARTED); downgrade refusal | Evidence recorded |

- [x] Every story criterion has an observed test/result reference in the feature action's evidence package.
- [x] Changed-code coverage is at least 80% (98.9%), and real PostgreSQL paths are exercised.
- [x] Rejected identities, carriers and values have zero prohibited rows.
- [x] Pilot slots, fact versions and evidence are unchanged.
- [x] Existing permission grants and routes remain as specified in the PRD (no Casbin, route or grant change).
- [x] Obligations owned by F0008, F0011, F0016, F0017 and F0018 are not reported as delivered by F0007.

Requirements review happened at plan G3, and architecture review with KG exit checks at plan G5. The feature run's G3 reviews, G4 approval, G5 signoff and G8 closeout are complete.
