## Story Header

**Story ID:** F0001-S0004
**Feature:** F0001 — Repository and engineering foundation
**Title:** Proof: native review round trip with lineage
**Priority:** High
**Phase:** Infrastructure

## User Story

**As a** Rosa the Business Reviewer
**I want** a deliberately wrong extracted limit routed to the Nebula Review Panel, shown against the region of the source it was claimed from, corrected exactly once, and recorded as a governed ReviewDecision
**So that** the human-correction loop is proven end to end, duplicate and stale submissions are rejected, evidence that cannot be anchored blocks the decision instead of misplacing it, and the original machine assertion stays readable

## Context & Background

Master blueprint section 75 defines the v0.1 minimum review path and section 111.1 requires a narrow proof of the review workflow before the review contracts are frozen. [ADR-0057](../../../architecture/decisions/ADR-0057-nebula-owns-the-native-evidence-review-panel.md) moved that surface into Nebula on 2026-09-08, superseding ADR-0034: there is no external task, no webhook, and no second identity system, so this proof covers the panel, the anchor resolution behind [ADR-0058](../../../architecture/decisions/ADR-0058-evidence-anchoring-and-selector-contract.md), and the decision transaction. ADR-0037 governs correction lineage; proposed ADR-0044 (approval contract) and ADR-0058 (anchoring) are settled by the outcome. Section 125 defines the panel and its honest-failure behavior.

The prototype at [`planning-mds/examples/nebula-review-panel-live-files.html`](../../../examples/nebula-review-panel-live-files.html) demonstrates the rendering and anchoring approach against real byte streams and is the design input for this story. It is not evidence of the loop: it has no server, no persistence, and no authorization.

## Acceptance Criteria

**Happy Path:**
- **Given** an assertion "EachOccurrence limit = $20,000,000" from S0003 seeded with confidence 0.41 against a source page whose value is $2,000,000
- **When** the review policy routes it
- **Then** a ReviewItem of type LOW_CONFIDENCE_ASSERTION exists in a ReviewBatch, and opening the batch renders the source page from the immutable content artifact with the predicted value, the confidence, and the anchored region at its declared precision

- **Given** Rosa is signed in as a principal with `review:annotate` on the review item's knowledge base
- **When** she changes the value to $2,000,000 and submits the batch
- **Then** Nebula records a ReviewDecision with action CORRECT and reason code MISREAD_VALUE linked to the original assertion, creates a corrected assertion with origin HUMAN_REVIEW carrying the evidence target and precision she saw, and emits one audit event — all in one transaction

- **Given** the correction is applied
- **When** the original machine assertion is queried
- **Then** it is returned unchanged with its original confidence and evidence

**Alternative Flows / Edge Cases:**
- The same batch is submitted twice → the second submission is a no-op by decision event hash; exactly one ReviewDecision per item exists
- The assertion is superseded (version N+1) between batch assembly and submission → the decision is recorded as stale against version N and not applied; a new review item is opened for N+1
- A field's stored locator cannot be re-anchored in the artifact → the panel shows it as unresolved and offers no accept or correct action; submission records action BLOCKED with reason code EVIDENCE_UNRESOLVED, no assertion is created, and the review item stays open
- The stored grounding is page-level only → the panel renders a page-level mark and labels the precision; it does not draw a tight box
- A reviewer outside the item's knowledge base opens the batch URL → 404, and no evidence is rendered or fetched
- A reviewer with `review:annotate` but not `review:approve` submits a correction → the decision persists and no canonical fact is committed

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|-----------------------|-------------|----------------|-------------------------|-------------------------------|----------------------------|
| Nebula Review Panel, opened on a review batch | Inspect the anchored region, edit the value, accept, correct, or reject each field, submit the batch | Field values editable while the batch is open; read-only after submission; fields with unresolved evidence are not editable at all | ReviewDecision per field persisted in one transaction; corrected assertions created; originals preserved; one audit event per decision | Query the review item after submission: status decided, decision id present, audit event present; values survive a service restart | Reviewer bound to a verified principal with `review:annotate` on the item's knowledge base; submission never commits canonical truth (section 111.2) |

Required checks for this mutation story:
- [ ] Render-only behavior cannot satisfy the story; the decision must persist and be queryable
- [ ] The submission path has validation and error behavior specified (authorization, duplicate, stale, unresolved evidence)
- [ ] The successful mutation emits an audit event
- [ ] Tests prove the decision exists after processing and after a service restart

## Data Requirements

**Required Fields:**
- ReviewItem: id, type, assertion id and version, tenant, knowledge base, status, created at
- ReviewBatch: id, review item ids, assembled at, assembling principal
- EvidenceLocator: source artifact identity, part, selectors, precision, unresolved reason
- ReviewDecision: id, review item id, review batch id, action (ACCEPT, CORRECT, REJECT, BLOCKED), reason code, corrected value, evidence, reviewer principal id, decided at, assertion version, stale flag, event sha256
- Corrected assertion linked to the original assertion id

**Optional Fields:**
- Reviewer comment

**Validation Rules:**
- Decision event hash unique per review item
- A decision applies only when the item's assertion version equals the current version
- `BLOCKED` is valid only with reason code `EVIDENCE_UNRESOLVED` and creates no assertion
- Character offsets in stored locators are Unicode code points; the panel converts at its boundary

## Role-Based Visibility

**Roles that can annotate:**
- Business reviewer bound to a verified principal — `review:annotate` on review items in their knowledge base

**Roles that can adjudicate or approve canonical changes:**
- None in this proof; annotation is separate from business approval (section 111.2)

**Data Visibility:**
- The batch renders only artifacts and regions the reviewer is currently entitled to read; entitlement is resolved at assembly and rechecked at submission
- InternalOnly content: the fixture page and predicted values
- ExternalVisible content: none

## Non-Functional Expectations

- Performance: a four-artifact batch renders its first page and resolves its anchors within 2 seconds on the local stack; decision submission completes within 2 seconds
- Security: the reviewer is the authenticated session principal and is never read from the request payload; artifact bytes are served through authorized reads, not a public URL
- Reliability: submission is idempotent under resubmission and service restart

## Dependencies

**Depends On:**
- F0001-S0001 — the `experience/` root and its toolchain
- F0001-S0003 — the low-confidence assertion and its evidence locator
- F0001-S0006 — verified principals for the reviewer binding

**Related Stories:**
- F0001-S0007 — records the outcome in ADR-0044 and ADR-0058

## Business Rules

1. Human corrections append; they never rewrite evidence or the original machine assertion (ADR-0037).
2. Submitting a review decision does not confer approval authority; adjudication and canonical approval are separate permissions (section 111.2).
3. Nebula owns the review surface as well as ReviewItem, ReviewDecision, provenance, audit, and semantic commits; evidence is never copied outside the Brain to be reviewed (ADR-0057).
4. Unresolved evidence blocks the decision; a reviewer is never asked to adjudicate evidence they were not shown (ADR-0058, invariant 37).

## Out of Scope

- The full Document 360 surface and the complete renderer set (F0022); this proof carries the PDF renderer plus one OOXML renderer
- Generalized review queues and business-approval workflow (F0043)
- Golden Corpus export from the decision (F0026)
- Canonical commit of the corrected value (F0018); this proof stops at the corrected assertion
- OCR and scanned-page handling; a page with no text layer is a declared-precision case here, not a solved one

## UI/UX Notes

- Screens involved: the Nebula Review Panel at proof scope — artifact rail, rendered viewport with anchored regions, field list with per-field actions, batch submission. F0022 delivers it inside Document 360.
- The panel must render precision honestly: a page-level ground is a page-level mark, and an unresolved anchor says so in place of a region.

## Questions & Assumptions

**Open Questions:**
- [ ] Which OOXML renderer ships in the proof — DOCX or XLSX — Architect to decide at feature G0 from what S0003's fixture package contains
- [ ] Whether artifact bytes reach the panel through a signed short-lived read or a streamed authorized endpoint — Architect to decide at feature G0

**Assumptions (to be validated):**
- `pdf.js` and `fflate` are pinned in the dependency matrix and bundled with the app; the panel makes no third-party network request
- The reviewer principal is provisioned in authentik and resolved through the same verifier as every other protected read (S0006)

## Definition of Done

- [x] Acceptance criteria met
- [x] Edge cases handled
- [x] Permissions enforced (reviewer binding verified; annotate cannot commit)
- [x] Audit/timeline logged (one audit event per decision)
- [x] Tests pass
- [x] Documentation updated (panel notes under `experience/src/review-panel/`, ADR-0044 and ADR-0058 input for S0007)
- [x] Story filename matches `Story ID` prefix
- [x] Story index regenerated

## Review Provenance

Recorded in `STATUS.md` (Required Signoff Roles, Story Signoff Provenance).
