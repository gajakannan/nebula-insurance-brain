# F0004 isolated validation jobs

These run-scoped jobs provide the application-container execution required by
the feature contract. The product Compose file defines dependencies only.
They add no public port, grant, model engine, production worker activation, or
product deployment boundary. The neuron job waits for explicit validation
commands; it does not consume the ingestion queue.

The Dockerfile uses digest-pinned Python 3.14.4 and uv 0.11.31 images and installs
each workspace with `uv sync --locked`. The two lockfiles remain unchanged.
Jobs run as UID/GID 1000, join the existing dependency network, and mount the
selected product source at `/app/brain`. API health scratch storage is an
isolated tmpfs. The preflight database checks are read-only; migration and
restore proofs must use isolated targets later in the run.

From the selected product root, set `F0004_COMPOSE` to the relative path
`planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/artifacts/runtime/compose.yaml`.

```sh
docker compose -f "$F0004_COMPOSE" build
docker compose -f "$F0004_COMPOSE" up -d --no-build
docker compose -f "$F0004_COMPOSE" ps
docker compose -f "$F0004_COMPOSE" exec -T engine-validation python --version
docker compose -f "$F0004_COMPOSE" exec -T neuron-validation python --version
```

Use `exec -T` on these services for stack-specific tests and scans. Check their
health before validation. Rebuild if a lockfile changes. Stop these jobs with
`docker compose -f "$F0004_COMPOSE" down` when the run no longer needs them;
the external dependency network and dependency services are preserved.
