# G2 Test Environment Note

- The host-side Python socket probe to `127.0.0.1:5432` failed at socket creation with `PermissionError: Operation not permitted`.
- Rechecked after syncing the squash merge to local `main` on 2026-10-04; socket creation is still denied.
- `docker compose exec` could not access `/var/run/docker.sock` (`permission denied`), so pytest could not be run inside the healthy Compose PostgreSQL container.
- GitHub Actions run `37241111686` provided a hosted PostgreSQL 18 environment. Its runtime-stack job passed the focused engine (4 tests) and recovery (5 tests) suites; see `g2-ci-37241111686.md`.
- The hosted runtime-suites job stopped at a Ruff error before broader pytest and coverage steps. The issue is fixed locally in continuation commit `038a87d`; a hosted rerun is needed to collect full results.
- These focused hosted results supplement G1 health/readiness evidence but do not establish all F0003 acceptance criteria or current-run coverage.
