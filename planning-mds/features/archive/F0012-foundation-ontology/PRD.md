# F0012 — Foundation ontology

**Feature ID:** F0012
**Feature Name:** Foundation ontology
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Phase A approved 2026-11-25 by operator token `approve-phase-a`; Phase B approved 2026-11-25 by operator token `approve-phase-b`; implemented and Done in feature run `2026-11-26-54387a08` (archived 2026-11-26)
**Plan Run:** `2026-11-25-120320e9` (A+B, new)

## Feature Statement

**As a** domain steward and persistence engineer
**I want** a validated, versioned foundation ontology module with stable term identities, explicit semantics and immutable, reviewed releases
**So that** every insurance module, predicate contract and interpretation can pin exact meaning, and a change to that meaning is classified and reviewed before new work uses it.

## Business Objective

- **Goal:** deliver the foundation module (master blueprint §§19–22, 67, 112) and the release contract that F0013, F0014, F0015 and F0016 build on, proving the F0012 share of proposed [ADR-0045](../../../architecture/decisions/ADR-0045-ontology-release-compatibility.md) and the vocabulary half of proposed [ADR-0070](../../../architecture/decisions/ADR-0070-account-party-and-role-model.md).
- **Baseline:** no `ontology/` tree, authoring schema, compiler or release record exists. The predicate registry serves only the four `sys` name predicates; every other namespace is `PREDICATE_UNREGISTERED` (ADR-0077 D2). `temporal_kind` is reserved but only `STATE` is written (ADR-0078 D10). The ontology and Cedar Bridge examples use an illustrative namespace and are not production contracts.
- **Target:** all 46 ACs across seven stories have observed evidence in the later feature run. Zero reassigned IRIs, mutated published releases, floating dependencies, silently approximated constructs or activations without a reviewed impact report.

## Problem Statement

Downstream features cannot author GL vocabulary, compile extraction profiles or pin interpretation runs without a stable identity scheme and an immutable release to pin. The master blueprint leaves the authoring shape inconsistent (§20 `parents:` vs §82 `parent:`), does not separate inference from validation, and gives no executable rule for how a change to meaning is detected before activation. The account/party/role direction in ADR-0070 also needs production vocabulary before Entity 360, identity resolution and role-based access can rely on it.

## Scope & Boundaries

**In Scope (MVP):**

1. A versioned authoring schema for ontology module files, with explicit inference rules, validation constraints carrying execution context, mandatory definitions/examples/regression cases, language-tagged labels and a declared `temporal_kind` on every property.
2. Stable term identity: deterministic `urn:nebula:ont:` IRIs, collision and reuse rejection, rename/alias handling, explicit change records for semantic change, split, merge and retirement, and a reserved (rejected) tenant-extension namespace.
3. The foundation module: §22 base classes plus the ADR-0070 party, organization, location, employment, account, designated-parent, ownership-interest and scoped role-assignment vocabulary.
4. A deterministic compiler producing an immutable, hashed composed release with exact dependency locks and a projection mapping, installed as append-only records in PostgreSQL.
5. Foundation predicate contracts served by the existing `PredicateContractRegistry` from the installed release, with `ETERNAL` and `EVENT` temporal kinds activated for registered predicates over the existing ADR-0078 D10 shapes.
6. A predecessor-to-candidate release impact report and an activation gate that refuses activation without a reviewed report; audited activation and rollback selections.
7. Reproducible delivery evidence for the F0012-owned ADR-0045 acceptance cases, RDF/OWL interchange round trip and compatibility with the shipped kernel.

**Out of Scope / Future owners:**

- F0013: insurance-core and GL vocabulary, including Policy, PolicyTerm, Submission, Program, the policy/submission-to-account and program links, GL predicates, limits and qualifiers. Cedar Bridge cases that need those terms (EX-PC-016, EX-PC-018, EX-PC-019, EX-PC-020) are proved there.
- F0014/F0015: document profiles, extraction profile/template compilation and their artifacts in the release manifest. F0012 reserves manifest slots for them; it compiles none.
- F0016: interpretation runs that pin a release. F0017: account and organization identity resolution and merge. F0018: canonical-admission enforcement of the tenant-wide one-current-account invariant and source-authority policy.
- F0002-successor scope amendment (ADR-0070 §5): any access reach or decision right derived from role assignments. The vocabulary grants nothing.
- F0030/F0062: ontology workbench, external mapping/crosswalk analysis, logical module extraction, reasoner providers, `symmetric`/`transitive` and any OWL construct beyond the supported subset. F0034: AGE projection writer. F0065: stored assessments and their replay.
- Tenant-extension installation, OKF import/export, an HTTP ontology API, any screen, reparse, model calls or production rollout.

## Personas

See [personas.md](personas.md). Sameer (Domain Steward) owns what a term means and approves releases; Ingrid (Persistence Engineer) needs immutable records, exact locks and safe migrations; Mateo (Document Intelligence Engineer) consumes predicate contracts and pinned releases. These reuse existing personas and create no runtime roles.

## Acceptance Criteria Overview

- An authored module either validates completely or is refused with every error listed; retired fields and unsupported constructs are explicit errors, never ignored.
- Every term has a deterministic, never-reassigned IRI; meaning changes need an explicit change record; tenant namespaces are reserved and refused.
- The foundation module carries the §22 classes and the ADR-0070 vocabulary with temporal kinds, definitions, regression cases and constraint execution context, and the F0012-owned Cedar Bridge cases pass.
- Compilation is deterministic; published module versions and releases are immutable, exactly locked and installed atomically without activation.
- Registered foundation predicates come from the installed release; unregistered keys stay refused; `ETERNAL`/`EVENT` commits work only for predicates that declare them.
- Activation requires a reviewed impact report that separates structural reach, inference change, constraint change and unexamined populations; rollback preserves history.
- F0012-owned ADR-0045 cases, RDF round trip, contract conformance, migration safety and coverage have observed proof.

The [acceptance checklist](acceptance-criteria-checklist.md) indexes every AC and its required later evidence.

## UX / Screens

No new or materially changed screen. Release compilation, installation, impact reporting and activation are operator command-line and service boundaries in v0.1A; the ontology workbench is F0030. Each mutation story names its entry point, authority, refused states, transaction result and fresh-read proof.

## Screen Layouts (ASCII)

No UI — this feature defines authoring files, a compiler, append-only release records, predicate contracts and an operator activation gate. No screen, zone or user editing flow is introduced, so Desktop/narrow layouts do not apply.

## Data Requirements

- **Authoring:** module ID, version and dependencies; terms with dotted IDs, `parents:` lists, language-tagged labels and aliases, definitions, examples, regression cases; properties with domain/range, `temporal_kind`, cardinality and value type where a FactSlot is implied; validation constraints with lifecycle stage, consumer, applicability, severity/action and data basis.
- **Identity:** term IRI, prior-release identity history, change records (class, source IRIs, replacement IRIs, rationale).
- **Release:** module-version digests, composed release ID, dependency lock, authoring-schema and compiler versions, supported-semantics declaration, constraint metadata, projection mapping and digest, reserved slots for profile/template/compiler/validation artifacts, ownership scope, creation actor/time.
- **Activation:** impact report bound to exact predecessor/candidate digests, reviewer identity, decision and time; append-only activation/rollback selections per tenant/KB.
- **Predicates:** predicate key, release reference, cardinality, value type, qualifiers, member-key source, basis requirement and `temporal_kind`, deterministically derived from the release.

Physical tables, key formats, the predicate namespace prefix, the grant names, contract schemas and migrations are Phase B decisions. F0011 offline contract delivery applies to any new payload schema.

## Role-Based Access

| Principal / existing role | Compile / validate (offline) | Install release | Review impact report / activate / roll back | Read release, predicates |
|---|---|---|---|---|
| Operator at the command line (no runtime principal) | Yes — offline files only; no database effect | No, unless acting as a principal with the install grant | No, unless acting as a principal with the activation grant | — |
| ServicePrincipal | No new authority | Only with an explicit new install grant named in Phase B | Only with an explicit new activation grant; never inferred from principal type | Existing scoped read for predicate resolution during commit |
| TenantMember / Reviewer | No | No | No | Scoped read of installed releases and their predicate contracts only if Phase B grants it |
| Unverified, nonmember, cross-tenant/KB, external broker/MGA | No access introduced | No | No | No |

Install and activation decisions are audited with actor, release digest and outcome, including denials. No existing role gains a new grant implicitly. Role assignments in the vocabulary confer no access (EX-PC-011).

## Success Criteria

All 46 ACs pass with later observed evidence. Byte-identical recompilation; zero mutations of published module versions or releases; zero reassigned IRIs; zero activations without a reviewed report; unchanged behavior for the `sys` predicates and existing STATE commits. PostgreSQL proves atomic install, immutability and audited selection. At least 80% changed executable-code coverage. No latency budget is invented; compile and install times are measured and recorded.

## Risks & Assumptions

**Operator decisions at G1 (2026-11-25), recorded in the run's [gate decisions](../../../operations/evidence/runs/2026-11-25-120320e9/gate-decisions.md):**

- **D1 delivery depth:** YAML modules, deterministic offline compile, immutable PostgreSQL release records with audited activation, and the predicate registry served from the installed release.
- **D2 module boundary:** F0012 owns §22 plus the ADR-0070 party/account/ownership/role vocabulary. Policy, PolicyTerm, Submission, Program and policy/program links are F0013.
- **D3 semantics:** inference = `subClassOf`, `subPropertyOf`, `inverseOf`; validation-only = `domain`, `range`, `disjoint`, `minCardinality`, `maxCardinality`; `symmetric`, `transitive` and all other constructs are rejected.
- **D4 namespace:** `urn:nebula:ont:<dotted-id>` for shared terms; `urn:nebula:tenant:<tenant_id>:ont:<dotted-id>` reserved for tenant extensions.
- **D5 tenant extensions:** rules and rejection only; no install path.
- **D6 temporal kind:** declare on every property and activate `ETERNAL`/`EVENT` commits for registered predicates without DDL.
- **D7 impact gate:** full report plus gated activation; populations with no producer are reported as unexamined.
- **D8 authoring shape:** `parents:` (0..n) is canonical; singular `parent:` is rejected with a migration hint.

**PM assumptions for G3 review:**

- **A1 — entry points:** install, impact reporting, review and activation are command-line/service entry points in v0.1A. No HTTP route or screen is added; F0030 owns the workbench.
- **A2 — admission enforcement:** F0012 declares the one-current-account-per-organization-per-tenant invariant and the ownership/parent constraints as constraints with a named consumer (canonical admission). Executing them at canonical admission across knowledge bases and time is F0017/F0018 work; F0012 proves them on example snapshots only.
- **A3 — labels:** labels use BCP 47 tags; each term has exactly one preferred `en-US` label; other languages are optional. Labels and aliases never contribute to identity (master blueprint §67).
- **A4 — Cedar Bridge split:** F0012 proves EX-PC-001, EX-PC-011, EX-PC-015, EX-PC-017 (account-scoped rows) and EX-PC-021 on production foundation IRIs. The policy-dependent cases stay on the illustrative namespace until F0013.
- **A5 — release scope:** the foundation release is authored once and installed per tenant/KB under ADR-0030 ownership; Phase B settles shared-distribution mechanics without bypassing scoped installation.
- Proposed ADR-0045 and ADR-0070 stay Proposed. This feature supplies part of their evidence; acceptance is a separate operator decision.
- The application database role has elevated privileges (F0018 handoff). Immutability must be enforced structurally (triggers/constraints), not only by application code.

## Dependencies

Direct dependency: [F0011](../../archive/F0011-json-schema-contract-system/README.md) (JSON Schema contract system, Done). Kernel carry-ins: F0002 authority and audit, F0007 predicate registry and FactSlot identity (ADR-0077), F0008 temporal contract (ADR-0078). Dependency evidence references and audit-pending notes are in the run's [artifact trace](../../../operations/evidence/runs/2026-11-25-120320e9/artifact-trace.md). Downstream consumers F0013, F0014, F0015, F0016, F0017, F0023, F0030 and F0065 are not prerequisites.

## Related Stories

| Story | Outcome | ACs |
|---|---|---|
| [F0012-S0001](F0012-S0001-validate-foundation-module-authoring.md) | Validate foundation module authoring | 7 |
| [F0012-S0002](F0012-S0002-assign-stable-term-identities.md) | Assign stable term identities | 6 |
| [F0012-S0003](F0012-S0003-model-parties-accounts-and-scoped-roles.md) | Model parties, accounts and scoped roles | 7 |
| [F0012-S0004](F0012-S0004-compile-and-install-immutable-releases.md) | Compile and install immutable releases | 7 |
| [F0012-S0005](F0012-S0005-register-predicates-and-activate-temporal-kinds.md) | Register predicates and activate temporal kinds | 6 |
| [F0012-S0006](F0012-S0006-gate-activation-with-impact-report.md) | Gate activation with an impact report | 7 |
| [F0012-S0007](F0012-S0007-prove-reproducible-release-delivery.md) | Prove reproducible release delivery | 6 |

## Rollout & Enablement

No implementation or rollout is authorized by this planning checkpoint. The Architect authors the assembly plan, contracts, ADR and KG bindings after Phase A approval. A separate plan-review precedes the feature action, which supplies runtime evidence, signoffs and completion approval.

## Sources

[BLUEPRINT](../../../BLUEPRINT.md) §§0–4.18; [master blueprint](../../../architecture/master-blueprint.md) §§13, 14, 19–22, 67, 79, 82, 106.3, 112; the dated amendments in [README](README.md); [ontology planning handoff](../../../architecture/ontology-planning-handoff.md); [commercial P&C handoff](../../../architecture/commercial-pc-example-handoff.md); [ADR-0011](../../../architecture/decisions/ADR-0011-ontology-is-versioned-and-modular.md), [ADR-0012](../../../architecture/decisions/ADR-0012-flexible-authoring-normalized-runtime.md), [ADR-0045](../../../architecture/decisions/ADR-0045-ontology-release-compatibility.md), [ADR-0063](../../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0064](../../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md), [ADR-0070](../../../architecture/decisions/ADR-0070-account-party-and-role-model.md), [ADR-0077](../../../architecture/decisions/ADR-0077-factslot-identity-and-typed-answer-carriers.md), [ADR-0078](../../../architecture/decisions/ADR-0078-bitemporal-version-contract-and-close-only-immutability.md); [release contract examples](../../../examples/ontology-release-contracts.md); [Cedar Bridge cases](../../../examples/commercial-pc-account/cases.md). No external insurance or regulatory authority is asserted.
