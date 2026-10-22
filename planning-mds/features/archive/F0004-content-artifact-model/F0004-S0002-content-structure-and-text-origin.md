## Story Header

**Story ID:** F0004-S0002

**Feature:** F0004 — Content artifact model

**Title:** Preserve content structure and text origin

**Priority:** Critical

**Phase:** MVP — v0.1A

**Status:** Done

## User Story

**As a** document intelligence engineer

**I want** retain attributable blocks, tables and layout through publication and readback

**So that** consumers can locate evidence and distinguish native words from OCR or generated text.

## Context & Background

The 2026-09-25 F0004 amendment admits text-origin storage and validation. Master blueprint §§5/108 require actual source structure and honest precision. ADR-0058 as amended retains the accepted PDF/BoxSelector boundary. See [PRD](PRD.md) for authority, scope and exclusions.

## Acceptance Criteria

- [x] **F0004-S0002-AC1:** Given parsed native and scanned PDF fixtures, when content is published and reloaded, then block IDs, reading order, section/page membership and available table/cell relationships point to the same immutable artifact; dangling or cross-artifact references fail validation.
- [x] **F0004-S0002-AC2:** Given new-contract block records, when they are validated, then each has exactly one text_origin from STATED, OCR, TRANSCRIBED or DESCRIBED, an attributable producing engine/model/version, and the applicable origin-specific anchor. Non-model producers explicitly record that no model applies.
- [x] **F0004-S0002-AC3:** Given OCR, transcript and description examples, when they round-trip, then page/region, time-span/speaker and page/figure anchors respectively retain their meaning. Native/scanned PDF uses observed parser provenance; transcript/description fixtures prove storage only and introduce no new engine.
- [x] **F0004-S0002-AC4:** Given a rotated page, Unicode astral characters or unavailable geometry, when locators are stored/read, then page numbering, coordinate origin/units/page dimensions/transform, normalization version and Unicode code-point offset conventions are explicit where applicable; missing precision remains coarse or unresolved with no invented box.
- [x] **F0004-S0002-AC5:** Given repeated values, merged cells, repeated headers and continuation-table content, when represented relations are stored/read, then cell/header/continuation identities remain distinguishable; matching a value alone does not establish its location.
- [x] **F0004-S0002-AC6:** Given an origin/producer/anchor validation failure or a block mixing origins, when publication is attempted, then the new-contract record is rejected explicitly and no already published bundle is changed. Readable legacy content follows S0004 and is never relabeled without evidence.

- [x] **F0004-S0002-AC7:** Given an authorized publication that carries structure/origin records, when validated content becomes available, then the single publication audit event required by F0004-S0001-AC6 also covers those records; no separate per-story or per-record success event is created, and failed publication records none. Evidence is shared with S0001-AC6.

**Edge Cases & Error Scenarios:** Unknown origin, impossible offsets, invalid dimensions, dangling table references or mixed-origin text → explicit contract failure. Missing parser geometry → truthful reduced precision, not guessed geometry. Described text remains labeled so downstream admission/review can enforce its restrictions.

## Interaction Contract

No UI; the named service handoff is the entry point. Render-only output or an in-memory round-trip cannot satisfy persistence requirements.

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Existing parse-to-bundle handoff and authorized metadata read | Publish and inspect attributable content records | New candidate content; published blocks read-only | Validated structure/origin retained with the bundle | Durable readback resolves each fixture block/table/anchor after restart | Verified F0002 principals with current action/resource authority; no new grants |

**Validation and audit:** reject invalid or unauthorized input without altering accepted content or prior history. Record authorization decisions with the existing policy version; successful content/metadata mutations retain actor, timestamp, scope and identity in audit history. Failure never reports a successful mutation. Phase B binds exact interfaces, validation responses and events.

## Data Requirements

Artifact-local block/table/cell IDs, actual text and reading order, section/page membership, table header/merge/continuation relationships, coordinate/offset conventions, text_origin, producer identity and origin-specific anchor. Optional confidence remains producer-provided; absent confidence is not synthesized.

## Role-Based Visibility

- Existing scoped ServicePrincipal ingestion authority permits the applicable publication handoff only.
- TenantMember/Reviewer reads require current artifact/evidence permission and parent/source restrictions; neither role gains unrestricted writes.
- HUMAN date provenance requires an attributable authorized human decision. All content stays internal and scoped; external broker/MGA access is excluded.

## Non-Functional Expectations

- Reliability: persisted readback after restart; explicit integrity/validation failures; no silent mutation of accepted bytes or provenance.
- Security: current resource authorization before access, immutable ownership and no cross-tenant disclosure.
- Verification: versioned contract checks and integration/negative cases, with at least 80% changed-runtime coverage in the later feature action. No new throughput/latency commitment is introduced.

## Dependencies

F0004-S0001 publication contract; the Step 1 per-item provenance spike (assembly plan); accepted ADR-0040 and amended ADR-0058; bounded ADR-0065 amendment. F0005 translates parse output; F0006/F0016/F0022 consume origin/evidence metadata.

## Out of Scope

New transcription/description engines; full W3C/OOXML locators; browser UTF-16 conversion; assertion admission or automatic canonical acceptance; new review UI.

## Questions & Assumptions

No unresolved business question. This story uses the existing blueprint and bounded amendments, not broader acceptance of Proposed ADRs. Physical schema, compatibility matrix and interface/error details are specified in the approved [assembly plan](feature-assembly-plan.md) and [ADR-0073](../../../architecture/decisions/ADR-0073-versioned-content-contracts-and-document-metadata.md). **Provenance gate (operator decision 2026-10-16):** the v2 origin criteria (AC2–AC4, AC6) are proven on v2 publication. New sources keep publishing v1 bundles until the assembly plan's Step 1 provenance spike proves per-item origin on the pinned converter. After a PASS, a document whose items cannot all be attributed publishes as a v1 bundle with a recorded `ORIGIN_UNAVAILABLE` fallback reason (operator decision 2026-10-16, re-review R-M1); it never receives inferred v2 origins. If the spike fails, this story cannot be signed off and returns to the operator for a scope decision; it is never satisfied by inferring origin from page-level OCR counts.

## Definition of Done

- [x] Every acceptance criterion has actual persisted-output or negative-case evidence.
- [x] Permissions and audit expectations are verified; invalid input cannot alter prior accepted state.
- [x] [EX-CONTENT-002](worked-examples.md) has a reproduction command and expected-versus-observed results; synthetic development cases remain outside the frozen holdout.
- [x] Versioned fixtures validate and affected consumers retain compatibility.
- [x] Required tests pass and documentation records remaining scope boundaries.
- [x] Story status/index and append-only signoff provenance are updated in [STATUS](STATUS.md).

## Review Provenance

Implementation signoff belongs in STATUS.md. This planning draft is not runtime completion or reviewer approval.
