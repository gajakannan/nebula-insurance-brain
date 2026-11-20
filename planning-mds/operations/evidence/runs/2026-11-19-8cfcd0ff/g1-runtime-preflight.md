# G1 Runtime Preflight — F0008 second remediation

- Run: `2026-11-19-8cfcd0ff`
- Role: DevOps
- Reviewer: Claude (Opus 5.5) / DevOps
- Date: 2026-11-19
- Verdict: PASS
- runtime_bearing: true

The preflight was recorded **before** any test or regression in this run (QE2-L1):

| Probe | Result | Evidence |
|---|---|---|
| Container health | `brain-postgres:18-pgvector-age` healthy at 2026-11-19T22:24:02-05:00 | `artifacts/test-results/g1-runtime-probe.txt` (`commands.log` line 1) |
| Server and extensions | PostgreSQL 18.6; age 1.8.0, btree_gist 1.8, vector 0.8.6 | same |
| Disposable shared-suite DB | `brain_f0008_shared` recreated and migrated 0001→0015, rc=0 | `artifacts/test-results/command-output/fresh-db-upgrade-head.txt` |

The engine venv (Python 3.14.4) and tzdata (PostgreSQL 2025b, Python 2026e) are unchanged from the prior runs.
