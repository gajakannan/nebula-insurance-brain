# G1 Runtime Preflight

Feature: F0006. Run: 2026-11-02-5a00b0ff. Reviewer: Codex (DevOps).
Recorded: 2026-11-03T00:08:30.065388+00:00

## Required Runtime and Recovery

The original WSL/sandbox failure is retained verbatim at
`artifacts/runtime/logs/g1-original-failure.md`. The operator relaunched Codex with
on-request permissions. Docker commands now reach the daemon through approved
execution. The runtime stop condition is cleared.

F0006 needs PostgreSQL and the engine/neuron validation jobs, using the existing
application container definitions and locked F0005 baseline images with the current
source mounted. Structural admission makes no model/conversion/OCR calls, so the
GPU/model service is not a prerequisite. Authentik has no new deployment or grant
change; scoped authorization tests use the existing signed-principal fixture boundary.

## Executed Checks

| Check | Result | Evidence |
|---|---|---|
| Docker Compose access and PostgreSQL recovery | PASS; brain-postgres healthy | commands.log |
| Engine/neuron validation job health | PASS; both healthy | artifacts/runtime/compose.yaml, commands.log |
| Application `/health` and storage | PASS; both ok | artifacts/runtime/logs/g1-resumed-health.json |
| PostgreSQL version | 18.6 | artifacts/runtime/logs/g1-resumed-health.json |
| Existing migration recovery | Source head0010; restored pre-existing0009 database to0010; no F0006 migration yet | commands.log, artifacts/runtime/logs/g1-resumed-health.json |
| Python/runtime dependencies | Python3.14.4, pytest9.1.1, pydantic2.13.5 | artifacts/runtime/logs/g1-resumed-health.json |
| Framework scan-staging repair regression | Seven passing in engine container; G2+ scans still required | artifacts/test-results/framework-security-scan-staging.xml |

The first Alembic attempt used the API's asyncpg URL with the synchronous migration
runner and failed with MissingGreenlet; rerunning with a command-scoped psycopg URL
passed. No source change was made for this configuration mismatch. Product tests
will run only inside the healthy validation jobs; changed package/dependency images
will be rebuilt before final validation. No production deployment is claimed.

## Result

PASS
