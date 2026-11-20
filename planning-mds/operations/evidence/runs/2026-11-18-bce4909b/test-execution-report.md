# Test Execution Report — F0008 review remediation (run 2026-11-18-bce4909b)

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-18
- Verdict: PASS

## Results

| Run | Result | Raw evidence |
|---|---|---|
| Full engine regression (fresh disposable DB at 0015; owned DBs per F0008 test) | **1085 passed, 0 failed, 0 errors, 0 skipped** | `artifacts/test-results/full-engine-regression.xml`, `command-output/full-engine-regression.txt` |
| Concurrency suite, three repeats | 6/6, 6/6, 6/6 | `command-output/concurrency-repeat-{1,2,3}.txt` |
| CI no-DB package gates | `brain_temporal` 97.40%, `brain_api` 81.78%, `brain_domain` 90.84%, `brain_factslots` 87.65%; all rc=0 | `command-output/ci-nodb-gate-brain_*.txt` |
| Migration 0015 cycle | covered by `test_0015_*` (preflight refusal, up/down/up) and `fresh-db-upgrade-head.txt` | as listed |

Four mislabeled files, `ci-nodb-gate-brain_* packages/...txt` (names containing a space, rc=1), came from a zsh word-splitting mistake that collected the whole suite under each gate. They are superseded by the correct runs above. `commands.log` keeps all eight entries.

## Acceptance criteria

All 46 ACs, as amended on 2026-11-18 (S0004 AC1, S0007 AC6, with an annotation on S0002 AC7), have observed passing evidence. S0002 AC7 and S0004 AC1 were the two criteria the review found unmet; both now pass as written.
