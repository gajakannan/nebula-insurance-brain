# F0011 — Getting started

## Current implementation state

Feature run `2026-11-22-885e8734` is **Done** (G0–G8 PASS, archived 2026-11-23,
merged in PR #64). The generated bundle contains 86 artifacts. Its 443 shared cases produced 1,329 matching
Python JSON Schema, source-gated Pydantic and AJV results with no mismatches.
See the [conformance result](../../../operations/evidence/runs/2026-11-22-885e8734/artifacts/test-results/conformance-review-final.json)
and [Node test evidence](../../../operations/evidence/runs/2026-11-22-885e8734/artifacts/test-results/js-unit.tap).

Code/security review, approval, required signoffs and PM closeout are complete.
Neither ADR-0079 nor ADR-0039 is accepted by these results. The approved
[assembly plan](feature-assembly-plan.md), [contract design](contract-design.md)
and [STATUS](STATUS.md) retain their respective design and progress authority.

## Prerequisites

- Canonical product selection for this run:
  `NEBULA_PRODUCT_ROOT=/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`.
  Pass that absolute path explicitly to every product-aware framework command.
- Framework checkout: `/home/gajap/uSandbox/repos/nebula/nebula-agents`, pinned in
  the product blueprint to `840e724b72fdbaf8157dacfee579488252e1a193`.
- Docker and Docker Compose. Run compile, test, lint and scan commands in the
  application validation containers after runtime readiness checks.
- The committed validation images pin Python 3.14.4, uv 0.11.31 and Node 22.23.1;
  the workspace locks pin Python packages, AJV 8.20.0, ajv-formats 3.0.1,
  jsonc-parser 3.3.1 and pnpm 12.21.0. The model generator is build-only.
- PostgreSQL integration uses the existing local stack and shipped migration
  head 0015. F0011 adds no migration, application deployment, route, grant,
  model/prompt activation, screen or document reparse.

For clean image builds and their default checks, follow
[Contract validation runtimes](../../../../docker/contracts/README.md). Those are
build/test images, not additional application services. The run-specific Compose
definition below is the existing mounted-workspace proof environment.

## Source authority and generated artifacts

`planning-mds/schemas/` remains the authored JSON Schema 2020-12 source.
`scripts/contracts/sources.yaml` selects the 21 payload resources, versions,
owners and consumer dispositions. `scripts/contracts/profile.yaml` is the
stable build profile. Do not hand-edit generated copies or redefine a released
identity's accepted payloads in place; changed acceptance needs a new identity
and explicit version selector.

| Product-relative path | Purpose |
|---|---|
| `schemas/contracts/v1/` | Generated release snapshot and digest manifest |
| `engine/packages/brain-contracts/src/brain_contracts/resources/v1/` | Same installed offline resources, profile, metadata and self-contained OpenAPI |
| `engine/packages/brain-contracts/src/brain_contracts/generated/` | Generated Pydantic models, gated by source schemas before parsing and after serialization |
| `engine/packages/brain-contracts/src/brain_contracts/schema_runtime.py` | Installed immutable registry; explicit `ContractRef` and wire-profile APIs |
| `experience/src/generated/contracts/v1/` | Same generated schema/manifest/metadata snapshot for JavaScript |
| `experience/scripts/contracts/` | Strict portable decoder, headless AJV runner and Node unit tests |
| `scripts/contracts/cases.json` | Complete 443-case portable inventory; imported expectations retain their provenance |
| `scripts/contracts/case-behavior-map.json` | Source-pointer witnesses for keywords, formats and all 21 source conditionals |

The wheel carries the common `brain_contracts` resource bundle. Existing content
and assertion readers delegate to it; runtime loading has no planning-directory
fallback and never retrieves a schema over the network. The API serves its
generated OpenAPI snapshot from this same installed bundle and refuses startup
when bundle integrity fails.

## Run the checks in the current proof environment

From the product root, with the run's engine and Node containers healthy:

```sh
NEBULA_PRODUCT_ROOT=/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
cd "$NEBULA_PRODUCT_ROOT"
F0011_RUN=planning-mds/operations/evidence/runs/2026-11-22-885e8734
F0011_COMPOSE="$F0011_RUN/artifacts/runtime/compose.yaml"

docker compose -f "$F0011_COMPOSE" ps
docker compose -f "$F0011_COMPOSE" exec -T engine-validation uv run --no-sync --project engine --group contract-build python scripts/contracts/generate.py --check
docker compose -f "$F0011_COMPOSE" exec -T node-validation corepack pnpm --dir experience contracts:test
docker compose -f "$F0011_COMPOSE" exec -T node-validation corepack pnpm --dir experience contracts:check --cases ../scripts/contracts/cases.json --output "../$F0011_RUN/artifacts/test-results/ajv-conformance.json"
docker compose -f "$F0011_COMPOSE" exec -T engine-validation uv run --no-sync --project engine --group contract-build python scripts/contracts/check.py --cases scripts/contracts/cases.json --ajv-results "$F0011_RUN/artifacts/test-results/ajv-conformance.json" --python-output "$F0011_RUN/artifacts/test-results/python-conformance.json" --output "$F0011_RUN/artifacts/test-results/conformance-review-final.json"
```

These command forms ran in this feature run. The generator's `--check` builds
temporary outputs and refuses missing, stale or edited artifacts without changing
tracked outputs. After an authorized source change, use the same generator command
without `--check` to regenerate the coherent set, then repeat the checks.

The join requires every case from all three real consumers; missing/duplicate
results, unsupported formats, crashes and skipped cases fail. The AJV CLI returns
0 for complete conformance, 1 for expectation mismatches and 2 for a broken run.
The Python join prints `status: pass` only when all results and behavior witnesses
are complete. Preserve raw results under the run; do not treat build/readiness
checks as consumer, authorization or acceptance-criterion proof.

The wider test selection is in `.github/workflows/ci-gates.yml` and the assembly
plan: installed-wheel/offline reproduction and deliberate drift/corruption,
native-reader differential, PostgreSQL mutation/authorization regressions, actual
API/OpenAPI parity and unchanged Neuron-reader smoke. The current proof uses
synthetic development fixtures, not frozen holdout or production documents.

## Wire profiles and consumer ordering

- New generic consumers explicitly select `portable-json/v1`: unique-key UTF-8
  JSON, paired Unicode, finite binary64 numbers and safe integral values, with the
  declared byte/depth/node limits. Money and identifiers remain strings. The four
  asserted formats are UUID, date, date-time and URI-reference.
- Existing readers select `native-compat/v1` before inspecting or parsing input.
  The legacy content/assertion resources deliberately freeze their shipped
  UUID/date format checks; adding build dependencies does not activate new
  date-time/URI checks on those old boundaries. Newly adopted canonical/response
  guards check all declared formats. Native parsing and established domain/refusal
  semantics remain separate from the new portable admission limits.
- Validation never mutates instances: no coercion, inserted defaults or property
  removal. Unknown schema instructions/annotations and unresolved, external,
  recursive or dynamic references fail. Declared annotations are descriptive;
  they establish neither evidence validity nor authorization. No failed portable
  or v2 validation retries through native or legacy readers.
- Source READ discovery stays tolerant and completes before protected refusal
  reasons. Normalized FactSlot/answer/temporal guards retain the existing
  authorized unit of work. Commit-response serialization/validation happens
  inside the mutation operation before its outer commit, so invariant failures
  roll back business writes. GET validation happens after all exact source READ
  checks and the read audit. A normalized invariant failure exposes only generic
  `contract_invariant_failed` 500 details.

PR-L3 remains a G3 Security follow-up: an authorized GET can record a successful
read audit before an internal response invariant fails with that generic 500.
This document does not accept that bounded audit meaning or claim it was removed.
Legacy pilot payloads are not recast as identity-v1 answers, and F0008 temporal
validity-unknown is not a new information state.

## Rollout, stored history and rollback

Before enabling candidate response guards in an existing environment, run
`scripts/contracts/check_stored_fact_versions.py` in the engine container for both
`--environment integration` and `--environment dev`, each with a durable `--output`
path under the current run. `--help` lists the verified arguments.
`scripts/contracts/environments.json` names the actual local databases; credentials
come from the existing application Settings, not a new exported secret or logged
DSN. The command streams every `canonical_fact_version` row, including closed
history and legacy remainders, in a read-only repeatable-read transaction and uses
the same serializer/guard as the API. It emits safe counts and identities only.

Zero rows need a fresh QE/DevOps-signed inventory passed with
`--zero-row-inventory`; an unavailable database never becomes an empty pass.
Refuse cutover on a mapping, serialization, guard or enumeration failure. Repeat
both sweeps for the final candidate while old writers are paused; changes to the
bundle, guard, serializer or stored population require fresh reports.

Rollback restores the previous coherent package set and generated snapshot
together. Never mix resource hashes, rewrite historical values, repair source
evidence or reinterpret saved content as a deployment shortcut. Schema shape alone
does not establish ownership, supported currency, predicate-required basis,
evidence admissibility or permission to disclose an answer.

## Resume this feature run

From `/home/gajap/uSandbox/repos/nebula/nebula-agents`:

```sh
python3 agents/scripts/resume-brief.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --run-id 2026-11-22-885e8734
python3 agents/scripts/project_context.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --action feature
```

Reuse this run ID and recorded absolute root. Do not initialize a competing run or
write a completion `latest-run.json` before the required G8 closeout sequence.
