# Test Execution Report — F0011 run 2026-11-22-885e8734

Owner/reviewer: Codex / Quality Engineer; final refresh Claude / Quality Engineer
Date: 2026-11-23

## Commands Executed

Exact commands, working directories and exits are in commands.log. Runtime
commands use the run-local Compose file and the locked Engine/Neuron/Node
environments. The final execution lanes are:

- Engine: `uv run --no-sync --project engine --group contract-build python .../run_unit_regressions.py -c engine/pyproject.toml engine/packages engine/apps/api/tests scripts/contracts/tests -q --cov ...` — exit0.
- PostgreSQL: `.../run_consumer_tests.py` executes the selected F0011/F0007/F0008 actual consumer integration suites — exit0.
- Conformance: `python scripts/contracts/check.py --cases scripts/contracts/cases.json --ajv-results .../ajv-review-final.json --output .../conformance-review-final.json` — exit0, under coverage.
- Reproducibility: `python scripts/contracts/generate.py --check` — exit0, 86 exact artifacts.
- Neuron: `pytest -c neuron/pyproject.toml neuron/tests/integration/test_f0011_shared_bundle.py` — exit0.
- Node: `pnpm --dir experience contracts:test` and `contracts:check` — exit0.
- Existing frontend: frozen install, lint, Vitest and build — exit0.
- Installed wheel/sdist: isolated installation/probe commands in DevOps evidence — exit0.
- Canonical Node image (after the pnpm-selection Dockerfile correction): `docker run --rm --network none brain-f0011-contract-node:2026-11-22-885e8734` — exit0, 19/19 (`artifacts/runtime/canonical-node-tests.txt`); `contracts:check` in the same image — 443 cases, 0 failed, joined by the clean Engine image into 1329 results with 0 mismatches (`artifacts/test-results/canonical-node-conformance.json`).
- Static checks: full Engine Ruff/format and CI mypy108 files — exit0; `artifacts/test-results/static-checks.json`.

## Pass/Fail Counts

| Lane | Total | Pass | Fail | Skip | Retries |
|---|---:|---:|---:|---:|---:|
| Engine/package/API/tool unit regressions | 1239 | 1239 | 0 | 0 | 0 |
| Actual PostgreSQL consumer integration | 83 | 83 | 0 | 0 | 0 |
| Full Neuron suite on SoupSieve 4.1.3 (G4 follow-up) | 313 | 265 | 0 | 48 | 0 |
| Neuron existing shared-bundle callers | 8 | 8 | 0 | 0 | 0 |
| Headless Node contract tests | 19 | 19 | 0 | 0 | 0 |
| Existing frontend Vitest regressions | 12 | 12 | 0 | 0 | 0 |
| Shared conformance results (443 cases × 3 consumers) | 1329 | 1329 | 0 | 0 | 0 |

These are distinct lanes, not a claim that every result represents a unique
business scenario. Native baseline/candidate each matched seven cases exactly.
Each actual environment sweep selected and checked all zero existing versions,
with explicit QE/DevOps zero-row signatures. Nonempty history, closed versions,
legacy pilots and remainders were separately exercised in owned PostgreSQL
fixtures; the empty production-like inventory is not presented as that proof.

## Skipped Tests And Rationale

Full Neuron suite (G4 follow-up only): 48 skips are pre-existing environment
opt-ins, none HTML/selector-related: 26 live F0005 qualification, 12 PostgreSQL URL
opt-ins, 4 user/network namespaces, 2 systemd scope, 2 vLLM endpoint, 1 live
Graph/vLLM, 1 uncached tokenizer. The F0011 lanes below remain zero-skip.

No selected test skipped. The final Engine runner enabled the five existing
optional PostgreSQL job tests using the already-configured integration connection;
they each create/drop their own random schema, without modifying public history.

Browser E2E, screenshot, theme and accessibility lanes are outside this headless
tooling change: no screen or interaction changes. QE owns this disposition; no
later UI work is needed for F0011. Existing frontend regressions still passed.
Live inference, model evaluation and PDF reparse are outside the approved scope;
Neuron caller regressions execute without a model call. No new latency SLO or
load-bearing endpoint is introduced; correctness/resource bounds are tested.

## Raw Test Artifact Paths

- `artifacts/test-results/python-unit-final.xml`
- `artifacts/test-results/python-unit-closeout.xml` (final, after G4 Low fixes)
- `artifacts/test-results/consumer-integration-closeout.xml` (final, after G4 Low fixes)
- `artifacts/test-results/neuron-full-soupsieve4.xml`
- `artifacts/test-results/consumer-integration-ci.xml`
- `artifacts/test-results/consumer-integration-ci.txt`
- `artifacts/test-results/neuron-shared-bundle.xml`
- `artifacts/test-results/js-review-unit-final.tap`
- `artifacts/test-results/frontend-test.txt`
- `artifacts/test-results/frontend-lint.txt`
- `artifacts/test-results/frontend-build.txt`
- `artifacts/test-results/frontend-frozen-install.txt`
- `artifacts/test-results/conformance-review-final.json`
- `artifacts/test-results/ajv-review-final.json`
- `artifacts/test-results/generation-final.txt`
- `artifacts/test-results/expected-mutation.xml`
- `artifacts/test-results/native-differential-ci-comparison.txt`
- `artifacts/test-results/stored-versions-integration-cutover-ci.json`
- `artifacts/test-results/stored-versions-dev-cutover-ci.json`
- `artifacts/install-final/installed-distribution-results.json`
- `artifacts/runtime/canonical-node-tests.txt`
- `artifacts/test-results/canonical-node-cases.json`
- `artifacts/test-results/canonical-node-conformance.json`

## Failed / Retried Command History

Historical failed attempts remain under artifacts and in commands.log:

- Generator format projection initially exposed datamodel class naming collisions
  for dotted JSON property names; deterministic class titles fixed naming while
  aliases preserved the wire. All declared cases then passed before publication.
- Generated files initially inherited restrictive staging permissions; publication
  now makes readable0644 output and restores previous bytes/modes on failure.
  Both rollback and nonroot-reader checks pass.
- Initial full unit run had one route-parity test failure after FastAPI lazy
  routing and five unconfigured optional job skips. The parity test now enumerates
  actual effective route contexts and asserts a nonempty route set; the final
  full1148 run has neither failure nor skip.
- Native environment probing found optional date-time checker differences.
  Delegated legacy resources now retain the observed pre-change UUID/date policy;
  newly adopted carriers use the four explicit formats. Exact old/candidate
  native results match, without changing portable expectations.
- Installed probes initially selected an inactive Pydantic lock candidate and a
  source-valid fixture missing old DTO-required nullable fields. Active marker/
  actual installed version checks and explicit native-producer fixtures corrected
  those proof defects; portable cases and native reader behavior were preserved.
- Initial CI lint/format/type checks identified generated-format policy and six
  typing issues. The exact generated path now uses its pinned generator format;
  authored files are formatted and type annotations/stub boundaries are explicit.
  Full CI lint/format/type checks and runtime regressions pass after correction.
- DNS/credential-helper/runtime installation failures were restored within the
  run's containers/client configuration, then the unchanged affected commands
  reran. See baseline-restoration/dns-restoration and DevOps evidence; no runtime
  preflight failure remains unresolved.

These are diagnosed/fixed attempts, not automatic retries masking flaky tests.
The two final Engine warnings are existing anyio deprecation and a deliberately
short synthetic HMAC test key.

## AC Coverage Result

`artifacts/test-results/ac-evidence.md` maps all41 feature-local criteria to
observed tests and raw artifacts. Structural results do not prove source ownership,
currency support, normalization, evidence admissibility or authorization; their
actual domain/transaction boundaries have separate test references.

PR-L3's injected read-invariant failure is observed and recorded. G3 Security must
explicitly accept the bounded audit meaning or require a redesign. This is a
future required review gate, not a QE waiver or an accepted security finding.
Independent review, implementation approval, signoff and closeout remain pending.

## Result

Result: PASS

G4 follow-up (2026-11-23): after the user chose to fix all three Lows, the Engine
unit lane (1239), the PostgreSQL consumer lane (83), Engine Ruff/format/mypy (108 files),
the full Neuron suite and the canonical image lanes were re-run on current source and pass.

All lanes pass on current source with no selected skips. The canonical
Node image, previously blocked by package-manager selection, now builds and
passes its 19 tests and all 443 cases offline. Coverage is in `coverage-report.md`
(Python changed statements 86.0%, JavaScript lines 98.5%). This is the QE G2 verdict
only: independent review, approval, signoff and closeout remain with their owners.
