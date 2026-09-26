# ADR-0067: Automation Gated by Unrecallable Impact, Human Precedent, and a Fuse

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-25
**Direction authorized by:** Operator, 2026-09-25. Formal acceptance waits for the proof gates below.
**Would refine:** [ADR-0044](ADR-0044-review-surface-and-approval-contract.md), [ADR-0047](ADR-0047-controlled-learning-and-reinterpretation.md), and [ADR-0052](ADR-0052-delegated-agents-and-review-authority.md); gives the section 64 Execution Gate its first concrete check
**Source:** Master blueprint sections 53, 64, 75, 110.5, 111. Informed by Utopia decisions 0025, 0026, 0027, 0028, and 0043 (see References).

## Context

Section 64 lists what the Execution Gate is meant to consult, and section 53 says merges are reversible. Neither addresses what Utopia found in production use.

**Undo restores the graph, not what the graph was read into.** Suppose an automated merge of "Acme" and "Acme Corp" is reverted on Monday. Meanwhile it had already:

- produced a derived assessment;
- opened a conflict someone looked at;
- been cited in a chat answer;
- entered an export.

None of that is recalled by the revert.

Confidence is the wrong axis for this. A 0.93-confident merge that touches nothing downstream is cheap to undo. A 0.99-confident merge that an F0065 assessment rests on is not.

Utopia also found two other failure modes:

- An agent that learns from its own past decisions cites itself and grows more confident each round.
- Nothing stops automation that keeps being wrong.

## Proposed Decision

### 1. Hold automated changes whose effects cannot be recalled

This applies to every automatic change made without a person's decision:

- entity merges (F0017, F0027);
- automated resolution of review queue items (F0043);
- automatic promotion (F0042);
- agent-proposed actions (F0059).

Before applying such a change, the service computes its impact. Any one of the following holds the change for a person, whatever the confidence:

| Impact kind | Hold when |
|---|---|
| `CONFLICT` | Two values of a single-valued FactSlot would hold at the same valid-time moment in current recorded time. A succession is not a conflict (ADR-0064). |
| `DERIVED` | A live derived fact, assessment (F0065), or derivation (F0055) rests on an affected row |
| `CITED` | An affected entity or fact was cited in a conversation answer (F0037) or a decision-ledger entry (F0057) |
| `EXPORTED` | An affected row has left the Brain through an export or an external projection; opt-in per knowledge base |

The hold reason is recorded as `IMPACT_HOLD:<kind> <detail>`, for example `IMPACT_HOLD:DERIVED 3 assessments`. The UI presents it as a reason, not as doubt about the verdict.

**The recorded reason can reveal restricted content.** The impact computation runs with system authority, so it sees derived results, answers, and decisions the reviewer may not be allowed to see. A count or a kind can reveal that restricted content exists. Master blueprint §107.4, ADR-0042, and ADR-0053 forbid that. So:

- **The full detail** is stored in the automated-decision row and audit record, which follow the authorization of the underlying resources.
- **What a reviewer sees** is re-evaluated against that reviewer's current authorization at display time. The detail shows only impacts the reviewer may read.
- **When any contributing impact is not visible to the reviewer,** the reason shows only the generic `IMPACT_HOLD` ("held for a person; the change would affect content outside this view"), with no kind, count, or identifier. The hold still applies.
- **A reviewer without authority** over every affected resource cannot approve the held change. The item routes to a reviewer who has it (ADR-0044, ADR-0052).
- **Holds are computed the same way** whether or not the eventual reviewer can see the impacts, so whether a change is held reveals nothing either.

Decisions that only keep things apart (keep separate, keep both) are not gated, because the next decision undoes them and nothing outside the Brain is told.

### 2. Only human decisions are precedent

Automated deciders may read the knowledge base's review ledger as precedent: earlier decisions on these names, on either name, on this type pair, on reverted merges, and on this queue.

- **Only rows with a human actor count.** An agent's own decisions are never precedent.
- **Precedent contradicting a verdict blocks automatic application.** Agreeing precedent may lower the threshold by a configured amount.
- **Pairs already decided by a person** are applied as that person decided.
- **A precedent includes the reviewer's optional free-text `why`.** Reason codes remain for analytics. A free-text `why` is optional and never required, because a mandatory field teaches that people decide without reasons.
- **Verdict caches are keyed on the precedent set they were decided with** (ADR-0068).

### 3. Automated decisions act through the people's paths and can be reverted

- **Each automated decision is a row:** target, action, confidence, the model's sentence, the precedents shown, the tool trace, status, and the data needed to undo it.
- **It calls the same service function a person's decision calls,** so the graph ends up in the same shape.
- **A person can accept, override, or revert it.** An override becomes a precedent.

### 4. A fuse turns automation off

Per knowledge base and automation type, a configured number of reverts of automatic actions within a window turns that automation off. The default is two within seven days. Tripping the fuse:

- raises an alert;
- writes an audit event with a system actor;
- requires a person to re-enable it.

### 5. Defaults differ from Utopia

Every automation type is **off by default** per knowledge base. It is enabled only after its agreement rate has been measured against human decisions on the Golden Corpus (F0026 and the F0043 gate).

## Consequences

- **F0027 and F0043** implement the impact computation, the precedent reading, automated-decision rows, and the fuse.
- **F0059** reuses the impact check as its first concrete gate.
- **F0022 and F0043** capture the optional `why` beside reason codes.
- **F0037 and F0057** record which entities and facts an answer or decision cited, so `CITED` is computable.

## Proof gates before acceptance

- **A confident merge that an F0065 assessment rests on** is held with `IMPACT_HOLD:DERIVED`. The same merge with nothing downstream applies.
- **A reviewer without access** to the assessment behind a hold sees only the generic `IMPACT_HOLD` reason, with no kind, count, or identifier, and cannot approve the change. A reviewer with access sees the detail. The audit record keeps the full detail under the assessment's authorization.
- **A merge that would put two legal names on one entity at the same moment** is held with `CONFLICT`. A dated rename succession is not held.
- **An agent's own decision** never appears as precedent. A person's contrary decision blocks the next automatic verdict on the same pair.
- **Two reverts within the window** disable the automation and produce the alert and audit event.
- **Measured on a labelled set:** agreement rate, share decided automatically, wrong-merge count, and revert rate. Report these before any automation is enabled.

## References

Utopia at commit [`b3919ca`](https://github.com/deeplethe/utopia/tree/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a):

- [0027 — An automatic merge is gated by what it can undo](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0027-an-automatic-merge-is-gated-by-what-it-can-undo.md)
- [0025 — Governance reads the ledger before it decides](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0025-governance-reads-the-ledger-before-it-decides.md)
- [0026 — A decision records why](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0026-a-decision-records-why.md)
- [0028 — The adjudicator looks before it asks](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0028-the-adjudicator-looks-before-it-asks.md)
- [0043 — Every review queue is governed](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0043-every-review-queue-is-governed.md)
- [design/governance](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/design/governance.md)

Worked and boundary examples: [EX-SEM-009](../../examples/statements-time-and-governance.md#automation-and-impact).
