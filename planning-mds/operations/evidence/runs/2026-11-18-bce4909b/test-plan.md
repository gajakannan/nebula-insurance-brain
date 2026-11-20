# Test Plan — F0008 review remediation (run 2026-11-18-bce4909b)

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-18

## Approach

This run keeps the full prior test plan (`../2026-11-17-1a4ae2f0/test-plan.md`) and re-runs every case. It adds or changes tests only where a review finding showed a gap. Expectations come from the ACs as amended by the operator on 2026-11-18 and from the contracts.

## Finding → test

| Finding | AC | Test |
|---|---|---|
| CR-F8-01 | S0002 AC7 (commit response) | `test_temporal_v1_commit.py::test_s0002_ac7_commit_response_returns_temporal_metadata` (order, remainder lineage, UNKNOWN attestation, equality with the read); `test_contract_examples.py::test_runtime_commit_response_validates_for_v1_and_legacy` |
| CR-F8-01 | S0007 AC3/AC6 (pilot shape kept) | `test_temporal_reads.py::test_legacy_slot_reads_keep_pilot_behaviour` (legacy commit response has exactly the three pilot fields) |
| FR-ARCH-M1 | S0006 AC5, contract | `test_legacy_slot_reads_keep_pilot_behaviour` (`temporal` absent, not null) |
| QE-M1 | S0004 AC1 (amended) | `test_temporal_concurrency.py::test_s0004_ac1_racing_commits_*`: `failed` decisions equal the losers |
| FR-ARCH-L2 | S0004 AC6, ADR-0078 D5 | `test_temporal_immutability.py::test_fr_arch_l2_split_lineage_cannot_cross_slots`; `test_temporal_migration.py::test_0015_preflight_refuses_cross_slot_lineage_and_cycles_cleanly` |
| QE-L1 | evidence support | three concurrency repeats and four no-DB CI gates with raw output under `artifacts/test-results/command-output/` |

The AC traceability for the other 44 ACs is unchanged; see the prior test plan.
