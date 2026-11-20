# Test Execution Report — F0008 second remediation (run 2026-11-19-8cfcd0ff)

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-19
- Verdict: PASS

## Results

The runtime preflight (`commands.log` line 1, 22:24:02) precedes every test run below.

| Run | Result | Raw evidence |
|---|---|---|
| **Final full engine regression** (fresh DB at 0015; owned DBs per F0008 test) | **1101 passed, 0 failed, 0 errors, 0 skipped** | `artifacts/test-results/final-full-engine-regression.xml`, `command-output/final-full-engine-regression.txt` |
| Earlier full run, before the helper unit tests existed | 1090 passed | `full-engine-regression.xml` |
| Concurrency suite, three repeats | 6/6, 6/6, 6/6 | `command-output/concurrency-repeat-{1,2,3}.txt` |
| CI no-DB package gates | `brain_temporal` 97.44%, `brain_api` 82.78%, `brain_domain` 90.84%, `brain_factslots` 87.65% | `command-output/ci-nodb-gate-*.txt` |

The first `brain_api` no-DB gate run reported 79.44%, because the new route helpers were exercised only on PostgreSQL. The helper unit tests were added and the gate re-run; both entries are in `commands.log`.

## Acceptance criteria

All 46 ACs (as amended on 2026-11-18) remain evidenced. SEC-F8-NEW-01 is closed by the four new behaviours above.
