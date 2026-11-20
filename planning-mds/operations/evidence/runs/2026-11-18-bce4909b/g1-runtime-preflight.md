# G1 Runtime Preflight — F0008 review remediation

- Run: `2026-11-18-bce4909b`
- Role: DevOps
- Reviewer: Claude (Opus 5.5) / DevOps
- Date: 2026-11-18
- Verdict: PASS
- runtime_bearing: true

## Runtime under test

The runtime is the same as in the prior run (`2026-11-17-1a4ae2f0`, `g1-runtime-preflight.md`): the Docker Desktop `brain-postgres` container (`brain-postgres:18-pgvector-age`, PostgreSQL 18.6, `healthy`) plus the locked `engine/.venv` (Python 3.14.4).

| Probe | Result | Evidence |
|---|---|---|
| Container health and server | healthy; PostgreSQL 18.6 | `artifacts/test-results/g1-runtime-probe.txt` |
| Disposable shared-suite DB | `brain_f0008_shared` recreated fresh with `btree_gist`; `alembic upgrade head` 0001→0015 rc=0 | `artifacts/test-results/command-output/fresh-db-upgrade-head.txt` |
| Owned test databases | `BRAIN_MIGRATION_ADMIN_URL` harness in use (the F0008 suites ran 237 cases during implementation) | `commands.log` |
| tzdata | unchanged since the prior run: PostgreSQL 2025b, Python 2026e | prior run `artifacts/test-results/g1-tzdata-versions.txt` |

The shared development database `brain` stays at 0010, untouched. The runtime-blocked protocol is the same as in the prior run.
