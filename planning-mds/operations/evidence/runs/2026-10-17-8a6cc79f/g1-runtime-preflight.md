# Runtime Preflight — F0004 run 2026-10-17-8a6cc79f

## Feature

- Feature ID: F0004
- Run ID: 2026-10-17-8a6cc79f
- Date: 2026-10-17 (America/New_York)
- Owner: Codex (DevOps role)
- NEBULA_PRODUCT_ROOT: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain

## Runtime Services / Containers / Jobs

The approved plan requires the existing engine/API and neuron converter/worker runtime, PostgreSQL 18 for migration/ownership/locking proofs, and isolated database/content restoration. Step 1a requires the pinned converter for actual per-item provenance observations. No frontend runtime is in scope.

## Command Evidence

- `docker --version` — exit 1, Docker Desktop reports that Docker is unavailable in this WSL 2 distro. See `artifacts/test-results/docker-version.txt`.
- `docker compose ps --format json` — exit 1, same missing WSL integration. See `artifacts/test-results/docker-compose-preflight.txt`.
- `docker-compose ps` — exit 1, the standalone shim also reports missing WSL integration. See `artifacts/test-results/docker-compose-fallback-preflight.txt`.
- Runtime availability probe at `2026-10-18T00:54:43.636673+00:00`: no `/var/run/docker.sock` or rootless Docker socket; Docker CLI resolves to the Windows Docker Desktop shim. See `artifacts/test-results/runtime-availability.json`.
- Executable discovery found no `dockerd`, `containerd`, or `podman`; there is no local daemon/runtime available to start. The exact commands and exits are in `commands.log`.

## Initial health status (historical)

| Service | Status | Notes |
|---|---|---|
| Container runtime | unavailable | Docker Desktop WSL integration missing; no local socket/daemon |
| Engine/API and neuron/converter runtime | not verified | Required container execution cannot start |
| PostgreSQL 18 proof runtime | not verified | No reachable container runtime established |
| Isolated restore target | not verified | No proof execution attempted |

## Restore Steps If Unavailable

Docker Desktop must be running on the Windows host with WSL integration enabled for this distro. This session has no exposed host settings control, local daemon binary, or local socket through which to restore it. No unrelated host configuration or runtime replacement was attempted.

After integration is restored, resume this same run with:

```sh
python3 agents/scripts/resume-brief.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --run-id 2026-10-17-8a6cc79f
```

Reload product context, rerun the same Docker/Compose probes, restore the existing product runtime from its configuration/runbook, and establish service health. Replace this failed preflight with observed health evidence and rerun G1 through run-gate.py before the provenance spike or any application validation. Preserve the failed command artifacts. Do not generate a new run ID or start a competing feature action.

## Resume attempt — 2026-10-18T01:18:29Z

Owner: Codex (DevOps role). Operator authorized resuming the existing run.
The earlier missing-WSL-integration observations above are preserved as history.

- `docker --version` now passes: Docker 29.6.2, build dfc4efb. Evidence: `artifacts/test-results/resume-20261018T011829Z-docker-version.txt`.
- `docker compose ps --format json` and `docker-compose ps` both exit 1: permission denied connecting to the Docker API at `unix:///var/run/docker.sock`. Evidence: `artifacts/test-results/resume-20261018T011829Z-docker-compose.txt` and `artifacts/test-results/resume-20261018T011829Z-docker-compose-fallback.txt`.
- `/var/run/docker.sock` now exists; no rootless socket or local `dockerd`, `containerd`, or `podman` executable was found. Evidence: `artifacts/test-results/resume-20261018T011829Z-runtime-availability.json`.
- Compose also reports unset Authentik configuration variables. No secret values were read, generated, or logged. Service health cannot be determined until Docker access is restored.

Current blocker: Docker socket access is denied in this managed session. The host permission policy disables elevated execution, and the socket is outside the writable workspace. This run cannot restore access through an authorized in-session action. Restore Docker API access for the execution environment, then resume this same run and verify the existing configured services before implementation or application validation. Do not weaken socket permissions or bypass the managed sandbox.

The runtime stop condition still applies. No implementation, provenance spike, application tests, migration, or restore drill ran during this resume.

## Resume attempt — 2026-10-18T01:54Z

Owner: Codex (DevOps role). The operator requested the same run and product root,
with G1 rechecked first. Earlier failed probes above remain historical evidence.
Docker API access now works through approved elevated commands in this session.

The product Compose file contains dependencies only. Run-scoped application
validation jobs were restored from the existing engine and neuron workspaces,
using digest-pinned Python 3.14.4 and uv 0.11.31 images and `uv sync --locked`.
Their definitions and reproduction instructions are in `artifacts/runtime/`.
These jobs introduce no public port or product deployment boundary. They run
as UID/GID 1000; the neuron job does not consume the production ingestion queue.
No model engine, permission grant, or Graph activation was added.

| Runtime | Observed result | Evidence under artifacts/test-results/ |
|---|---|---|
| Dependency Compose stack | PostgreSQL, Authentik server and worker running and healthy | resume-g1-dependencies.txt |
| PostgreSQL | 18.6; vector 0.8.6, AGE 1.8.0, btree_gist 1.8 | resume-g1-postgres.txt |
| Authentik | Live endpoint HTTP 200 | resume-g1-authentik.txt |
| Application job builds | Both locked-workspace builds exit 0; immutable base digests recorded | resume-g1-pinned-build.txt |
| Application jobs | Both running and healthy after bounded Compose wait | resume-g1-runtime-start.txt; resume-g1-application-jobs.txt |
| Engine/API | HTTP health status ok; isolated content round trip ok; database SELECT succeeds | resume-g1-engine-health.txt |
| Neuron converter/worker runtime | DoclingAdapter constructs; worker imports; database SELECT succeeds | resume-g1-neuron-health.txt |
| Isolated restore readiness | Database role may create an isolated target; scratch content is isolated | resume-g1-engine-health.txt |

Measured neuron versions: Python 3.14.4, Docling 2.126.0, docling-core 2.95.0,
docling-parse 7.18.0, RapidOCR 3.9.2, Torch 2.14.0. The workspace lockfiles were
not changed. Compose warnings about unset Authentik variables remain; existing
healthy dependency containers were neither recreated nor reconfigured, and
no secret values were read or logged.

This is readiness evidence. Per-item provenance, migration, ownership/locking,
restart/reuse and isolated backup/restore acceptance still require their planned
executions. No application tests, parser conversion, migration, restore drill
or feature implementation had run when this preflight was recorded.

## Step 1a runtime restoration — 2026-10-18T01:56Z

The first actual converter initialization discovered that RapidOCR downloads its
weights under its package directory. The non-root validation job could not write
there, so the spike stopped before conversion (`step1a-runtime-cache-failure.txt`).
This is runtime-blocked, not a provenance FAIL. Application source edits stopped.
The neuron job now has an isolated UID/GID 1000 tmpfs at that model-cache path.
Both jobs returned healthy and a non-root write/read/remove probe succeeded
(`step1a-cache-restored-health.txt`, `step1a-model-cache-writable.txt`). Re-run G1,
then the identical failed spike command without application source changes.

## Result

PASS

The previous runtime-blocked condition is resolved. Run the ordered G1 validator
before Step 1a. G2–G8 remain unexecuted. Planning approval is unchanged; no
feature-completion approval or latest-run pointer has been published.


## Final locked runtime refresh — 2026-10-19

All three run-scoped application jobs are healthy on the final rebuilt locks.
The engine and neuron builds include the targeted dependency remediation;
Docling/OCR/Graph pins are unchanged. The restore-validation job separately
proved actual isolated v1/v2 restore with four passing cases. Dependency
containers and shared database were not recreated or migrated.

Evidence: `artifacts/test-results/g2-security-remediated-locked-build.txt`;
`artifacts/test-results/g2-remediated-runtime-start.txt`;
`artifacts/test-results/g2-remediated-runtime-health.txt`;
`artifacts/test-results/g2-final-restore-tests.txt`.
The ordered G1 replay and G2 subsequently passed. This refresh supersedes the
old pre-implementation position above; it does not grant G4 approval.
