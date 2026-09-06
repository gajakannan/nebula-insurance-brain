## Story Header

**Story ID:** F0001-S0004
**Feature:** F0001 — Repository and engineering foundation
**Title:** Proof: Label Studio review round trip with lineage
**Priority:** High
**Phase:** Infrastructure

## User Story

**As a** Rosa the Business Reviewer
**I want** a deliberately wrong extracted limit routed to Label Studio, corrected exactly once, and returned to Nebula as a governed ReviewDecision
**So that** the human-correction loop is proven with the selected edition, duplicate and stale callbacks are rejected, and the original machine assertion stays readable

## Context & Background

Master blueprint section 75 defines the v0.1 minimum review path and section 111.1 requires a narrow proof with the intended Label Studio edition before selecting deployment or estimating effort: create a task from immutable evidence, display page and evidence, bind the reviewer to a verified principal, receive events securely and persist the payload hash, translate to a ReviewDecision, reject duplicates and stale versions, commit through the semantic boundary. ADR-0034 and ADR-0037 govern; proposed ADR-0044 is settled by the outcome.

## Acceptance Criteria

**Happy Path:**
- **Given** an assertion "EachOccurrence limit = $20,000,000" from S0003 seeded with confidence 0.41 against a source page whose value is $2,000,000
- **When** the review policy routes it
- **Then** a ReviewItem of type LOW_CONFIDENCE_ASSERTION exists and a Label Studio task is created showing the rendered page, the bounding box, the predicted value, and the confidence, with the task reference stored as a ReviewExternalTask

- **Given** Rosa is logged into Label Studio as a user bound to her verified Nebula principal
- **When** she changes the value to $2,000,000 and submits the annotation
- **Then** Nebula persists the raw event payload with its sha256, records a ReviewDecision with action CORRECT linked to the original assertion, creates a corrected assertion linked to the original, and emits one audit event

- **Given** the correction is applied
- **When** the original machine assertion is queried
- **Then** it is returned unchanged with its original confidence and evidence

**Alternative Flows / Edge Cases:**
- The same annotation event is delivered twice → the second delivery is rejected as a duplicate by payload hash; exactly one ReviewDecision exists
- The assertion is superseded (version N+1) between task creation and annotation return → the decision is recorded as stale against version N and not applied; a new task is created for N+1
- The webhook arrives without a valid shared secret or signature → HTTP 401 and no decision recorded
- A second reviewer outside Rosa's scope opens the task URL → the edition's access behavior is recorded (allowed or denied) as a finding for ADR-0044

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|-----------------------|-------------|----------------|-------------------------|-------------------------------|----------------------------|
| Label Studio task view (deep link from the ReviewItem) | Edit the predicted value, submit the annotation | Value and bounding box editable while the task is open; read-only after submission | ReviewDecision CORRECT persisted; corrected assertion created; original preserved | Query the ReviewItem after webhook processing: status decided, decision id present; audit event present | Reviewer bound to a verified principal with annotate permission on the task's knowledge base; annotation does not grant canonical approval (section 111.2) |

Required checks for this mutation story:
- [ ] Render-only behavior cannot satisfy the story; the decision must persist and be queryable
- [ ] The webhook path has validation and error behavior specified (signature, duplicate, stale)
- [ ] The successful mutation emits an audit event
- [ ] Tests prove the decision exists after processing and after a service restart

## Data Requirements

**Required Fields:**
- ReviewItem: id, type, assertion id and version, tenant, knowledge base, status, created at
- ReviewExternalTask: review item id, Label Studio project id, task id, created at
- Review event: raw payload, sha256, received at, reviewer principal id
- ReviewDecision: id, review item id, action (ACCEPT, CORRECT, REJECT), corrected value, reviewer principal id, decided at, stale flag
- Corrected assertion linked to the original assertion id

**Optional Fields:**
- Reviewer comment

**Validation Rules:**
- Payload hash unique per review item
- Decision applies only when the task's assertion version equals the current version

## Role-Based Visibility

**Roles that can annotate:**
- Business reviewer bound to a verified principal — annotate tasks in their knowledge base

**Roles that can adjudicate or approve canonical changes:**
- None in this proof; annotation is separate from business approval (section 111.2)

**Data Visibility:**
- InternalOnly content: the fixture page and predicted values
- ExternalVisible content: none

## Non-Functional Expectations

- Performance: webhook processing completes within 2 seconds of receipt in the local stack
- Security: webhook signature or shared secret required; reviewer identity verified against the Nebula principal registry, not trusted from the payload
- Reliability: processing is idempotent under redelivery and service restart

## Dependencies

**Depends On:**
- F0001-S0002 — Label Studio container
- F0001-S0003 — the low-confidence assertion and its evidence locator
- F0001-S0006 — verified principals for the reviewer binding

**Related Stories:**
- F0001-S0007 — records the outcome in ADR-0044

## Business Rules

1. Human corrections append; they never rewrite evidence or the original machine assertion (ADR-0037).
2. Label Studio completion does not confer approval authority; annotation and canonical approval are separate permissions (section 111.2).
3. Nebula owns ReviewItem, ReviewDecision, provenance, audit, and semantic commits; Label Studio owns task presentation and annotation workflow (ADR-0034).

## Out of Scope

- Generalized review queues and business-approval workflow (F0043)
- Golden Corpus export from the decision (F0026)
- Canonical commit of the corrected value (F0018); this proof stops at the corrected assertion

## UI/UX Notes

- Screens involved: Label Studio task view as shipped; no Nebula screen

## Questions & Assumptions

**Open Questions:**
- [x] Label Studio edition — decided at the F0001 clarification gate (2026-09-06): Community, self-hosted. The proof records which role, assignment, and reviewer features are missing and which isolation controls Nebula must own (section 111.1, reference R3); ADR-0044 is settled from those findings
- [ ] Webhook trust mechanism — Architect to decide at Phase B from what the Community edition supports (custom header secret at minimum)

**Assumptions (to be validated):**
- Pre-annotations and webhooks are available in the selected edition
- The reviewer principal is provisioned in authentik and mapped to the Label Studio user by email

## Definition of Done

- [ ] Acceptance criteria met
- [ ] Edge cases handled
- [ ] Permissions enforced (reviewer binding verified)
- [ ] Audit/timeline logged (one audit event per decision)
- [ ] Tests pass
- [ ] Documentation updated (integration notes under `integrations/label-studio/`, ADR-0044 input for S0007)
- [ ] Story filename matches `Story ID` prefix
- [ ] Story index regenerated

## Review Provenance

Recorded in `STATUS.md` (Required Signoff Roles, Story Signoff Provenance).
