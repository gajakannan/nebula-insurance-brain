# Deployability Check — F0012-foundation-ontology run 2026-11-26-54387a08

Reviewer: Claude (Opus 5.5) / DevOps. Date: 2026-11-26. Verdict: PASS.
Product root: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain.

Result: PASS

## Runtime / Deployment Config Changes

- **New workspace package `engine/packages/brain-ontology`.** It is registered in `engine/pyproject.toml` and depends on `brain-contracts`, `brain-domain`, `brain-security`, `brain-persistence`, PyYAML and jsonschema. The `engine/uv.lock` delta only adds the workspace member (37 insertions, no third-party pin changed). Nothing in the engine depends on `brain-ontology`, so the dependency graph has no cycle. `uv lock --check --project neuron` passes; the neuron lock is unchanged.
- **Migration 0017** (`engine/migrations/versions/0017_f0012_ontology_releases.py`), after 0016:
  - Adds eight append-only tables, 17 triggers and two functions.
  - Widens `resource_access.ck_resource_access_type` to admit `ontology_release`. Existing rows are revalidated, not rewritten.
  - Downgrade refuses, under ACCESS EXCLUSIVE locks, while any ontology row or `ontology_release` access row exists. An empty downgrade restores the original CHECK.
  - Proven on `brain_f0012` with up/down/up ([alembic-0017-roundtrip.txt](artifacts/runtime/alembic-0017-roundtrip.txt)), and on a populated F0007–F0009 database with unchanged checksums of every existing table ([migration-0017-checksums.json](artifacts/test-results/migration-0017-checksums.json)).
- **Policy.** Six `ontology_release` rows are added to `planning-mds/security/policies/policy.csv`, mirrored in `kg-source/policies` (drift check passes). No existing row changed. Activation goes through the existing policy-release activation path.
- **Operational prerequisite.** Each KB that will install ontology releases needs a trusted `resource_access` row for `ResourceKey(ontology_release, <kb_id>)` with explicit classifications, provisioned through the existing `brain_persistence.tenancy.provision_resource_access`. Without it, every ontology command fails closed (`missing_attributes`). This is documented in GETTING-STARTED.md.
- **CLI.** `python -m brain_ontology.cli` runs from the engine environment. It reads the API's existing environment variables (`BRAIN_DATABASE_URL`, `BRAIN_OIDC_ISSUER`, `BRAIN_CASBIN_MODEL_PATH`/`BRAIN_CASBIN_POLICY_PATH`, `BRAIN_IDENTITY_PROFILE_PATH`). There is no new container, port, environment variable, credential or secret. The bearer token is read from a file and never echoed.
- **Committed artifacts.** `ontology/modules/foundation/**` (sources) and `ontology/releases/foundation/1/**` (compiled lock: manifest, normalized, projection mapping, Turtle, JSON-LD).
- **CI (`.github/workflows/ci-gates.yml`):**
  - `brain-ontology/src` joins the mypy set.
  - New step: `compile --check` of the foundation lock (byte-identical recompile).
  - New gate: `brain_ontology` coverage ≥ 80% (unit; measured 87%).
  - The four F0012 PostgreSQL suites join the persistence coverage step: install, activation, temporal kinds, migration.
  - New step: `build_foundation_examples.py --check` in product-gates.
  - `validate_semantic_rdf.py --require` now also checks the foundation release and fixtures.

## Executed Checks

| Check | Result | Evidence |
|---|---|---|
| Runtime preflight | PASS | [g1-runtime-preflight.md](g1-runtime-preflight.md) |
| `uv sync --locked` after relock | PASS | [uv-lock-engine.txt](artifacts/runtime/uv-lock-engine.txt) |
| Migration 0017 up/down/up and populated preservation | PASS | as above |
| Refused downgrade after install | PASS | `test_downgrade_refused_after_install` |
| API startup with the release-backed registry (uvicorn, `GET /openapi.json` 200, 7 paths) | PASS | [http-preflight.json](artifacts/security/dast/http-preflight.json) |
| `compile --check` | PASS | [cli-compile-check.txt](artifacts/test-results/cli-compile-check.txt) |
| Contract bundle `generate.py --check`; install smoke | PASS | [contracts-generate-check.txt](artifacts/test-results/contracts-generate-check.txt), [install-smoke.txt](artifacts/test-results/install-smoke.txt) |
| SQLite `create_all` with the neuron recovery exclusions (ontology `ARRAY` columns use their JSON variant) | PASS, 8 ontology tables | [sqlite-create-all-probe.txt](artifacts/test-results/sqlite-create-all-probe.txt) |
| Host runtime-stack restore lane | PASS, 13/13 | [g2-restore-suites.txt](artifacts/test-results/g2-restore-suites.txt) |

## Rollback

Before any release is installed, `alembic downgrade 0016` is safe and restores the original access CHECK. After installation, roll forward. The refusal is deliberate, so released definitions are never lost.
