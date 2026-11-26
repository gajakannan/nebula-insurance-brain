# Feature Assembly Plan — F0012: Foundation ontology

**Created:** 2026-11-25
**Author:** Claude / Architect
**Status:** Phase B approved 2026-11-25 by operator token `approve-phase-b`; implementation not started
**Plan Run:** 2026-11-25-120320e9 (A+B, new)
**Requirements:** Phase A approved with token `approve-phase-a` on 2026-11-25; seven stories, 46 ACs; G1 decisions D1–D8; assumptions A1–A5.
**Governing design:** [ADR-0081](../../architecture/decisions/ADR-0081-foundation-ontology-authoring-and-release-runtime.md) (Proposed), refining [ADR-0045](../../architecture/decisions/ADR-0045-ontology-release-compatibility.md) (Proposed) and using [ADR-0070](../../architecture/decisions/ADR-0070-account-party-and-role-model.md) (Proposed) for vocabulary.

## Overview

Add an offline authoring/compile toolchain (`brain-ontology`), the foundation module, eight append-only release tables (migration 0017), a release-backed predicate registry, temporal-kind activation in the existing commit path, and an impact report with gated activation. Everything runs from command-line entry points under the existing authorization service; no HTTP route, screen, parse or model call is added.

The design inputs in this folder are: [foundation-module-design.yaml](foundation-module-design.yaml) (validates against the authoring schema; 53 terms, 15 predicates, 7 constraints, full projection coverage), [migration-design.sql](migration-design.sql), [contract-inventory.yaml](contract-inventory.yaml) and three design schemas under `planning-mds/schemas/`: `ontology-module-authoring-v1`, `ontology-release-manifest-v1`, `ontology-impact-report-v1`.

## Build Order

| Step | Scope | Stories | Depends on |
|---|---|---|---|
| 1 | Authoring schema, validation, identity rules (offline) | S0001, S0002 | F0011 bundle |
| 2 | Foundation module content and example gates | S0003 | Step 1 |
| 3 | Compiler, RDF/JSON-LD export, committed release locks | S0004 AC1–AC5, S0007 AC2 | Steps 1–2 |
| 4 | Migration 0017, release store, install command, grants | S0004 AC6–AC7, S0002 AC6 | Step 3 |
| 5 | Release-backed registry and temporal-kind activation | S0005 | Step 4 |
| 6 | Impact report, review, activation and rollback | S0006 | Steps 4–5 |
| 7 | Delivery proof | S0007 | Steps 1–6 |

## Existing Code (Must Be Modified)

| Path | Change |
|---|---|
| `engine/packages/brain-domain/src/brain_domain/fact_slots.py` | `PredicateContract.temporal_kind: TemporalKind = STATE` |
| `engine/packages/brain-factslots/src/brain_factslots/predicates.py` | Keep `StaticPredicateRegistry` for `sys`/`test`; add `ReleasePredicateRegistry` composing it with release snapshots |
| `engine/packages/brain-factslots/src/brain_factslots/service.py` | Call `registry.prepare(scope, release_refs)` inside the unit of work before resolution |
| `engine/packages/brain-temporal/src/brain_temporal/commit.py` | Replace the constant `TemporalKind.STATE` (≈line 499) with the contract kind; ETERNAL/EVENT shape checks; `KIND_SHAPE_MISMATCH`, `ETERNAL_CONFLICT` |
| `engine/packages/brain-domain/src/brain_domain/temporal.py` | Add the two `TemporalReason` values |
| `engine/packages/brain-domain/src/brain_domain/authx.py` | `ResourceType.ONTOLOGY_RELEASE`; `Action.INSTALL`, `REVIEW`, `ACTIVATE`; role `OntologySteward` |
| `planning-mds/security/policies/policy.csv` + `kg-source/policies/**` | Six rows from ADR-0081 D5, added together so the Casbin drift check passes |
| `engine/apps/api/src/brain_api/deps.py` | Compose the release-backed registry |
| `scripts/contracts/sources.yaml` | Three resources from the contract inventory |
| `scripts/validation/validate_semantic_examples.py`, `validate_semantic_rdf.py` | Add the foundation release export and the re-expressed Cedar Bridge fixtures |

## New Files

- `ontology/modules/foundation/module.yaml` (from the design draft), `ontology/modules/foundation/changes.yaml` (empty for version 1)
- `ontology/releases/foundation/1/{release.yaml,manifest.json,normalized.json,projection-mapping.json,release.ttl,release.jsonld}`
- `engine/packages/brain-ontology/` — `authoring.py`, `identity.py`, `semantics.py`, `compiler.py`, `rdf_export.py`, `impact.py`, `cli.py`, `errors.py`, tests
- `engine/packages/brain-persistence/src/brain_persistence/ontology_releases.py` — `OntologyReleaseStore` (install, history, reach counts, review, selection)
- `engine/migrations/versions/0017_f0012_ontology_releases.py`
- `engine/tests/integration/test_ontology_release_install.py`, `test_ontology_activation.py`, `test_temporal_kind_activation.py`
- `planning-mds/examples/commercial-pc-account/foundation/**` — EX-PC-001/011/015/017/021 on production IRIs

## Step 1 — Authoring Validation and Identity (S0001, S0002)

`brain_ontology.authoring.validate_module(path) -> ValidationResult` runs in this order and collects every error, sorted by (file, JSON path, code):

1. YAML load (one `YAML_INVALID` error with position on failure).
2. Retired-field pre-check: any `parent` key → `AUTHORING_FIELD_RETIRED` with replacement `parents`.
3. JSON Schema `ontology-module-authoring/v1` (via the F0011 runtime).
4. Semantic checks: term ID grammar; unique IDs; resolvable `parents`, `domain`, `range`, `inverse_of`, `sub_property_of`, `code_of`; exactly one `en-US` preferred label and valid BCP 47 tags; resolvable example/regression references (file exists; `cases.md#ID` anchors resolve); `temporal_kind` on every property; constructs outside ADR-0081 D2 → `UNSUPPORTED_CONSTRUCT`; constraint execution context complete; unique predicate keys matching the ADR-0077 grammar; tenant namespace → `TENANT_NAMESPACE_RESERVED`.

`brain_ontology.identity` maps ID → `urn:nebula:ont:<id>` and checks a candidate against identity history (committed release locks plus, at install, installed rows): same IRI with a different `definition_digest` and no change record → `IDENTITY_REUSE_REJECTED`; equal IRIs → `IRI_COLLISION`; a predecessor term missing from the candidate without `retirement` → `TERM_REMOVED_WITHOUT_RETIREMENT`; label-only differences are classified `rename_alias`. The ASCII-only grammar makes NFC/case collisions impossible by construction; a test proves a non-ASCII or uppercase ID is refused at the grammar step (S0002 AC3).

Exit codes: 0 valid, 1 errors, 2 invalid invocation. No database access.

## Step 2 — Foundation Content (S0003)

Copy [foundation-module-design.yaml](foundation-module-design.yaml) to `ontology/modules/foundation/module.yaml`. Key design choices:

| Term | Kind | temporal_kind | Predicate | Cardinality / value |
|---|---|---|---|---|
| organization.parent-organization | object | STATE | `fnd:parentOrganization@v1` | SINGLE entity_ref |
| organization.operates-at | object | STATE | `fnd:operatesAt@v1` | RELATIONSHIP |
| person.employed-by | object | STATE | `fnd:employedBy@v1` | RELATIONSHIP |
| account.organization | object | ETERNAL | `fnd:accountOrganization@v1` | SINGLE entity_ref |
| account.status | object | STATE | `fnd:accountStatus@v1` | SINGLE code (`current`, `closed`) |
| account.parent-account | object | STATE | `fnd:parentAccount@v1` | SINGLE entity_ref |
| ownership-interest.owner / owned-organization | object | ETERNAL | `fnd:ownershipOwner@v1`, `fnd:ownershipOwnedOrganization@v1` | SINGLE entity_ref |
| ownership-interest.percentage | datatype | STATE | `fnd:ownershipPercentage@v1` | SINGLE decimal |
| role-assignment.party / acted-for | object | STATE | `fnd:roleParty@v1`, `fnd:roleActedFor@v1` | SINGLE entity_ref |
| role-assignment.role-kind / scope | object | ETERNAL | `fnd:roleKind@v1`, `fnd:roleScope@v1` | SINGLE code / entity_ref |
| role-assignment.coverage-part | object | STATE | `fnd:roleCoveragePart@v1` | MULTI entity_ref (range narrowed by F0013) |
| role-assignment.authoritative-source | datatype | STATE | `fnd:roleAuthoritativeSource@v1` | SINGLE code |
| organization.child-organization | object (inverse) | STATE | none — derived | projection omitted |

Ownership interests and role assignments are reified entities so their ETERNAL parts and STATE parts can differ. `role-scope` is a class with `account` as subclass; F0013 adds policy-term and submission. Role-kind code values carry `PartyRoleTypeCode` with an explicit status: `existing` (BROKER_OF_RECORD, ADDITIONAL_INSURED), `proposed` per the cross-repo plan (FIRST_NAMED_INSURED, ADDITIONAL_NAMED_INSURED, PLACEMENT_BROKER, BROKER_CONTACT, RISK_MANAGER, ACCOUNT_CONTACT, UNDERWRITER) or `unmapped` (five kinds). This satisfies S0003 AC3's "mapped or marked unmapped" while not claiming proposed codes exist.

Constraints: two `authoring`-stage constraints execute in the compiler (one account organization; role-scope range). One `example-validation` constraint (one parent account) executes in the semantic examples gate. Four `canonical-admission` constraints (no parent cycle, percentage range, percentage total, one current account per organization per tenant) are declared contracts for F0017/F0018 and are exercised in F0012 only through the example SHACL shapes (PRD A2).

Cedar Bridge: re-express EX-PC-001/011/015/017 (account-scoped rows)/021 with `urn:nebula:ont:foundation.*` IRIs in `examples/commercial-pc-account/foundation/`, keeping the existing `pc:` fixtures for F0013's policy-dependent cases. Expected and forbidden rows are copied from `expected-results.yaml`; boundaries self-parent, parent-cycle, ownership-over-100, two-parent-accounts and duplicate-organization-account must fail; close/reopen must conform.

## Step 3 — Compiler and Release Locks (S0004 AC1–AC5, S0007 AC2)

`python -m brain_ontology.cli compile ontology/releases/foundation/1/release.yaml` reads the release request (name, sequence, module paths, predecessor release lock), validates each module (Step 1), resolves dependencies exactly (`DEPENDENCY_UNRESOLVED` otherwise), normalizes with RFC 8785 JCS, sorts by IRI, computes digests, builds the manifest (schema-validated) and writes the five output files. `release_ref = ontrel:sha256-<manifest_digest>`.

- Projection mapping: generated from each module's `projection` list; a property without a rule → `PROJECTION_UNCOVERED`. Required context is fixed: tenant, KB, valid_as_of, known_as_of, exact source fact/relationship versions, assertion/evidence references, ontology release, mapping version, asserted/derived basis.
- RDF export: a deterministic in-house Turtle and JSON-LD writer (no runtime rdflib dependency). Classes → `owl:Class` + `rdfs:subClassOf`; properties → `owl:ObjectProperty`/`owl:DatatypeProperty` with `rdfs:domain`/`rdfs:range` annotated as validation (`nebula:constraintRole "validation"`), `owl:inverseOf`; labels as language-tagged `skos:prefLabel`. The `semantic_rdf` gate (rdflib/pySHACL extra) checks Turtle/JSON-LD isomorphism and the expected subclass entailments.
- CI: `compile --check` recompiles and byte-compares the committed outputs.

## Step 4 — Persistence, Install and Grants (S0004 AC6–AC7, S0002 AC6)

Migration 0017 follows [migration-design.sql](migration-design.sql) (rebase the number at G0 if another migration lands). `OntologyReleaseStore.install(scope, manifest, normalized)`:

1. `AuthorizationExecution.mutate(resource=ontology_release@tenant/KB, action=install)`; denial audited, no rows.
2. Recompute digests; mismatch → `MANIFEST_DIGEST_MISMATCH`.
3. Identity history check against installed rows in the tenant/KB (Step 1 rules).
4. Lock the tenant/KB release head (`pg_advisory_xact_lock(hash(tenant,kb,'ontology'))`); if `release_ref` exists, return `already_installed` (idempotent, no rows); else insert module versions (an existing module/version with another digest → `MODULE_VERSION_IMMUTABLE`), release, memberships, terms, change records — one transaction.
5. Audit row with actor, tenant/KB, release_ref, digest and outcome. Install never writes a selection.

`cli install --tenant … --kb … --token-file …` verifies the token through existing F0002 credential verification. `cli install-extension` exists only to return `TENANT_EXTENSION_UNSUPPORTED` with exit 1 and an audit row (S0002 AC6).

## Step 5 — Registry and Temporal Kinds (S0005)

- `ReleasePredicateRegistry(static, store)`: `prepare(scope, refs)` loads `ontology_term` predicate rows for the given `release_ref`s installed in that tenant/KB (one query, same session) into an immutable snapshot keyed `(PredicateKey, release_ref)`; `contract()` checks `sys`/`test` first, then the snapshot; misses → `PREDICATE_UNREGISTERED`. Release refs come from the request (new slots) or from the stored `predicate_release_ref` (existing slots). No active-release lookup exists in this path (S0005 AC6).
- Slot identity: unchanged code; `predicate_release_ref` is already outside identity (ADR-0077 D2). A test commits under foundation@1, installs a foundation@2 with the same key and confirms the same slot is resolved (S0005 AC3).
- Commit: `kind = contract.temporal_kind`. ETERNAL: request with any valid-time bound → `KIND_SHAPE_MISMATCH`; write `(,)`, `valid_to_state = OPEN`, NULL granularity/basis columns; a different value in an existing open SINGLE ETERNAL slot → `ETERNAL_CONFLICT`; same value → existing duplicate path. EVENT: bounds must be one granularity period (existing placement), otherwise `KIND_SHAPE_MISMATCH`. STATE: unchanged. The database `ck_cfv_v1_kind_shape` CHECK is the backstop.
- Legacy inventory (S0005 AC5): `limit`, `each_occurrence_limit` → unmapped, owner F0013; `__OPEN_STATEMENT_V2__` → not a predicate (OPEN sentinel, F0066). The G0 check re-runs `SELECT DISTINCT slot_type FROM fact_slot WHERE identity_version IS NULL` on the integration database and appends any new value. No backfill.

## Step 6 — Impact Report and Activation (S0006)

`brain_ontology.impact.build_report(predecessor, candidate, reach) -> ontology-impact-report/v1`:

- **Changes:** per IRI: new → `additive`; removed with retirement record → `retirement`; label/alias only → `rename_alias`; definition digest changed → the class named by its change record (`semantic_change`/`split`/`merge`); a constraint stricter on the same subject/property (lower max, higher min, new constraint at a stage that refuses, narrowed range) → `constraint_tightening`; anything else → `unclassified` and status `incomplete`.
- **Inference:** fixpoint closure of `subClassOf`/`subPropertyOf` (reflexive-transitive) and `inverseOf` (symmetric) on each release; compare entailments whose subject and object both exist in the predecessor. Bound: 100,000 entailments per release; exceeding it → `result: unresolved`.
- **Constraints:** diff by constraint ID and by (subject, property, construct): added/removed/tightened/loosened/applicability/stage/data-basis changes, with consumer.
- **Reach:** `fact_slot` identity-v1 rows grouped by `predicate_key` for changed predicate terms (denominator: all identity-v1 slots in tenant/KB) and `assertion` rows by `predicate_id` (denominator: typed assertions in tenant/KB), read under `ontology_release:read` plus `fact_slot:read` authorization for the tenant/KB.
- **Unexamined:** always lists extraction profiles/templates (F0015), assessments (F0065) and graph projections (F0034) with reason "no producer in this release".

Commands: `cli report --candidate <ref>` (persists the report, status from content), `cli review --report <id> --decision approve|reject --rationale …` (`review` grant), `cli activate --release <ref> --review <id>` and `cli rollback --release <ref>` (`activate` grant). Activation refusals, all audited: `ACTIVATION_REPORT_REQUIRED`, `REPORT_DIGEST_MISMATCH`, `REPORT_INCOMPLETE`, `REVIEW_REJECTED`, `PREDECESSOR_MISMATCH`, `ROLLBACK_TARGET_NEVER_ACTIVE`, `SELECTION_CONFLICT`. Selection appends under `SELECT … FOR UPDATE` of the current head row (or the advisory lock when none); the DB guard trigger re-checks. `cli history` lists selections in sequence order.

Split scenario (S0006 AC7): a test release foundation@2 splits a test-only class into two, with a `split` record; the report lists the affected predicate/slots/assertions; existing versions keep `predicate_release_ref` of @1; after rollback the head selects @1 and both releases and all selections remain.

## Step 7 — Delivery Proof (S0007)

Record in the feature run: each ADR-0045 F0012 case (identity/locks, inference change EX-ONT-003, constraint change EX-ONT-004, split/rollback, scope across two tenants/KBs) with command and exit code; `semantic_rdf --require`; F0011 conformance suite with the three new resources; migration upgrade on a database containing F0007–F0009 fixture data, row counts and checksums before/after; full engine suite; downgrade refusal after install; coverage ≥80% changed lines; parse/model call counters at zero; `examples/README.md` entries for stable term IRI, release, release reference, impact report, release selection and the foundation vocabulary.

## Acceptance Criteria to Implementation / Proof Map

| Story / AC | Step | Proof |
|---|---|---|
| S0001 AC1 | 1 | Foundation module validates; summary names authoring schema |
| S0001 AC2 | 1 | `parent:` fixture → `AUTHORING_FIELD_RETIRED`, no output |
| S0001 AC3 | 1 | Missing definition/example/regression and unresolved reference fixtures |
| S0001 AC4 | 1 | Missing `en-US`, duplicate preferred, bad tag fixtures |
| S0001 AC5 | 1 | Missing/invalid `temporal_kind` fixtures |
| S0001 AC6 | 1 | `symmetric`, `transitive`, `equivalentClass` → `UNSUPPORTED_CONSTRUCT`; domain does not infer type (closure test) |
| S0001 AC7 | 1 | Missing execution-context fields; multi-error ordering; non-zero exit; no output |
| S0002 AC1 | 1 | Mapping table test, grammar refusals, cross-run determinism |
| S0002 AC2 | 1, 4 | Reuse fixture offline and at install |
| S0002 AC3 | 1 | Duplicate IRI across modules; uppercase/non-ASCII refused by grammar |
| S0002 AC4 | 1, 3 | Label change → same IRI, `rename_alias`, both labels in release history |
| S0002 AC5 | 1 | Each change class; removal without retirement refused |
| S0002 AC6 | 1, 4 | Tenant namespace refused; `install-extension` refused, audited, zero rows |
| S0003 AC1 | 2 | Class list and parents validated; no Broker/Carrier/MGA/Insured subclass |
| S0003 AC2 | 2 | temporal_kind table assertion test |
| S0003 AC3 | 2 | 14 role kinds, three distinct named-insured/insured kinds, code status present |
| S0003 AC4 | 2 | Scope range = role-scope; non-member scope fixture refused |
| S0003 AC5 | 2 | Seven constraints with execution context; no majority property |
| S0003 AC6 | 2, 4 | Policy rows/decisions identical before/after install (only new `ontology_release` rows added) |
| S0003 AC7 | 2 | `semantic_examples` and `semantic_rdf --require` on foundation fixtures |
| S0004 AC1 | 3 | Double compile and fresh-checkout digest equality; shuffled-source test |
| S0004 AC2 | 4 | Same module/version different digest refused; identical idempotent |
| S0004 AC3 | 3 | Manifest schema validation and field assertions |
| S0004 AC4 | 3 | Floating/range/missing/conflict dependency fixtures |
| S0004 AC5 | 3 | Uncovered property fixture → `PROJECTION_UNCOVERED` |
| S0004 AC6 | 4 | Rollback injection, idempotent reinstall, concurrent install, UPDATE/DELETE/TRUNCATE refused |
| S0004 AC7 | 4 | Denied install audited; no selection row; parse/model/canonical write counters zero |
| S0005 AC1 | 3, 5 | Predicate rows from manifest; IRI→key map in release |
| S0005 AC2 | 5 | `sys` unchanged; unknown key and uninstalled ref → `PREDICATE_UNREGISTERED`; other-tenant install not visible |
| S0005 AC3 | 5 | Same slot across @1/@2; major change requires semantic_change |
| S0005 AC4 | 5 | ETERNAL/EVENT/STATE commits and mismatches on PostgreSQL; no DDL in 0017 for canonical_fact_version |
| S0005 AC5 | 5 | Legacy inventory document and G0 query |
| S0005 AC6 | 5 | Existing slot resolves recorded ref after a new activation; authorization/audit unchanged |
| S0006 AC1 | 6 | Change classification fixtures; unclassified → incomplete |
| S0006 AC2 | 6 | EX-ONT-003 entailment added; bound exceeded → unresolved |
| S0006 AC3 | 6 | EX-ONT-004 constraint tightening with unchanged closure |
| S0006 AC4 | 6 | Reach counts with denominators; unexamined list non-empty |
| S0006 AC5 | 6 | Each activation refusal reason; first release report has null predecessor |
| S0006 AC6 | 6 | Selection history query; existing rows unchanged after activate/rollback |
| S0006 AC7 | 6 | Split scenario end to end |
| S0007 AC1 | 7 | ADR-0045 case log |
| S0007 AC2 | 3, 7 | Isomorphism and entailment output |
| S0007 AC3 | 7 | F0011 conformance results |
| S0007 AC4 | 4, 7 | Upgrade checksums, full suite, downgrade refusal |
| S0007 AC5 | 7 | Coverage report; zero parse/model counters |
| S0007 AC6 | 7 | examples/README.md entries; ADR evidence notes |

## Scope Breakdown and Handoffs

- **F0013:** GL and insurance-core modules (Policy, PolicyTerm, Submission, Program, links); GL predicates; narrows `role-assignment.coverage-part`; proves EX-PC-016/018/019/020; maps legacy `limit` slots.
- **F0015:** fills manifest `artifact_slots`. **F0016:** stores `release_ref` on interpretation runs and passes it to `prepare`.
- **F0017/F0018:** execute the four `canonical-admission` constraints across KBs and time.
- **F0010:** correction of ETERNAL values (today `ETERNAL_CONFLICT`).
- **F0034:** consumes `projection-mapping.json`. **F0030/F0062:** workbench, crosswalks, extra constructs, external reasoners.
- **F0002-successor amendment:** role-based reach. **Data contracts repo:** proposed role codes (operator's cross-repo plan).

## Integration Checkpoints and Completion Criteria

1. After Step 3: committed release locks recompile byte-identically in CI.
2. After Step 4: install/idempotence/immutability pass on PostgreSQL 18; Casbin drift check passes with the new rows.
3. After Step 5: the full F0007/F0008/F0009 suites pass unchanged.
4. After Step 6: activation refusal matrix and rollback history pass.
5. Feature complete: all 46 ACs with observed proof, ≥80% changed-line coverage, security review of the new role/resource.

## Risks and Blockers

| Risk | Mitigation |
|---|---|
| New role `OntologySteward` widens the authorization surface | Grants limited to `ontology_release`; security review required; no existing role changes |
| Reach counts could leak cross-scope data | Counts run under tenant/KB authorization only; integration test with two tenants |
| `prepare` forgotten by a future caller → spurious `PREDICATE_UNREGISTERED` | Fail closed by design; registry raises a typed `REGISTRY_NOT_PREPARED` in tests when a non-`sys` key is resolved without prepare |
| Committed release outputs drift from source | CI `compile --check` byte comparison |
| Proposed PartyRoleTypeCode values change in the data contracts | Codes carry explicit `proposed` status; a later release reclassifies with `rename_alias` or `semantic_change` |
| Migration number collision with F0010/F0021 lanes | Rebase at G0 |
| Migration design SQL not machine-parsed at plan (pglast unavailable locally) | The feature run's real migration on PostgreSQL 18 is the proof; G0 re-reviews the DDL |

## DI Registration / Runtime Deployment

`brain_api.deps` composes `ReleasePredicateRegistry(static=production_registry(), store=OntologyReleaseStore)`. The CLI builds the same store and `AuthorizationExecution` from the existing configuration (`config/local.yaml`); no new environment variable, secret, container or deployable. Operators run `python -m brain_ontology.cli` from the engine environment.

## Planning Status and Follow-ups

Phase B approved 2026-11-25 (`approve-phase-b`); no implementation. Proposed ADR-0081 records the design; ADR-0045/0070 remain Proposed. Plan-review precedes the feature action. G0 must: rebase the migration number, fill `source_sha256_at_design`, re-run the legacy slot-type query, and confirm whether the temporal reason enumeration is schema-closed.
