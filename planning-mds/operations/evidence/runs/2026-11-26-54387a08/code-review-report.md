# Code Review Report — F0012-foundation-ontology run 2026-11-26-54387a08

- Reviewer: Claude (Opus 5.5) / Code Reviewer
- Date: 2026-11-26
- Base: `origin/main` `87fe31c`; head: working tree of `feature/f0012-foundation-ontology`

## Summary

- Assessment: APPROVED WITH RECOMMENDATIONS
- Files reviewed: every changed or new file under `engine/`, `scripts/`, `ontology/` and `.github/workflows/` in [changed-files.txt](artifacts/diffs/changed-files.txt)
- Issues found: 0 critical, 0 high, 0 medium, 5 low. Three lows are closed in this run; two are recommendations (CR-L4, CR-L5).

## Reviewed Files

The highest-risk paths were read line by line:

- `brain_temporal/commit.py` (kind resolution, `_commit_eternal`, EVENT `_one_period`);
- `brain_temporal/ranges.py`;
- `brain_persistence/repositories.py` (range mapping);
- `brain_factslots/predicates.py` (`ReleasePredicateRegistry`, `prepare_registry`), `resolution.py`, `answers.py`;
- `brain_persistence/ontology_releases.py`, `ontology_models.py`, `authx.py`/`tenancy.py` owner lookups;
- migration 0017;
- `brain_ontology/{authoring,compiler,impact,semantics,rdf_export,service,runtime,cli}.py`;
- `engine/apps/api/src/brain_api/deps.py`, `engine/apps/api/src/brain_api/schemas/facts.py`.

The tests, fixtures and CI changes were checked for what they prove.

## Validation Artifacts

[test-execution-report.md](test-execution-report.md), [coverage-report.md](coverage-report.md), [conformance.json](artifacts/test-results/conformance.json), ruff/format/mypy clean (commands.log), the SAST/DAST/dependency/secrets artifacts under `artifacts/security/`.

## Severity-Ranked Findings

### CR-F0012-L1 (low) — CLOSED: reserved predicate namespaces and manifest/term consistency were not enforced at install.

Install recomputed every digest, but a self-consistent hand-crafted release could still:

- declare `sys:`/`test:` predicate keys, which belong to the static registry;
- list manifest predicates that differ from the normalized terms the `ontology_term` rows are built from.

Fixed in review. `RESERVED_PREDICATE_NAMESPACES` is now refused at authoring (`PREDICATE_KEY_INVALID`) and at install (`MANIFEST_INVALID`). Install also requires the manifest predicate list to equal the terms (`MANIFEST_DIGEST_MISMATCH`). Tests: `test_reserved_predicate_namespaces`, `test_crafted_release_cannot_claim_reserved_or_mismatched_predicates`.

### CR-F0012-L2 (low) — CLOSED: F0012 integration modules did not import the owned-database cleanup override.

`integration/conftest.py`'s autouse cleanup truncated tables in the owned test database at teardown. In one full run it deadlocked with a still-open world connection (`test_scope_across_two_tenants`, teardown error only). All four modules now import the harness's no-op `_clean_fact_tables`, as F0007/F0009 do. 45/45 pass, and the full suite was re-run.

### CR-F0012-L3 (low) — CLOSED at G2: projection entries lacked `predicate_key`.

Found by `test_ac5_projection_mapping_contents` before any install. It was fixed and the foundation lock was recompiled to `ontrel:sha256-3602b71f…`.

### CR-F0012-L4 (low) — RECOMMENDATION: untested branches.

- `runtime.compose` (production OIDC/Casbin composition) is not exercised.
- The `_commit_eternal` `attestation_zone`/`expected_attestation` branches are not exercised.

Both reuse covered F0002/F0008 components, and the dispatch and refusal mapping are covered. Non-blocking. Severity low. Owner: Quality Engineer. Follow-up: add an ETERNAL commit with `expected_attestation` and a CLI smoke against a test issuer in the next F0013 run, which reuses these paths.

### CR-F0012-L5 (low) — RECOMMENDATION: widened `fact-version-read-v1`.

`valid_start` can now be `null`, for ETERNAL versions only. Shipped consumers (API, provenance, experience copies) are updated and conformance passes. A future external client of v1 must treat null as unbounded below. Non-blocking. Severity low. Owner: Architect. Follow-up: carry the note into the F0020 (HTTP states) contract review.

### Informational notes (no action required)

- `ReleasePredicateRegistry` resets its snapshot when the scope changes. A per-request registry therefore never serves another tenant's contracts, and an unprepared key fails closed as `PREDICATE_UNREGISTERED`.
- Activation serializes with install on the same per-KB advisory lock. The `uq_f0012_selection_seq` constraint and the guard trigger are the backstop, and an `IntegrityError` maps to `SELECTION_CONFLICT`.
- An ETERNAL same-value recommit replaces the current version whole, with no remainder, so its valid time stays `(,)`.

## Recommendations

Both are non-blocking and deferred; PM acceptance is requested at G4/G8.

- [low] CR-F0012-L4 exercise runtime.compose and the ETERNAL expected_attestation branches in tests — owner: Quality Engineer; follow-up: add a CLI smoke against a test issuer and an ETERNAL commit with expected_attestation in the F0013 feature run
- [low] CR-F0012-L5 document that fact-version-read-v1 valid_start may be null for ETERNAL versions for external v1 readers — owner: Architect; follow-up: carry the note into the F0020 HTTP-states contract review

## Vertical-Slice Completeness

- [x] Backend complete: offline toolchain, persistence, registry, commit path, CLI.
- [x] Frontend: no UI scope. Generated contract copies only; AJV and the frontend regression pass.
- [x] AI layer: not in scope.
- [x] Tests complete: unit, PostgreSQL integration, real-route commits, conformance, semantic gates.
- [x] Deployable independently: migration with refused downgrade; CI steps added.

## AC / Test Adequacy

All 46 ACs map to tests that assert the observed outcome, not only success ([test-plan.md](test-plan.md)). The negative fixtures assert exact codes and order. The PostgreSQL proofs use fresh-session queries.

## Architecture Compliance

- [x] Clean layering. Pure domain in `brain_domain.ontology`. Persistence never imports `brain_ontology`; shared digest and identity rules live in the domain module.
- [x] Authorization precedes validation detail. Every command goes through `AuthorizationExecution`, and audit commits with the effects.
- [x] SOLUTION-PATTERNS: typed refusals, append-only records, no hard-coded secrets.
- [x] The deviations recorded at G0/G2 are reviewed in [architect-implementation-review.md](architect-implementation-review.md).

## Coverage Verification

95.64% of changed executable lines are covered (floor 80%). `brain_ontology` unit coverage is 87%.

## Result

Result: APPROVED WITH RECOMMENDATIONS
