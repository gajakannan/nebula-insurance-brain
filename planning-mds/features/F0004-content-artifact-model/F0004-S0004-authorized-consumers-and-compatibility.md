## Story Header

**Story ID:** F0004-S0004\
**Feature:** F0004 — Content artifact model\
**Title:** Protect artifact consumers and compatibility\
**Priority:** Critical\
**Phase:** MVP — v0.1A\
**Status:** Not Started

## User Story

**As a** persistence engineer\
**I want** keep content access, legacy readers and restoration consistent across consumers\
**So that** an artifact remains reusable without leaking source bytes or rewriting historical evidence.

## Context & Background

F0002 owns current-scope authorization and F0003 persistence boundaries. ADR-0059 makes database metadata plus retained bytes the restore unit. The F0005 opt-in proof is a compatibility consumer, not evidence of production activation. See [PRD](PRD.md) for authority, scope and exclusions.

## Acceptance Criteria

- [ ] **F0004-S0004-AC1:** Given current F0002 authority, when source bytes, native/normalized files, metadata, evidence or referenced run outputs are accessed, then the existing service path enforces tenant, KB and applicable parent/source restrictions before returning data, with attributable authorization audit and policy version.
- [ ] **F0004-S0004-AC2:** Given cross-tenant, disallowed-KB, revoked-membership or restricted-source requests, when any covered read/publication path is invoked, then it returns no unauthorized bytes or protected metadata and creates no unauthorized artifact; alternate object-key/preview paths cannot bypass the check.
- [ ] **F0004-S0004-AC3:** Given supported historical manifests and new-contract manifests, when existing consumers load them, then each follows its declared version; historical bytes/hashes stay unchanged and missing historical date/origin data remains absent. Unsupported versions fail explicitly instead of being guessed or silently upgraded.
- [ ] **F0004-S0004-AC4:** Given a backup of metadata, source and artifact files plus referenced retained run outputs, when the supported local restore procedure is executed, then source/artifact identities, hashes, references and restrictions round-trip. Missing or mismatched bytes prevent a verified ready response.
- [ ] **F0004-S0004-AC5:** Given the existing F0005 publication and saved-native-JSON proof seam, when contract compatibility is exercised after restart, then its two-profile reuse and honest evidence behavior remain intact without reparse, source mutation, or moving run-owned outputs into the parse bundle.
- [ ] **F0004-S0004-AC6:** Given the four worked examples, when the feature is implemented, then reproducible commands compare independently expected versus observed persisted outcomes, cover failure and authorization cases, validate versioned structured fixtures, and keep development cases separate from the frozen holdout.

**Edge Cases & Error Scenarios:** Restore with only a database dump, missing required assets, hash mismatch, unknown version, revoked access or cross-owner references → explicit failure without granting access or exposing an accepted artifact. Legacy missing provenance is reported, not repaired with invented values.

## Interaction Contract

No UI; the named service handoff is the entry point. Render-only output or an in-memory round-trip cannot satisfy persistence requirements.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Existing authorized artifact/evidence services and local backup/restore procedure | Read persisted content, validate compatibility, restore the supported artifact unit | Read-only consumer access; restoration does not grant permissions | Same attributable content under current access rules or explicit failure | Cross-process readback, denied-access checks, old/new fixture loads and actual local restore | Verified F0002 principals with current action/resource authority; no new grants |

**Validation and audit:** reject invalid or unauthorized input without altering accepted content or prior history. Record authorization decisions with the existing policy version; successful content/metadata mutations retain actor, timestamp, scope and identity in audit history. Failure never reports a successful mutation. Phase B binds exact interfaces, validation responses and events.

## Data Requirements

Existing F0002 principal/resource context; source/artifact/run ownership references; contract version and checksums; persisted authorization audit; restore inventory. Use the existing non-secret local storage configuration, never provider URLs or raw filesystem paths as an application contract.

## Role-Based Visibility

- Existing scoped ServicePrincipal ingestion authority permits the applicable publication handoff only.
- TenantMember/Reviewer reads require current artifact/evidence permission and parent/source restrictions; neither role gains unrestricted writes.
- HUMAN date provenance requires an attributable authorized human decision. All content stays internal and scoped; external broker/MGA access is excluded.

## Non-Functional Expectations

- Reliability: persisted readback after restart; explicit integrity/validation failures; no silent mutation of accepted bytes or provenance.
- Security: current resource authorization before access, immutable ownership and no cross-tenant disclosure.
- Verification: versioned contract checks and integration/negative cases, with at least 80% changed-runtime coverage in the later feature action. No new throughput/latency commitment is introduced.

## Dependencies

F0004-S0001/S0002/S0003; F0001 accepted artifacts; F0002 AuthX; F0003 migration/restore discipline. F0005 synthetic proof is consumed with its limits; F0026 owns production operational qualification.

## Out of Scope

Cloud adapters, new retention periods or automatic deletion policies, distributed deployment, F0005 release approval, production live-model benchmark, new permissions or review UI.

## Questions & Assumptions

No unresolved business question. This story uses the existing blueprint and bounded amendments, not broader acceptance of Proposed ADRs. Physical schema, compatibility matrix and interface/error details must be completed in Phase B before architecture approval.

## Definition of Done

- [ ] Every acceptance criterion has actual persisted-output or negative-case evidence.
- [ ] Permissions and audit expectations are verified; invalid input cannot alter prior accepted state.
- [ ] [EX-CONTENT-004](worked-examples.md) has a reproduction command and expected-versus-observed results; synthetic development cases remain outside the frozen holdout.
- [ ] Versioned fixtures validate and affected consumers retain compatibility.
- [ ] Required tests pass and documentation records remaining scope boundaries.
- [ ] Story status/index and append-only signoff provenance are updated in [STATUS](STATUS.md).

## Review Provenance

Implementation signoff belongs in STATUS.md. This planning draft is not runtime completion or reviewer approval.
