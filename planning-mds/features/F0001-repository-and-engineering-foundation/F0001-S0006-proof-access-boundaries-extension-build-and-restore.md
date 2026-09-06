## Story Header

**Story ID:** F0001-S0006
**Feature:** F0001 — Repository and engineering foundation
**Title:** Proof: access boundaries, extension build, and restore
**Priority:** High
**Phase:** Infrastructure

## User Story

**As a** Dana the Platform Engineer
**I want** two security scopes provisioned in authentik with credentials verified before any storage read, revocation propagated, object and review access denied across scopes, the exact PostgreSQL extension build installed, and a timed backup and restore drill
**So that** hosting and access assumptions are proven before the contracts that depend on them freeze

## Context & Background

Master blueprint section 115.4 names the access and hosting proof: two security scopes, revocation, object and review access, exact extension build and restore. Section 120.1 requires credential verification for the receiving service's issuer and audience before identity resolution, a stable internal principal, and a native Casbin adapter; section 119 lists the CRM gaps that must not be copied. Section 114.3 requires proving backup and restore of relational state, original content, artifact manifests, ontology releases, and review evidence. Proposed ADR-0049 and ADR-0050 are settled by the outcome.

## Acceptance Criteria

**Happy Path:**
- **Given** authentik issues tokens for principal A in tenant A and principal B in tenant B
- **When** the engine receives a request
- **Then** issuer, audience, signature, expiry, and not-before are verified before any protected storage is read, and the verified `(issuer, subject)` resolves to a stable internal principal id

- **Given** principal A
- **When** A requests A's content artifact and A's review task
- **Then** both return HTTP 200 and an authorization audit event records policy hash, principal, resource, action, decision, reason code, and trace id

- **Given** principal A
- **When** A requests B's content artifact, B's review task, or B's fact
- **Then** the response does not disclose existence (HTTP 404 by policy) and the audit event records the denial reason code

- **Given** A's membership is revoked in authentik and the grant revision advances
- **When** A's next request arrives after the configured propagation window
- **Then** it is denied and the measured propagation time is recorded

- **Given** the pinned PostgreSQL, pgvector, and AGE build from S0002
- **When** installed on the S0002 image on the local Docker Compose stack
- **Then** both extensions create successfully and the version triple is recorded in the dependency matrix

- **Given** a backup taken after S0003, S0004, and S0005 data exists
- **When** it is restored to a fresh instance
- **Then** relational state, original content objects, artifact manifests, and review evidence are present, every citation from S0003 resolves, and the measured restore time and data loss window are recorded against the pilot objectives

**Alternative Flows / Edge Cases:**
- Wrong audience, expired token, wrong signature, malformed bearer → HTTP 401 with an internal reason code logged and not disclosed
- Same subject from a different issuer → resolves to a different internal principal (issuer namespaced)
- Backup missing the content objects → the restore drill fails its citation check and the failure is recorded as a finding

## Interaction Contract

N/A — proof harness driven by tests; no user-facing mutation of business data.

## Data Requirements

**Required Fields:**
- `principal`: internal id, issuer, subject, kind (user, service, agent), status
- `membership`: principal id, tenant, knowledge base, role, grant revision
- Casbin model and policy files under `planning-mds/security/policies/` covering the proof's resources and actions
- `audit_event` for authorization decisions with policy hash, grant revision, actor, resource, action, decision, reason code, trace id
- Backup manifest: database dump, object store snapshot, timestamps

**Optional Fields:**
- Delegation record for the worker service principal

**Validation Rules:**
- No request reads protected storage before verification completes (section 120.1)
- Denials never disclose resource existence to the caller (section 118.2)

## Role-Based Visibility

**Roles and what each can see:**
- Tenant A principal — tenant A artifacts, tasks, and facts only
- Tenant B principal — tenant B artifacts, tasks, and facts only
- Worker service principal — write artifacts and commit facts in the fixture tenant; no review annotation rights
- Revoked principal — nothing after propagation

**Data Visibility:**
- InternalOnly content: all fixture data
- ExternalVisible content: none

## Non-Functional Expectations

- Performance: authorization decision adds no more than 20 milliseconds median to a local request; the restore drill is timed and recorded
- Security: the four scan classes (dependency, secrets, SAST, DAST) run against the proof services in the feature run
- Reliability: two consecutive restore drills produce identical citation checks

## Dependencies

**Depends On:**
- F0001-S0001 — engine skeleton
- F0001-S0002 — authentik, PostgreSQL, object store

**Related Stories:**
- F0001-S0004 — reviewer principal binding
- F0001-S0007 — records the outcome in ADR-0049 and ADR-0050

## Business Rules

1. Authorization is the conjunction of current tenant and knowledge-base membership, permitted action, actual resource or parent scope, classification, and delegation limits; role allows cannot override those boundaries (section 66).
2. Forwarding a token to a later call is not verification (section 66).
3. Historical business query dates cannot reinstate revoked permissions (proposed ADR-0053).

## Out of Scope

- Browser session transport and the BFF decision (F0021, proposed ADR-0051)
- The full permission catalog and review boundaries (F0002, F0018, section 120.2)
- Retention, deletion, and restore of deleted data (F0026, proposed ADR-0043)

## UI/UX Notes

- N/A

## Questions & Assumptions

**Open Questions:**
- [x] Proof host — decided at the F0001 clarification gate (2026-09-06): local Docker Compose only; the production host decision waits for F0026 (section 117.1 item 3)
- [ ] authentik version — Architect to decide at Phase B and pin in the dependency matrix

**Assumptions (to be validated):**
- The proof host image is the PostgreSQL 18 image built in S0002
- Pilot recovery objectives are recorded as measured values here and adopted as targets in F0026

## Definition of Done

- [ ] Acceptance criteria met
- [ ] Edge cases handled
- [ ] Permissions enforced
- [ ] Audit/timeline logged (authorization decision audit)
- [ ] Tests pass
- [ ] Documentation updated (security README, ADR-0049 and ADR-0050 input for S0007)
- [ ] Story filename matches `Story ID` prefix
- [ ] Story index regenerated

## Review Provenance

Recorded in `STATUS.md` (Required Signoff Roles, Story Signoff Provenance).
