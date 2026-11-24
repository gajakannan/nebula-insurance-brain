# G1 Runtime Preflight — F0011

- Role: DevOps
- Reviewer: Codex / DevOps
- Date: 2026-11-22
- Run: `2026-11-22-885e8734`
- Verdict: PASS — engine/Node and restored database baseline ready for their checks.

The run-local [compose definition](artifacts/runtime/compose.yaml) starts isolated
application validation containers from the cached Python and Node runtimes.
All three services report healthy. The engine's new writable environment has
completed `uv sync --project engine --group contract-build --locked`; the Node
container completed the exact dependency install. No feature test or scan was run
before these readiness probes. Neuron compatibility tests remain gated on its
clean lock sync and a fresh probe; its old image environment is not counted as
the current locked candidate.

This G1 verdict admits engine and Node validation. It does not record a Neuron
candidate validation or deployment pass: no Neuron test, scan or compatibility
command may run until the clean lock sync completes and its readiness refresh
is recorded here. G2 must include that refresh and the actual Neuron caller proof.

The [read-only probe](artifacts/runtime/preflight-probe.json) records Python
3.14.4, datamodel-code-generator 0.96.0, build 1.6.1, Pydantic 2.13.5,
jsonschema 4.26.0, referencing 0.37.0 and rfc3986-validator 0.1.1. Node is
22.23.1 with pnpm 12.21.0; installation evidence is
[node-dependencies.txt](artifacts/runtime/node-dependencies.txt).

Both existing PostgreSQL environments were identified from actual database
inventory. `brain` is the Settings default dev database; `brain_f0008_shared`
is the existing integration database identified in the previous F0008 G1
report (`2026-11-19-8cfcd0ff/g1-runtime-preflight.md`). Both now report schema
0015, PostgreSQL 18.6 and zero canonical history rows in READ ONLY snapshots.
The integration database has btree_gist; dev additionally has the prior AGE and
pgvector extensions. This feature does not require a graph/vector runtime.

Dev was initially at schema 0010. It was backed up privately before applying
only the already-shipped 0011–0015 migrations. The
[restoration record](artifacts/runtime/baseline-restoration.json) records the
backup digest and before/after counts. No new migration or historical payload
repair was introduced. No response guard has been deployed. These inventory
counts are not the required candidate history sweeps; both candidate sweeps and
signed zero-row inventory remain G2/rollout obligations.

The previous deployment had no common bundle. The probe records SHA-256 for all
nine existing packaged schemas, preserving the previous coherent contract set
as the rollback baseline. Candidate generation must retain one common digest
across the root snapshot, installed package and JavaScript copy.

The initial Docker socket denial was resolved using approved direct Docker
commands. The first sync could not mutate the image's root-owned `/opt/venv`;
the restored containers use writable task-specific virtual environments under
`/tmp`, without changing the host cache or package permissions.

## Readiness refresh after initial G1

The clean Neuron sync completed successfully (185 installed packages). The
[Neuron readiness probe](artifacts/runtime/neuron-readiness.json) now records
Python 3.14.4, Docling 2.142.0, Pillow 13.0.0 and the current common contract
dependencies. This removes the earlier restriction on Neuron validation; actual
caller regressions remain required at G2. No inference or PDF conversion was used
by installation or the readiness probe.

During additional packaging-tool resolution, Docker Desktop's internal resolver
failed public lookups. Host resolution and a direct alternate-resolver probe
isolated the problem. DNS was restored only in the two task containers, retaining
the observed PostgreSQL hostname mapping and all existing virtual environments.
The exact previously failed lock command then succeeded without code changes.
[DNS restoration](artifacts/runtime/dns-restoration.json) records that triage.
The offline installation build tools are now pinned and installed:
setuptools 84.1.0 and wheel 0.48.0. Service application processes remain nonroot.
