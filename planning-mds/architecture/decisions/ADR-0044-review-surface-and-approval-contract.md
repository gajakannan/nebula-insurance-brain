# ADR-0044: Review Surface and Approval Contract

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Revised:** 2026-09-08 — the decision to settle no longer includes selecting a Label Studio edition; [ADR-0057](ADR-0057-nebula-owns-the-native-evidence-review-panel.md) settled the surface question by moving review into Nebula. What remains open, and what this record still owes, is the approval contract.
**Deciders:** Pending; becomes Accepted only when the stated tests, owners, and release gates are satisfied (master blueprint section 106 decision posture)
**Settled by:** F0001-S0004 (native review round trip with lineage); results recorded by F0001-S0007
**Source:** `planning-mds/architecture/master-blueprint.md` sections 111.2, 116, 125

## Context

Proposed in the master blueprint pre-build requirements to settle two things: which Label Studio edition the governed review loop would run on, and how annotation is separated from canonical approval.

The first half is closed. ADR-0057 removed Label Studio; the review surface is the native Nebula Review Panel, so there is no edition to select and no external annotation event to trust.

The second half is untouched by that change and is the harder one. Moving the surface in-house removes the webhook trust boundary but does not by itself separate a reviewer confirming what the PDF says from a reviewer deciding that a document governs a policy term. Section 111.2 draws that line; nothing yet enforces it.

Example and reference: stale reviewer correction; section 111.2.

## Decision

Pending. The decision to settle is: **annotation, adjudication, and business approval are separate authorities, enforced separately.**

Specifically, what F0001-S0004 must settle:

- The permission split across `review:annotate`, `review:adjudicate`, and `review:approve`, and which of them the Review Panel can exercise at all. Submitting a decision must not be able to commit canonical truth.
- Stale handling: a decision submitted against a superseded assertion version is recorded and attributed, and is not applied.
- Concurrent correction: two reviewers correct the same assertion differently; both submissions stay auditable and the second does not silently overwrite the first accepted result.
- Reason codes, escalation, and which high-impact disputes require a second review.
- The review-routing policy: low confidence alone is not the trigger. Risk-based sampling of high-confidence results, critical missing fields, package incompleteness, impossible values, and conflicts with trusted sources all route to review.

## Consequences

- Until accepted, implementation treats master blueprint sections 111.2 and 125 as requirements to prove, not as settled contracts.
- Acceptance requires recording the executed test, the owner, and the release gate in this record.
- The isolation and edition-capability findings this record originally owed are withdrawn with ADR-0034; reference R3 no longer applies.

## References

- `planning-mds/architecture/master-blueprint.md` sections 111.2, 116, 125
- Related: [ADR-0057](ADR-0057-nebula-owns-the-native-evidence-review-panel.md), [ADR-0037](ADR-0037-human-corrections-append-they-do-not-rewrite-evidence.md), [ADR-0052](ADR-0052-delegated-agents-and-review-authority.md)
