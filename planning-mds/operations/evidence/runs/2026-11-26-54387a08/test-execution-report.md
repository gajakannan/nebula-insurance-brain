# F0012 Test Execution Report — Foundation ontology

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-26
- Run: `2026-11-26-54387a08`
- Verdict: PASS

Result: PASS

[commands.log](commands.log) records every command with its working directory and exit code. Runtime commands run in the [run-local compose](artifacts/runtime/compose.yaml) validation containers against the dedicated `brain_f0012` database. Integration suites create and drop their own owned databases. Plan: [test-plan.md](test-plan.md).

## Results

| Suite | Result | Artifact |
|---|---|---|
| `brain-ontology` unit (authoring, compiler, semantics/impact, CLI) | 83 passed | [g2-full-engine.txt](artifacts/test-results/g2-full-engine.txt) |
| `test_ontology_release_install.py` (PostgreSQL) | 25 passed | same |
| `test_temporal_kind_activation.py` (PostgreSQL, real `POST/GET /facts` route) | 9 passed | same |
| `test_ontology_activation.py` (PostgreSQL) | 10 passed | same |
| `test_ontology_migration.py`: 0017 on F0007–F0009 data, checksums | 1 passed | [migration-0017-checksums.json](artifacts/test-results/migration-0017-checksums.json) |
| Full engine suite (`pytest -c engine/pyproject.toml engine`) | 1883 passed, 3 failed\* | [g2-full-engine.txt](artifacts/test-results/g2-full-engine.txt) |
| Host restore lane (the 3 container failures) | 13 passed | [g2-restore-suites.txt](artifacts/test-results/g2-restore-suites.txt) |
| Contract unit, OpenAPI and `scripts/contracts` tests | 590 passed | [contracts-unit.txt](artifacts/test-results/contracts-unit.txt) |
| F0011 conformance (jsonschema + Pydantic + AJV) | 490 cases, 1470 results, 0 mismatches; 26 source conditionals, 95 branch witnesses | [conformance.json](artifacts/test-results/conformance.json) |
| `generate.py --check` | pass, 110 artifacts, digest `8b3721e9…` | [contracts-generate-check.txt](artifacts/test-results/contracts-generate-check.txt) |
| Install smoke (brain-domain, brain-contracts, brain-content wheels) | pass | [install-smoke.txt](artifacts/test-results/install-smoke.txt) |
| `validate_semantic_examples.py` | pass | [semantic-examples.txt](artifacts/test-results/semantic-examples.txt) |
| `validate_semantic_rdf.py --require` (rdflib 7.1.4, pySHACL 0.30.1, owlrl 7.1.4) | pass | [semantic-rdf-require.txt](artifacts/test-results/semantic-rdf-require.txt) |
| `brain_ontology.cli compile --check` (foundation@1) | exit 0 | [cli-compile-check.txt](artifacts/test-results/cli-compile-check.txt) |
| ruff check, ruff format --check, mypy (CI package list plus `brain-ontology`) | clean | commands.log |

\* The 3 failures are `test_content_restore_v2.py` ×2 and `test_job_event_reason_migration.py::test_backup_and_isolated_restore…`. The validation image lacks `pg_dump`/`pg_restore`/Docker CLI. They failed identically in the pre-change [baseline](artifacts/test-results/g1-baseline-engine.txt) (1729 passed). In the host lane, which matches CI runtime-stack, all 13 tests in those files pass with migration 0017 at head. The suite grew by 154 tests, and no previously passing test fails.

## Frontend (feature-level notes)

`frontend_in_scope=true` because F0012 regenerates the shared contract copies under `experience/src/generated/contracts/v1/`:

- the manifest, OpenAPI and UI metadata;
- the three new ontology schemas;
- the widened `fact-version-read-v1`.

No component, screen, route or style changed. The feature-level frontend proof:

- AJV conformance over those copies passes: 490 cases, 0 failures ([ajv-results.json](artifacts/test-results/ajv-results.json));
- the frontend regression `pnpm lint && pnpm test && pnpm build` passes: ESLint clean, Vitest 3 files / 12 tests, `tsc -b` and `vite build` succeed ([g2-frontend-regression.txt](artifacts/test-results/g2-frontend-regression.txt)).

## ADR-0045 case log (S0007 AC1)

Each F0012-owned case, with its command and observed outcome. The test commands are in commands.log (exit 0) and their output is in the artifacts above.

| Case | Command / test | Input | Observed output | Exit |
|---|---|---|---|---|
| Identity and locks: deterministic compile | `python -m brain_ontology.cli compile --check ontology/releases/foundation/1/release.yaml` | committed foundation module and lock | `pass`, `ontrel:sha256-3602b71f…` | 0 |
| Identity and locks: order-independence, fresh checkout | `test_ac1_fresh_checkout_and_shuffled_source` | reversed terms, constraints, projection and keys, compiled in a new root | byte-identical files | 0 |
| Identity and locks: refusals | `test_s0002_ac2_identity_reuse_rejected`, `test_s0002_ac5_removal_needs_retirement`, `test_identity_reuse_refused_at_install`, `test_same_module_version_with_new_content_refused`, `test_installed_rows_are_immutable` | redefined IRI; dropped term; relabelled module@1; UPDATE/DELETE/TRUNCATE | `IDENTITY_REUSE_REJECTED`, `TERM_REMOVED_WITHOUT_RETIREMENT`, `MODULE_VERSION_IMMUTABLE`, `check_violation` | 0 |
| Authoring refusal (CLI) | `python -m brain_ontology.cli validate …/fixtures/bad-module.yaml` | [bad-module.yaml](artifacts/test-results/fixtures/bad-module.yaml) | 8 ordered errors incl. `AUTHORING_FIELD_RETIRED`, `UNSUPPORTED_CONSTRUCT`, `DEPENDENCY_UNRESOLVED` ([output](artifacts/test-results/cli-validate-bad.txt)) | 1 |
| Inference change (EX-ONT-003) | `test_ex_ont_003_and_004_reported` | foundation@2 adds `ownership-interest subClassOf agreement` | change `additive`; inference `changes_detected`, added `ownership-interest subClassOf agreement` | 0 |
| Constraint change (EX-ONT-004) | `test_ex_ont_003_and_004_reported` | foundation@3 adds a `minCardinality 1` status constraint at canonical-admission | closure `no_change_within_scope`; constraint `added` for the F0017/F0018 consumer; `constraint_tightening` on `foundation.account` | 0 |
| Split and rollback | `test_split_scenario_end_to_end` | foundation@2 splits `operates-at` into premises/office, with a split record | split classes; reach `fnd:operatesAt@v1` slots 1/1, assertions 0/0; existing slot keeps @1; rollback appends sequence 3; both releases remain | 0 |
| Scope (two tenants) | `test_scope_across_two_tenants`, `test_ac2_registry_serves_installed_releases_of_the_scope_only` | foundation@1 in KB A and KB C (another tenant) | separate rows; C's reach excludes A's slot; A's history empty after C's activation; a release installed only in B is unregistered in A | 0 |
| Missing-limit case | — | — | Owned by F0013/F0065, not run here | — |

## Behaviour notes

- **Atomicity:** an injected failure after every release row was written leaves zero rows, and the install decision is audited `failed`.
- **Concurrency:** two concurrent installs give one `installed` and one `already_installed`. Two concurrent activations give one selection and one `SELECTION_CONFLICT`. The selection guard trigger refuses an out-of-sequence or never-activated rollback inserted by direct SQL.
- **Temporal kinds** (S0005 AC4), through the real route on PostgreSQL:
  - ETERNAL stores `(,)` with NULL bound columns, and `GET /facts/{id}` returns `valid_start: null`.
  - Bounded or UNKNOWN shapes are refused with `kind_shape_mismatch`, a different value with `eternal_conflict`, and the same value is accepted.
  - EVENT accepts exactly one day; an open or two-day span is refused.
  - STATE is unchanged.
- **No parse or model calls** (S0007 AC5): no command or package in the change imports Docling, a model client or the worker. Install leaves `content_artifact`, `assertion`, `fact_slot`, `canonical_fact_version` and `canonical_commit` counts unchanged (`test_install_writes_one_immutable_release`).
- **Timing** (S0004/S0006 NFR, measured not budgeted): the 45 PostgreSQL F0012 tests, including database creation and migration per test, ran in about 40 s. The foundation compile takes under 1 s.

## Open items

None blocking. The SAST false-positive triage and the scan verdicts belong to Security (G3).
