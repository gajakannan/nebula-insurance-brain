# F0012 G2 — Self-review

- Reviewers: Claude (Opus 5.5) as Backend Developer, Quality Engineer and DevOps; Architect conformance check
- Date: 2026-11-26
- Run: `2026-11-26-54387a08`
- Verdict: PASS

Result: PASS

## Scope Review

The build covers F0012-S0001 to S0007 only, under the PRD scope:

- offline authoring and compile;
- immutable releases per tenant/KB;
- release-backed predicates with temporal kinds;
- the impact report with gated activation;
- delivery proof.

Out of scope, as the plan states: GL/insurance-core vocabulary (F0013), admission-time constraint enforcement (F0017/F0018), workbench and extended reasoning (F0030/F0062), role-based access (the F0002-successor amendment), and any HTTP route or UI.

## Backend Developer

- [x] **Steps 1–7 implemented per the assembly plan and its G0 reconciliation.**
  - `brain-ontology`: authoring, compiler, semantics, rdf_export, impact, service, runtime, cli.
  - `brain_domain.ontology`.
  - Migration 0017 and the ORM models.
  - `OntologyReleaseStore`.
  - `ReleasePredicateRegistry` with `prepare`.
  - `PredicateContract.temporal_kind`.
  - The ETERNAL/EVENT commit paths.
  - Lower-unbounded `TimeRange` (G0-6).
  - The authorization resource, actions and role; six policy rows.
- [x] Unit and PostgreSQL integration tests pass. The migration applies, refuses a populated downgrade and preserves F0007–F0009 data.
- [x] No HTTP route, screen, model call, parse or new environment variable. The CLI reuses the API's configuration variables.
- [x] ruff, ruff format and mypy are clean on the CI scope plus `brain-ontology`.

## Frontend

No UI change. `frontend_in_scope` is true only because the F0011 generator rewrites the shared contract copies under `experience/src/generated/contracts/v1/`: three new schemas and the widened `fact-version-read-v1`. AJV conformance passes over those copies (490 cases, 0 failures), so no further frontend work is needed.

## Quality Engineer

- [x] [Test plan](test-plan.md) maps all 46 ACs. [Execution report](test-execution-report.md) and [coverage report](coverage-report.md) show 95.64% of changed lines covered.
- [x] Every authoring rejection rule has a negative fixture with its stable code. Error order is deterministic.
- [x] PostgreSQL proofs:
  - atomic, idempotent and concurrent install;
  - database immutability;
  - every activation refusal;
  - concurrent activation;
  - append-only rollback history;
  - split scenario;
  - two-tenant scope;
  - ETERNAL/EVENT/STATE commits and mismatches through the real route.
- [x] Security scans run for all four classes; see the manifest `security_scans` and `artifacts/security/`.

## DevOps

See [g2-deployability-check.md](g2-deployability-check.md).

## Architect conformance (does the build match the Step 0 plan?)

Yes. The build follows the G0 reconciliation, with these refinements made during G2 and recorded for the Architect review at G3:

1. **Authorization resource (G0-5, operator decision 2026-11-26).** A trusted `resource_access` row is required, and migration 0017 widens `ck_resource_access_type`. That is the only change to an existing table.
2. **ETERNAL reads (operator decision 2026-11-26).** `fact-version-read-v1` `valid_start` is widened to `string|null`; `source_sha256_at_design` and the bundle were regenerated.
3. **RDF export.** Domain and range are written as `nebula:validationDomain`/`nebula:validationRange` (ADR-0081 D2: never inferring).
4. **Additive axioms.** A definition change that only adds `parents`/`sub_property_of` keeps the IRI without a change record (EX-ONT-003).
5. **Report grant.** Report generation requires `ontology_release:review` (steward), not `read`. Reach counts are tenant/KB aggregates.
6. **Committed foundation module.** References are repository-relative so each resolves. The design draft's "master-blueprint section 22" became `planning-mds/architecture/master-blueprint.md`.
7. **Contract inventory.** The approved `contract-inventory.yaml` was not valid YAML (`retained_boundaries`); it was repaired.
8. **Compiler defect found by tests.** Projection entries lacked `predicate_key`. It was fixed before any install; the committed lock is `ontrel:sha256-3602b71f…`.

## Acceptance Criteria Review

All 46 ACs have observed proof. The AC-to-test map is in [test-plan.md](test-plan.md). Results and the ADR-0045 case log are in [test-execution-report.md](test-execution-report.md). Nothing is deferred or waived. ADR-0045, ADR-0070 and ADR-0081 stay Proposed (S0007 AC6).

## Implementation Risks

| Risk | Status |
|---|---|
| New `OntologySteward` role and `ontology_release` resource widen the authorization surface | Grants are limited to `ontology_release`. A trusted `resource_access` row is required, so access fails closed without it. Denials and refusals are audited. **Security review at G3.** |
| `fact-version-read-v1` widening (`valid_start` nullable) could break a strict reader | Only ETERNAL versions produce null, and none existed before F0012. Contract, OpenAPI and AJV conformance pass. **Code review at G3.** |
| `resource_access` CHECK change on an existing table | Revalidates existing rows, rewrites none; restored by an empty downgrade; checksum proof |
| A caller resolves a release-backed key without `prepare` | The resolver and answer policy prepare themselves. Otherwise the result fails closed as `PREDICATE_UNREGISTERED`. Strict mode exists for tests. |
| Committed release outputs drift from sources | The CI `compile --check` step. The foundation examples are regenerated by `--check`. |
| Network-dependent audits | Runtime-blocked twice; the unchanged command succeeded on retry. No code changed in between. |

## Validation Evidence

The [test execution report](test-execution-report.md) records:

- the full engine suite: 1883 passed, plus 3 known image-only failures that pass 13/13 in the host lane;
- 45 F0012 PostgreSQL tests and 83 offline tests;
- conformance: 490 cases, 0 mismatches;
- `semantic_rdf --require` pass;
- the frontend regression (lint, Vitest 12/12, build).

Changed-line coverage is 95.64% ([coverage-report.md](coverage-report.md)). The neuron recovery suite passes (5 passed, 5 PostgreSQL-only skipped) in the cached F0011 neuron image against the current sources ([neuron-recovery.txt](artifacts/test-results/neuron-recovery.txt)). All four scan classes are recorded in the manifest.

## Story × Role matrix

STATUS.md now shows Backend, QA and DevOps done for every story. Code Review and Security resolve at G3.
