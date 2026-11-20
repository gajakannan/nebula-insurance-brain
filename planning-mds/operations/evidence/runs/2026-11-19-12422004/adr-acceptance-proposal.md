# F0008 ADR acceptance proposal — ADR-0078

- Prepared: 2026-11-19, by Claude (Opus 5.5) / Architect
- Basis: approved feature run `2026-11-19-8cfcd0ff` (merged as #58, `388aa17`). It supersedes `2026-11-18-bce4909b` (#56) and `2026-11-17-1a4ae2f0` (#55).
- Decision run: `2026-11-19-12422004`

ADR acceptance is a separate decision from approving and merging the feature. Merging this PR records the operator's acceptance.

## Proposed disposition

- **Accept ADR-0078** (bitemporal version contract and close-only immutability). All six of its proof gates have passing PostgreSQL 18 evidence below. The operative decisions include the remediation clarifications:
  - D4 covers the commit response;
  - D5 states the three copied source timestamps and the same-slot lineage guard of migration 0015.
- **Keep ADR-0064 and ADR-0039 Proposed.** F0008 implements only their storage share (precision, unknown ends, information-state supersession). Their own acceptance gates belong to F0016/F0026 (ADR-0064) and the downstream owners recorded in ADR-0039.

## ADR-0078 proof map

All tests are under `engine/`. They pass in the final full engine regression of run `2026-11-19-8cfcd0ff`: 1101 passed, 0 failed, 0 skipped (`final-full-engine-regression.xml`).

| Proof gate | Current proof |
|---|---|
| 1. §115.4 bitemporal proof under v1: retroactive change and correction, 8+ concurrent commits on a coordinate grid, distinct received/accepted times, remainder lineage | `tests/integration/test_temporal_v1_commit.py` (`test_s0003_ac1_ac6_*`, `test_s0003_ac2_*`, `test_s0003_ac3_*`); `tests/integration/test_temporal_concurrency.py` (`test_s0004_ac1_*`: 12 racers, at least 200 coordinates, failed decisions equal losers; 3/3 repeats in run `2026-11-19-8cfcd0ff`) |
| 2. Immutability negatives and the single permitted close | `tests/integration/test_temporal_immutability.py` (`test_s0003_ac5_*`: 23 columns, reopen, move, DELETE, TRUNCATE, change append-only; `test_fr_arch_l2_*`: same-slot lineage) |
| 3. Zone and precision fixtures, every granularity, DST, `Etc/GMT+6`, both tzdata versions recorded | `packages/brain-temporal/tests/test_bounds.py`; `test_temporal_v1_commit.py` (`test_s0001_*`, including trigger authority); tzdata PostgreSQL 2025b / Python 2026e in `runs/2026-11-17-1a4ae2f0/artifacts/test-results/g1-tzdata-versions.txt` |
| 4. EX-SEM-004 and EX-PC-014 A–D reads, validity-unknown | `tests/integration/test_temporal_reads.py` (`test_s0006_ac3_*`, `test_ex_pc_014_a_to_d_*`) |
| 5. Envelope backstop, guards, per-member independence; disclosure under D4 | `test_temporal_immutability.py` (`test_s0004_ac5_*`); `test_temporal_v1_commit.py` (`test_s0005_*`); `test_temporal_concurrency.py` (`test_s0004_ac3_*`); `test_temporal_reads.py` (`test_d4_*`, `test_sec_f8_new_01_*`) |
| 6. Migration: pilot and F0007 snapshot byte-identical across up/down/up; downgrade guard names rows | `tests/integration/test_temporal_migration.py` (`test_s0007_*`, `test_d7_*`, `test_0015_*`) |

**CI:** PR #58 [CI Gates run 44672709480](https://github.com/gajakannan/nebula-insurance-brain/actions/runs/44672709480) passed every job on `326c9dc`, including the F0008 PostgreSQL step. It ran with `main` already merged in, at framework pin `840e724`.

**Independent review:**
- Closeout audit `2026-11-18-a3709ba0`.
- Reviews `2026-11-18-d34a095e` and `2026-11-19-b21ec2de`.

Their findings were remediated in runs `2026-11-18-bce4909b` and `2026-11-19-8cfcd0ff`.

## Residuals that do not block acceptance

- **SEC-F8-02:** the local/CI superuser application role can skip triggers. It goes to F0018 with the non-superuser application role.
- **Durable refusal reason codes:** F0018 (ADR-0078 D8 note).
- **Pre-existing `brain-api.yaml` `FactVersion` field-name drift (CR-I1):** Architect.

## Operator decision

Accept ADR-0078, recorded by merging this PR.
