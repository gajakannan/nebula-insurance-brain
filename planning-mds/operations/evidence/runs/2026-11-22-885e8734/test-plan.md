# F0011 Test Plan

Owner: Codex / Quality Engineer
Date: 2026-11-22
Run: 2026-11-22-885e8734
Status: execution in progress; final runtime and security evidence in test-execution-report.md

## Scope and acceptance traceability

All six approved stories and 41 ACs are required. The assembly plan's complete
AC-to-proof map controls scope. No planning or authored-fixture result counts as
runtime proof. Synthetic development fixtures remain outside the frozen holdout.

| Story | Required layers and cases | Planned durable evidence |
|---|---|---|
| S0001 AC1–AC7 | Offline registry, identity/hash/version, dormant bad refs, dialect/keyword/annotation policy, no network/mutation, installed package | artifacts/test-results/python-contracts.txt; installed-package report; bundle manifest |
| S0002 AC1–AC7 | Nine answer states and scoped absence; malformed scope/duplicates; denied source before protected metadata; temporal UNKNOWN separate | common-case conformance; existing fact-answer and source READ suites |
| S0003 AC1–AC7 | Exact decimal/currency and scoped identifiers; structural versus domain currency/basis/normalization/interval outcomes | common-case conformance; existing FactSlot domain/integration suites |
| S0004 AC1–AC7 | Real JSON Schema/source-gated generated Pydantic/AJV, every supported behavior/format and source conditional; no missing/duplicate/skipped results; metadata/OpenAPI drift | artifacts/test-results/conformance.json; node unit log; generator/drift tests |
| S0005 AC1–AC7 | Every mapped real consumer; native legacy/current dispatch; actual integration/dev full-history preflight; source READ/admission; no partial authoritative writes | two stored-version reports, signed empty inventories if applicable, PostgreSQL consumer regressions and native differential proof |
| S0006 AC1–AC6 | Deterministic generation/check; outside-checkout wheel/sdist and JS; intentional drift failure; complete AC ledger and coherent rollback/CI | artifacts/test-results/reproducibility.txt; packaging/CI evidence; coverage artifacts |

## Runtime and execution order

Use the current checkout mounted at `/app/brain` in the run-local Engine, Neuron
and Node containers. Verify health and database connectivity before stack-specific
commands. A runtime failure stops code edits until health is restored and the
unchanged failed command is rerun. G1 must pass before validation suites begin.

1. Confirm locked tool versions and both existing databases at the shipped 0015 baseline.
2. Generate and source-check the complete candidate. Execute registry/decoder/model
   tests and real AJV cases; join all 363 declared results per consumer.
3. Run full-history READ ONLY REPEATABLE READ sweeps for integration and dev,
   reconciling same-snapshot selected/checked counts with zero skips. If zero rows
   are observed, QE and DevOps sign that explicit inventory, then rerun the same
   sweep with the signed file. A missing/old-schema/unavailable DB is a failure.
4. Only after both candidate sweeps pass, activate response guards inside the
   existing write unit of work and after complete read authorization. Rerun
   affected container integration suites and final cutover sweeps while prior
   application writers are paused. Record exact candidate code and bundle digests.
5. Verify full affected Engine/Neuron regressions, existing frontend regressions,
   deterministic rebuild, intentional drift injection and installed distribution.
6. Measure changed executable-line coverage against the contract-owned floor;
   use Python coverage JSON/XML and Node coverage for headless JS. Generated code
   is explicitly reported separately from authored runtime logic.

## Critical regression cases

- Malformed v2 never falls back to legacy; disabled v2 still refuses.
- Money precision, scientific notation and original currency survive typed round trips.
- Schema-valid unsupported currency/basis/normalization remains a domain refusal.
- Denied absence/name/attestation source returns the existing non-disclosing response
  before any output-contract reason; structural success grants no authority.
- Injected normalized result, temporal and commit-response failures leave no slot,
  qualifier, version, change or outbox partial mutation; fresh DB reads prove this.
- PR-L3: authorized read audit may be SUCCEEDED before output invariant failure;
  HTTP must be generic `contract_invariant_failed` 500 without payload/pointers.
  Security must explicitly decide this bounded audit meaning at G3.
- Sweeper covers closed history, legacy/remainder versions, incomplete enumeration,
  empty/unavailable databases, mapper/serializer/format faults and PostgreSQL READ ONLY.

## Coverage and exclusions

Coverage is required, with no waiver planned. Report numerator, denominator,
changed-path basis and durable artifacts. UI/theme/accessibility/screenshot and live
model/PDF evaluation layers are outside this headless infrastructure feature;
the existing UI and Neuron caller regressions still run. No new latency SLO,
ontology release proof or formal ADR acceptance is claimed.

## Completion rules

Every expected case and consumer result must be present and match. A crash,
unsupported profile/dependency/format, missing or duplicate case, stale artifact,
failed guard-order/atomicity check or incomplete history sweep blocks a PASS.
Record actual commands, exits, report paths and remaining findings in the execution
and coverage reports before G2. All five required roles remain required at signoff.
