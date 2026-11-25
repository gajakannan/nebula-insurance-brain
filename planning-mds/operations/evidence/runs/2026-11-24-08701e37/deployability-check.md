# Deployability Check — F0009-provenance-and-human-correction-lineage run 2026-11-24-08701e37

Reviewer: Claude (Opus 5.5) / DevOps. Date: 2026-11-24. Verdict: PASS.
Product root: /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain.

Result: PASS

## Runtime / Deployment Config Changes

- **New workspace package `engine/packages/brain-provenance`.** It is registered in `engine/pyproject.toml`, and is a dependency of `brain-api` and `brain-persistence`. `brain-persistence` also declares its existing transitive `brain-contracts` dependency explicitly. The `engine/uv.lock` delta only adds the workspace member; no third-party pin changed.
- **CI (`.github/workflows/ci-gates.yml`).**
  - `brain-provenance/src` is added to the mypy set.
  - A per-package coverage gate for `brain_provenance` is added.
  - A runtime-stack step runs the four F0009 PostgreSQL suites with owned databases.
- **No new service or env var.** There is no new container, environment variable, credential, secret, port or Casbin policy change. The existing settings and identity profile are unchanged.
- **Contract bundle.** The shared contract bundle went from 86 to 101 generated artifacts, at digest `17189a61…`. The root snapshot, installed package resources and `experience` copies all carry the same digest, and generation is reproducible (`generate.py --check`).

## Migrations / Rollback

Migration `0016_f0009_provenance_hooks` (after 0015) is additive. It adds the nullable `review_decision.correction_lineage_contract` marker with a CHECK, `uq_review_decision_owner`, two append-only tables, seven indexes, SECURITY INVOKER guard functions, and append-only protection on `review_decision`. It also adds a deferred "correction requires reservation" constraint trigger.

- **Upgrade procedure:**
  1. Quiesce review writers.
  2. Run `alembic upgrade 0016`. It holds SHARE ROW EXCLUSIVE on `review_item` and `review_decision` during the install, and asserts that no historical decision was stamped.
  3. Deploy the new application, then resume writers.

  Old application writers must not resume against 0016. A CORRECT written without a reservation is refused at commit, by design.
- **Downgrade:** quiesce writers, then run `alembic downgrade 0015`. It takes ACCESS EXCLUSIVE locks in fixed order and refuses before any drop when either new table has a row. After real lineage rows exist, roll forward or redeploy a compatible reader instead. There is no CASCADE or truncation path.
- **Proof:**
  - [test_f0009_migration.py](artifacts/test-results/g2-engine-full.txt) on owned PostgreSQL 18 covers empty down/up byte-identity, populated refusal, and legacy rows byte-identical with the marker NULL.
  - The dev `brain_f0009` database upgraded 0015 → 0016 cleanly ([g2-migrate-0016-up.txt](artifacts/test-results/g2-migrate-0016-up.txt)).
- **Backup/restore:** the full `scripts/ops/backup.sh` and isolated restore suites pass in the host lane (13/13). pg_restore creates triggers in post-data, so restored history is not re-stamped. A data-only restore into an existing 0016 schema must use `--disable-triggers`, like the other append-only tables.

## Container / Build Smoke

- The engine validation image (`brain-f0011-contract-engine`, Python 3.14.4, uv 0.11.31) passes the full suite, ruff, format and the CI mypy set.
- The node image (Node 22.23.1, pnpm 12.21.0) passes the frozen install, AJV conformance and runtime tests.
- The Neuron image (offline) passes the shared-bundle callers.
- The candidate API (`uvicorn brain_api.app:app`) starts against `brain_f0009` and serves the unchanged 7-path OpenAPI ([http-preflight.json](artifacts/security/dast/http-preflight.json)).
- Wheels for brain-domain, brain-contracts, brain-security and brain-provenance install into a fresh venv and run from outside the checkout ([install/smoke.log](artifacts/install/smoke.log)).

## Environment Contract

Unchanged. Tests and runtime use the existing `BRAIN_DATABASE_URL`, `BRAIN_WORKER_DATABASE_URL`, `BRAIN_MIGRATION_ADMIN_URL` and `BRAIN_TEST_POSTGRES_URL` names. No new variable is introduced.
