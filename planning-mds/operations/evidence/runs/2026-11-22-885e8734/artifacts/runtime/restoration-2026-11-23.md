# Runtime restoration on 2026-11-23

Reviewer: Codex / DevOps. Result: PASS for task-container and database readiness;
no source validation or security scan is claimed by this restoration record.

The first Compose probe failed because Docker Desktop's WSL integration was not
available: the Linux CLI symlink target and socket were absent. The installed
Docker Desktop application was started with approval. Its backend launched at
15:34 UTC. The GUI launcher remains running; no process exit is claimed.

PostgreSQL restarted healthy. The existing F0011 engine, Neuron and Node task
containers were restarted with `docker compose ... start`, preserving their
installed task virtual environments. All three subsequently reported healthy.
The [fresh read-only engine/database probe](resume-preflight-2026-11-23.json)
records both actual environments at schema 0015 with zero canonical history rows.

The preserved engine uses Python 3.14.4, Pydantic 2.13.5 and generator 0.96.0.
Neuron's existing task environment still contains Docling 2.142.0, Pillow 13.0.0,
Pydantic 2.13.5 and the shared brain-contracts/content packages. Node's cached
pnpm is 12.21.0. No reinstall or payload rewrite was needed.

The [scanner inventory](scanner-inventory-2026-11-23.json) records cached immutable
image IDs, without claiming scan results. No Trivy image was cached. Existing task
services are headless validation processes; an HTTP application server has not
been activated. The proposed internal DAST target becomes available only after
the root orchestrator authorizes the final candidate server start.
