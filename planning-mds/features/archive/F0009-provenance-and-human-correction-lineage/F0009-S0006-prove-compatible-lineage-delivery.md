# F0009-S0006 — Prove compatible lineage delivery

**Story ID:** F0009-S0006
**Feature:** F0009 — Provenance + human-correction lineage
**Title:** Prove compatible lineage delivery
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Done

## User Story

**As a** persistence engineer (Ingrid)
**I want** the lineage contract to survive deployment and remain reproducible on existing records
**So that** new explanations do not corrupt pilot history or claim that synthetic examples prove production readiness.

## Context & Background

F0006/F0007/F0008 preserve explicitly qualified legacy records, and F0011 supplies the installed offline contract system. New provenance contracts must integrate with that shipped system rather than creating another validator path.

## Acceptance Criteria

- [x] **AC1:** An additive upgrade preserves seeded legacy assertions, evidence, review decisions, canonical versions, changes and ownership byte-for-byte except explicitly documented new nullable/defaulted metadata. Legacy incomplete provenance stays labelled incomplete; no fabricated evidence, identity-v1 slot, candidate or precision is backfilled.
- [x] **AC2:** Downgrade/re-upgrade is proven on PostgreSQL with legacy data. Once new lineage or reservation data would be lost, a guarded downgrade is rejected before destructive effects; Phase B states the exact deployment and rollback procedure.
- [x] **AC3:** Every introduced/changed public or internal payload contract is inventoried with its producer, consumer and offline bundle identity under F0011. JSON Schema, generated Pydantic and AJV conformance are required where the payload crosses those consumer boundaries; native domain/authorization guards retain their ordering.
- [x] **AC4:** The existing review batch/decision, fact read and canonical commit routes retain their shipped envelopes and behavior except additive changes explicitly approved in Phase B. The feature adds no route, grant, deployable, parse or extraction activation.
- [x] **AC5:** The later feature run executes the independently authored EX-PROV-001–005 expectations against real PostgreSQL, compares actual IDs/edges/outcomes with expected results and records reproduction commands. Synthetic development examples remain separate from the frozen holdout, and rollback/denial cases include durable audit evidence.
- [x] **AC6:** Every story AC has observed runtime evidence before feature completion, the changed executable code has at least 80% coverage and required reviews pass. This planning run contains no runtime-pass claim, feature-completion approval or role-signoff evidence.

## Edge Cases & Error Scenarios

Legacy incomplete rows remain qualified (AC1). A downgrade that would lose new lineage refuses before destructive effects (AC2); failure/denial proof includes durable audit (AC5).

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Operator Alembic upgrade/downgrade of migration 0016 (assembly plan Step 2) | Quiesce review writers, then run `alembic upgrade` or a guarded `alembic downgrade` | Schema only; no existing row is rewritten or backfilled | Upgrade adds the two append-only tables, triggers and the nullable decision marker in one transaction; downgrade refuses before any drop when either new table has rows | Compare legacy row snapshots before and after; record empty down/up and populated-refusal logs | Deployment authority only; no new runtime permission, grant or route |

No new screen is introduced. Validation/authorization failure cannot report a successful mutation. Existing error envelopes remain; Phase B specifies any added failure categories. Persistence and audit evidence are mandatory; render-only behavior cannot satisfy this story.

## Data Requirements

Legacy and modern fixtures; contract/consumer inventory; migration/rollback state; PostgreSQL reproduction results and coverage in the later feature evidence package.

Required fields and referential constraints are enforced before effects. Optional legacy metadata stays absent/qualified rather than invented. Persisted source text is not copied into denial output.

## Role-Based Visibility

Use the [PRD role matrix](PRD.md#role-based-access). TenantMember has only scoped read authority; Reviewer adds existing review annotation without canonical commit; ServicePrincipal uses its explicit scoped grants. Unverified, nonmember, cross-tenant/KB and external broker/MGA callers obtain no access. Current parent/classification restrictions apply to each source. Engineering personas confer no runtime role.

## Non-Functional Expectations

Zero unauthorized payload disclosure or partial mutation; zero source reparse/model calls. At least 80% changed executable-code coverage in the later feature run. PostgreSQL proves durable behavior and concurrency where applicable. No unmeasured latency target is asserted. Use existing authorization/decision audit and correlation fields.

## Dependencies

S0001–S0005; shipped F0011 offline schema pipeline; F0006/F0008 legacy fixtures and F0007 identity compatibility.

## Out of Scope

Production rollout, untrusted-document qualification, broad dependency remediation, repo-wide feature-evidence audit, independent frozen evaluation.

## Questions & Assumptions

No open business-rule question is introduced. The [PRD assumptions](PRD.md#risks--assumptions) require Phase A review; storage, limits, contracts and rollback are explicit Architect decisions for Phase B. Requirements do not grant formal acceptance to a Proposed ADR.

## Definition of Done

- [x] Every AC above has a concrete observed proof in the later feature run.
- [x] PostgreSQL seeded upgrade/downgrade/re-upgrade, loss guard, old-route regressions, scoped contract checks and an observed AC-to-evidence matrix in the later feature run.
- [x] Error scenarios, permission checks and audit/persistence expectations pass.
- [x] Documentation and tracker state reflect observed results.
- [x] Required story-level review provenance is appended to STATUS.md in the feature action.

## Review Provenance

Planning only. No runtime signoff is claimed. The Architect sets the required role matrix in [STATUS.md](STATUS.md) during Phase B; the feature action supplies actual evidence.
