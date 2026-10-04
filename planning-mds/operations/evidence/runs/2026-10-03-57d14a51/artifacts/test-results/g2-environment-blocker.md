# G2 Test Environment Note

- The host-side Python socket probe to `127.0.0.1:5432` failed at socket creation with `PermissionError: Operation not permitted`.
- `docker compose exec` could not access `/var/run/docker.sock` (`permission denied`), so pytest could not be run inside the healthy Compose PostgreSQL container.
- The in-container PostgreSQL health/readiness evidence remains the G1 preflight. No live database test result is claimed for G2.
