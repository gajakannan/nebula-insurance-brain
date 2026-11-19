# Test Plan — F0008 Bitemporal canonical facts (run 2026-11-17-1a4ae2f0)

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-17
- Scope: seven stories with 46 ACs, plus the six ADR-0078 proof gates. Engine only; there is no UI and no AI.

## Approach

Expectations come from the story ACs, ADR-0078 and the worked examples (§87/§115.4, EX-SEM-003/004, EX-PC-014 A–D, EX-OWN-003), not from the implementation. There are three layers:

1. **Pure unit tests** (`engine/packages/brain-temporal/tests`), with no database:
   - zone, truncation and DST arithmetic;
   - parse refusal codes;
   - attestation derivation and placement;
   - the v1 service algorithm and D9 reader over the in-memory fake;
   - the 20 contract examples checked against both the design schemas and the runtime parser.
2. **PostgreSQL 18 integration**:
   - **Harness:** each test owns a database migrated to head, using `BRAIN_MIGRATION_ADMIN_URL` and the F0006/F0007 harness pattern. Evidence documents carry F0004 date selections seeded as rows.
   - **Paths exercised:** commits go through `POST /facts/{id}/commits` with real authorization. Recorded-time grids use the commit service with a fixed acceptance clock. Reads go through `GET /facts/{id}`.
   - **Negatives:** they run as the database owner role, the most privileged client role available.
3. **Regression**: the full engine suite, including the existing F0001 bitemporal, F0002 AuthX, F0006 and F0007 suites.

There is no frontend and no E2E browser flow. The HTTP-level API tests are the end-to-end path for this engine-only feature.

## AC → test traceability

`v1` = `tests/integration/test_temporal_v1_commit.py`, `imm` = `test_temporal_immutability.py`, `con` = `test_temporal_concurrency.py`, `rd` = `test_temporal_reads.py`, `mig` = `test_temporal_migration.py`, `unit-b` = `brain-temporal/tests/test_bounds.py`, `unit-s` = `test_temporal_service.py`, `ce` = `test_contract_examples.py`.

| Story / AC | Tests |
|---|---|
| S0001 AC1 granularity/zone codes, nothing written | unit-b `test_s0001_ac1_*`; v1 `test_s0001_ac1_ac2_invalid_bounds_are_refused_and_write_nothing` (5 cases); ce N01/N02 |
| S0001 AC2 truncation in zone (Chicago midnight vs UTC) | unit-b `test_s0001_ac1_ac2_every_granularity_*`, `test_s0001_ac2_chicago_midnight_*`; v1 `test_s0001_ac2_chicago_midnight_is_accepted`, `test_s0001_database_trigger_is_authoritative_*` (4 cases) |
| S0001 AC3 EX-SEM-003 `MINUTE` `Etc/GMT+6` | unit-b `test_s0001_ac3_*`; v1 `test_s0001_ac3_ex_sem_003_*` |
| S0001 AC4 round trip, every granularity, never the previous day | unit-b `test_s0001_ac4_*`; v1 `test_s0001_ac4_every_granularity_round_trips_exactly` (7 cases) |
| S0001 AC5 independent start/end granularities | unit-b `test_s0001_ac5_*`; v1 `test_s0001_ac5_*` |
| S0001 AC6 EVENT/ETERNAL representable, STATE written | v1 `test_s0001_ac6_event_and_eternal_shapes_need_no_ddl_and_state_is_written` |
| S0001 DoD DST boundary | unit-b `test_s0001_dst_boundaries_in_chicago` (6), `test_s0001_dst_fall_back_second_hour_*` |
| S0002 AC1 end states and `END_STATE_INVALID` | unit-b `test_s0002_ac1_s0005_ac1_structural_refusals`; v1 `test_s0002_ac1_each_end_state_*`; ce N03–N05 |
| S0002 AC2 EX-SEM-004 | unit-b `test_s0002_ac2_*`; v1 `test_s0002_ac2_ac3_ac7_ex_sem_004_prior_carrier`; rd `test_s0006_ac3_ex_sem_004_*` |
| S0002 AC3 UNKNOWN end in the exclusion | v1 `test_s0002_ac2_ac3_ac7_*` (direct insert → `23P01`) |
| S0002 AC4 floor at `attested_from`; validity-unknown before it | unit-b `test_s0002_ac4_*`; v1 `test_s0002_ac4_*`; rd `test_ex_pc_014_a_to_d_*` (B) |
| S0002 AC5 `START_UNATTESTED` (undated, cleared, no evidence) | unit-b `test_s0002_ac5_*`; v1 `test_s0002_ac5_*` |
| S0002 AC6 dates from F0004 selections; `ATTESTATION_MISMATCH` | unit-b `test_s0002_ac6_*`, `test_d4_*`; v1 `test_s0002_ac6_*` (2) |
| S0002 AC7 response distinguishes end states | v1 `test_s0002_ac2_ac3_ac7_*`; rd `test_s0006_ac5_*` |
| S0003 AC1 §115.4 retroactive change | v1 `test_s0003_ac1_ac6_*`; unit-s `test_d5_retroactive_*` |
| S0003 AC2 correction re-split, change links | v1 `test_s0003_ac2_*` |
| S0003 AC3 remainder keeps payload, evidence, review linkage, timestamps | v1 `test_s0003_ac3_*`; unit-s `test_d5_*`, `test_legacy_path_remainders_keep_predecessor_timestamps` |
| S0003 AC4 untouched intervals | v1 `test_s0003_ac4_*` |
| S0003 AC5 close-only UPDATE, no reopen, no DELETE | imm `test_s0003_ac5_update_of_any_column_*` (23 columns), `test_s0003_ac5_the_single_close_*`, `test_s0003_ac5_delete_and_truncate_*` |
| S0003 AC6 distinct times | v1 `test_s0003_ac1_ac6_*` |
| S0003 AC7 one transaction; fault before outbox writes nothing | imm `test_s0003_ac7_fault_before_the_outbox_*` |
| S0004 AC1 ≥8 racers, grid ≥200, losers write nothing, one audit/outbox per winner | con `test_s0004_ac1_racing_commits_*` (12 racers), `test_s0004_ac1_unconditional_racers_*` |
| S0004 AC2 direct overlapping insert | imm `test_s0004_ac2_*` |
| S0004 AC3 MULTI members independent | con `test_s0004_ac3_*` |
| S0004 AC4 RELATIONSHIP slot, no separate table | con `test_s0004_ac4_*`; v1 `test_relationship_slot_versions_share_the_table` |
| S0004 AC5 envelope backstop; legacy exempt | imm `test_s0004_ac5_*` (3 cases plus the legacy case) |
| S0004 AC6 cross-scope rows refused | imm `test_s0004_ac6_*` (version, change, split lineage) |
| S0005 AC1 basis recorded; `START_BASIS_INVALID`; no confidence input | unit-b `test_s0005_ac1_*`, structural refusals; ce N06/N07/N09 |
| S0005 AC2 anchored bases close | v1 `test_s0005_ac2_*` (4 bases) |
| S0005 AC3 `MENTION_C`/floor refused and audited; standalone accepted; end revision allowed | v1 `test_s0005_ac3_*` (2 tests); unit-s `test_d8_end_revision_*` |
| S0005 AC4 EX-OWN-003 | v1 `test_s0005_ac4_*`; unit-s `test_d8_state_guard` |
| S0005 AC5 PRESENT not replaced by six states | v1 `test_s0005_ac5_*` (6 cases) |
| S0005 AC6 PRESENT → PRESENT/EXPLICIT_NEGATIVE; non-PRESENT → any | v1 `test_s0005_ac6_*` (3 tests) |
| S0005 AC7 guards per member | v1 `test_s0005_ac7_*` |
| S0006 AC1 §87 grid | rd `test_s0006_ac1_*` |
| S0006 AC2 at most one; internal `NOT_PROCESSED`; GET 404 | rd `test_s0006_ac2_*`, `test_ex_pc_014_a_to_d_*` (D) |
| S0006 AC3 validity-unknown never returns a value | rd `test_s0006_ac3_*`, `test_ex_pc_014_a_to_d_*` (B, C) |
| S0006 AC4 half-open boundaries | rd `test_s0006_ac4_*` |
| S0006 AC5 full read shape; pilot names kept | rd `test_s0006_ac5_*` |
| S0006 AC6 default and malformed coordinates | rd `test_s0006_ac6_*` |
| S0006 AC7 revoked grant denied at every coordinate, non-disclosing | rd `test_s0006_ac7_*` |
| S0007 AC1 byte-for-byte snapshot, audit unchanged | mig `test_s0007_ac1_ac2_ac4_ac6_*` |
| S0007 AC2 legacy marker, nothing invented, NULL upper reads OPEN | mig same test (null new columns; `valid_to_state` property) |
| S0007 AC3 legacy shape kept; pilot shape to v1 refused | v1 `test_s0007_ac3_*`; rd `test_legacy_slot_reads_keep_pilot_behaviour`; unit-s `test_d1_contract_binding` |
| S0007 AC4 up/down/up; downgrade refusal names rows | mig `test_s0007_ac1_*`, `test_s0007_ac4_*`; `g2-migration-cycle.txt` |
| S0007 AC5 existing F0001 and F0007 suites pass | full regression |
| S0007 AC6 no grant, role or route | mig grants/roles snapshot, `test_s0007_ac6_no_route_is_added` |

Additional security cases (Phase B risk list):

- D4 read disclosure: rd `test_d4_attestation_dates_of_unreadable_documents_are_not_disclosed`.
- D4 commit disclosure: `test_d4_committer_must_read_every_attesting_document`.
- D6 `23P01` → `temporal_conflict`: con `test_d6_*`.
- D7 upgrade preflight: mig `test_d7_*`.

## ADR-0078 proof gates

| Gate | Evidence |
|---|---|
| 1 §115.4 under v1 (retroactive, correction, race ≥8 on a grid, distinct times, lineage) | v1 S0003 tests, con S0004 AC1 |
| 2 Immutability negatives and the single close | imm S0003 AC5 |
| 3 Zone and precision fixtures, both tzdata versions | unit-b, v1 S0001; `artifacts/test-results/g1-tzdata-versions.txt` |
| 4 EX-SEM-004 and EX-PC-014 A–D reads | rd |
| 5 Envelope backstop, guards, per-member independence | imm S0004 AC5, v1 S0005, con S0004 AC3 |
| 6 Migration snapshot and downgrade guard | mig |

## Environment

`brain-postgres:18-pgvector-age` (PostgreSQL 18.6) and the locked `engine/.venv` (Python 3.14.4). The shared-DB suites use the disposable `brain_f0008_shared` database migrated to head (see `g1-runtime-preflight.md`).
