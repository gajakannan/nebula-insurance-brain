# Test Execution Report — F0009 run 2026-11-24-08701e37

Owner/reviewer: Claude (Opus 5.5) / Quality Engineer
Date: 2026-11-24

Result: PASS

## Commands executed

[commands.log](commands.log) records every command with its exact working directory and exit code. Runtime commands run in the [run-local compose](artifacts/runtime/compose.yaml) validation containers. The host lane mirrors CI's runtime-stack job, which uses the Docker CLI.

- **Engine (final):** `uv run --no-sync --project engine python -m pytest -c engine/pyproject.toml engine -q -rfEs --junitxml=… --cov=…`. Output in [g2-engine-full.txt](artifacts/test-results/g2-engine-full.txt) and [junit](artifacts/test-results/g2-engine-full.junit.xml).
- **Host restore lane:** `engine/.venv/bin/python -m pytest … test_content_restore_v2.py test_job_event_reason_migration.py`. Output in [g2-restore-suites.txt](artifacts/test-results/g2-restore-suites.txt).
- **Conformance:**
  - `node scripts/contracts/check.mjs --output …/ajv-results.json` ([ajv-results.json](artifacts/test-results/ajv-results.json));
  - `python scripts/contracts/check.py --ajv-results …` ([conformance.json](artifacts/test-results/conformance.json)).
- **Contract reproducibility:**
  - `python scripts/contracts/generate.py --check` ([g2-contracts-generate-check.txt](artifacts/test-results/g2-contracts-generate-check.txt));
  - `pytest scripts/contracts/tests` ([g2-contract-tool-tests.txt](artifacts/test-results/g2-contract-tool-tests.txt));
  - `node --test scripts/contracts/runtime.test.mjs` (in [g2-ajv-run.txt](artifacts/test-results/g2-ajv-run.txt)).
- **Neuron shared bundle:** `pytest -c neuron/pyproject.toml neuron/tests/integration/test_f0011_shared_bundle.py`, offline, in the cached Neuron image ([g2-neuron-shared-bundle.txt](artifacts/test-results/g2-neuron-shared-bundle.txt)).
- **Installed package:** wheels for brain-domain, brain-contracts, brain-security and brain-provenance, installed into a fresh venv and run from `/tmp` with `python -I` ([install/smoke.log](artifacts/install/smoke.log)).
- **Static checks:** `ruff check .`, `ruff format --check .`, and the CI mypy package list plus `packages/brain-provenance/src`. All clean ([g2-ruff-check.txt](artifacts/test-results/g2-ruff-check.txt); final reruns in commands.log).

## Pass/fail counts

| Lane | Total | Pass | Fail | Skip |
|---|---:|---:|---:|---:|
| Engine, all packages + API + PostgreSQL integration (container) | 1732 | 1729 | 3* | 0 |
| — of which F0009 tests | 75 | 75 | 0 | 0 |
| Host restore lane (the 3 container-only failures plus their files) | 13 | 13 | 0 | 0 |
| Conformance results (464 cases × JSON Schema / Pydantic / AJV) | 1392 | 1392 | 0 | 0 |
| Contract tooling tests | 21 | 21 | 0 | 0 |
| Node contract runtime tests | 19 | 19 | 0 | 0 |
| Neuron shared-bundle callers | 8 | 8 | 0 | 0 |
| Installed-package smoke | 1 | 1 | 0 | 0 |

\* The 3 container failures are `test_content_restore_v2.py` ×2 and `test_job_event_reason_migration.py::test_backup_and_isolated_restore…`. `scripts/ops/backup.sh` calls the Docker CLI, which the validation container does not have (exit 127). They failed identically in the pre-change [baseline](artifacts/test-results/g1-baseline-engine.txt). Run in the host lane, which matches CI runtime-stack, all 13 tests in those files pass. That proves a full dump and isolated restore still work with the migration 0016 triggers present, because pg_restore creates triggers after the data load.

F0009 tests by file: corrections 14, review service 10, migration 10, provenance 9, API compatibility 3, temporal lineage 7, domain 9, facade prepare_reads 7, reader 6.

## Frontend (feature-level notes)

`frontend_in_scope=true` because F0009 regenerates the shared contract copies under `experience/src/generated/contracts/v1/` (manifest, OpenAPI, UI metadata and five new schema files). No component, screen, route or style changed. The feature-level frontend proof:

- headless AJV validates all 464 shared cases with 0 failures, including the 21 F0009 cases;
- the Node contract runtime tests pass 19/19;
- the existing frontend regression `pnpm lint && pnpm test && pnpm build` passes: ESLint clean, Vitest 3 files / 12 tests, `tsc -b` and `vite build` succeed ([g2-frontend-regression.txt](artifacts/test-results/g2-frontend-regression.txt)).

The UX audit and theme checks are not applicable, because nothing renders differently.

## EX-PROV reproduction (S0006 AC5)

| Example | Test | Expected (QE stored-basis SQL) vs actual |
|---|---|---|
| EX-PROV-001 | test_ex_prov_001_exact_source_chain_is_complete | edge sets equal; COMPLETE; stored semantics, content record and run metadata equal the database rows |
| EX-PROV-002 | test_ex_prov_002_correction_lineage_and_reservation | corrected_from, created_assertion, reviews and reserved_learning edges equal; no fact version |
| EX-PROV-003 | test_ex_prov_003_remainder_names_its_predecessor_and_changes | `expected_version_edges` equals actual; split change `('split', V1, R)` |
| EX-PROV-004 | test_ex_prov_004_one_denied_source_refuses_the_whole_history | V2 and V1 refused; remainder readable with no trace of the denied source; no leak in logs or exceptions |
| EX-PROV-005 | corrections::test_effective_correction…, test_replay…, test_reservation_failure… | one reservation per effective correction; replay reuses it; an injected failure leaves zero rows |

Each example also has negative or rollback coverage, with durable audit rows queried from a fresh session.

## Defects found and fixed during G2

- **The plan's schema could not represent a creation change.** `fact_change.from_version_id` was a required string, but the shipped commit writes NULL for a slot's first version. Architect change: it is now nullable, and no `changed_from` edge is emitted for a creation change.
- **The plan's DDL referenced the wrong audit key.** It pointed `review_submission_attempt.authorization_decision_id` at `audit_event(id)`. Audit rows carry a fresh id, and the decision id lives in `audit_event.decision_id`. The guard now requires a matching allowed `review_task:annotate` audit row by `decision_id`.
- **A composite key was missing.** `review_decision` had no `(id, tenant_id, knowledge_base_id)` key; migration 0016 adds `uq_review_decision_owner`.
- **The reader's closure was inconsistent.** A version's recorded decision did not include its assertion ancestry's review history; this is fixed.
- **One F0008 regression test needed rescoping.** It snapshotted grants across 0014 up/down/up against `head`. It is now pinned to F0008's own head, 0015, because 0016 adds tables by design.

## Residual limits

- **The plan's "unregistered legacy evidence ids" boundary is kept, not extended.** Legacy pilot versions whose stored evidence ids name no registered row are labelled `LEGACY_UNQUALIFIED`. The same condition on a modern temporal-v1 version is refused as non-disclosing not-found.
- **No derivation reference is stored anywhere in v0.1.** The reader therefore emits no `derivation_reference` record; a DERIVED assertion yields the `DERIVATION_UNAVAILABLE` gap, per the plan.
