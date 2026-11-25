# Self Review — F0009 run 2026-11-24-08701e37

Reviewer: Claude (Opus 5.5) / Backend implementation self-review; Architect conformance check
Date: 2026-11-24

Result: PASS

## Scope review

The build follows the reconciled assembly plan's five steps: carriers and contracts, migration 0016, the review boundary, the metadata-first reader, and temporal closure. No route, grant, Casbin policy, UI, deployable, parse, model call, canonical orchestration or learning processing was added. The HTTP route surface and envelopes are byte-identical (`test_f0009_review_compatibility`). OpenAPI paths are unchanged, and only four `Contract…` components were added.

## Backend self-review checklist

- [x] The internal reader (`brain_provenance.ProvenanceReader`) and the `get_provenance_reader` factory are exported. No route registers them; F0020 owns exposure.
- [x] Domain logic is complete and unit-tested: closed edge table, invariants, limits.
- [x] Unit and PostgreSQL integration tests pass: 75 F0009 tests and the full engine regression.
- [x] SOLUTION-PATTERNS are followed:
  - clean layering: domain carriers have no I/O; the application package depends on domain, security and contracts; persistence implements its port;
  - ProblemDetails mapping is unchanged;
  - every mutation is audited.
- [x] All 41 ACs have observed runtime proof ([test-plan.md](test-plan.md) traceability).
- [x] Migration 0016 applies, round-trips when empty, and refuses a populated downgrade.

## Architect conformance (implementation vs plan)

Where the implementation differs from the approved design text, every difference is a correction found against the shipped code, and each is recorded:

1. **`fact_change.from_version_id` is nullable.** It was a required string in `provenance-result-v1`. The shipped commit writes NULL for a slot's creation change, so the authored schema had to admit it. No `changed_from` edge is emitted for such a change. The schema hash in `sources.yaml` is updated. This is a fix to an F0009-owned, not-yet-released schema.
2. **Attempt authorization binding.** The design's `REFERENCES audit_event(id)` pointed at a per-row random id. The guard instead requires an allowed `authorization_decision` audit row with the same `decision_id`, actor, `review_task` resource and `annotate` action. `decision_id` is the identity the existing review audit already calls `authorization_decision_id`, and its index already exists.
3. **`uq_review_decision_owner` (id, tenant_id, knowledge_base_id).** Migration 0016 adds it, because the composite owner FKs need it and 0005/0006 did not provide it.
4. **`review-decision` is now a bundled resource.** It moved from OpenAPI-only into `sources.yaml` resources, because `provenance-result-v1` `$ref`s it. The existing DTOs and component are unchanged.
5. **PR-L1 and PR-L2 are implemented as decided at G0.** The legacy GET keeps the stale fields null. A source-set change after the item locks returns 503, with a durable failed audit.

The reader's closure is exactly the plan's Step 4-5 definition. The QE stored-basis derivation agrees with the actual output edge-for-edge on every fixture.

## Frontend / AI self-review

There is no UI, model or Neuron source change. `frontend_in_scope=true` only because the regenerated shared contract copies under `experience/` changed. They are covered by AJV conformance (464/464), the Node runtime tests (19/19), and the unchanged frontend lint, Vitest (12/12) and build.

## Quality Engineer self-review

- [x] The test plan is complete, with independent expectations.
- [x] All lanes pass in the application runtime containers; the restore lane runs on the host, as in CI.
- [x] Coverage is 94.41% of changed lines.
- [x] Every AC is testable and tested.

## DevOps self-review

See [g2-deployability-check.md](g2-deployability-check.md): PASS.

## Security scans (run by QE, verdict for Security at G3)

| Class | Result | Artifact |
|---|---|---|
| dependency | clean: engine 75 and neuron 171 packages, 0 vulnerabilities; experience 0 at all levels | [scan-summary.json](artifacts/security/scan-summary.json), artifacts/security/dependency/ |
| secrets | clean: 107 changed files, 4.59 MB, 0 leaks | artifacts/security/secrets/report/ |
| sast | 4 findings, `avoid-sqlalchemy-text`, all in migration 0016; to be triaged at G3 | artifacts/security/sast/final-timeout60/results.json |
| dast | clean: 0 fail, 0 warn, 119 pass (ZAP API scan, 59 URLs) | artifacts/security/dast/api-scan.json |

## Acceptance Criteria Review

All 41 ACs (S0001 7, S0002 8, S0003 7, S0004 7, S0005 6, S0006 6) map to passing runtime tests in [test-plan.md](test-plan.md). No AC is closed by a planning artifact. S0006 AC6's review signoffs are pending G3/G5.

## Implementation Risks

| Risk | Mitigation in this build | Residual / owner |
|---|---|---|
| Shared authorization facade regression | `prepare_reads` is opt-in; the old `read` path is unchanged (dedicated test); all F0002/F0007/F0008 suites pass | Security review at G3 |
| A refused batch's audit is rolled back | The operation returns `RefusedBatch`; the route raises 422 after commit; proven by the competing and mixed-batch tests | none |
| An old application writer runs against 0016 | The deferred trigger refuses a CORRECT without a reservation; the upgrade procedure quiesces writers | DevOps runbook (deployability-check.md) |
| The elevated application DB role | All guards are SECURITY INVOKER and still hold under the superuser test role | Row-level security and role remediation remain F0018 |
| A data-only restore into a 0016 schema | The full restore is proven; data-only restores need `--disable-triggers` | DevOps note |
| Reader cost on large histories | Fixed limits (256 links, 2048 records, 8192 edges); refuse at limit+1 | F0020 to measure before any public route |

## Validation Evidence

- Engine: 1729 passed, and the 3 container-only restore tests pass 13/13 in the host lane. 75 F0009 tests. 0 skipped.
- Changed-line coverage 94.41% (912/966); per-package gates pass (brain_provenance 100%).
- Conformance 1392/1392; generation reproducible; installed-package smoke passes; Neuron shared bundle 8/8.
- Static checks: ruff, format and mypy (115 files) clean.
- Security scans: dependency, secrets and DAST clean; SAST has 4 migration findings for G3 triage.
- Artifacts: [test-execution-report.md](test-execution-report.md), [coverage-report.md](coverage-report.md), [deployability-check.md](deployability-check.md), `artifacts/security/scan-summary.json`.
