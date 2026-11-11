# F0007 ADR acceptance proposal — PR-M1

Prepared 2026-11-10 after commit `4c4e37ec92c602e9eb9584bf0aa1b9634ec6625e` passed every PR CI check. PR #44 remains open and unmerged at the operator's explicit request. ADR acceptance is a separate decision from merging the PR.

## Proposed disposition

- Accept ADR-0077, whose operative D4/D5/D7/D8 now include the reviewed member-value, numeric, protected-read and identity-guard invariants. All five acceptance proof gates have evidence below.
- Retain ADR-0039 and ADR-0066 as Proposed. Their own status sections now identify the outstanding downstream proofs, owners and acceptance checkpoints. Accepting a broader decision before those gates pass is not required to complete F0007.

## ADR-0077 proof map

| Acceptance gate | Current proof |
|---|---|
| Concurrent resolution and forced collisions | `test_factslot_resolution.py`: `test_s0001_ac1_resolving_twice_and_concurrently_returns_one_slot`, `test_s0001_ac3_forced_collision_is_rejected_never_merged` |
| Independent members and SINGLE exclusion | `test_factslot_ownership.py`: `test_s0002_ac3_ac5_members_carry_independent_versions`, `test_s0002_ac2_single_slot_overlap_still_hits_the_exclusion` |
| Carrier/value rejections write zero rows; three kinds of missing value | `test_factslot_answers.py`: `test_s0003_ac2_state_value_mismatch_writes_no_version`, `test_s0003_ac5_ex_own_003_three_kinds_of_no_value`, numeric-bound and member-mismatch regressions |
| Ownership and protected-scope negatives without disclosure | `test_factslot_ownership.py`, `test_factslot_answers.py`, `test_factslot_authorized_reads.py`: exact selected payload authorization and revocation interleaving |
| Pilot preservation and regression compatibility | `test_factslot_migration.py`: `test_s0006_ac1_ac6_up_down_up_keeps_pilot_rows_identical`; `test_factslot_identity_guard_migration.py`: 0013 up/down/up, strict identity shape and refusal without repair; prior full engine/Neuron regressions |

The test files above are under `engine/tests/integration/`. The local combined current-source run passed 369 tests with zero skips and 98.60% FactSlot coverage (`artifacts/tests.xml`). The approved remediation run `2026-11-09-81798e61` contains the full 868-engine/27-Neuron regression evidence. PR [CI Gates run 42948384156](https://github.com/gajakannan/nebula-insurance-brain/actions/runs/42948384156) passed every job, including the expanded F0007 PostgreSQL gate, on commit `4c4e37e`; graph reproducibility passed separately.

## Operator decision

Pending an explicit choice between accepting ADR-0077 with the above narrower deferrals, or retaining all three Proposed with a recorded F0008 Phase B decision checkpoint. The earlier implementation/closeout approval is not relabeled as formal ADR acceptance.
