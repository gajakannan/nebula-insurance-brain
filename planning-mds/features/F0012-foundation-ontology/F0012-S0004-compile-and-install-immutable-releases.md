# F0012-S0004 — Compile and install immutable releases

**Story ID:** F0012-S0004
**Feature:** F0012 — Foundation ontology
**Title:** Compile and install immutable releases
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Not Started

## User Story

**As a** persistence engineer (Ingrid)
**I want** module files compiled deterministically into a hashed, exactly locked release that is installed as immutable records
**So that** any later run can name the release it used and get exactly the same definitions back.

## Context & Background

ADR-0012 compiles authoring formats into normalized PostgreSQL structures. ADR-0045 and the [proposed release records](../../architecture/data-model.md#proposed-ontology-release-records-f0012f0013-adr-0045) require immutable module versions, composed releases with exact dependency locks and digests, and a versioned projection mapping. Operator decision D1 (G1, 2026-11-25) selects offline compile plus PostgreSQL release records.

## Acceptance Criteria

- [ ] **AC1:** Compiling the same module files with the same compiler version produces byte-identical normalized output and identical SHA-256 digests on two runs and on a fresh checkout. Reordering terms or files in the source does not change the output.
- [ ] **AC2:** Publishing a module ID and version whose content digest differs from an already published version with the same ID and version is rejected; publishing identical content again is idempotent and creates no new row.
- [ ] **AC3:** A release manifest records the release ID, each module version with its digest, the dependency lock, authoring-schema and compiler versions, the supported-semantics declaration, constraint metadata, the projection mapping and its digest, reserved slots for profile/template/compiler/validation artifacts, ownership scope, creating actor and time.
- [ ] **AC4:** Every module dependency resolves to exactly one member version by exact version and digest. A floating, ranged, missing or conflicting dependency is rejected, and a release contains at most one version per module.
- [ ] **AC5:** The projection mapping covers every object and datatype property: each is either mapped (edge or property label, direction, endpoint types, required context) or explicitly omitted with a reason. An uncovered property is rejected; missing coverage is never treated as no impact.
- [ ] **AC6:** Installing a release for a tenant/KB writes normalized append-only records in one transaction. A failure at any step leaves no release rows. Installing an identical digest again is idempotent. Any update or delete of installed release rows is refused by the database.
- [ ] **AC7:** Install requires an explicit install grant, does not activate the release, and audits actor, tenant/KB, release ID, digest and outcome, including denials. Compile and install make zero Docling parses, model calls or canonical fact writes.

## Edge Cases & Error Scenarios

A concurrent install of the same digest results in one set of rows and one success (AC6). A release whose manifest digest does not match its contents is refused at install. An install for a tenant/KB the principal is not a member of is denied without revealing whether the release exists.

## Interaction Contract

Entry points: the offline compile command (files to compiled bundle) and an install command acting as an authenticated principal. Install is allowed only with the install grant; it is refused for an unknown digest mismatch, a mutated module version or a missing dependency. Success commits the release rows atomically; proof is a fresh-session query returning the same digests. Every install decision writes an audit record. No editable state exists after install.

## Data Requirements

Module versions with digests, composed release with manifest and dependency lock, projection mapping, artifact slots, tenant/KB ownership, install audit. Tables, immutability triggers, digest canonicalization and the migration are Phase B decisions.

## Role-Based Visibility

Compile is offline. Install performs an authorization check against the explicit install grant named in Phase B; no existing role gains it, and a denied install is audited. See the [PRD role matrix](PRD.md#role-based-access).

## Non-Functional Expectations

PostgreSQL proves atomicity, idempotence, concurrency and database-enforced immutability. Compile and install durations are measured and recorded; no budget is invented. At least 80% changed executable-code coverage in the later feature run.

## Dependencies

S0001 and S0002 validation; F0002 authority and audit; F0011 contract delivery for any manifest schema.

## Out of Scope

Activation (S0006); profile, template and compiler artifacts themselves (F0014/F0015); AGE projection writing (F0034).

## Questions & Assumptions

No open business-rule question. PM assumptions A1 (command-line entry points) and A5 (per tenant/KB installation) are in the [PRD](PRD.md#risks--assumptions).

## Definition of Done

- [ ] Every AC above has a concrete observed proof in the later feature run.
- [ ] Double-compile digest comparison, immutability and dependency-lock fixtures, rollback injection during install, concurrent install, audit queries.
- [ ] Error scenarios, permission checks and persistence expectations pass.
- [ ] Documentation and tracker state reflect observed results.
- [ ] Required story-level review provenance is appended to STATUS.md in the feature action.

## Review Provenance

Planning only. No runtime signoff is claimed. The Architect sets the required role matrix in [STATUS.md](STATUS.md) during Phase B; the feature action supplies actual evidence.
