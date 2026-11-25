# F0009 — Provenance + human-correction lineage

**Feature ID:** F0009
**Feature Name:** Provenance + human-correction lineage
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Phase A approved 2026-11-24; Phase B approved 2026-11-24 by operator token `approve-phase-b`; implemented and closed 2026-11-25 in feature run `2026-11-24-08701e37` (Done / Archived)
**Plan Run:** `2026-11-24-bfdbbf04` (A+B, new)

## Feature Statement

**As a** business reviewer and persistence engineer
**I want** a stored explanation linking a source claim, human correction and exact accepted version without rewriting their history
**So that** “why do we believe this?” and “who corrected it on which evidence?” have attributable answers under current access rights.

## Business Objective

- Goal: make mandatory provenance and additive human correction consumable over the shipped kernel (master blueprint §§17, 75; ADR-0010/0037).
- Baseline: the pilot already stores evidence, decisions and corrected assertions; F0006 supplies v2 semantics/ancestry checks; F0008 supplies close-only versions, split links and ending evidence. There is no dedicated consumer lineage contract or reserved learning reference.
- Target: all 41 ACs across six stories have observed evidence in the later feature run; zero original-source rewrites, unauthorized lineage disclosures, duplicate correction effects or automatic learning/dataset changes.

## Problem Statement

Evidence is distributed across assertions, immutable artifacts, review decisions and bitemporal versions. A correction does not itself accept a fact, and an unchanged remainder is not a newly extracted claim. Consumers need those distinctions preserved rather than a flattened list of current values or pointers that imply a complete explanation when evidence is missing.

## Scope & Boundaries

**In Scope (MVP):**

1. An authorized internal explanation of one assertion or exact canonical version, using persisted evidence/interpretation metadata and explicit completeness.
2. Durable original-to-corrected assertion and review-decision lineage, verified reviewer identity, evidence seen, replay/stale/concurrent outcomes and transactional audit. Existing v2 corrections stay v2.
3. Read-only consumption of `split_of_version_id`, `canonical_fact_change`, supporting/ending evidence and exact temporal metadata. RELATIONSHIP slots use the shipped version table too.
4. Current authority across the complete returned lineage, including correction ancestors, predecessor attestation sources and ending sources; non-disclosing refusal for any inaccessible required resource.
5. One reserved LearningCandidate reference for each new effective CORRECT, in the same transaction. This is the §88 hook, with no learning behavior.
6. Additive compatibility/rollback, F0011 offline contract integration and reproducible synthetic development examples with later PostgreSQL proof.

**Out of Scope / Future owners:**

- F0010: change/retraction vocabulary and the PRESENT-to-missing retraction exception. F0009 must not amend ADR-0078's current guard.
- F0018: full evidence/source-authority enforcement for every canonical commit, review-to-canonical orchestration, derivation dependency tables, RLS and production database-role remediation. F0009 consumes existing stored commits and never commits from a review submission.
- F0020: new provenance/history/temporal HTTP/query surfaces. F0022/F0023: new Review Panel, Document 360 or Entity 360 displays and interactions.
- F0016: new interpretation metadata/time/date producers; no metadata is fabricated for an undelivered producer.
- F0041/F0042/F0056: learning, scoring, promotion and automatic derivation invalidation. F0026: governed Golden Corpus workflow and frozen evaluation. A reserved reference changes none of those datasets.
- New roles, grants, deployables, external broker/MGA access, reparse, extraction activation, W3C/OOXML evidence-locator expansion or production rollout.

## Personas

See [personas.md](personas.md). Rosa needs attributable corrections and honest evidence; Ingrid needs durable lineage and unchanged history; Mateo supplies qualified interpretation metadata. These reuse existing personas and create no access roles.

## Acceptance Criteria Overview

- Explain an exact assertion/version with its actual stored context; distinguish absent/incomplete/legacy metadata and direct evidence versus a derivation reference.
- Append effective corrections with the exact decision and evidence seen, preserve original rows, and make replay/stale/competing outcomes auditable without canonical effects.
- Preserve the different meanings of assertion correction, canonical replacement and temporal remainder links; distinguish supporting evidence from `ending_refs`.
- Authorize every required source under current grants and refuse the whole explanation without exposing hidden identities/content when any required source is inaccessible.
- Persist exactly one future-learning reference per new effective correction, with zero learning jobs or dataset effects.
- Prove compatibility and rollback over PostgreSQL, use F0011 contract delivery, and retain at least 80% changed-code coverage in implementation.

The [acceptance checklist](acceptance-criteria-checklist.md) indexes every AC and the required later evidence.

## UX / Screens

No new or materially changed screen. The existing review decision entry point gains durable lineage/reservation behavior; the lineage reader is an internal consumer boundary. F0020 owns new HTTP/history exposure and F0022/F0023 own UI. Existing review route behavior is regression-tested. Each mutation story specifies its entry, current authority, non-applying states, transaction result and fresh-query proof.

## Screen Layouts (ASCII)

No UI — this feature defines internal provenance reads and append-only persistence at existing review/commit boundaries. No screen, zone or new user editing flow is introduced, so Desktop/narrow layouts do not apply.

## Data Requirements

- Exact assertion/version/slot identity and structural tenant/KB ownership.
- Source document/version/artifact, evidence IDs and stored locators, declared precision/text origin, hashes and available producing parser/run/profile/ontology/contract/model/prompt versions. “Unavailable” is not “verified.”
- Decision/item/batch identity; verified reviewer and time; action/reason/comment and submitted revision/value/evidence as applicable; original/created assertion links and applied/stale/duplicate outcomes.
- Stored version valid/recorded coordinates, `split_of_version_id`, canonical change endpoints/reason/actor/time, supporting refs and `ending_refs`. No inferred current replacement for historical data.
- A reserved LearningCandidate identity attached to the exact effective correction, without asserting a processed candidate exists.
- Existing derivation/input-version references when supplied; explicit unsupported/incomplete status when no producer has delivered them. No derivation execution is required here.

Physical storage, bounded traversal, error/result schemas, consumer wiring and safe migrations are Phase B decisions. Existing F0011 schema delivery applies to any new or changed payload.

## Role-Based Access

| Principal / existing role | Read lineage | Submit correction | Canonical acceptance |
|---|---|---|---|
| TenantMember | Only when root and every linked resource have current scoped read authority | No review annotation grant | No commit grant |
| Reviewer | Only with the same current scoped read requirements | Existing `review:annotate` authority, verified session principal; stale/blocked/replay rules apply | Review grants never confer commit authority |
| ServicePrincipal | Explicit current scoped read grants only | Only an existing explicit grant, never inferred from principal type | Existing explicit `fact_slot:commit` grant only; orchestration stays F0018 |
| Unverified, nonmember, cross-tenant/KB, external broker/MGA | No access introduced | No access introduced | No access introduced |

Parent/classification restrictions remain conjunctive. Any inaccessible required lineage resource refuses the whole explanation, consistently with the shipped kernel's non-disclosure behavior. Authorization/decision audit remains correlated and contains no copied protected excerpts. Historical coordinates never restore revoked access.

## Success Criteria

All 41 ACs pass with later observed evidence. Zero original artifact/assertion rewrites, temporal lineage reinterpretations, unauthorized payloads, duplicate reservation effects or learning/holdout changes. PostgreSQL proves atomic rollback, concurrency and migration behavior. At least 80% changed executable-code coverage. Latency is measured during implementation; this PRD invents no service-level budget.

## Risks & Assumptions

- **A1 — bounded foundation:** F0009 exposes an internal lineage contract and uses existing routes only. New public history/provenance surfaces and UI remain with F0020/F0022/F0023.
- **A2 — reservation semantics:** “human correction” means a new effective non-stale CORRECT producing a child assertion. Reserve one future candidate identity per such decision; ACCEPT/REJECT/BLOCKED/stale/losing submissions and historical rows get none. This minimal interpretation of the §88 hook was approved at Phase A.
- **A3 — honesty before completeness:** preserve metadata actually produced. Legacy/undelivered derivation and interpretation provenance is explicitly incomplete; F0009 does not silently expand F0016/F0018 delivery.
- Accepted ADR-0010/0037/0044/0077/0078 govern the bounded contract. ADR-0058's accepted PDF BoxSelector amendment applies; its broader W3C selectors remain future work. Proposed ADR-0075/0079 remain Proposed despite shipped contracts.
- Current already-decided/stale code does not retain every submitted detail named by ADR-0044. S0002 requires durable attributed non-applied outcomes, with the minimal reconciliation documented by the Architect; it does not create a new adjudication policy.
- The application database role currently has elevated privileges (F0018 handoff). Authority tests cannot rely on future RLS; application checks and structural constraints must both hold.
- The approved assembly plan settles: internal reader shape and caller; completeness/failure taxonomy and traversal limits; reserved-reference storage/identity and future adoption; race/rollback behavior; contract inventory; additive migrations and downgrade refusal; AC-to-step proof mapping. These are technical design decisions, not unresolved insurance business rules.

## Dependencies

Direct feature dependencies already recorded: [F0006](../F0006-assertion-plane-origin-and-interpretation-basis/README.md) and [F0008](../F0008-bitemporal-canonical-facts/README.md). The existing F0002/F0004/F0007 kernel supplies authority, content evidence and slot identity. Shipped [F0011](../F0011-json-schema-contract-system/README.md) is a contract-system carry-in; the Architect binds it as a technical dependency when designing payloads.

Direct/impacted dependency evidence and audit-pending notes are in the run's [artifact trace](../../../operations/evidence/runs/2026-11-24-bfdbbf04/artifact-trace.md). Future consumers F0010/F0018/F0020/F0022/F0023/F0026/F0041/F0065 do not become delivery prerequisites for this bounded foundation.

## Related Stories

| Story | Outcome | ACs |
|---|---|---|
| [F0009-S0001](F0009-S0001-reconstruct-source-provenance.md) | Reconstruct source provenance | 7 |
| [F0009-S0002](F0009-S0002-append-auditable-human-corrections.md) | Append auditable human corrections | 8 |
| [F0009-S0003](F0009-S0003-trace-temporal-version-lineage.md) | Trace temporal version lineage | 7 |
| [F0009-S0004](F0009-S0004-enforce-current-authority-across-lineage.md) | Enforce current authority across lineage | 7 |
| [F0009-S0005](F0009-S0005-reserve-learning-candidate-reference.md) | Reserve a learning-candidate reference | 6 |
| [F0009-S0006](F0009-S0006-prove-compatible-lineage-delivery.md) | Prove compatible lineage delivery | 6 |

## Rollout & Enablement

No implementation or rollout is authorized by this planning checkpoint. The Architect authored the approved assembly plan, contracts/proposed ADR and KG bindings after Phase A approval. A separate plan-review precedes the feature action. The feature action supplies runtime evidence, required signoffs and completion approval.

## Sources

[BLUEPRINT](../../../BLUEPRINT.md) §§0–4.17; [master blueprint](../../../architecture/master-blueprint.md) §§17, 75, 88, 96, 106.3, 111.2, 125; the dated amendments in [README](README.md); [ADR-0010](../../../architecture/decisions/ADR-0010-provenance-is-mandatory.md), [ADR-0037](../../../architecture/decisions/ADR-0037-human-corrections-append-they-do-not-rewrite-evidence.md), [ADR-0044](../../../architecture/decisions/ADR-0044-review-surface-and-approval-contract.md), [ADR-0077](../../../architecture/decisions/ADR-0077-factslot-identity-and-typed-answer-carriers.md), [ADR-0078](../../../architecture/decisions/ADR-0078-bitemporal-version-contract-and-close-only-immutability.md). These define system behavior; no external insurance/regulatory authority is asserted.

## Architecture Traceability

The [assembly plan](feature-assembly-plan.md) maps all 41 approved ACs to five implementation steps. Proposed [ADR-0080](../../../architecture/decisions/ADR-0080-bounded-provenance-and-correction-reservations.md) selects an internal metadata-first reader, two append-only hook tables, a nullable server-owned new-decision marker and current-authority source closure. Existing HTTP envelopes and canonical mutation rules stay intact. This is architecture traceability, not a change to the approved requirements. F0011 supplies the installed contract pipeline; four new design schemas and their explicit consumers are in [contract-inventory.yaml](contract-inventory.yaml).
