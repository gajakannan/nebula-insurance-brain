# F0009-S0004 — Enforce current authority across lineage

**Story ID:** F0009-S0004
**Feature:** F0009 — Provenance + human-correction lineage
**Title:** Enforce current authority across lineage
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Done

## User Story

**As a** business reviewer (Rosa)
**I want** to receive explanations only from the resources my current grants allow me to inspect
**So that** historical lineage cannot restore revoked access or expose another tenant’s evidence.

## Context & Background

F0002 scope conjunction and F0007/F0008 security remediation apply to lineage too. In particular F0008 second remediation refuses an entire commit response when predecessor attestation evidence is unreadable.

## Acceptance Criteria

- [x] **AC1:** Before materializing an explanation, the boundary verifies current root access and discovers the ownership/access requirements of every traversed assertion, correction ancestor, review record, canonical version, supporting source, ending source and attestation source. It authorizes those requirements before returning protected content.
- [x] **AC2:** A cross-tenant or cross-KB root or linked resource, or one required source denied by current grants, refuses the whole explanation with the existing non-disclosing not-found outcome. No partial values, excerpts, hidden identities, topology, counts or denial details are returned.
- [x] **AC3:** A principal retaining root fact access but losing one ancestor, ending or attestation source grant receives the same refusal as a missing target. Neither a historical knownAsOf coordinate nor a previous successful read reinstates that grant.
- [x] **AC4:** TenantMember may read only through existing scoped read authority; Reviewer may submit through existing review:annotate authority but cannot commit; ServicePrincipal may use only its explicit read/commit grants. An unverified principal, a principal without membership and an external broker/MGA gain no access from this feature.
- [x] **AC5:** Caller-supplied IDs and actor fields cannot override structural tenant/KB ownership, verified identity, parent/classification conjunction or grant-revision checks. Tests use application checks as well as PostgreSQL ownership constraints; future F0018 RLS is not assumed delivered.
- [x] **AC6:** Authorization and its decision audit remain durable under the existing F0002 boundary. A refused mutation leaves zero correction/reservation/canonical effects; a source or authority change cannot allow payloads checked against a stale grant revision to be returned.
- [x] **AC7:** Failure output, application logs and result metadata contain no protected excerpts or hidden graph details. The feature suite explicitly challenges mixed-access correction ancestors, split predecessors, ending_refs and attestation sources, including duplicate decision replay.

## Edge Cases & Error Scenarios

One inaccessible ancestor, ending or attestation source refuses the whole result (AC2–3). Revocation and replay cannot bypass current grant checks (AC6–7).

## Interaction Contract

N/A — read-only story. Entry is the authorized internal lineage reader selected in Phase B. Completion is a returned, current-authorized result for an exact root or an explicit non-disclosing refusal. No editable state or save action is introduced.

## Data Requirements

Verified principal; current membership/grant revision and policy identity; root and linked structural scope/access keys; authorization outcome and correlation identity, with no copied source text in denial audit.

Required fields and referential constraints are enforced before effects. Optional legacy metadata stays absent/qualified rather than invented. Persisted source text is not copied into denial output.

## Role-Based Visibility

Use the [PRD role matrix](PRD.md#role-based-access). TenantMember has only scoped read authority; Reviewer adds existing review annotation without canonical commit; ServicePrincipal uses its explicit scoped grants. Unverified, nonmember, cross-tenant/KB and external broker/MGA callers obtain no access. Current parent/classification restrictions apply to each source. Engineering personas confer no runtime role.

## Non-Functional Expectations

Zero unauthorized payload disclosure or partial mutation; zero source reparse/model calls. At least 80% changed executable-code coverage in the later feature run. PostgreSQL proves durable behavior and concurrency where applicable. No unmeasured latency target is asserted. Use existing authorization/decision audit and correlation fields.

## Dependencies

F0002 authorization facade; F0006 metadata-first source discovery; F0007 read-before-reason guard; F0008 predecessor/attestation remediation; S0001–S0003 lineage shapes.

## Out of Scope

New roles or grants; new account-scope semantics; F0018 RLS or production-superuser remediation; retrieval/search caches.

## Questions & Assumptions

No open business-rule question is introduced. The [PRD assumptions](PRD.md#risks--assumptions) require Phase A review; storage, limits, contracts and rollback are explicit Architect decisions for Phase B. Requirements do not grant formal acceptance to a Proposed ADR.

## Definition of Done

- [x] Every AC above has a concrete observed proof in the later feature run.
- [x] Cross-tenant/KB, parent-plus-classification, revoked/mixed source, historical coordinate, replay and concurrent authority-change cases with non-disclosure checks and durable audit queries.
- [x] Error scenarios, permission checks and audit/persistence expectations pass.
- [x] Documentation and tracker state reflect observed results.
- [x] Required story-level review provenance is appended to STATUS.md in the feature action.

## Review Provenance

Planning only. No runtime signoff is claimed. The Architect sets the required role matrix in [STATUS.md](STATUS.md) during Phase B; the feature action supplies actual evidence.
