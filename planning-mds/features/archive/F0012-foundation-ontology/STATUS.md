# F0012 — Foundation ontology — Status

**Overall Status:** Done / Archived 2026-11-26 — feature run `2026-11-26-54387a08` (G0–G8)
**Last Updated:** 2026-11-26
**Plan Run:** `2026-11-25-120320e9` (A+B, new)
**Phase A:** Approved 2026-11-25 — operator token `approve-phase-a`
**Phase B:** Approved 2026-11-25 — operator token `approve-phase-b`; G5 journal/manifest records post-approval validation/publication ([assembly plan](feature-assembly-plan.md), proposed [ADR-0081](../../../architecture/decisions/ADR-0081-foundation-ontology-authoring-and-release-runtime.md))
**Feature Run:** `2026-11-26-54387a08` started 2026-11-26 (mode clean); G0 reconciliation in the [assembly plan](feature-assembly-plan.md#g0-reconciliation--feature-run-2026-11-26-54387a08)
**Implementation:** Complete; 46/46 ACs with observed proof in run `2026-11-26-54387a08`

## Story Checklist

| Story | Title | Status |
|---|---|---|
| F0012-S0001 | [Validate foundation module authoring](F0012-S0001-validate-foundation-module-authoring.md) | Done |
| F0012-S0002 | [Assign stable term identities](F0012-S0002-assign-stable-term-identities.md) | Done |
| F0012-S0003 | [Model parties, accounts and scoped roles](F0012-S0003-model-parties-accounts-and-scoped-roles.md) | Done |
| F0012-S0004 | [Compile and install immutable releases](F0012-S0004-compile-and-install-immutable-releases.md) | Done |
| F0012-S0005 | [Register predicates and activate temporal kinds](F0012-S0005-register-predicates-and-activate-temporal-kinds.md) | Done |
| F0012-S0006 | [Gate activation with an impact report](F0012-S0006-gate-activation-with-impact-report.md) | Done |
| F0012-S0007 | [Prove reproducible release delivery](F0012-S0007-prove-reproducible-release-delivery.md) | Done |

## Story × Role Progress

Feature run `2026-11-26-54387a08`. Cells: not-started / in-progress / done / not-in-scope; review columns resolve to PASS/FAIL. No UI or AI/model scope (generated contract copies under `experience/` only). G2 2026-11-26: Backend, QA and DevOps done. G3 2026-11-26: Code Review PASS (approved with recommendations), Security PASS. G8 2026-11-26: Overall Done.

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|---|---|---|---|---|---|---|---|---|
| F0012-S0001 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | Done |
| F0012-S0002 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | Done |
| F0012-S0003 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | Done |
| F0012-S0004 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | Done |
| F0012-S0005 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | Done |
| F0012-S0006 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | Done |
| F0012-S0007 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | Done |

## Backend Progress

- [x] Authoring schema and offline validation with explicit construct support.
- [x] Stable identity, change records and tenant-namespace refusal.
- [x] Foundation vocabulary with ADR-0070 terms and constraints.
- [x] Deterministic compile, immutable release records and audited install.
- [x] Release-backed predicate registry and ETERNAL/EVENT activation.
- [x] Impact report, reviewed activation and rollback.

## Frontend / AI Progress

N/A — no new UI, model calls, parsing or extraction producer.

## Cross-Cutting

- [x] Real PostgreSQL proof of atomic install, immutability, concurrency and selection history.
- [x] F0011 contract inventory and conformance for new payloads.
- [x] RDF/JSON-LD interchange round trip and `semantic_rdf` gate.
- [x] At least 80% changed executable-code coverage and exact AC evidence (95.61%).

## Required Role Matrix

Architect set the matrix below for a runtime-bearing, security-sensitive feature (new role, resource type, migration). It was reconfirmed at feature G0 on 2026-11-26. No runtime signoff has occurred.

| Role | Required | Why Required | Set By | Date |
|---|---|---|---|---|
| Quality Engineer | Yes | All 46 ACs, PostgreSQL install/activation/temporal proof, coverage | Architect | 2026-11-25 |
| Code Reviewer | Yes | Compiler determinism, registry and commit-path regression review | Architect | 2026-11-25 |
| Security Reviewer | Yes | New `OntologySteward` role, `ontology_release` grants, scoped reach counts | Architect | 2026-11-25 |
| DevOps | Yes | Migration 0017, downgrade refusal, CI recompile check | Architect | 2026-11-25 |
| Architect | Yes | Shared ontology semantics, ADR-0081/0045/0070 proof gates, KG bindings | Architect | 2026-11-25 |

## Story Signoff Provenance

Append-only. Recorded at G5 of feature run `2026-11-26-54387a08`.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|
| F0012-S0001 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/test-execution-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0001 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/code-review-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0001 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/security-review-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0001 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/deployability-check.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0001 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/architect-implementation-review.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0002 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/test-execution-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0002 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/code-review-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0002 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/security-review-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0002 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/deployability-check.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0002 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/architect-implementation-review.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0003 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/test-execution-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0003 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/code-review-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0003 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/security-review-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0003 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/deployability-check.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0003 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/architect-implementation-review.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0004 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/test-execution-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0004 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/code-review-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0004 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/security-review-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0004 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/deployability-check.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0004 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/architect-implementation-review.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0005 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/test-execution-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0005 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/code-review-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0005 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/security-review-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0005 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/deployability-check.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0005 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/architect-implementation-review.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0006 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/test-execution-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0006 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/code-review-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0006 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/security-review-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0006 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/deployability-check.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0006 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/architect-implementation-review.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0007 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/test-execution-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0007 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/code-review-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0007 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/security-review-report.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0007 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/deployability-check.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |
| F0012-S0007 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-26-54387a08/architect-implementation-review.md` | 2026-11-26 | PM verified the role evidence after the G4 operator approval |

## Deferred Scope / Handoffs

F0013 owns insurance-core/GL vocabulary and the policy-dependent Cedar Bridge cases; F0014/F0015 own profile and template artifacts; F0016 pins interpretation runs; F0017/F0018 own identity resolution and admission enforcement; the F0002-successor amendment owns role-based access; F0030/F0062 own workbench and extended reasoning. See [PRD](PRD.md#scope--boundaries).

## Tracker Sync Checklist

- [x] REGISTRY/ROADMAP retained at Planned / Now; generated regions untouched by PM.
- [x] STORY-INDEX regenerated after adding the seven stories.
- [x] BLUEPRINT §3 links the feature and the approved requirements.
- [x] Story and tracker validators pass before G2.
- [x] Architect completes the KG source bindings and passes G4 compile/drift validation.
- [x] Explicit G3 and G5 operator approval tokens recorded.
- [x] G8 closeout (run `2026-11-26-54387a08`): feature archived, shard `archived-done`, REGISTRY/ROADMAP regenerated, BLUEPRINT, umbrella plan and STORY-INDEX updated.

## Closeout Summary

Done 2026-11-26 in feature run `2026-11-26-54387a08`. Seven stories and 46 ACs, with all five required roles signed. Two low code-review recommendations and three low security findings were accepted as deferred (pm-closeout.md). ADR-0081, ADR-0045 and ADR-0070 stay Proposed; acceptance is a separate operator decision.
