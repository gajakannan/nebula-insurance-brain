# Test Execution Report — F0008 (run 2026-11-17-1a4ae2f0)

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-18 (G2 runs on 2026-11-17, final run after the G3 fixes on 2026-11-18)
- Verdict: PASS

## Runtime

- PostgreSQL: `brain-postgres:18-pgvector-age` (18.6, healthy).
- Python: `engine/.venv` 3.14.4.
- Databases:
  - every F0008 integration test owns a database migrated to head (`BRAIN_MIGRATION_ADMIN_URL`);
  - the shared-DB suites use the disposable `brain_f0008_shared`, created fresh at head.
- tzdata: PostgreSQL 2025b, Python 2026e (`artifacts/test-results/g1-tzdata-versions.txt`).

## Results

| Run | Scope | Result | Evidence |
|---|---|---|---|
| G1 baseline (before any change) | F0001/F0007 fact suites, brain-temporal unit | 74 passed | `artifacts/test-results/g1-baseline-regression.xml` |
| G2 full engine regression | all engine tests | 1076 passed, 0 failed, 0 skipped | `artifacts/test-results/g2-full-engine-regression.xml`, `command-output/g2-full-engine-regression.txt` |
| **Final full engine regression (after the G3 fixes)** | all engine tests | **1081 passed, 0 failed, 0 errors, 0 skipped** | `artifacts/test-results/g3-full-engine-regression.xml`, `command-output/g3-full-engine-regression.txt` |
| Concurrency suite, repeated | `test_temporal_concurrency.py` | 3 runs with 5/5 each, then 6/6 after the SEC-F8-01 test was added | `commands.log` |
| CI no-DB package gates, emulated | `brain_temporal` / `brain_api` / `brain_domain` / `brain_factslots` | 97.4% / 82.3% / 90.8% / 87.7%, every one ≥ 80% | `commands.log` |
| Alembic CLI cycle | head → 0013 → head | PASS | `command-output/g2-migration-cycle.txt` |

The final run contains 213 F0008 cases, none failed or skipped:

| Suite | Cases |
|---|---|
| `test_bounds.py` | 56 |
| `test_contract_examples.py` (F0008) | 39 |
| `test_temporal_service.py` | 12 |
| `test_temporal_v1_commit.py` | 50 |
| `test_temporal_immutability.py` | 35 |
| `test_temporal_concurrency.py` | 6 |
| `test_temporal_reads.py` | 11 |
| `test_temporal_migration.py` | 4 |

## Acceptance criteria

All 46 ACs have observed passing evidence, mapped test by test in `test-plan.md`.

| Story | ACs | Result |
|---|---|---|
| S0001 Precision and zone | 6/6 | PASS, including a DST spring/fall case and the trigger agreeing (4 direct-insert negatives) |
| S0002 Open, bounded and unknown ends | 7/7 | PASS: EX-SEM-004; floor; `START_UNATTESTED` for undated, cleared and absent evidence; `ATTESTATION_MISMATCH` |
| S0003 Split and close | 7/7 | PASS: §115.4 retroactive change and correction; the remainder keeps the predecessor's timestamps; 23 immutable columns; fault injection leaves nothing |
| S0004 Integrity under concurrency | 6/6 | PASS: 12 racers on a grid of at least 200 coordinates; members; RELATIONSHIP; envelope; cross-scope |
| S0005 Succession guards | 7/7 | PASS: each basis, end revision, EX-OWN-003, six refused states, per member |
| S0006 Two-coordinate reads | 7/7 | PASS: §87 grid, EX-PC-014 A–D, half-open bounds, revocation |
| S0007 Pilot preservation | 6/6 | PASS: byte-identical up/down/up, downgrade refusal naming rows, no grant, role or route |

## ADR-0078 proof gates

All six have passing evidence (see `test-plan.md`). The tzdata versions of both runtimes are recorded.

## Defects found during execution

- **Code (fixed):**
  - a right remainder re-opened the old fact after an UNKNOWN end revision;
  - commit-side date disclosure for legacy evidence;
  - the migration envelope helper;
  - a malformed instant returned the wrong code (CR-L1);
  - the 409 detail echoed database text (SEC-F8-01).
- **Test-side (fixed):** four expectation or fixture mistakes (`g2-self-review.md`).
- **Runtime (resolved, not code):** Docker Desktop was stopped; the shared `brain` database is at 0010 (`g1-runtime-preflight.md`).

## Changes to existing suites

- The F0007 harness commit helper sends the v1 block.
- `test_factslot_ownership` uses `EXPLICIT_NEGATIVE`.
- `test_factslot_migration` is pinned to 0013.
- The three cleanup fixtures use `session_replication_role`.

All are logged as reconcile decisions (`artifacts/workstate.json`, plan "Feature-Action G0 Reconciliation"). No assertion in an existing test was weakened.
