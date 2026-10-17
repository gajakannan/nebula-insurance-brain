## Story Header

**Story ID:** F0004-S0001\
**Feature:** F0004 — Content artifact model\
**Title:** Publish and reuse an immutable content bundle\
**Priority:** Critical\
**Phase:** MVP — v0.1A\
**Status:** Not Started

## User Story

**As a** document intelligence engineer\
**I want** publish one attributable content bundle and retrieve it after restart\
**So that** downstream interpretation reuses the accepted source representation without conversion.

## Context & Background

ADR-0003/0004/0040 define separate source, artifact and run identities. ADR-0059 requires manifest-last publication through ContentArtifactStore. F0005 owns the job that invokes this boundary. See [PRD](PRD.md) for authority, scope and exclusions.

## Acceptance Criteria

- [ ] **F0004-S0001-AC1:** Given a retained source version and authorized ingestion handoff, when its parse is published, then the six required files and native-export assets are retained with source/artifact identities, ownership, version metadata and hashes; a read after restart returns the same bytes and references.
- [ ] **F0004-S0001-AC2:** Given a complete bundle, when it is published, then file integrity is verified before the manifest completion marker and database ready visibility; an empty valid tables file is allowed, but a missing required file is not.
- [ ] **F0004-S0001-AC3:** Given a parser result, when the artifact is stored and reloaded, then parser name/version/configuration identity, native schema/content contract version, parse quality, failed pages and warnings round-trip. Partial parsing is visible and cannot be reported as complete extraction.
- [ ] **F0004-S0001-AC4:** Given the same published artifact and two existing profile consumers after restart, when they read the saved native JSON, then converter/OCR entry points are never called, original and bundle hashes are unchanged, and extraction graph/provenance/configuration remain separate run-owned outputs.
- [ ] **F0004-S0001-AC5:** Given a published artifact, when an overwrite or conflicting publication is attempted, then accepted bytes and identity are unchanged and the result explicitly identifies reuse or conflict. Retry execution remains F0005; the storage boundary must not create two conflicting accepted versions for one identity.

- [ ] **F0004-S0001-AC6:** Given an authorized publication, when validated content becomes available, then durable audit history records actor, scope, artifact identity and recorded time; failed publication never records a successful content mutation.

**Edge Cases & Error Scenarios:** Missing native asset/file, invalid hash, interruption before manifest, or metadata readiness failure → no verified ready artifact is exposed. Tampering after publication → integrity failure, not silent acceptance. A governed parser replacement has a new artifact version and preserves the prior one; corpus migration is excluded.

## Interaction Contract

No UI; the named service handoff is the entry point. Render-only output or an in-memory round-trip cannot satisfy persistence requirements.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Authorized ingestion publication boundary | Publish source-linked parse bundle | New candidate only; published bytes immutable | Verified manifest and attributable ready metadata, or explicit failure | Restart process and read from durable metadata/store; compare all hashes | Verified F0002 principals with current action/resource authority; no new grants |

**Validation and audit:** reject invalid or unauthorized input without altering accepted content or prior history. Record authorization decisions with the existing policy version; successful content/metadata mutations retain actor, timestamp, scope and identity in audit history. Failure never reports a successful mutation. Phase B binds exact interfaces, validation responses and events.

## Data Requirements

Source/document version, artifact identity, tenant/KB owner, original source reference, six-file inventory, hashes, parser recipe identity, native/contract versions, quality diagnostics, recorded actor/time. PostgreSQL stores metadata and references; ADR-0059 ports own bytes.

## Role-Based Visibility

- Existing scoped ServicePrincipal ingestion authority permits the applicable publication handoff only.
- TenantMember/Reviewer reads require current artifact/evidence permission and parent/source restrictions; neither role gains unrestricted writes.
- HUMAN date provenance requires an attributable authorized human decision. All content stays internal and scoped; external broker/MGA access is excluded.

## Non-Functional Expectations

- Reliability: persisted readback after restart; explicit integrity/validation failures; no silent mutation of accepted bytes or provenance.
- Security: current resource authorization before access, immutable ownership and no cross-tenant disclosure.
- Verification: versioned contract checks and integration/negative cases, with at least 80% changed-runtime coverage in the later feature action. No new throughput/latency commitment is introduced.

## Dependencies

F0001 accepted bundle/storage baseline; F0002 authorization and ownership; F0003 persistence integrity. F0005-S0002/S0003 are downstream publication/reuse consumers.

## Out of Scope

New parser/model engine, worker scheduling/retry/lease logic, cloud adapters, production Graph activation, profile compilation, canonical fact writes.

## Questions & Assumptions

No unresolved business question. This story uses the existing blueprint and bounded amendments, not broader acceptance of Proposed ADRs. Physical schema, compatibility matrix and interface/error details must be completed in Phase B before architecture approval.

## Definition of Done

- [ ] Every acceptance criterion has actual persisted-output or negative-case evidence.
- [ ] Permissions and audit expectations are verified; invalid input cannot alter prior accepted state.
- [ ] [EX-CONTENT-001](worked-examples.md) has a reproduction command and expected-versus-observed results; synthetic development cases remain outside the frozen holdout.
- [ ] Versioned fixtures validate and affected consumers retain compatibility.
- [ ] Required tests pass and documentation records remaining scope boundaries.
- [ ] Story status/index and append-only signoff provenance are updated in [STATUS](STATUS.md).

## Review Provenance

Implementation signoff belongs in STATUS.md. This planning draft is not runtime completion or reviewer approval.
