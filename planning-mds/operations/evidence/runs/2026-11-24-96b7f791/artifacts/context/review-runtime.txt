# Contract validation runtimes

F0011 uses the engine, Neuron and Node targets in `Dockerfile` for contract proof.
These images are build/test tools. They do not add an application deployment.

The build pins Python 3.14.4, uv 0.11.31 and Node 22.23.1. The workspace lockfiles
pin all dependencies, including the build-only model generator. Generation uses
the engine target so its tool versions match the release manifest.

From the repository root:

```sh
docker build -f docker/contracts/Dockerfile --target engine-validation -t brain-contracts-engine:local .
docker build -f docker/contracts/Dockerfile --target node-validation -t brain-contracts-node:local .
docker build -f docker/contracts/Dockerfile --target neuron-validation -t brain-contracts-neuron:local .
docker run --rm brain-contracts-engine:local
docker run --rm brain-contracts-node:local
docker run --rm brain-contracts-neuron:local
```

The default commands check generated-artifact freshness, run the JavaScript
decoder tests, and smoke the unchanged Neuron readers, respectively. CI also
joins the three consumers' case results and runs installation, corruption and
PostgreSQL integration proofs. See `.github/workflows/ci-gates.yml`.

For an existing local environment, run the complete read-only stored-history
preflight before enabling candidate response guards. `scripts/contracts/environments.json`
names the actual local dev and shared integration databases; connection credentials
continue to come from the existing application Settings. Zero rows require the
signed QE/DevOps inventory accepted by `check_stored_fact_versions.py`.

Rollback restores the previous coherent contract package set and generated
snapshot. It never rewrites historical values or reinterprets persisted content.
F0011 adds no database migration. An old local clone must first apply the already
shipped migrations through 0015 using the normal migration procedure and a backup.
