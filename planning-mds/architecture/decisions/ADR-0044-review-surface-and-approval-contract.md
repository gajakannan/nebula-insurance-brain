# ADR-0044: Review Surface and Approval Contract

## Status

- [ ] Proposed
- [x] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Revised:** 2026-09-08 — the decision to settle no longer includes selecting a Label Studio edition; [ADR-0057](ADR-0057-nebula-owns-the-native-evidence-review-panel.md) settled the surface question by moving review into Nebula. What remains open, and what this record still owes, is the approval contract.
**Settled:** 2026-09-10 (F0001-S0007), from F0001-S0004's live proof run on 2026-09-09
**Deciders:** Architect (record owner); backend-developer and frontend-developer executed the proof
**Settled by:** F0001-S0004 (native review round trip with lineage); results recorded by F0001-S0007
**Source:** `planning-mds/architecture/master-blueprint.md` sections 111.2, 116, 125

## Context

Proposed in the master blueprint pre-build requirements to settle two things: which Label Studio edition the governed review loop would run on, and how annotation is separated from canonical approval.

The first half is closed. ADR-0057 removed Label Studio; the review surface is the native Nebula Review Panel, so there is no edition to select and no external annotation event to trust.

The second half is untouched by that change and is the harder one. Moving the surface in-house removes the webhook trust boundary but does not by itself separate a reviewer confirming what the PDF says from a reviewer deciding that a document governs a policy term. Section 111.2 draws that line; nothing yet enforces it.

Example and reference: stale reviewer correction; section 111.2.

## Decision

**Accepted.** **Annotation, adjudication, and business approval are separate authorities, enforced separately.**

Specifically, what F0001-S0004 must settle:

- The permission split across `review:annotate`, `review:adjudicate`, and `review:approve`, and which of them the Review Panel can exercise at all. Submitting a decision must not be able to commit canonical truth.
- Stale handling: a decision submitted against a superseded assertion version is recorded and attributed, and is not applied.
- Concurrent correction: two reviewers correct the same assertion differently; both submissions stay auditable and the second does not silently overwrite the first accepted result.
- Reason codes, escalation, and which high-impact disputes require a second review.
- The review-routing policy: low confidence alone is not the trigger. Risk-based sampling of high-confidence results, critical missing fields, package incompleteness, impossible values, and conflicts with trusted sources all route to review.

## Results (F0001-S0004, measured 2026-09-09)

- **Permission split enforced, not just documented:** the Casbin policy
  (`planning-mds/security/policies/policy.csv`) grants `Reviewer` the
  `review:annotate` action but no `fact_slot:commit` action anywhere; only
  `ServicePrincipal` has `fact_slot:commit`. A `TenantMember` — read-only —
  attempting to submit a decision is denied outright (404, existence never
  disclosed). Structurally, nothing a reviewer submits through
  `POST /reviews/batches/{id}/decisions` can itself write a
  `canonical_fact_version` row; a decision produces a `ReviewDecision` and, for
  `CORRECT`, a new `Assertion` with `origin=HUMAN_REVIEW` — never a commit.
  Test: `engine/apps/api/tests/test_reviews.py::test_tenant_member_without_annotate_permission_cannot_submit_a_decision`.
- **Review workflow steps proven end to end:** batch assembly → routed review
  item → decision (`ACCEPT`/`CORRECT`/`REJECT`/`BLOCKED`) → for `CORRECT`, a
  new `Assertion` linked via `original_assertion_id` to the untouched original
  (ADR-0037: corrections append, never rewrite).
  Tests: `engine/packages/brain-review/tests/`, `engine/apps/api/tests/test_reviews.py`
  (47 tests total across `brain-review`/`brain-security`/`test_reviews.py`).
- **Duplicate delivery is a no-op, not a second decision:** resubmitting the
  same decision (`event_sha256`) is recognized as a duplicate and does not
  create a second `ReviewDecision` row.
  Test: `test_resubmitting_the_same_decision_is_a_duplicate_no_op`.
- **Stale handling:** a decision submitted against a superseded assertion
  version is recorded and flagged `stale=True`, and is not applied — it is
  auditable, not silently dropped and not silently accepted.
- **Unresolved evidence forces `BLOCKED`:** a decision cannot be `ACCEPT`ed or
  `CORRECT`ed against evidence the reviewer was not actually shown; it must
  carry `action=BLOCKED`, `reason_code=EVIDENCE_UNRESOLVED`, and produces no
  assertion (`brain_review.decisions.UnresolvedEvidenceRequiresBlocked`).
- **Out-of-scope reviewer behavior:** a reviewer with a real, verified
  credential but zero matching tenant/KB membership is denied identically to a
  cross-tenant reviewer — HTTP 404, never 403, and the audit event records the
  denial reason code (`no_membership` / `policy_denied`).

## Limitation

The wiring from an *accepted* review decision into an actual
`CanonicalCommitService.commit()` call is not built in this feature — a
`CORRECT` decision produces a corrected `Assertion`, not yet a
`canonical_fact_version`. That integration is F0002's scope (the review→commit
pipeline), not a gap in what this ADR asks F0001-S0004 to prove: the
*boundary* (a reviewer cannot commit canonical truth) is what's settled here,
and it holds regardless of who eventually calls the commit endpoint.

## Consequences

- The permission split, stale handling, duplicate-suppression, and
  unresolved-evidence-blocks-decision behaviors are locked contracts other
  features build on (F0002's review→commit pipeline, F0018's expanded
  permission catalog).
- The isolation and edition-capability findings this record originally owed are withdrawn with ADR-0034; reference R3 no longer applies.

## References

- `planning-mds/architecture/master-blueprint.md` sections 111.2, 116, 125
- Related: [ADR-0057](ADR-0057-nebula-owns-the-native-evidence-review-panel.md), [ADR-0037](ADR-0037-human-corrections-append-they-do-not-rewrite-evidence.md), [ADR-0052](ADR-0052-delegated-agents-and-review-authority.md)
