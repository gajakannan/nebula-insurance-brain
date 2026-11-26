# F0012 — Foundation ontology — Status

**Overall Status:** Planned — Phase A and Phase B approved; awaiting plan-review
**Last Updated:** 2026-11-25
**Plan Run:** `2026-11-25-120320e9` (A+B, new)
**Phase A:** Approved 2026-11-25 — operator token `approve-phase-a`
**Phase B:** Approved 2026-11-25 — operator token `approve-phase-b`; G5 journal/manifest records post-approval validation/publication ([assembly plan](feature-assembly-plan.md), proposed [ADR-0081](../../architecture/decisions/ADR-0081-foundation-ontology-authoring-and-release-runtime.md))
**Feature Run:** Not started
**Implementation:** Not started; no runtime proof is claimed

## Story Checklist

| Story | Title | Status |
|---|---|---|
| F0012-S0001 | [Validate foundation module authoring](F0012-S0001-validate-foundation-module-authoring.md) | Not Started |
| F0012-S0002 | [Assign stable term identities](F0012-S0002-assign-stable-term-identities.md) | Not Started |
| F0012-S0003 | [Model parties, accounts and scoped roles](F0012-S0003-model-parties-accounts-and-scoped-roles.md) | Not Started |
| F0012-S0004 | [Compile and install immutable releases](F0012-S0004-compile-and-install-immutable-releases.md) | Not Started |
| F0012-S0005 | [Register predicates and activate temporal kinds](F0012-S0005-register-predicates-and-activate-temporal-kinds.md) | Not Started |
| F0012-S0006 | [Gate activation with an impact report](F0012-S0006-gate-activation-with-impact-report.md) | Not Started |
| F0012-S0007 | [Prove reproducible release delivery](F0012-S0007-prove-reproducible-release-delivery.md) | Not Started |

## Backend Progress

- [ ] Authoring schema and offline validation with explicit construct support.
- [ ] Stable identity, change records and tenant-namespace refusal.
- [ ] Foundation vocabulary with ADR-0070 terms and constraints.
- [ ] Deterministic compile, immutable release records and audited install.
- [ ] Release-backed predicate registry and ETERNAL/EVENT activation.
- [ ] Impact report, reviewed activation and rollback.

## Frontend / AI Progress

N/A — no new UI, model calls, parsing or extraction producer.

## Cross-Cutting

- [ ] Real PostgreSQL proof of atomic install, immutability, concurrency and selection history.
- [ ] F0011 contract inventory and conformance for new payloads.
- [ ] RDF/JSON-LD interchange round trip and `semantic_rdf` gate.
- [ ] At least 80% changed executable-code coverage and exact AC evidence.

## Required Role Matrix

Architect set the matrix below for a runtime-bearing, security-sensitive feature (new role, resource type, migration). No runtime signoff has occurred.

| Role | Required | Why Required | Set By | Date |
|---|---|---|---|---|
| Quality Engineer | Yes | All 46 ACs, PostgreSQL install/activation/temporal proof, coverage | Architect | 2026-11-25 |
| Code Reviewer | Yes | Compiler determinism, registry and commit-path regression review | Architect | 2026-11-25 |
| Security Reviewer | Yes | New `OntologySteward` role, `ontology_release` grants, scoped reach counts | Architect | 2026-11-25 |
| DevOps | Yes | Migration 0017, downgrade refusal, CI recompile check | Architect | 2026-11-25 |
| Architect | Yes | Shared ontology semantics, ADR-0081/0045/0070 proof gates, KG bindings | Architect | 2026-11-25 |

## Story Signoff Provenance

Append-only. Populated by the feature action.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|

## Deferred Scope / Handoffs

F0013 owns insurance-core/GL vocabulary and the policy-dependent Cedar Bridge cases; F0014/F0015 own profile and template artifacts; F0016 pins interpretation runs; F0017/F0018 own identity resolution and admission enforcement; the F0002-successor amendment owns role-based access; F0030/F0062 own workbench and extended reasoning. See [PRD](PRD.md#scope--boundaries).

## Tracker Sync Checklist

- [x] REGISTRY/ROADMAP retained at Planned / Now; generated regions untouched by PM.
- [x] STORY-INDEX regenerated after adding the seven stories.
- [x] BLUEPRINT §3 links the feature and the approved requirements.
- [x] Story and tracker validators pass before G2.
- [x] Architect completes the KG source bindings and passes G4 compile/drift validation.
- [x] Explicit G3 and G5 operator approval tokens recorded.
