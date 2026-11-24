# Knowledge-Graph Reconciliation — F0011-json-schema-contract-system run 2026-11-22-885e8734

## Scope

- Feature ID: F0011
- Run ID: 2026-11-22-885e8734
- Date: 2026-11-23
- Reconciled by: Claude (Opus 5.5) / Architect (feature-action)

Result: PASS

## Binding Delta

Baseline: none declared. `feature-assembly-plan.md` has no "Knowledge-Graph Binding Plan"
section. The planning run bound only ADR-0079 and the authored planning schemas to the two
F0011 capabilities (`bindings/f0011-planning.yaml`), and both capability nodes stated that no
implementation binding was claimed.

All 114 new source files are untracked until the feature commit, and wildcard bindings resolve
only against git-tracked files. So they are bound by literal path, following the F0008
precedent. Every untracked non-evidence file is bound exactly once (checked by script; zero unbound).

| Capability / node | code-index binding | G0-declared? | Action |
|-------------------|--------------------|--------------|--------|
| capability:offline-contract-bundle | backend: `brain_contracts/{schema_runtime,model_adapter}.py`, `brain_contracts/generated/*`, `brain_api/contract_openapi.py` | no (planning paths only) | added |
| capability:offline-contract-bundle | resources: 25 `brain_contracts/resources/v1/*` + 25 `schemas/contracts/v1/*` snapshot files | no | added |
| capability:offline-contract-bundle | validation: `scripts/contracts/{generate.py,sources.yaml,profile.yaml,install_smoke.py,installed_probe.py,run_installed_probe.py}` | no | added |
| capability:offline-contract-bundle | infra: `docker/contracts/{Dockerfile,README.md}`, `.dockerignore` | no | added |
| capability:offline-contract-bundle | tests: bundle runtime, generated models, OpenAPI, reproducibility, Neuron shared-bundle | no | added |
| capability:cross-language-contract-validation | backend: `brain_api/contract_guards.py` | no | added |
| capability:cross-language-contract-validation | frontend: `experience/scripts/contracts/*.mjs`, 25 `experience/src/generated/contracts/v1/*` | no | added |
| capability:cross-language-contract-validation | validation: checker, case data/inventories, native probe, stored-history sweep, environments | no | added |
| capability:cross-language-contract-validation | tests: native compatibility, PostgreSQL consumer contracts, case data, stored-history sweep | no | added |
| existing consumers (FactSlot answers/resolution, temporal commit, content contracts, assertions, API facts/errors/app) | existing bindings | n/a | confirmed-existing-coverage (modified files stay on their current capability records) |

## Canonical Nodes

None introduced; F0011 reuses the two capability nodes created at planning
(`capability:offline-contract-bundle`, `capability:cross-language-contract-validation`).
Their `notes` were updated from "planning design only; no implementation binding claimed" to
the as-built state (feature run 2026-11-22-885e8734, G4 approved 2026-11-23; ADR-0079 still
Proposed). No new `WHY` rationale; the existing ADR-0079 Decision rationale stands.

## Validator Results

| Check | Command | Result |
|-------|---------|--------|
| shard validation | `shard_validate.py bindings/f0011-planning.yaml nodes/capabilities/{offline-contract-bundle,cross-language-contract-validation}.yaml` | PASS |
| compile | `compile.py` | PASS (one pre-existing F0006 `binding-overlap` warning on `interpretation-result-v2.schema.json`, not F0011) |
| symbol + decision regen + check | `validate.py --regenerate-symbols --check-symbols --regenerate-decisions --check-decisions` | PASS (exit 0) |
| drift | `validate.py --check-drift` | PASS (exit 0) |
| symbol freshness | `lookup.py --defines ContractBundle` / `--defines _checked_result` | 1 match each (were 0 at G3 review) |

`coverage-report.yaml` was **not** regenerated at this gate. That is deferred to `G8`, after the
archive move relocates the feature-doc paths.

## Handoff to Closeout

The semantic graph is green and ready for PM closeout to verify, not re-author. After the
feature commit, the literal per-file bindings can be collapsed to directory globs in a
follow-up KG hygiene pass. That is optional and changes no coverage.
