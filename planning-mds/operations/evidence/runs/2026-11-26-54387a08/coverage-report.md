# F0012 Coverage Report

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-26
- Run: `2026-11-26-54387a08`
- Verdict: PASS (changed executable lines 95.64% against the 80% floor)

Result: PASS

## Method

The full engine suite (unit and PostgreSQL integration) ran with `--cov` for `brain_ontology`, `brain_persistence`, `brain_factslots`, `brain_temporal`, `brain_domain` and `brain_api` ([engine-coverage.json](artifacts/coverage/engine-coverage.json)). Changed executable lines are the lines added or modified against `origin/main` `87fe31c` (`git diff -U0`), plus every line of a new file, intersected with coverage's executable statements ([changed-line-coverage.json](artifacts/coverage/changed-line-coverage.json)).

Excluded:

- tests;
- generated contract code (`brain_contracts/generated`, produced by the F0011 toolchain);
- migration 0017, which package coverage does not measure. It is exercised by `test_ontology_migration.py` (upgrade, empty downgrade, re-upgrade on populated F0007–F0009 data), `test_downgrade_refused_after_install`, and every owned-database integration test, which migrates to head.

## Result

| Scope | Covered / changed | % |
|---|---|---|
| All changed executable lines | 1754 / 1834 | **95.64** |
| `brain_ontology` (new package; unit suite alone, CI gate) | 1111 / 1277 statements | 87 |
| `brain_persistence/ontology_releases.py` (new) | 204 / 212 | 96.2 |
| `brain_persistence/ontology_models.py` (new) | 108 / 108 | 100 |
| `brain_ontology/service.py` (new) | 142 / 154 | 92.2 |
| `brain_ontology/runtime.py` (new) | 78 / 99 | 78.8 |
| `brain_temporal/commit.py` (changed lines) | 47 / 54 | 87.0 |
| `brain_factslots/predicates.py` (changed lines) | 49 / 50 | 98.0 |

## Uncovered changed lines (reviewed)

- **`runtime.compose`:** the production composition (OIDC verifier, identity profile, Casbin, engine) needs a live issuer. Tests substitute `COMPOSE`; every command dispatch and refusal mapping is covered (`test_cli.py`). The verification and authorization it composes are the shipped, covered F0002 components.
- **`commit._commit_eternal`:** the `attestation_zone`/`expected_attestation` validation branches (lines 656–670) are not covered. They reuse the covered F0008 `zone_info`/`check_expected` functions.
- **`service.py`:** the `ScopeMismatch` and `IntegrityError` backstop handlers (lines 88, 107–121) are not covered. The database guard itself is proven by `test_selection_guard_is_the_database_backstop`.
- **`authoring.py` / `compiler.py`:** defensive branches for malformed non-mapping inputs (16 and 8 lines) are not covered.

None of these lines changes an acceptance outcome. All are listed for the code reviewer.
