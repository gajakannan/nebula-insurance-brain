# PR #27 CI follow-up

The runtime-suites failure in [run 39709411098](https://github.com/gajakannan/nebula-insurance-brain/actions/runs/39709411098/job/119596889780?pr=27) exposed an archived fixture path and missing PostgreSQL test configuration.

The contract example test now reads the archived F0004 feature directory. The owned-database fixture skips only when BRAIN_MIGRATION_ADMIN_URL is absent; configured connection, migration and restore failures still fail the tests.

The existing 80% persistence coverage gate now runs in runtime-stack with PostgreSQL and Docker. It includes the F0004 migration, date concurrency and actual backup/restore suites, so the generic runtime-suites job can run without a database while the stack job enforces real persistence coverage.

Validation ran in the existing run-scoped application containers:

- [Full engine without database configuration](artifacts/test-results/ci-followup-engine-no-db.txt): 301 passed, 103 environment-dependent skips.
- [Configured persistence, migrations and restore](artifacts/test-results/ci-followup-persistence-restore.txt): 46 passed, no skips, 89.89% persistence coverage (80% required).
- [API and content coverage](artifacts/test-results/ci-followup-api-content-coverage.txt): API 30 passed and four optional skips at 88.40%; content 93 passed at 89.43%.
- Ruff lint and format checks passed for the two changed test files; workflow YAML parsed successfully.

These checks supplement the approved implementation evidence. Runtime implementation and activation settings are unchanged.
