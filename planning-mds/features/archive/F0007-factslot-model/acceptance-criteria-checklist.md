# F0007 acceptance criteria checklist

**Status:** All 39 criteria revalidated in approved remediation run `2026-11-09-81798e61`; code review APPROVED, security PASS, operator approval at G4, rearchived at G8 (2026-11-10). Original run `2026-11-09-b94cfa12` is superseded history.
**Total:** 39 acceptance criteria across six stories. A checkbox records observed implementation evidence. See the [current per-AC test mapping](../../../operations/evidence/runs/2026-11-09-81798e61/test-plan.md).

| Story | Criteria | Observed runtime evidence (run `2026-11-09-81798e61`) | State |
|---|---|---|---|
| S0001 | AC1–AC7 (7) | `test_factslot_resolution.py`: 6-way concurrent resolve gives one slot and one qualifier set; order and normalization fixtures; forced collision rejected without merge; omitted vs null; cross-KB slots and 404 denial; predicate-key rejection with zero rows; creation audit; identity UPDATE rejected | Evidence recorded |
| S0002 | AC1–AC6 (6) | Resolution and ownership tests prove distinct insureds, duplicate resolution, independent per-member exclusion and out-of-KB object rejection. `test_factslot_answers.py` proves a mismatched member value rejects with zero commit, version or outbox rows. | Evidence recorded |
| S0003 | AC1–AC7 (7) | `test_factslot_answers.py` proves state/value/scope validation, unread `NOT_PROCESSED`, EX-OWN-003 and audit/zero-write rejection. `test_factslot_authorized_reads.py` proves exact payload scope denial and current-grant revocation locking. | Evidence recorded |
| S0004 | AC1–AC7 (7) | Numeric/identifier and resolution tests prove exact PostgreSQL round trips, equivalent forms, issuer scope, invalid currency/basis/conversion rejection and denial precedence. New decimal regressions verify the 64-character canonical limit and preallocation rejection. | Evidence recorded |
| S0005 | AC1–AC5 (5) | `test_factslot_names.py` uses real admitted v2 evidence for same-slot legal rename, trade-name member consistency, cross-KB denial and precedence-free name access. | Evidence recorded |
| S0006 | AC1–AC7 (7) | Pilot snapshot, ownership and 16 guard migration cases prove preserved rows, composite-FK/trigger checks, NULL-shape rejection, downgrade refusal, 0013 up/down/up and safe refusal of malformed 0012 rows. Full engine: 868 passed; RLS inventory remains in GETTING-STARTED. | Evidence recorded |

- [x] Every story criterion has an observed test/result reference in the feature action's evidence package.
- [x] Changed application coverage is 97.37% (37/38 executable lines); real PostgreSQL paths are exercised.
- [x] Rejected identities, carriers and values have zero prohibited rows.
- [x] Pilot slots, fact versions and evidence are unchanged.
- [x] Existing permission grants and routes remain as specified in the PRD (no Casbin, route or grant change).
- [x] Obligations owned by F0008, F0011, F0016, F0017 and F0018 are not reported as delivered by F0007.

Requirements review happened at plan G3, and architecture review with KG exit checks at plan G5. The feature run's G3 reviews, G4 approval, G5 signoff and G8 closeout are complete.
