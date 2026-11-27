# Security Review Report — F0012-foundation-ontology run 2026-11-26-54387a08

- Reviewer: Claude (Opus 5.5) / Security Reviewer
- Date: 2026-11-26

## Scope

Security review of:

- the new `ontology_release` resource and `OntologySteward` role;
- the six policy rows;
- the KB-scope authorization resource (G0-5);
- the widened `resource_access` CHECK;
- install, report, review, activation and rollback commands;
- the release-backed predicate registry;
- ETERNAL/EVENT commits on the existing route;
- the CLI's credential handling.

## Reviewed Surfaces

- `brain_domain/authx.py`, `brain_persistence/authx.py` (`_semantic_owner`), `tenancy.py` (`_record_owner`), `policy.csv`, `kg-source/policies`;
- `brain_ontology/service.py`, `runtime.py`, `cli.py`;
- `brain_persistence/ontology_releases.py`, migration 0017;
- `brain_factslots/predicates.py`;
- `brain_temporal/commit.py`.

## Threat Boundary

The trusted inputs are:

- installed `resource_access` rows (operator-provisioned);
- the `knowledge_base` row, which is the owner of the ontology scope;
- policy releases;
- verified principals.

The untrusted inputs are:

- compiled release files supplied to `install`;
- CLI arguments;
- commit request bodies.

An attacker with only `TenantMember` must not install, review, activate or learn reach counts. Another tenant must not see or affect a KB's releases. A crafted release must not hijack system predicates or break immutability.

## Auth / Authz

- Every command authorizes `ResourceKey(ontology_release, kb_id)` through `AuthorizationExecution`: `install`, `review` (report and review), `activate` (activate and rollback) and `read` (history).
- Hydration requires a trusted `resource_access` row with explicit classifications. No default label is invented. Missing metadata fails closed (`test_unprovisioned_scope_fails_closed`).
- The owner is the KB row, so a mismatched tenant is a denial (`ScopeMismatch`), and the CLI output is a non-disclosing `DENIED`.
- `OntologySteward` holds grants only on `ontology_release`; no existing role gained review or activation. Decisions on existing resources are identical before and after install (`test_vocabulary_grants_nothing`).
- Cross-tenant and cross-KB isolation is tested: a principal from another tenant is denied with `no_membership`; installs, reports and selections are per KB; the registry serves only releases installed in the slot's KB.
- Commits keep `fact_slot:commit`. A steward without it gets the existing non-disclosing 404.

## Validation

- **Install** validates the manifest against its schema, recomputes the manifest, module, term and terms digests, and checks that manifest predicates match the terms. It refuses `sys`/`test` namespaces and identity reuse against installed history. All of this runs before any row is written.
- **Database:** append-only triggers on all eight tables (UPDATE, DELETE, TRUNCATE), CHECKs on references and digests, and the selection guard trigger.
- **Commits:** a temporal shape that does not match the kind is refused before any write (`kind_shape_mismatch`, `eternal_conflict`). The 0014 kind-shape CHECK remains the backstop.

## Audit / Logging

- Every command writes the durable authorization decision plus an `ontology_release_<command>` event (release reference, digest, typed outcome), including denials and refusals, after the durable decision.
- Tests assert the events and their decision linkage.
- The bearer token is read from a file and never printed. A CLI test asserts it is absent from output.

## Secrets / Config

No new secret, credential, environment variable or port. Gitleaks scanned 119 changed files and found no leaks.

## Scan Disposition

| Class | Result | Disposition |
|---|---|---|
| Dependency | pip-audit (engine 75, neuron 171): 0 vulnerabilities; pnpm audit experience: 0 at all levels | Clean. Two retries were runtime-blocked by network; the unchanged command succeeded. |
| Secrets | gitleaks filesystem mode: no leaks | Clean |
| SAST | semgrep, 200 rules, 45 files: 2 `avoid-sqlalchemy-text` at `0017_f0012_ontology_releases.py:305-306` | **False positive.** The `LOCK TABLE {table}` and `SELECT count(*) FROM {t}` identifiers come from the module constant `TABLES` plus the literal `resource_access`. They never take input, and the downgrade runs only under the operator's Alembic. Same pattern as F0009's accepted 0016 finding. |
| DAST | ZAP API scan of the candidate API: 0 fail, 0 warn, 113 pass | Clean. No new HTTP route; protected behaviour is proven by the PostgreSQL suites. |

## OWASP Top 10 Coverage

- **A01 Broken Access Control:** per-KB resource, scope check, non-disclosing denials, two-tenant tests.
- **A02 Cryptographic Failures:** SHA-256 content addressing only; no secrets stored.
- **A03 Injection:** SQLAlchemy bound parameters; the two `text()` uses take constants (SAST FP). The authoring YAML is loaded with `safe_load`.
- **A04 Insecure Design:** append-only, gated activation, reviewed reports, refused downgrade.
- **A05 Security Misconfiguration:** fails closed without provisioning.
- **A06 Vulnerable Components:** audits clean.
- **A07 Identification and Authentication Failures:** CLI uses F0002 verification.
- **A08 Software and Data Integrity:** digests recomputed at install; immutable rows; `compile --check` in CI.
- **A09 Logging Failures:** every outcome audited.
- **A10 SSRF:** no outbound calls.

## Findings

- **SEC-F0012-L1 (low, accepted).** `TenantMember` holds `ontology_release:read`, so `history` shows the steward principal ids that made selections. This is the ADR-0081 D5 grant as approved, and the ids are already visible in audit to authorized readers. Non-blocking. Owner: Product Manager (accept at G4). Follow-up: revisit with the F0002-successor role amendment.
- **SEC-F0012-L2 (low, accepted).** Report reach counts are KB-wide aggregates, gated by `review` (steward) rather than per-slot `fact_slot:read`. Only counts are disclosed, never values or identifiers. Non-blocking. Owner: Security. Follow-up: re-evaluate when classification-restricted slots exist in a KB that has stewards.
- **SEC-F0012-L3 (low, accepted).** The offline `resolve_reference` follows symlinks inside the repository root when checking anchors. It is an offline authoring tool over the author's own checkout, with no runtime exposure. Non-blocking. Owner: Code Reviewer. No follow-up required.

There are no critical, high or medium findings.

## Recommendation Disposition

All three lows are non-blocking with named owners. PM acceptance is requested at G4 (gate-decisions.md).

## Result

Result: PASS
