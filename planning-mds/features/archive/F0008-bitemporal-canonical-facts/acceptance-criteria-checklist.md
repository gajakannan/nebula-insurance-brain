# F0008 acceptance criteria checklist

**Status:** All 46 criteria have observed evidence in feature run `2026-11-17-1a4ae2f0` (`test-plan.md`, `test-execution-report.md`).
**Total:** 46 acceptance criteria across seven stories. A box is ticked only when the feature action records observed implementation evidence.

| Story | Criteria | Runtime evidence required | State |
|---|---|---|---|
| S0001 | AC1–AC6 (6) | Fixtures for every granularity, including a DST boundary; the EX-SEM-003 `Etc/GMT+6` round trip; refusal codes with zero rows | Evidenced |
| S0002 | AC1–AC7 (7) | EX-SEM-004 read sequence; unknown end inside the exclusion; attestation floor; `START_UNATTESTED` and `ATTESTATION_MISMATCH` negatives | Evidenced |
| S0003 | AC1–AC7 (7) | §115.4 retroactive and correction cases on PostgreSQL; remainder lineage; database refusal of UPDATE and DELETE; fault injection | Evidenced |
| S0004 | AC1–AC6 (6) | Race of at least eight concurrent commits with a coordinate grid; direct-insert overlap and envelope negatives; per-member independence; cross-scope rejection | Evidenced |
| S0005 | AC1–AC7 (7) | A fixture per start basis and per state transition; both refusal codes with the predecessor unchanged | Evidenced |
| S0006 | AC1–AC7 (7) | §87 grid; half-open boundaries; validity-unknown; revoked-grant historical denial | Evidenced |
| S0007 | AC1–AC6 (6) | Pre- and post-upgrade snapshot; up/down/up log; the F0001 and F0007 suites unchanged | Evidenced |

- [x] Every story criterion has an observed test or result reference in the feature action's evidence package.
- [x] Changed-code coverage is at least 80%, and real PostgreSQL paths are exercised.
- [x] Every refused proposal writes zero rows.
- [x] Pilot versions and F0007 answers are unchanged.
- [x] No permission grant or route is added. API changes are additive fields only.
- [x] Obligations owned by F0009, F0010, F0016, F0018, F0019 and F0020 are not reported as delivered by F0008.

The operator reviews requirements at plan G3, and reviews the architecture and KG exit checks at plan G5.
